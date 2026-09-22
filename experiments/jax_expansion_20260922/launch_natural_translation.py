"""One persistent translation worker, followed by initial common evaluation."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from formal_runner import check_hashes,sha,dump

BASE=Path(__file__).resolve().parent
RUN=BASE/'natural12_v2'
PYTHON='/media/main/whj/miniconda3/envs/torchax311/bin/python'


def main():
    if len(sys.argv)>1 and sys.argv[1]=='worker':
        subprocess.run([PYTHON,str(RUN/'formal_runner.py'),'translate','--run',str(RUN)],check=True)
        subprocess.run([PYTHON,str(RUN/'formal_runner.py'),'initial-check','--run',str(RUN),'--python',PYTHON],check=True)
        return
    if (RUN/'translation_launch.json').exists():raise RuntimeError('Refusing duplicate translation launch')
    check_hashes(RUN,'pretranslation_hashes.json')
    if not (RUN/'backend_controls_passed.json').exists():raise RuntimeError('Healthy backend gate required')
    source=json.loads((BASE/'formal_source_checks_v2/results.json').read_text())
    if len(source)!=36 or any(r['status']!='ok' for r in source):raise RuntimeError('Source gate incomplete')
    smoke=json.loads((BASE/'formal_methods_smoke_v1/smoke_results.json').read_text())
    if len(smoke)!=4 or any(r['status']=='infrastructure_error' for r in smoke):raise RuntimeError('Method integration smoke failed')
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',JAX_PLATFORMS='cpu',JAX_ENABLE_X64='true')
    for line in (Path.home()/'.autofix_llm_env').read_text().splitlines():
        text=line.strip()
        if text.startswith('export '):text=text[7:]
        if text.startswith('AUTOFIX_LLM_') and '=' in text:
            key,value=text.split('=',1);tokens=shlex.split(value)
            if len(tokens)==1:env[key]=tokens[0]
    if not env.get('AUTOFIX_LLM_API_KEY'):raise RuntimeError('Credential unavailable')
    process=subprocess.Popen([PYTHON,str(Path(__file__).resolve()),'worker'],env=env,
             stdout=open(RUN/'translation_and_initial_check.log','x'),stderr=subprocess.STDOUT,start_new_session=True)
    record={'pid':process.pid,'api_workers':1,'source_tasks':12,'max_initial_translation_calls':12,'max_output_tokens_per_call':16384,
            'manifest_sha256':sha(RUN/'manifest.json'),'pretranslation_hashes_sha256':sha(RUN/'pretranslation_hashes.json'),
            'launcher_sha256':sha(Path(__file__)),'log':str(RUN/'translation_and_initial_check.log'),
            'repair_suite_started':False}
    dump(RUN/'translation_launch.json',record);print(json.dumps(record))


if __name__=='__main__':main()
