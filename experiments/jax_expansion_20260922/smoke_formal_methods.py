"""Zero-API native lifecycle smoke on an independent healthy linear control."""
import json
from pathlib import Path
import shutil
import sys
from formal_runner import runtime,dump

BASE=Path(__file__).resolve().parent
SOURCE=BASE/'natural12_v1'
RUN=BASE/'formal_methods_smoke_v1'


def main():
    RUN.mkdir(exist_ok=False)
    for name in ('code_snapshot','public_backend'):
        shutil.copytree(SOURCE/name,RUN/name)
    shutil.copytree(SOURCE/'private_reference/backend_sgd',RUN/'private_reference/backend_sgd')
    public=RUN/'private_inputs/backend_sgd'
    shutil.copytree(SOURCE/'backend_controls/backend_sgd/workspace',public,ignore=shutil.ignore_patterns('.runtime','scratch_tests'))
    (public/'source.py').write_text('import torch\ndef forward(parameters, buffers, batch, task):\n    return torch.nn.functional.linear(batch["x"], parameters["weight"], parameters["bias"]), buffers\n')
    contract=json.loads((public/'task.json').read_text());contract.update({'target_framework':'native JAX/Optax','source_framework':'pytorch','source_entry':'source.py','target_entry':'candidate.py'})
    dump(public/'task.json',contract)
    manifest=json.loads((SOURCE/'manifest.json').read_text());manifest.update({'max_repair_attempts':1,'max_calls':4,'max_seconds':120,'tasks':[{'anonymous_id':'backend_sgd','original_id':'backend_sgd'}]})
    dump(RUN/'manifest.json',manifest)
    experiment=runtime(RUN)
    from autofix.autonomous import agent
    def fake_client(request,timeout):
        content='Thought: Offline lifecycle smoke; the supplied candidate is unchanged.\n```bash\nsubmit\n```'
        if 'MatchFix' in str(request) or 'is_equivalent' in str(request):
            content='<final_response_format>{"is_equivalent": "true", "explanation": "Offline transport smoke, no real judgement"}</final_response_format>'
        return {'model':'offline-fake-transport','choices':[{'message':{'role':'assistant','content':content},'finish_reason':'stop'}],
                'usage':{'prompt_tokens':0,'completion_tokens':0,'total_tokens':0}}
    original=agent.AutonomousAgent
    class FakeAgent(original):
        def __init__(self,*args,**kwargs):super().__init__(*args,client=fake_client,**kwargs)
    agent.AutonomousAgent=FakeAgent
    rows=[]
    for method in ('autonomous_layered','direct_shared_tools','matchfix_full_orchestration','swe_native_isolated'):
        result=experiment.run_condition(RUN,'backend_sgd',method,Path(sys.executable));rows.append(result)
        dump(RUN/'smoke_results.json',rows)
        print(json.dumps({'method':method,'status':result['status'],'accepted':result['accepted'],'error':result.get('error'),'calls':result['budget']['calls'],'tokens':result['budget']['usage']['total_tokens']}),flush=True)


if __name__=='__main__':main()
