"""Wait for the frozen comparison, audit once, and archive metadata with array hashes."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import time

BASE = Path(__file__).resolve().parent
RUN = BASE / 'natural12_v2'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    while not (RUN / 'formal_dispatch_complete.json').exists():
        time.sleep(30)
    subprocess.run([sys.executable, str(BASE / 'audit_formal.py')], check=True)
    audit = json.loads((RUN / 'final_audit_summary.json').read_text())
    if not audit['complete']:
        raise RuntimeError('Audit did not finish')
    records = []
    files = sorted(p for p in RUN.rglob('*') if p.is_file() or p.is_symlink())
    for path in files:
        row = {'path': str(path.relative_to(RUN))}
        if path.is_symlink():
            row['symlink_target'] = str(path.readlink())
        else:
            row.update(size_bytes=path.stat().st_size, sha256=digest(path))
        records.append(row)
    manifest = BASE / 'formal_evidence_inventory.json'
    manifest.write_text(json.dumps({'run': str(RUN), 'files': records}, indent=2) + '\n')
    archive = BASE / 'formal_metadata_complete_20260922.tar.gz'
    if archive.exists():
        raise RuntimeError('Refusing to replace evidence archive')
    with tarfile.open(archive, 'x:gz') as tar:
        tar.add(manifest, arcname=manifest.name)
        for path in files:
            if path.suffix in ('.npz', '.pyc'):
                continue
            tar.add(path, arcname='natural12_v2/' + str(path.relative_to(RUN)), recursive=False)
        for name in ('formal_methods_smoke_v1', 'formal_source_checks_v2', 'formal_backend_checks_v1'):
            path = BASE / name
            if path.exists():
                tar.add(path, arcname=name)
    result = {'archive': str(archive), 'size_bytes': archive.stat().st_size,
              'sha256': digest(archive), 'inventory_sha256': digest(manifest),
              'array_storage': str(RUN), 'array_files': sum(p.suffix == '.npz' for p in files),
              'array_bytes': sum(p.stat().st_size for p in files if p.suffix == '.npz')}
    (BASE / 'formal_archive_record.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
