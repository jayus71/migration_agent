"""Summarize frozen repository outcomes without rerunning models or acceptance."""
import argparse
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def summarize(root):
    rows = []
    for repository in ('timeseries', 'twotower'):
        for method in ('ladim', 'swe', 'matchfix'):
            folder = root / repository / 'conditions' / method
            if not (folder / 'result.json').exists():
                rows.append({'repository': repository, 'method': method, 'status': 'not_run'})
                continue
            result = read(folder / 'result.json')
            final = result.get('final', {})
            public = final.get('public', {})
            numeric = public.get('numeric', {})
            ledger = []
            for path in sorted((folder / 'evidence/agent').glob('call_*_response.json')):
                response = read(path)
                usage = response.get('usage', {})
                choice = (response.get('choices') or [{}])[0]
                ledger.append({'call': int(path.name.split('_')[1]), 'usage': usage,
                    'finish_reason': choice.get('finish_reason'), 'model': response.get('model')})
            stages = [attempt['stage'] for attempt in result.get('attempts', [])]
            checks = numeric.get('checks', {})
            rows.append({'repository': repository, 'method': method, 'status': result['status'],
                'accepted': result.get('accepted'), 'calls': result.get('calls'), 'usage': result.get('usage'),
                'end_to_end_tokens': result.get('end_to_end_tokens'), 'translation_usage': result.get('translation_usage'),
                'stop_reason': result.get('stop_reason'), 'stage_statuses': [s.get('status') for s in stages],
                'submissions': len(stages), 'source_unchanged': result.get('source_unchanged'), 'task_unchanged': result.get('task_unchanged'),
                'numeric_execution': numeric.get('execution'), 'numeric_accepted': numeric.get('accepted'),
                'numeric_failures': [k for k, v in checks.items() if not v] if checks else None,
                'numeric_check_outcomes': len(checks) if checks else None,
                'numerical_values_measured': len(numeric['measurements']) if numeric.get('measurements') else None,
                'workflow_accepted': (public.get('workflow') or {}).get('accepted'),
                'tests_accepted': (public.get('tests') or {}).get('accepted'),
                'entrypoints_accepted': (public.get('entrypoints') or {}).get('accepted'),
                'documentation_accepted': (public.get('documentation') or {}).get('accepted'),
                'confirmations': len(final.get('confirmations', [])), 'error': result.get('error'),
                'cache_hit_input_tokens': sum(x['usage'].get('prompt_cache_hit_tokens', 0) for x in ledger),
                'recorded_response_count': len(ledger), 'response_usage_total': sum(x['usage'].get('total_tokens', 0) for x in ledger)})
    development = []
    for path in sorted((root / 'development').glob('*/result.json')):
        result = read(path)
        development.append({'path': str(path.relative_to(root)), 'status': result['status'],
            'accepted': result.get('accepted'), 'calls': result.get('calls'), 'usage': result.get('usage'),
            'end_to_end_tokens': result.get('end_to_end_tokens'),
            'role': 'Preserved context-development run; final comparison uses the fixed implementation for both repositories.'})
    translation = read(root / 'twotower/translation/result.json')
    measured = [r for r in rows if r.get('usage')] + development
    ledger = {'new_model_calls': sum(r.get('calls', 0) for r in measured) + translation['calls'],
        'new_measured_tokens': sum(r['usage']['total_tokens'] for r in measured) + translation['usage']['total_tokens'],
        'new_completion_tokens': sum(r['usage']['completion_tokens'] for r in measured) + translation['usage']['completion_tokens'],
        'historical_translation_reused_tokens': 163661,
        'meaning': 'Physical new calls include all six final conditions, the retained development condition, and one new two-tower translation. Historical time-series translation is attributed to each end-to-end row but was not repeated.'}
    return {'rows': rows, 'development_runs': development, 'physical_ledger': ledger,
        'all_conditions_terminal': len(rows) == 6 and all(r['status'] not in ('running', 'not_run') for r in rows),
        'cost_definition': 'Each end-to-end row includes the full common translation cost and every charged repair call. Missing numerical measurements are null.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('root', type=Path)
    a = p.parse_args()
    result = summarize(a.root)
    (a.root / 'summary.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(result, ensure_ascii=False))
