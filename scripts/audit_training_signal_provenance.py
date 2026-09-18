"""Compare the actual copied model/library files against their declared sources."""
import hashlib
import json
from pathlib import Path

base = Path('/media/main/whj/projects/torch4ms')
root = base / 'maintext-ablations-20260918/training_signal16_v2'
control = base / 'ascend-torch4ms-autonomous-verifier-20260917/experiments/autonomous_verifier_20260917/progress_v4'
diagnostics = base / 'maintext-diagnostics-20260918'


def hashes(folder):
    return {str(path.relative_to(folder)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in folder.rglob('*') if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc'}


original = hashes(control / 'private_inputs/task_001/torch4ms')
diagnostic = hashes(diagnostics / 'source/torch4ms')
copied = hashes(root / 'execution/private_inputs/task_001/torch4ms')
record = {'declared_diagnostic_source': json.loads((diagnostics / 'provenance.json').read_text())['source_commit'],
          'copied_matches_diagnostic_library': copied == diagnostic,
          'copied_matches_control_library': copied == original,
          'diagnostic_library_file_count': len(diagnostic),
          'control_library_file_count': len(original),
          'different_library_files': sorted(name for name in set(original) | set(diagnostic)
                                           if original.get(name) != diagnostic.get(name)),
          'actual_library_hashes': diagnostic}
path = root / 'library_provenance_audit.json'
if path.exists():
    raise ValueError('Audit already exists')
path.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({key: value for key, value in record.items() if key != 'actual_library_hashes'}))
