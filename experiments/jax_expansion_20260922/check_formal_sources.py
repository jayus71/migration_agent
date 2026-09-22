"""No API calls: execute every draft source workload for all three seeds."""
import json
from pathlib import Path
import time
import traceback
import torch
from formal_workloads import TASKS,build,batches,loss_and_outputs,contracts


def main():
    root=Path(__file__).resolve().parent/'formal_source_checks_v2'
    root.mkdir(exist_ok=False)
    torch.set_num_threads(1)
    (root/'contracts.json').write_text(json.dumps(contracts(),indent=2)+'\n')
    rows=[]
    for task in TASKS:
        for seed in (8101,8102,8103):
            row={'task':task,'seed':seed,'started':time.time(),'status':'running','steps':[]}
            try:
                model,opt=build(task,seed)
                row['parameter_shapes']={k:list(p.shape) for k,p in model.named_parameters()}
                row['parameter_count']=sum(p.numel() for p in model.parameters())
                row['buffer_shapes']={k:list(p.shape) for k,p in model.named_buffers()}
                for batch in batches(task,seed):
                    opt.zero_grad(); loss,output=loss_and_outputs(task,model,batch);loss.backward()
                    missing=[k for k,p in model.named_parameters() if p.grad is None]
                    if not torch.isfinite(loss) or not all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters()):
                        raise RuntimeError('Nonfinite loss/gradient')
                    opt.step()
                    row['steps'].append({'loss':float(loss.detach()),'missing_gradients':missing,
                                         'gradient_l2':{k:None if p.grad is None else float(p.grad.norm()) for k,p in model.named_parameters()},
                                         'buffers':{k:{'shape':list(p.shape),'l2':float(p.double().norm())} for k,p in model.named_buffers()}})
                row['status']='ok'
            except Exception as exc:
                row['status']='failed';row['error']=str(exc);row['traceback']=traceback.format_exc()
            row['elapsed_seconds']=time.time()-row['started'];rows.append(row)
            (root/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
            print(json.dumps({k:row[k] for k in ('task','seed','status','elapsed_seconds')}),flush=True)


if __name__=='__main__':main()
