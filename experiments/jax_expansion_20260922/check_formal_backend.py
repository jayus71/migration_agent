"""Independent healthy controls for trusted JAX differentiation and optimizers.

These controls are outside the natural source pool and never enter repair rates.
"""
import json
from pathlib import Path
import sys
import numpy as np
import torch
from formal_runner import dump,Evaluator,runtime

BASE=Path(__file__).resolve().parent
RUN=BASE/'natural12_v1'
PYTHON=Path('/media/main/whj/miniconda3/envs/torchax311/bin/python')


def main():
    runtime(RUN);torch.set_num_threads(1);rows=[]
    for kind in ('sgd','adam'):
        task='backend_'+kind;workspace=RUN/'backend_controls'/task/'workspace'
        (workspace/'inputs').mkdir(parents=True,exist_ok=False);(workspace/'scratch_tests').mkdir()
        (workspace/'source.py').write_text('import torch\n# Independent float64 Linear(3,2) MSE optimizer control.\n')
        (workspace/'candidate.py').write_text('def forward(parameters, buffers, batch, task):\n    return batch["x"] @ parameters["weight"].T + parameters["bias"], buffers\n')
        cfg={'type':'SGD','learning_rate':0.01,'momentum':0.9} if kind=='sgd' else {'type':'Adam','learning_rate':0.001,'betas':[0.9,0.999],'epsilon':1e-8}
        dump(workspace/'task.json',{'task':task,'optimizer':cfg,'thresholds':{'atol':1e-7,'rtol':1e-5}})
        for seed in (8101,8102,8103):
            torch.manual_seed(seed);model=torch.nn.Linear(3,2).double()
            opt=torch.optim.SGD(model.parameters(),lr=0.01,momentum=0.9) if kind=='sgd' else torch.optim.Adam(model.parameters(),lr=0.001,eps=1e-8)
            a=lambda x:x.detach().numpy().copy()
            public={'p:'+k:a(v) for k,v in model.named_parameters()};ref={'initial:'+k:v.copy() for k,v in public.items()}
            for step in range(3):
                x,y=torch.randn(4,3,dtype=torch.float64),torch.randn(4,2,dtype=torch.float64)
                public[f'batch:{step}:x']=a(x);public[f'batch:{step}:y']=a(y)
                opt.zero_grad();out=model(x);loss=torch.nn.functional.mse_loss(out,y);loss.backward()
                old={k:a(v) for k,v in model.named_parameters()};grad={k:a(v.grad) for k,v in model.named_parameters()};opt.step()
                ref[f'{step}:loss']=a(loss);ref[f'{step}:outputs:0']=a(out)
                for k,v in model.named_parameters():
                    ref[f'{step}:gradients:{k}']=grad[k];ref[f'{step}:parameters:{k}']=a(v);ref[f'{step}:updates:{k}']=a(v)-old[k]
            np.savez_compressed(workspace/'inputs'/f'{seed}.npz',**public)
            folder=RUN/'private_reference'/task;folder.mkdir(parents=True,exist_ok=True)
            np.savez_compressed(folder/f'{seed}.npz',**ref)
        evaluator=Evaluator(RUN,task,workspace,workspace.parent/'evidence',PYTHON)
        for seed in (8101,8102,8103):
            result=evaluator.paired(seed);rows.append({'optimizer':kind,**result});dump(RUN/'backend_controls.json',rows)
            print(json.dumps({'optimizer':kind,'seed':seed,'accepted':result['accepted'],'observation':result['observation']}),flush=True)
    if not all(r['accepted'] for r in rows):raise RuntimeError('Healthy backend control failed')
    dump(RUN/'backend_controls_passed.json',{'passed':True,'controls':6,'scope':'independent float64 linear MSE, three steps, three seeds, SGD momentum and Adam; not natural model acceptance'})


if __name__=='__main__':main()
