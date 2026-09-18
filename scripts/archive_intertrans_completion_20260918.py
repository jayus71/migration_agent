"""Archive completed N18 evidence and frozen code, excluding credentials and arrays."""
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile

BASE = Path('/media/main/whj/projects/torch4ms')
ROOT = BASE / 'intertrans-completion-20260918'
REPO = BASE / 'ascend-torch4ms-intertrans-completion-20260918'
N18 = REPO / 'experiments/experiment_request_20260820/14_experiment_N_real_cross_language/n18'
ENGINE = BASE / 'intertrans-completion-engine-20260918'
OLD = BASE / 'ascend-torch4ms-n18-348e8cd/artifacts/n18_training/intertrans'
EXTENSIONS = {'.json', '.jsonl', '.csv', '.txt', '.log', '.md', '.py', '.java',
              '.ipynb', '.go', '.mod', '.sum', '.yaml', '.yml', '.toml', '.sh', '.patch'}


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    result = read(ROOT / 'paper_results.json')
    assert result['all_valid'] and result['completed'] == result['expected'] == 18
    assert result['valid_outcomes'] == 18
    assert result['current_usage'] == result['completed_usage']
    assert read(ROOT / 'calibration/summary.json')['passed']
    freeze = read(ROOT / 'freeze.json')
    assert digest(ENGINE / 'intertrans') == freeze['engine_sha256']
    assert digest(ROOT / 'run_completion.py') == freeze['launcher_sha256']
    assert digest(N18 / 'protocol.json') == freeze['protocol_sha256']
    assert digest(N18 / 'training_interface.txt') == freeze['interface_sha256']
    assert digest(N18 / 'pairing/intertrans_adapter.py') == freeze['adapter_sha256']
    secrets = [v.encode() for k, v in os.environ.items()
               if ('API_KEY' in k or k.endswith('_TOKEN')) and len(v) > 16]
    assert secrets, 'Load the existing credentials for an in-memory archive leak check'
    files, excluded = {}, []
    roots = [(ROOT, ''), (N18, 'code_snapshot/n18'), (ENGINE, 'code_snapshot/engine'),
             (OLD, 'historical_low_output_budget')]
    for directory, prefix in roots:
        for path in sorted(directory.rglob('*')):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(directory)
            name = (Path(prefix) / relative).as_posix()
            sensitive = ('credential' in path.name.lower() or path.name.startswith('.env')
                         or path.name == 'private_config.yaml')
            if (sensitive or '__pycache__' in path.parts or '.git' in path.parts or 'cache' in path.parts
                    or path.name in ('archive_receipt.json', 'archive_manifest.json')):
                excluded.append(dict(path=name, reason='credential_or_runtime_cache'))
                continue
            if path.suffix not in EXTENSIONS and path.name != 'Dockerfile':
                excluded.append(dict(path=name, bytes=path.stat().st_size, reason='binary_or_runtime_asset'))
                continue
            content = path.read_bytes()
            assert not any(secret in content for secret in secrets), f'Credential content in {name}'
            assert name not in files
            files[name] = dict(path=path, bytes=len(content), sha256=hashlib.sha256(content).hexdigest())
    index = BASE / 'ascend-torch4ms-n18-348e8cd/artifacts/evidence_index.json'
    assert digest(index) == freeze['index_sha256']
    files['code_snapshot/evidence_index.json'] = dict(path=index, bytes=index.stat().st_size, sha256=digest(index))
    manifest = dict(scope='Complete text evidence, raw responses and usage, code and calibration records.',
        binary_assets='Large tensor fixtures and runtime caches remain in the original remote directories.',
        original_root=str(ROOT), real_model_calls=0, completed_conditions=18,
        files=[dict(path=name, bytes=item['bytes'], sha256=item['sha256']) for name, item in sorted(files.items())],
        excluded=excluded)
    manifest_bytes = (json.dumps(manifest, indent=2) + '\n').encode()
    (ROOT / 'archive_manifest.json').write_bytes(manifest_bytes)
    archive = BASE / 'intertrans-completion-20260918-evidence.tar.gz'
    with tarfile.open(archive, 'w:gz') as bundle:
        for name, item in sorted(files.items()):
            bundle.add(item['path'], arcname=ROOT.name + '/' + name, recursive=False)
        entry = tarfile.TarInfo(ROOT.name + '/archive_manifest.json')
        entry.size = len(manifest_bytes)
        bundle.addfile(entry, io.BytesIO(manifest_bytes))
    with tarfile.open(archive) as bundle:
        for name, item in files.items():
            raw = bundle.extractfile(ROOT.name + '/' + name).read()
            assert hashlib.sha256(raw).hexdigest() == item['sha256']
    receipt = dict(archive=str(archive), sha256=digest(archive), bytes=archive.stat().st_size,
        evidence_files=len(files), all_member_hashes_verified=True, credentials_excluded=True,
        archive_manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest())
    (ROOT / 'archive_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
