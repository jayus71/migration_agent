"""Zero-model repository integration checks before a paid pilot."""
import json
from pathlib import Path
import shutil
import sys
import tempfile

from repository_timeseries_pilot import ROOT,RUN,BASE,TARGET_PY,save
sys.path.insert(0,str(ROOT))
from autofix.autonomous.agent import AutonomousAgent,AgentConfig
from autofix.autonomous.tools import WorkspaceTools,ToolError
from autofix.autonomous.baselines import MatchFixFullOrchestration
from autofix.autonomous.swe_upstream import SWEAgentNative,_validate_workspace
from autofix.autonomous.sandbox import run_isolated


def no_model(*args,**kwargs):raise AssertionError('Offline check attempted a model call')


def main():
    folder=Path(tempfile.mkdtemp(prefix='repository_preflight_',dir=RUN))
    ws=folder/'workspace';ws.mkdir()
    shutil.copytree(RUN/'source',ws/'source');shutil.copy2(RUN/'task.json',ws/'task.json')
    (ws/'target').mkdir();(ws/'scratch_tests').mkdir()
    (ws/'target/project.py').write_text('"""Integration fixture; no target implementation."""\n')
    tool=WorkspaceTools(ws,lambda args:{'execution':'offline_fixture'},named_tests=('paired','workflow','public'),validate_syntax=True)
    checks={}
    checks['complete_source_listing']=len([n for n in tool._files() if n.startswith('source/') and n.endswith('.py')])==12
    checks['notebook_visible']='source/demo-predicting-stock-prices.ipynb' in tool._files()
    tool.execute('search',{'query':'LSTM'})
    checks['repository_search']=True
    try:tool.execute('edit',{'edits':[{'path':'source/project.py','old':'import numpy as np','new':'pass'}]})
    except ToolError:checks['source_readonly']=True
    tool.execute('edit',{'edits':[{'path':'target/extra.json','old':'','new':'{"value":1}\n'}]})
    checks['target_nonpython_edit']=json.loads((ws/'target/extra.json').read_text())=={'value':1}
    _validate_workspace(ws);checks['swe_repository_validation']=True
    agent=AutonomousAgent(tool,folder/'matchfix_log',config=AgentConfig(method='single'),client=no_model)
    adapter=MatchFixFullOrchestration(agent,upstream_root=BASE/'external_baselines/MatchFixAgent-66a52a5',python='/media/main/whj/miniconda3/envs/matchfixagent/bin/python')
    checks['matchfix_initialization']=adapter.initialize({}).status=='ready'
    fragment=adapter._fragment()
    checks['matchfix_actual_paths']=fragment['source_path']=='source/project.py' and fragment['target_path']=='target/project.py'
    checks['matchfix_no_reference_target']=fragment['ground_truth_target_function']==''
    agent2=AutonomousAgent(tool,folder/'swe_log',config=AgentConfig(method='single'),client=no_model)
    swe=SWEAgentNative(agent2,upstream_root=BASE/'external_baselines/SWE-agent-v1.1.0',python='/media/main/whj/miniconda3/envs/sweagent110/bin/python',target_python=TARGET_PY,vendor=BASE/'experiments/autonomous_verifier_20260917/swe_native_vendor')
    try:
        ready=swe.initialize({'execution':'offline preflight'})
        checks['swe_native_worker_started']=ready.status=='ready'
    finally:swe.close()
    scratch=ws/'scratch_tests/backend.py'
    scratch.write_text('import mindspore as ms\nimport numpy as np\nms.set_context(mode=ms.PYNATIVE_MODE, device_target="CPU")\np=ms.Parameter(ms.Tensor(np.array([1.],dtype=np.float32)))\nf=ms.value_and_grad(lambda x: ((p*x)**2).sum(), None, (p,))\nv,g=f(ms.Tensor(np.array([2.],dtype=np.float32)))\nassert abs(float(v.asnumpy())-4)<1e-6\nassert abs(float(g[0].asnumpy()[0])-8)<1e-6\nprint("native gradient observation ready")\n')
    proc=run_isolated(ws,TARGET_PY,scratch,timeout=90)
    save(folder/'native_backend.json',proc)
    checks['isolated_native_gradient_execution']=proc['returncode']==0
    checks['model_calls_zero']=agent.calls==agent2.calls==0
    save(RUN/'integration_checks.json',{'checks':checks,'passed':all(checks.values()),'evidence':str(folder)})
    print(json.dumps(checks,indent=2))
    if not all(checks.values()):raise RuntimeError('Repository integration preflight failed')


if __name__=='__main__':main()
