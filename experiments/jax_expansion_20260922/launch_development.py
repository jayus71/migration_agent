"""Start one sequential API worker using the existing credential file."""
from pathlib import Path
import hashlib
import json
import os
import shlex
import subprocess

BASE = Path('/media/main/whj/projects/torch4ms/experiments/jax_expansion_20260922')
RUN = BASE / 'development_v2'
PYTHON = '/media/main/whj/miniconda3/envs/torchax311/bin/python'


def main():
    if not (RUN/'preflight_passed.json').exists():
        raise RuntimeError('Offline gate has not passed')
    if (RUN/'launch.json').exists():
        raise RuntimeError('Refusing duplicate launch')
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', JAX_PLATFORMS='cpu')
    for line in (Path.home()/'.autofix_llm_env').read_text().splitlines():
        text = line.strip()
        if text.startswith('export '): text = text[7:]
        if not text.startswith('AUTOFIX_LLM_') or '=' not in text: continue
        key, value = text.split('=', 1)
        tokens = shlex.split(value)
        if len(tokens) == 1: env[key] = tokens[0]
    if not env.get('AUTOFIX_LLM_API_KEY'): raise RuntimeError('Credential unavailable')
    manifest = json.loads((RUN/'manifest.json').read_text())
    assert manifest['model'] == 'deepseek-v4-flash'
    log = open(RUN/'development.log','x')
    process = subprocess.Popen([PYTHON, str(RUN/'runner.py'),'run','--run',str(RUN),'--python',PYTHON],
                               env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    record = {'pid':process.pid,'api_workers':1,'run':str(RUN),'log':str(RUN/'development.log'),
              'manifest_sha256':hashlib.sha256((RUN/'manifest.json').read_bytes()).hexdigest(),
              'launcher_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'conditions':4,'max_calls_per_condition':40,'max_submissions_per_condition':4}
    (RUN/'launch.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record))


if __name__=='__main__': main()
