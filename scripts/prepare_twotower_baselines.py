"""Prepare two native baseline integrations without changing prior runtimes."""
import difflib
import json
from pathlib import Path
import shutil
import hashlib

ROOT=Path('/media/main/whj/projects/torch4ms/ascend-torch4ms-repository-pilot-20260920')
RUN=ROOT/'experiments/repository_twotower_20260920'
DEST=RUN/'baseline_comparison'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')


def main():
    DEST.mkdir(exist_ok=False)
    runtime=DEST/'runtime'
    shutil.copytree(ROOT/'autofix',runtime/'autofix',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    path=runtime/'autofix/autonomous/swe_upstream.py';before=path.read_text()
    old='    if not ((root / "candidate.py").is_file() or (root / "target/project.py").is_file()) or not (root / "task.json").is_file():\n        raise ValueError("Required public files are missing")'
    new='''    task_path = root / "task.json"
    if not task_path.is_file():
        raise ValueError("Required public files are missing")
    declared = json.loads(task_path.read_text()).get("target_entry", "target/project.py")
    entry = Path(declared)
    if entry.is_absolute() or ".." in entry.parts:
        raise ValueError("Invalid declared target entry")
    if not ((root / "candidate.py").is_file() or (root / entry).is_file()):
        raise ValueError("Required public files are missing")'''
    assert before.count(old)==1
    after=before.replace(old,new);path.write_text(after)
    contract=json.loads((RUN/'task.json').read_text())
    contract.update(source_entry='source/train/train.py',target_entry='target/train/train.py')
    save(DEST/'task.json',contract)
    save(DEST/'preparation.json',{
        'original_runtime_hashes':{p.name:digest(p) for p in sorted((ROOT/'autofix/autonomous').glob('*.py'))},
        'baseline_runtime_hashes':{p.name:digest(p) for p in sorted((runtime/'autofix/autonomous').glob('*.py'))},
        'integration_diff':''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='original/swe_upstream.py',tofile='baseline_runtime/swe_upstream.py')),
        'integration_reason':'SWE workspace validation now resolves the declared entry; original hard-coded project.py is specific to the earlier time-series integration. Upstream algorithms remain unchanged.',
        'task_routing_only_additions':{'source_entry':contract['source_entry'],'target_entry':contract['target_entry']},
        'acceptance_contract_sha256':digest(RUN/'task.json'),'baseline_task_sha256':digest(DEST/'task.json'),
        'source_commit':json.loads((RUN/'manifest.json').read_text())['commit'],
        'initial_target':'Byte-identical copy of the frozen public PyTorch source; no generated or repaired LaDiM files supplied.',
        'budget':{'max_calls':40,'max_output_tokens':240000,'per_call_output_tokens':32768,'max_seconds':1800,'max_external_submissions':4},
        'model':'deepseek-v4-flash','thinking':'enabled','reasoning_effort':'high',
        'memory_policy':'native','baseline_prompt_policy':'Preserve native prompts, history processing and parser/retry behavior; no added prefix rewriting or repository planning.',
    })
    print('Prepared isolated baseline runtime and public entry metadata; no API requests.')


if __name__=='__main__':main()
