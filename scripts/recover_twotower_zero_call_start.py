"""Archive a zero-call bootstrap setup error before the first paid trial."""
from pathlib import Path
import shutil
from run_repository_twotower import RUN, ROOT, read, save, digest

folder = RUN / 'condition'
r = read(folder / 'result.json')
assert r['status'] == 'infrastructure_error'
assert r['calls'] == 0 and r['usage']['total_tokens'] == 0
assert not list((folder / 'evidence/agent').glob('*_response.json'))
archive = RUN / 'zero_call_config_error'
archive.mkdir(exist_ok=False)
shutil.move(str(folder), str(archive / 'condition'))
shutil.copy2(RUN / 'manifest.json', archive / 'manifest.json')
shutil.copy2(RUN / 'run.log', archive / 'run.log')
manifest = read(RUN / 'manifest.json')
old = manifest['bootstrap_sha256']
manifest['bootstrap_sha256'] = digest(ROOT / 'scripts/repository_bootstrap.py')
manifest['pre_api_setup_correction'] = {
    'reason': 'Replace frozen AgentConfig instead of assigning one field; restore original configuration after generation.',
    'previous_bootstrap_sha256': old,
    'calls': 0, 'tokens': 0,
    'test': 'Three bootstrap tests pass using real frozen AgentConfig.',
    'protocol_change': False,
}
save(RUN / 'manifest.json', manifest)
print('Archived zero-call startup failure; corrected bootstrap frozen before any API request.')
