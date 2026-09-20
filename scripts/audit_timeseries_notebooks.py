"""Post-run notebook execution audit; never edits candidates or changes frozen results."""
from __future__ import annotations
import argparse
from datetime import date,timedelta
import json
from pathlib import Path
import subprocess
import sys
import traceback

from repository_timeseries_pilot import RUN,ROOT,TARGET_PY,SOURCE_PY,hashes,read,save


def worker(repository,source,snippets=False):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import alpha_vantage.timeseries
    sys.path.insert(0,str(repository))
    if source:
        import torch
        torch.set_num_threads(1);torch.manual_seed(101)
        events={}
    else:
        from repository_timeseries_worker import block_torch
        block_torch()
        import mindspore as ms
        ms.set_context(mode=ms.PYNATIVE_MODE,device_target='CPU');ms.set_seed(101)
        events={'native_autodiff_calls':0}
        original=ms.value_and_grad
        def observe(*args,**kwargs):
            fn=original(*args,**kwargs)
            def call(*xs,**kw):
                value,gradients=fn(*xs,**kw)
                events['native_autodiff_calls']+=1
                if not all(np.isfinite(g.asnumpy()).all() for g in gradients):raise ValueError('Nonfinite gradients')
                return value,gradients
            return call
        ms.value_and_grad=observe;ms.ops.value_and_grad=observe
    from repository_timeseries_worker import prices
    values=prices(101)
    data={(date(2020,1,1)+timedelta(days=i)).isoformat():{'5. adjusted close':str(v)} for i,v in reversed(list(enumerate(values)))}
    class Fixture:
        def __init__(self,*args,**kwargs):pass
        def get_daily_adjusted(self,*args,**kwargs):return data,{'fixture':'frozen synthetic prices'}
    alpha_vantage.timeseries.TimeSeries=Fixture
    original_grid=plt.grid
    def grid(*args,**kwargs):
        if 'b' in kwargs:kwargs['visible']=kwargs.pop('b')
        return original_grid(*args,**kwargs)
    plt.grid=grid
    if snippets:
        order=['install_dependencies','add_configs','get_market_data','normalize_input_data','split_train_validate',
               'pytorch_dataloader','define_lstm_model','model_training','model_eval','model_eval_zoomed_in','predict_future_prices']
        notebook={'cells':[{'cell_type':'code','source':(repository/'step_by_step_code_blocks'/(name+'.py')).read_text()} for name in order]}
    else:
        notebook=read(repository/'demo-predicting-stock-prices.ipynb')
    namespace={'__name__':'__main__'};completed=[];skipped=[]
    for index,cell in enumerate(notebook['cells']):
        if cell['cell_type']!='code':continue
        code=''.join(cell['source']);lines=[]
        for line in code.splitlines():
            if line.lstrip().startswith(('!','%')):
                stripped=line.lstrip()
                if stripped.startswith(('! pip install ','!pip install ','%pip install ','%matplotlib ')):
                    skipped.append({'cell':index,'line':line});continue
                raise RuntimeError('Unsupported notebook magic requires explicit environment handling: '+line)
            lines.append(line)
        exec(compile('\n'.join(lines),f'notebook:cell_{index}','exec'),namespace)
        completed.append(index)
    state=namespace
    if 'predicted_train' not in state:
        matches=[v for v in namespace.values() if isinstance(v,dict) and 'predicted_train' in v]
        if len(matches)==1:state=matches[0]
    if len(state['predicted_train'])!=128 or len(state['predicted_val'])!=32:raise ValueError('Incomplete notebook predictions')
    prediction=np.asarray(state['prediction'])
    if prediction.size!=1 or not np.isfinite(prediction).all():raise ValueError('Invalid notebook forecast')
    if len(plt.get_fignums())!=5:raise ValueError('Notebook must produce the five source plots')
    if not source and events['native_autodiff_calls']<200:raise ValueError('Missing native notebook training')
    return {'status':'passed','executed_cells':completed,'skipped_dependency_magic':skipped,'plots':len(plt.get_fignums()),
            'forecast':prediction.tolist(),'observations':events}


def main():
    p=argparse.ArgumentParser();p.add_argument('--worker',type=Path);p.add_argument('--source',action='store_true');p.add_argument('--snippets',action='store_true');p.add_argument('--out',type=Path);p.add_argument('--method',action='append')
    args=p.parse_args()
    if args.worker:
        try:result=worker(args.worker,args.source,args.snippets)
        except Exception as exc:result={'status':'failed','error':str(exc),'traceback':traceback.format_exc()}
        args.out.write_text(json.dumps(result,indent=2));return
    from autofix.autonomous.sandbox import run_isolated
    results=[]
    methods=args.method or ['source','ladim','swe','matchfix','ladim_repository']
    for method in methods:
        root=RUN if method=='source' else RUN/'conditions'/method/'workspace'
        repository=root/('source' if method=='source' else 'target')
        if not repository.exists():continue
        audit_kind='snippet_audit' if args.snippets else 'notebook_audit'
        output=RUN/audit_kind/method;output.mkdir(parents=True,exist_ok=False)
        runtime=root/'.runtime';runtime.mkdir(exist_ok=True)
        resultfile=runtime/(audit_kind+'_'+method+'.json')
        before=hashes(repository)
        script=Path(__file__).resolve()
        command=['--worker',str(repository),'--out',str(resultfile)]+(['--source'] if method=='source' else [])+(['--snippets'] if args.snippets else [])
        proc=run_isolated(root,SOURCE_PY if method=='source' else TARGET_PY,script,timeout=240,
             extra_reads=[str(ROOT/'scripts'),str(ROOT/'autofix')],args=command)
        save(output/'execution.json',proc)
        r=read(resultfile) if resultfile.exists() else {'status':'infrastructure_error','log':proc['stdout'][-4000:]}
        r.update(method=method,files_unchanged=before==hashes(repository));save(output/'result.json',r);results.append(r)
    save(RUN/('snippet_audit' if args.snippets else 'notebook_audit')/'latest.json',results)
    print(json.dumps(results,indent=2))


if __name__=='__main__':main()
