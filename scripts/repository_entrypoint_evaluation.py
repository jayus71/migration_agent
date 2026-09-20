"""Our repository controller's execution coverage, separate from frozen pilot scoring."""
import json
from pathlib import Path
from repository_timeseries_pilot import Evaluator,ROOT,RUN,TARGET_PY,read,save,hashes
from autofix.autonomous.sandbox import run_isolated


class RepositoryEvaluator(Evaluator):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.entry_calls=0;self.entry_cache={}
    def entrypoints(self):
        key=json.dumps(hashes(self.workspace/'target'),sort_keys=True)
        if key in self.entry_cache:return self.entry_cache[key]
        self.entry_calls+=1
        folder=self.evidence/('entrypoints_%04d'%self.entry_calls);folder.mkdir(parents=True)
        outcomes={}
        runtime=self.workspace/'.runtime';runtime.mkdir(exist_ok=True)
        for kind in ('notebook','snippets'):
            out=runtime/('entrypoints_%04d_%s.json'%(self.entry_calls,kind))
            args=['--worker',str(self.workspace/'target'),'--out',str(out)]+(['--snippets'] if kind=='snippets' else [])
            proc=run_isolated(self.workspace,TARGET_PY,ROOT/'scripts/audit_timeseries_notebooks.py',timeout=240,
                 extra_reads=[str(ROOT/'scripts'),str(ROOT/'autofix')],args=args)
            save(folder/(kind+'_execution.json'),proc)
            result=read(out) if out.exists() else {'status':'infrastructure_error','error':proc['stdout'][-4000:]}
            save(folder/(kind+'.json'),result)
            outcomes[kind]=result
        result={'accepted':all(r['status']=='passed' for r in outcomes.values()),'entrypoints':outcomes}
        self.entry_cache[key]=result
        return result
    def tool(self,args):
        if args.get('test')=='entrypoints':return self.entrypoints()
        return super().tool(args)
    def complete_repository(self):
        core=self.evaluate()
        confirmations=[self.evaluate(seed=s,full=False) for s in (202,303)] if core['accepted'] else []
        entries=self.entrypoints()
        accepted=core['accepted'] and all(r['accepted'] for r in confirmations) and entries['accepted']
        return {'accepted':accepted,'core':core,'confirmations':confirmations,'entrypoints':entries,
                'observation':{**core['observation'],'entrypoints':entries,'complete_repository_accepted':accepted}}
