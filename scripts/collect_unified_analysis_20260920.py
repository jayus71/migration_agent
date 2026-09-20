"""Read saved results and verify their audited hashes; no execution or inference."""
import argparse
import hashlib
import json
from pathlib import Path


def compact(check):
    if not isinstance(check, dict):
        return check
    obs = check.get('observation', {})
    return {'accepted': check.get('accepted'), 'seed': check.get('seed'),
            'execution': obs.get('execution'), 'error': str(obs.get('error') or '')[:2500],
            'measurement': check.get('measurement'),
            'acceptance': obs.get('acceptance')}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    audit = json.loads(args.audit.read_text(encoding='utf-8-sig'))
    rows = []
    for row in audit['rows']:
        path = Path(row['result_path'])
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row['result_sha256'], path
        result = json.loads(path.read_text())
        rows.append({'id': row['id'], 'result_sha256': row['result_sha256'],
                     'status': result['status'], 'accepted': row['accepted'],
                     'initial': compact(result.get('initial')),
                     'initially_accepted': result.get('initially_accepted'),
                     'final': compact(result.get('final')),
                     'confirmation': [compact(c) for c in result.get('confirmation', [])],
                     'checks': [compact(c) for c in result.get('checks', [])],
                     'attempts': [{'attempt': a['attempt'], 'accepted': a['accepted'],
                                   'stage_status': a.get('stage', {}).get('status'),
                                   'evaluation': compact(a.get('evaluation')),
                                   'changed_files': a.get('changed_files', [])}
                                  for a in result.get('attempts', [])],
                     'checkpoints': result.get('checkpoints'),
                     'error': str(result.get('error') or '')[:3000],
                     'generation_failure': result.get('generation_failure'),
                     'wall_time_sec': result.get('wall_time_sec')})
    args.out.write_text(json.dumps({'verified_result_hashes': len(rows), 'rows': rows}, indent=2))
    print(json.dumps({'verified_result_hashes': len(rows), 'out': str(args.out)}))


if __name__ == '__main__':
    main()
