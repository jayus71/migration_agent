"""Verify source files after probes and the reported source-side outcomes."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', type=Path, required=True)
    args = parser.parse_args()
    base = args.base.resolve()
    inventory = json.loads((base / 'inventory.json').read_text())
    count = 0
    for repo in inventory:
        for record in repo['files']:
            path = base / repo['repository'] / record['path']
            assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'], path
            count += 1
    checks = base / 'source_checks'
    def result(name):
        return json.loads((checks / (name + '.json')).read_text())
    assert result('time_series_entry_numpy126')['status'] == 'passed'
    assert result('time_series_entry_numpy126')['epochs'] == 100
    assert '10 passed' in (checks / 'two_tower_tests.log').read_text()
    assert '3 passed' in (checks / 'simple_moe_tests.log').read_text()
    assert result('simple_moe_trainer_with_deps')['status'] == 'passed'
    assert result('simple_moe_metrics')['status'] == 'failed'
    value = {'source_python_files_unchanged': count, 'repositories': len(inventory),
             'time_series_full_source_entry': 'passed with documented environment and data fixture',
             'two_tower_existing_tests': '10/10 passed', 'simple_moe_existing_tests': '3/3 passed',
             'simple_moe_metrics': 'original source failure retained', 'migration_model_calls': 0}
    (base / 'assessment_verification.json').write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps(value))


if __name__ == '__main__':
    main()
