param([switch]$Full)
$ErrorActionPreference = 'Stop'
$sshKey = 'C:/Users/jayus71/.ssh/whj_ed25519'
$remoteHost = 'whj@218.194.42.215'
$remoteRoot = '/media/main/whj/projects/torch4ms/ascend-torch4ms-unit-planning-ablation-20260922'
$destination = Join-Path $PSScriptRoot '../output/work-unit-planning-ablation-20260922'
New-Item -ItemType Directory -Force -Path $destination | Out-Null
$collector = @'
from pathlib import Path
import hashlib,json,sys,tarfile,time
root=Path('/media/main/whj/projects/torch4ms/ascend-torch4ms-unit-planning-ablation-20260922')
experiment=root/'experiments/work_unit_planning_ablation_20260922'
run=experiment/'results'
full=sys.argv[1]=='full'
scheduler=json.loads((run/'scheduler.json').read_text())
if full and scheduler['status']!='completed':
    raise RuntimeError('Full archive requires completed scheduling; collect progress without -Full')
name='evidence.tar.gz' if full else 'progress.tar.gz'
archive=root/name
with tarfile.open(archive,'w:gz') as out:
    for path in sorted(experiment.rglob('*')):
        if not path.is_file() or '__pycache__' in path.parts: continue
        relative=path.relative_to(root)
        if full or (path.suffix=='.json' and not any(x in path.name for x in ('_request','_response','_context_input','_session','_conversation')) and 'workspace' not in path.parts and 'source' not in path.parts and 'translation' not in path.parts and 'references' not in path.parts and 'private_reference' not in path.parts and 'repository_state_evidence' not in path.parts):
            out.add(path,arcname=str(relative))
    if full:
        for directory in ('scripts','autofix'):
            for path in sorted((root/directory).rglob('*.py')):
                if '__pycache__' not in path.parts: out.add(path,arcname=str(path.relative_to(root)))
record={'archive':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size,'scheduler_status':scheduler['status'],'collected':time.time(),'full':full}
(root/'collection.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))
'@
$mode = if ($Full) { 'full' } else { 'progress' }
$collector | ssh -T -o BatchMode=yes -i $sshKey -p 40902 $remoteHost python3 - $mode
if ($LASTEXITCODE -ne 0) { throw 'Remote collection failed' }
$archiveName = if ($Full) { 'evidence.tar.gz' } else { 'progress.tar.gz' }
scp -q -i $sshKey -P 40902 "${remoteHost}:${remoteRoot}/${archiveName}" "${remoteHost}:${remoteRoot}/collection.json" $destination
if ($LASTEXITCODE -ne 0) { throw 'Archive transfer failed' }
$metadata = Get-Content (Join-Path $destination 'collection.json') -Raw | ConvertFrom-Json
$actualHash = (Get-FileHash (Join-Path $destination $archiveName) -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualHash -ne $metadata.sha256) { throw 'Archive SHA-256 mismatch' }
$snapshot = Join-Path $destination $(if ($Full) { 'runtime_snapshot' } else { 'progress_snapshot' })
New-Item -ItemType Directory -Force -Path $snapshot | Out-Null
tar -xzf (Join-Path $destination $archiveName) -C $snapshot
if ($LASTEXITCODE -ne 0) { throw 'Archive extraction failed' }
Write-Output "Verified snapshot: $snapshot"
