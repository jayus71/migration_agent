"""Read existing map-ablation or cumulative traces; never call a model."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import summarize_cumulative_component_ablations as common


def read(path):
    return json.loads(path.read_text())


def checks(repository, evaluation):
    training, retrieval, status, behavior, ts = common.expected_checks()
    public = evaluation.get('public', {}).get('numeric', {}).get('checks', {})
    if repository == 'twotower':
        return common.count(public, training + retrieval + status + behavior)
    seeds = {'public': public}
    for i, confirmation in enumerate(evaluation.get('confirmations', []), 1):
        seeds[f'confirmation_{i}'] = confirmation.get('observation', {}).get('numeric', {}).get('checks', {})
    observed = {f'{seed}:{key}': value for seed, values in seeds.items() for key, value in values.items()}
    return common.count(observed, [f'{seed}:{key}' for seed in ('public', 'confirmation_1', 'confirmation_2') for key in ts])


def analyze(root, conditions):
    rows = []
    for repo in ('timeseries', 'twotower'):
        for condition in conditions:
            folder = root / repo / 'conditions' / condition
            result_path = folder / 'result.json'
            if not result_path.exists():
                rows.append({'repository': repo, 'condition': condition, 'status': 'not_run'})
                continue
            result = read(result_path)
            evidence = folder / 'evidence/agent'
            metadata = {int(p.name.split('_')[1]): read(p) for p in evidence.glob('call_*_metadata.json')}
            counts = Counter()
            stages = {}
            selected = []
            edited_paths = set()
            for path in sorted(evidence.glob('event_*_tool.json')):
                event = read(path)['data']
                name = event.get('name')
                counts[name] += 1
                meta = metadata.get(event.get('call'), {})
                stage = f"{meta.get('stage')}:{meta.get('attempt')}"
                stages.setdefault(stage, Counter())[name] += 1
                if name in ('repository_map', 'plan_units', 'focus_unit', 'checkpoint_unit', 'edit', 'run_test'):
                    item = {'event': path.name, 'call': event.get('call'), 'stage': stage,
                            'name': name, 'arguments': event.get('arguments')}
                    outcome = event.get('result', {})
                    if isinstance(outcome, dict):
                        item['tool_ok'] = outcome.get('ok')
                    if name == 'edit' and isinstance(outcome, dict):
                        item['changed_files'] = [record['path'] for record in outcome.get('files', [])
                            if record.get('before_sha256') != record.get('after_sha256')]
                        edited_paths.update(item['changed_files'])
                    if name == 'repository_map':
                        inventory = event.get('result', {})
                        item.update(returned_keys=sorted(inventory), mapped_files=len(inventory.get('files', {})))
                    selected.append(item)
            responses = [read(p) for p in evidence.glob('call_*_response.json')]
            usage = [r.get('usage') for r in responses]
            request_paths = list(evidence.glob('call_*_request.json'))
            has_call_files = bool(request_paths)
            row = {key: result.get(key) for key in ('repository', 'condition', 'status', 'accepted', 'calls', 'usage', 'end_to_end_tokens', 'stop_reason', 'error', 'pid', 'started', 'finished')}
            row.update(result_sha256=hashlib.sha256(result_path.read_bytes()).hexdigest(),
                       evidence_scope='request_files_present' if has_call_files else 'summary_and_tool_events_only',
                       observed_metadata=len(metadata),
                       observed_requests=len(request_paths) if has_call_files else None,
                       observed_responses=len(responses) if has_call_files else None,
                       measured_response_tokens=sum(u.get('total_tokens', 0) for u in usage if isinstance(u, dict)) if has_call_files else None,
                       response_usage_missing=sum(not isinstance(u, dict) for u in usage) if has_call_files else None,
                       tool_counts=dict(counts), tool_counts_by_stage={k:dict(v) for k,v in stages.items()},
                       confirmed_edited_paths=sorted(edited_paths), trajectory=selected)
            row['progress'] = [{'submission': 0, 'calls': 0, 'repair_tokens': 0,
                                'accepted': result.get('initial', {}).get('accepted'),
                                'checks': checks(repo, result.get('initial', {}))}]
            for attempt in result.get('attempts', []):
                row['progress'].append({'submission': attempt['attempt'], 'calls': attempt['calls'],
                    'repair_tokens': attempt['usage']['total_tokens'], 'accepted': attempt['evaluation'].get('accepted'),
                    'checks': checks(repo, attempt['evaluation'])})
            if result.get('final'):
                row['final_checks'] = checks(repo, result['final'])
            rows.append(row)
    return {'rows': rows, 'definition': 'Fixed repositories, complete external acceptance. Check counts are descriptive and retain missing measurements; tool counts are actual execution events, not repeated tool messages in API prompts.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('--conditions', nargs='+', default=['full', 'no_automatic_map'])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.root, args.conditions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps([{k:r.get(k) for k in ('repository','condition','status','observed_requests','tool_counts')} for r in result['rows']], indent=2))
