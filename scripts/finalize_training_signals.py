"""Audit the complete measured training-signal grid and archive its evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    root, run = args.root.resolve(), args.run.resolve()
    last = None
    while not (run / 'dispatch_result.json').exists():
        path = run / 'progress.json'
        if path.exists():
            data = json.loads(path.read_text())
            count = len(data['completed'])
            if count != last:
                print(json.dumps({'completed': count, 'planned': data['planned'], 'blocked': data['blocked']}), flush=True)
                last = count
        time.sleep(30)
    done = json.loads((run / 'dispatch_result.json').read_text())
    if done['blocked'] or done['not_started']:
        raise RuntimeError('Signal grid stopped with unfinished conditions')
    sys.path.insert(0, str(root))
    from report_maintext_ablations import report
    value = report(run)
    if any(not group['complete'] or group['ledger_mismatches'] or group['request_treatment_violations']
           for group in value['groups'].values()):
        raise ValueError('Signal grid is incomplete or has ledger/treatment discrepancies')
    plan = json.loads((run / 'plan.json').read_text())
    records, violations = [], []
    for variant in plan['variants']:
        for item in plan['tasks']:
            path = run / variant / 'conditions' / item['anonymous_id'] / 'autonomous_layered/result.json'
            row = json.loads(path.read_text())
            checks = row['full_final_confirmation']
            if len(checks) != 3 or [check['seed'] for check in checks] != [4101, 5101, 6101]:
                violations.append(str(path) + ': incomplete final seeds')
            accepted = all(check['accepted'] for check in checks)
            if row['accepted'] != accepted:
                violations.append(str(path) + ': final score differs from full confirmation')
            backend = [check['observation']['target_backend_observed'] for check in checks]
            if accepted and not all(backend):
                violations.append(str(path) + ': accepted without target backend')
            agent = path.parent / 'evidence/agent'
            unknown = 0
            calls = 0
            for request in agent.glob('call_*_request.json'):
                calls += 1
                payload = json.loads(request.read_text())
                if payload['model'] != 'deepseek-v4-flash':
                    violations.append(str(request) + ': unexpected requested model')
                text = request.read_text()
                for hidden in ('full_evaluation', 'private_preparation', 'expected_signature'):
                    if hidden in text:
                        violations.append(str(request) + ': private evaluator field ' + hidden)
                response = request.with_name(request.name.replace('_request', '_response'))
                if not response.exists():
                    unknown += 1
                else:
                    response_data = json.loads(response.read_text())
                    unknown += any(type(response_data.get('usage', {}).get(key)) is not int
                                   for key in ('prompt_tokens', 'completion_tokens'))
                    if response_data.get('model') != 'deepseek-flash':
                        violations.append(str(response) + ': unexpected response model')
            recorded_unknown = row['budget']['usage']['unknown_usage_calls']
            if recorded_unknown != unknown:
                violations.append(str(path) + ': unknown usage accounting differs')
            if row['budget']['calls'] != calls:
                violations.append(str(path) + ': request count differs from ledger')
            records.append({'task': row['task'], 'variant': variant, 'model_family': item['model'],
                'private_construction': item['construction'], 'accepted': accepted,
                'controller_accepted': row['controller_accepted'], 'backend_observed': backend,
                'result_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    value.update(generated_at=datetime.now(timezone.utc).isoformat(), final_audit=records, violations=violations,
        interpretation='Four actual models, four declared program mutations, and four cumulative public-feedback settings. '
            'The visible checks control repair triggering and stopping; full three-seed checks score final acceptance. '
            'Additional scratch tests remain available. This is separate from the original three-fixture signal study.')
    destination = root / 'reports/training_signal16_final.json'
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(value, indent=2) + '\n')
    if violations:
        raise ValueError('Final signal audit has violations; see report')
    archive = root / 'archives/training_signal16_v2_complete'
    subprocess.run([sys.executable, str(root / 'archive_autonomous_recovery.py'),
                    '--source', str(run), '--output', str(archive)], check=True)
    (root / 'training_signal16_finalization.json').write_text(json.dumps({
        'finished_at': datetime.now(timezone.utc).isoformat(), 'complete': True, 'conditions': len(records),
        'report': str(destination), 'archive': str(archive), 'violations': []}, indent=2) + '\n')
    print(json.dumps({variant: {'accepted': group['accepted'], 'planned': group['planned']}
                      for variant, group in value['groups'].items()}), flush=True)


if __name__ == '__main__':
    main()
