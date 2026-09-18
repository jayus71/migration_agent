"""Run only frozen N18 InterTrans after concrete, current-checkout no-LLM gates."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

BASE = Path('/media/main/whj/projects/torch4ms')
REPO = BASE / 'ascend-torch4ms-intertrans-completion-20260918'
ROOT = BASE / 'intertrans-completion-20260918'
N18 = REPO / 'experiments/experiment_request_20260820/14_experiment_N_real_cross_language/n18'
ENGINE = BASE / 'intertrans-completion-engine-20260918/intertrans'
INDEX = BASE / 'ascend-torch4ms-n18-348e8cd/artifacts/evidence_index.json'
sys.path[:0] = [str(REPO), str(N18), str(N18 / 'pairing')]
from intertrans_adapter import prepare_assets, run
from source_prompt import source_text
from verify_candidate import save


def load(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    # This batch already has a frozen launcher; recovery must reuse saved responses.
    if (ROOT / 'freeze.json').exists():
        raise RuntimeError('Frozen completion already started; audit/replay existing outputs instead of restarting.')
    assert os.environ['AUTOFIX_LLM_MODEL'] == 'deepseek-v4-flash'
    assert int(os.environ['AUTOFIX_LLM_MAX_TOKENS']) == 131072
    assert not subprocess.check_output(['git', 'diff', 'HEAD', '--'], cwd=REPO)
    calibration = load(ROOT / 'calibration/summary.json')
    assert calibration['passed'] and len(calibration['rows']) == 108
    assert load(ROOT / 'isolation/summary.json')['passed']
    smoke = load(ROOT / 'native_smoke_02/summary.json')
    assert smoke['passed'] and smoke['visible_socket_calls'] >= 4
    protocol = load(N18 / 'protocol.json')
    index = load(INDEX)
    sources = {x['task_id']: x for x in load(N18 / 'sources/manifest.json')['sources']}
    upstream = BASE / 'external_baselines/InterTrans-84d2d43'
    build = ENGINE.parent
    for part in ['algo', 'common']:
        for source in (upstream / part).glob('*.go'):
            assert digest(source) == digest(build / part / source.name)
    freeze = dict(code_sha=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(),
        protocol_sha256=digest(N18 / 'protocol.json'), interface_sha256=digest(N18 / 'training_interface.txt'),
        source_manifest_sha256=digest(N18 / 'sources/manifest.json'), index_sha256=digest(INDEX),
        engine_sha256=digest(ENGINE), adapter_sha256=digest(N18 / 'pairing/intertrans_adapter.py'),
        launcher_sha256=digest(Path(__file__)), sources={t: sources[t]['sha256'] for t in protocol['task_ids']},
        calibration_sha256=digest(ROOT / 'calibration/summary.json'),
        isolation_sha256=digest(ROOT / 'isolation/summary.json'),
        native_smoke_sha256=digest(ROOT / 'native_smoke_02/summary.json'),
        candidate_image_id=subprocess.check_output(['docker', 'image', 'inspect',
            'intertrans-n/python:n18-torch271', '--format', '{{.Id}}'], text=True).strip(),
        method='InterTrans native graph search', model='deepseek-v4-flash', max_output_tokens=131072,
        reuse_count=0, required_count=18, prior_invalid_reason='All prior target edges FAILED_NO_EXTRACTED; 8192 completion tokens consumed by reasoning with empty extracted code.',
        search=dict(used_languages=['JavaScript','Python'], expansionIntermediaryNodes=3,
                    earlyStop=False, verifyIntermediateTranslations=False, useComputeEfficientMode=True),
        original_baseline_modified=False, transport_adaptations=['Docker execution', 'Raw response and usage logging'])
    if (ROOT / 'freeze.json').exists():
        assert load(ROOT / 'freeze.json') == freeze
    save(ROOT / 'freeze.json', freeze)
    prepare_assets(index, protocol['task_ids'], ROOT / 'intertrans_visible_assets')
    rows = []
    for task in protocol['task_ids']:
        case = ROOT / 'intertrans' / task
        print('INTERTRANS', task, flush=True)
        if (case / 'result.json').exists():
            row = load(case / 'result.json')
        else:
            row = run(task, Path(index['tasks'][task]['reference_root']), case, '',
                      source_text(sources[task]), ENGINE, ROOT / 'intertrans_visible_assets',
                      'intertrans-n/python:n18-torch271')
        rows.append(row)
        save(ROOT / 'summary.json', dict(expected=18, completed=len(rows), rows=rows,
             full_program_certified=False, scope=protocol['scope']))
        print(json.dumps(row), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
