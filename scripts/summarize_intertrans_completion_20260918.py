"""Reconcile frozen N18 outcomes and exact provider usage without inference."""
import collections
import csv
import hashlib
import json
from pathlib import Path

BASE = Path('/media/main/whj/projects/torch4ms')
ROOT = BASE / 'intertrans-completion-20260918'
OLD = BASE / 'ascend-torch4ms-n18-348e8cd/artifacts/n18_training/intertrans'
FIELDS = ['prompt_tokens', 'completion_tokens', 'total_tokens', 'reasoning_tokens',
          'prompt_cache_hit_tokens', 'prompt_cache_miss_tokens']


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def usage(root):
    records = []
    for path in sorted(root.glob('*/usage.jsonl')):
        for number, line in enumerate(path.read_text().splitlines(), 1):
            record = json.loads(line)
            raw = record.get('usage') or {}
            response = record.get('response') or {}
            if response.get('usage'):
                assert raw == response['usage'], 'Saved usage differs from provider response'
            if response.get('id'):
                assert record.get('response_id') == response['id']
            choice = (response.get('choices') or [{}])[0]
            content = choice.get('message', {}).get('content') or ''
            records.append(dict(task=path.parent.name, file=str(path), line=number,
                response_id=record.get('response_id'), model=record.get('model'),
                prompt_tokens=raw.get('prompt_tokens'), completion_tokens=raw.get('completion_tokens'),
                total_tokens=raw.get('total_tokens'),
                reasoning_tokens=raw.get('completion_tokens_details', {}).get('reasoning_tokens'),
                prompt_cache_hit_tokens=raw.get('prompt_cache_hit_tokens'),
                prompt_cache_miss_tokens=raw.get('prompt_cache_miss_tokens'),
                finish_reason=choice.get('finish_reason'), content_chars=len(content),
                content_sha256=digest(content), valid_service_response=bool(
                    record.get('response_id') and response.get('choices') and not response.get('error'))))
    ids = [r['response_id'] for r in records]
    assert all(ids) and len(ids) == len(set(ids)), 'Usage records need reconciliation'
    for r in records:
        if all(r[k] is not None for k in FIELDS[:3]):
            assert r['total_tokens'] == r['prompt_tokens'] + r['completion_tokens']
    return records


def totals(records):
    missing = {k: sum(r[k] is None for r in records) for k in FIELDS}
    return dict(calls=len(records), **{k: None if missing[k] else sum(r[k] for r in records)
        for k in FIELDS}, missing_fields=missing,
        known_subtotals={k: sum(r[k] for r in records if r[k] is not None) for k in FIELDS})


def errors(edge):
    return '\n'.join(t.get('actual_output', '') for t in edge.get('unit_tests', []))


def environment_error(text):
    return any(s in text for s in ['ModuleNotFoundError', 'ImportError:', 'infrastructure_error',
        'Cannot connect to the Docker daemon', 'No space left on device', 'libGL.so', 'libgomp.so'])


def main():
    current, historical = usage(ROOT / 'intertrans'), usage(OLD)
    assert not ({r['response_id'] for r in current} & {r['response_id'] for r in historical})
    freeze = json.loads((ROOT / 'freeze.json').read_text())
    rows = []
    for path in sorted((ROOT / 'intertrans').glob('*/result.json')):
        row = json.loads(path.read_text())
        task = row['task']
        assert task in freeze['sources'] and path.parent.name == task
        if row['status'] == 'evaluated':
            assert [s['seed'] for s in row['seeds']] == [101, 202, 303]
            assert row['passed'] == all(s['passed'] for s in row['seeds'])
        costs = [r for r in current if r['task'] == task]
        response_path = path.parent / 'response.json'
        response = json.loads(response_path.read_text()) if response_path.exists() else {}
        edges = [e for r in response.get('translation_responses', [])
                 for p in r.get('paths', []) for e in p.get('translation_edges', [])]
        generated = [e for e in edges if e.get('status') != 'SKIPPED_PARENT_FAILED']
        # Frozen single-worker search emits the direct edge, intermediary, then indirect edge.
        mapping_ok = len(costs) == len(generated) and bool(generated)
        evidence = []
        for e, c in zip(generated, costs):
            matches = digest(e.get('inference_output', '')) == c['content_sha256']
            mapping_ok = mapping_ok and matches and c['valid_service_response']
            evidence.append(dict(edge_id=e['edge_id'], response_id=c['response_id'],
                content_matches=matches, finish_reason=c['finish_reason'],
                content_chars=c['content_chars']))
        replayed, unresolved, native_environment, successful = [], [], [], []
        for edge in edges:
            if edge.get('target_language') != 'Python':
                continue
            effective = edge
            if environment_error(errors(edge)):
                native_environment.append(edge['edge_id'])
            replay = ROOT / 'environment_replay' / task / str(edge['edge_id']) / 'native_response.json'
            second = ROOT / 'environment_replay_round2' / task / str(edge['edge_id']) / 'native_response.json'
            if second.exists():
                replay = second
            if replay.exists():
                effective = json.loads(replay.read_text())['verification_responses'][0]
                replayed.append(dict(edge_id=edge['edge_id'], status=effective.get('status'),
                    passed=bool(effective.get('unit_tests')) and all(t.get('passed', False) for t in effective['unit_tests']),
                    record=str(replay)))
            if environment_error(errors(effective)):
                unresolved.append(edge['edge_id'])
            if effective.get('unit_tests') and all(t.get('passed', False) for t in effective['unit_tests']):
                successful.append(edge['edge_id'])
        extraction = any(e.get('status') == 'FAILED_NO_EXTRACTED' for e in edges)
        complete = row['status'] in ['evaluated', 'search_exhausted', 'generation_or_extraction_error']
        complete = complete and bool(edges) and not unresolved and mapping_ok
        accepted = row.get('passed') if row['status'] == 'evaluated' else False
        attribution = 'native_method_failure'
        if extraction:
            attribution = 'native_output_budget_or_extraction_failure' if mapping_ok else 'unresolved_generation_infrastructure'
        if successful and row['status'] != 'evaluated':
            full = ROOT / 'environment_replay' / task / 'selection.json'
            second = ROOT / 'environment_replay_round2' / task / 'selection.json'
            if second.exists():
                full = second
            if full.exists():
                selected = json.loads(full.read_text())
                assert selected['selected_edge_id'] == successful[0]
                assert [s['seed'] for s in selected['seeds']] == [101, 202, 303]
                accepted = selected['passed']
                attribution = 'environment_replay_evaluated'
            else:
                complete, accepted, attribution = False, None, 'pending_replay_selection_and_hidden_seeds'
        if unresolved:
            attribution = 'unresolved_environment'
        if not complete:
            accepted = None
        elif accepted:
            attribution = 'accepted_after_environment_replay' if replayed else 'native_accepted'
        rows.append(dict(task=task, status=row['status'], native_passed=row.get('passed'),
            accepted=accepted, valid_outcome=complete, attribution=attribution,
            native_edge_statuses=dict(collections.Counter(e.get('status') for e in edges)),
            usage=totals(costs), seeds=row.get('seeds'), result_path=str(path),
            native_environment_edges=native_environment, environment_replays=replayed,
            unresolved_environment_edges=unresolved, response_usage_reconciled=mapping_ok,
            response_usage_evidence=evidence,
            finish_reasons=dict(collections.Counter(str(r['finish_reason']) for r in costs)),
            result_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    completed_tasks = {r['task'] for r in rows}
    assert len(completed_tasks) == len(rows)
    assert completed_tasks <= freeze['sources'].keys()
    all_valid = len(rows) == 18 and all(r['valid_outcome'] for r in rows)
    accepted = sum(r['accepted'] is True for r in rows)
    result = dict(expected=18, completed=len(rows), valid_outcomes=sum(r['valid_outcome'] for r in rows),
        accepted=accepted, acceptance_rate=accepted / 18 if all_valid else None,
        all_valid=all_valid, status_counts=dict(collections.Counter(r['status'] for r in rows)),
        attribution_counts=dict(collections.Counter(r['attribution'] for r in rows)),
        current_usage=totals(current), completed_usage=totals([r for r in current if r['task'] in completed_tasks]),
        historical_incomplete_usage=totals(historical), cumulative_usage=totals(current + historical),
        usd_cost=None, usd_cost_note='Token usage is exact; no verified provider billing rate or invoice is archived.',
        rows=rows, full_program_certified=False)
    (ROOT / 'paper_results.json').write_text(json.dumps(result, indent=2))
    fields = ['task', 'status', 'native_passed', 'accepted', 'valid_outcome', 'attribution']
    with (ROOT / 'paper_results.csv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields + FIELDS[:3] + ['calls'])
        writer.writeheader()
        for row in rows:
            writer.writerow({**{k: row[k] for k in fields},
                             **{k: row['usage'][k] for k in FIELDS[:3] + ['calls']}})
    (ROOT / 'usage_ledger.json').write_text(json.dumps(dict(current=current, historical=historical), indent=2))
    print(json.dumps({k: v for k, v in result.items() if k not in ['rows']}, indent=2))


if __name__ == '__main__':
    main()
