"""Audit the saved natural-translation Tanh case; never execute an experiment.

Input is the locally downloaded, hash-manifested evidence snapshot. The output
keeps numerical observations and tool evidence without model reasoning traces.
"""

import argparse
import csv
import difflib
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def code_hashes(folder):
    return {str(p.relative_to(folder)): sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, default=Path('tmp/experiment-addition-review/case-evidence'))
    parser.add_argument('--output', type=Path, default=Path('docs/review-evidence/tanh-case-20260925'))
    args = parser.parse_args()
    root, out = args.evidence, args.output
    manifests = read(root / 'manifest.json') + read(root / 'workspace_manifest.json')
    for row in manifests:
        p = root / row['file']
        assert p.stat().st_size == row['size'] and sha(p) == row['sha256'], row['file']
    entries = {r['file']: r for r in manifests}
    selected = set()
    names = {'ladim': 'LaDiM', 'swe_native_isolated': 'SWE-agent', 'matchfix_full_orchestration': 'MatchFixAgent'}
    methods, ledgers, initial_codes, initial_observations = [], [], [], []
    source_hashes, task_hashes = [], []
    out.mkdir(parents=True, exist_ok=True)
    frozen_ladim = read(Path('output/maintext-ablations-20260918/recovery_final.json'))
    group = next(g for g in frozen_ladim['groups'] if g.get('study') == 'natural10_v3' and g.get('variant') == 'without_edit_format_feedback')
    frozen_baselines = read(Path('output/autonomous-verifier-20260917/autonomous_recovery_final.json'))
    for key, name in names.items():
        relative = Path('task_008') / key
        base = root / relative
        result_path = str(relative / 'result.json')
        result = read(base / 'result.json')
        selected.add(result_path)
        if key == 'ladim':
            frozen = next(r for r in group['rows'] if r['task'] == 'task_008')
        else:
            frozen_group = next(g for g in frozen_baselines['groups'] if g['benchmark'] == 'Natural10' and g['version'] == 'formal_v3' and g['method'] == key)
            frozen = next(r for r in frozen_group['conditions'] if r['task'] == 'task_008')
        assert entries[result_path]['remote_path'] == frozen['path']
        assert result['accepted'] == frozen['accepted']
        initial = code_hashes(base / 'evidence/initial_code')
        final = code_hashes(base / 'evidence/final_code')
        initial_codes.append(initial)
        initial_observations.append(result['initial']['observation'])
        changed = [f for f in sorted(initial.keys() | final.keys()) if initial.get(f) != final.get(f)]
        assert changed == (['torch4ms/ops/mtorch.py'] if key == 'ladim' else [])
        source_hashes.append(sha(base / 'workspace/source.py'))
        task_hashes.append(sha(base / 'workspace/task.json'))
        for filename in ['source.py', 'task.json']:
            selected.add(str(relative / 'workspace' / filename))
        usage = {k: 0 for k in ['prompt_tokens', 'completion_tokens', 'total_tokens']}
        calls = sorted((base / 'evidence/agent').glob('call_*_response.json'))
        assert len(calls) == result['budget']['calls']
        for number, p in enumerate(calls, start=1):
            response = read(p)
            assert int(p.name.split('_')[1]) == number
            u = response['usage']
            assert u['prompt_tokens'] + u['completion_tokens'] == u['total_tokens']
            for field in usage:
                usage[field] += u[field]
            ledgers.append({'method': name, 'call': number, 'prompt_tokens': u['prompt_tokens'], 'completion_tokens': u['completion_tokens'], 'total_tokens': u['total_tokens'], 'cumulative_tokens': usage['total_tokens'], 'response_sha256': sha(p)})
            selected.add(str(p.relative_to(root)))
        assert all(result['budget']['usage'][k] == v for k, v in usage.items())
        assert result['budget']['usage']['unknown_usage_calls'] == 0
        confirmations = [e for a in result['attempts'] for e in a['confirmation']]
        evaluations = [result['final']] + confirmations
        if key == 'ladim':
            assert [e['seed'] for e in evaluations] == [42, 1042, 2042]
            assert all(e['accepted'] and all(e['observation']['acceptance']['checks'].values()) for e in evaluations)
            patch_file = 'torch4ms/ops/mtorch.py'
            before, after = [base / 'evidence' / folder / patch_file for folder in ['initial_code', 'final_code']]
            patch = ''.join(difflib.unified_diff(before.read_text().splitlines(True), after.read_text().splitlines(True), fromfile='initial/' + patch_file, tofile='repaired/' + patch_file))
            (out / 'repair.patch').write_text(patch)
        methods.append({'method': name, 'calls': len(calls), 'usage': usage, 'accepted': result['accepted'], 'attempts': len(result['attempts']), 'stage_statuses': [a['stage']['status'] for a in result['attempts']], 'wall_time_seconds': result['wall_time_sec'], 'changed_production_files': changed, 'initial': result['initial'], 'final': result['final'], 'confirmations': confirmations, 'initial_code_sha256': initial, 'final_code_sha256': final, 'result_source': entries[result_path]})
    assert initial_codes[0] == initial_codes[1] == initial_codes[2]
    assert initial_observations[0] == initial_observations[1] == initial_observations[2]
    assert len(set(source_hashes)) == len(set(task_hashes)) == 1
    pool = read(Path('data/experiments/09_experiment_I_real_translation/runs_real_core_v3/pool_audit.json'))
    pool_rows = next(v for v in pool.values() if isinstance(v, list) and any(isinstance(r, dict) and r.get('task_id') == 'I-08' for r in v))
    origin = next(r for r in pool_rows if r.get('task_id') == 'I-08')
    assert origin['no_fault_injection'] and origin['source_sha256'] == source_hashes[0]
    events = []
    for filename in ['event_00073_tool.json', 'event_00094_tool.json', 'event_00097_tool.json']:
        p = root / 'task_008/ladim/evidence/agent' / filename
        selected.add(str(p.relative_to(root)))
        event = read(p)
        events.append({'source': str(p.relative_to(root)), 'sha256': sha(p), 'event': event})
    assert events[0]['event']['data']['result']['returncode'] == 0
    assert events[1]['event']['data']['result']['ok']
    assert events[2]['event']['data']['result']['acceptance']['accepted']
    alternate = []
    for key, name in names.items():
        p = root / 'task_009' / key / 'result.json'
        r = read(p)
        selected.add(str(p.relative_to(root)))
        alternate.append({'method': name, 'calls': r['budget']['calls'], 'total_tokens': r['budget']['usage']['total_tokens'], 'accepted': r['accepted'], 'wall_time_seconds': r['wall_time_sec']})
    summary = {'schema': 'saved-tanh-case-audit-v1', 'reviewed_commit': 'f36bc62fb7f8d73d6f82c20f27f9f03edfee5d17', 'task': 'task_008', 'origin': origin, 'source_sha256': source_hashes[0], 'task_contract_sha256': task_hashes[0], 'verified_download_files': len(manifests), 'all_initial_code_files_identical': True, 'initial_code_file_count': len(initial_codes[0]), 'all_initial_observations_identical': True, 'cost_scope': 'All investigation and repair LLM calls on the saved initial translation, including unsuccessful stages; initial translation generation is outside this repair study.', 'methods': methods, 'token_reduction_percent': {m['method']: 100 * (1 - methods[0]['usage']['total_tokens'] / m['usage']['total_tokens']) for m in methods[1:]}, 'alternative_groupnorm_case': alternate}
    dump(out / 'summary.json', summary)
    dump(out / 'tool-evidence.json', events)
    dump(out / 'source-manifest.json', [entries[p] for p in sorted(selected)])
    with (out / 'calls.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(ledgers[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(ledgers)
    print(json.dumps({'verified_files': len(manifests), 'case_calls': len(ledgers), 'source_equal': True, 'candidate_and_library_equal': True, 'out': str(out)}))


if __name__ == '__main__':
    main()
