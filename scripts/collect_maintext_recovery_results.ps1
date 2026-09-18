# Collect and verify the already-running experiment after its remote finalizer exits.
# This process performs no model calls and never launches or resumes experiments.
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$key = 'C:\Users\jayus71\.ssh\whj_ed25519'
$remote = 'whj@218.194.42.215'
$studyRoot = '/media/main/whj/projects/torch4ms/maintext-ablations-20260918'
$checkScript = @'
import json
from pathlib import Path
root=Path('/media/main/whj/projects/torch4ms/maintext-ablations-20260918')
p=json.loads((root/'recovery_round1/progress.json').read_text())
print(json.dumps({'completed':len(p['completed']), 'planned':p['planned'],
 'blocked':p['blocked'], 'finalized':(root/'recovery_finalization.json').exists()}))
'@
$previous = ''
while ($true) {
    $raw = $checkScript | & ssh -i $key -p 40902 -o BatchMode=yes -o ConnectTimeout=20 $remote '/media/main/whj/miniconda3/envs/mstorch/bin/python -'
    if ($LASTEXITCODE -ne 0) { throw 'Remote result collection check failed; experiments were not changed.' }
    $state = $raw | ConvertFrom-Json
    if ($raw -ne $previous) { Write-Output $raw; $previous = $raw }
    if ($state.blocked) { throw 'Recovery dispatcher is blocked; preserve its existing episodes.' }
    if ($state.finalized) { break }
    Start-Sleep -Seconds 30
}
& scp -i $key -P 40902 -o BatchMode=yes "${remote}:${studyRoot}/reports/recovery_final.json" "${remote}:${studyRoot}/reports/recovery_final.md" "${remote}:${studyRoot}/recovery_finalization.json" 'output/maintext-ablations-20260918/'
if ($LASTEXITCODE -ne 0) { throw 'Could not collect final recovery reports.' }
& scp -i $key -P 40902 -o BatchMode=yes "${remote}:${studyRoot}/archives/component_and_signal_recovery_round1.tar.gz" "${remote}:${studyRoot}/archives/component_and_signal_recovery_round1.json" 'output/maintext-ablations-20260918/archives/'
if ($LASTEXITCODE -ne 0) { throw 'Could not collect recovery archive.' }
& wsl -d Ubuntu --cd /home/jayus71/code/migration_agent python3 scripts/archive_autonomous_recovery.py --source "${studyRoot}/recovery_round1" --output output/maintext-ablations-20260918/archives/component_and_signal_recovery_round1 --verify
if ($LASTEXITCODE -ne 0) { throw 'Local recovery archive verification failed.' }
& wsl -d Ubuntu --cd /home/jayus71/code/migration_agent python3 scripts/build_maintext_results_bundle.py --recovery output/maintext-ablations-20260918/recovery_final.json
if ($LASTEXITCODE -ne 0) { throw 'Could not export the complete results bundle.' }
Write-Output 'Complete recovery evidence collected and verified; results report and CSV files updated.'
