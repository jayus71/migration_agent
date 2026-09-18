"""Read provider failures and dispatch state without reading credentials."""
from collections import Counter
import json
from pathlib import Path

root = Path('/media/main/whj/projects/torch4ms/maintext-ablations-20260918')
for name in ('fixed50_v3', 'natural10_v3', 'signal12_v3'):
    run = root / name
    statuses, errors, variants = Counter(), Counter(), {}
    samples = {}
    for path in run.glob('*/conditions/*/*/result.json'):
        row = json.loads(path.read_text())
        statuses[row.get('status')] += 1
        key = path.relative_to(run).parts[0]
        counts = variants.setdefault(key, Counter())
        counts[row.get('status')] += 1
        counts['accepted'] += row.get('status') == 'completed' and row.get('accepted') is True
        if row.get('status') == 'infrastructure_error' and len(samples) < 4:
            samples[str(path.relative_to(run))] = {k: row.get(k) for k in ('error', 'reason', 'status')}
    for path in run.glob('*/conditions/*/*/evidence/agent/call_*_error.json'):
        row = json.loads(path.read_text())
        errors[str(row.get('http_status')) + ' ' + str(row.get('error'))[:400]] += 1
    dispatch = json.loads((run/'dispatch_result.json').read_text()) if (run/'dispatch_result.json').exists() else {}
    print(json.dumps({'run': name, 'statuses': dict(statuses), 'variants': variants, 'errors': dict(errors),
        'samples': samples, 'not_started': len(dispatch.get('not_started', [])),
        'blocking_errors': len(dispatch.get('blocking_errors', []))}))
