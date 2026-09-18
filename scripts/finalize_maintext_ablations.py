"""Wait for the declared recovery, audit every selected ledger, then archive it."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--recovery', type=Path, required=True)
    args = parser.parse_args()
    root, recovery = args.root.resolve(), args.recovery.resolve()
    final = root / 'recovery_finalization.json'
    if final.exists():
        raise ValueError('Finalization record already exists')
    previous = None
    while not (recovery / 'dispatch_result.json').exists():
        progress = recovery / 'progress.json'
        if progress.exists():
            state = json.loads(progress.read_text())
            number = len(state['completed'])
            if number != previous:
                print(json.dumps({'completed': number, 'planned': state['planned'], 'blocked': state['blocked']}), flush=True)
                previous = number
        time.sleep(30)
    state = json.loads((recovery / 'dispatch_result.json').read_text())
    if state['blocked'] or state['not_started']:
        raise RuntimeError('Recovery stopped before completing all planned jobs')
    report = root / 'reports/recovery_final'
    subprocess.run([sys.executable, str(root / 'report_maintext_recovery.py'), '--root', str(root),
                    '--recovery', str(recovery), '--output', str(report)], check=True)
    value = json.loads(report.with_suffix('.json').read_text())
    if not value['complete'] or value['ledger_mismatches'] or value['treatment_violations']:
        raise ValueError('Incomplete or inconsistent recovery report')
    archive = root / 'archives/component_and_signal_recovery_round1'
    subprocess.run([sys.executable, str(root / 'archive_autonomous_recovery.py'),
                    '--source', str(recovery), '--output', str(archive)], check=True)
    final.write_text(json.dumps({'finished_at': datetime.now(timezone.utc).isoformat(),
        'selected_complete': value['selected_completed'], 'planned': value['selected_planned'],
        'ledger_mismatches': 0, 'treatment_violations': 0, 'archive': str(archive)}, indent=2) + '\n')
    print(final, flush=True)


if __name__ == '__main__':
    main()
