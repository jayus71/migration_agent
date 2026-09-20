$ErrorActionPreference='Stop'
$auditDir=Join-Path $PSScriptRoot '.'
$raw=Get-Content -LiteralPath (Join-Path $auditDir 'subagent_probe.py') -Raw | ssh -i 'C:\Users\jayus71\.ssh\whj_ed25519' -p 40902 -o BatchMode=yes -o ConnectTimeout=15 whj@218.194.42.215 'cd /media/main/whj/projects/torch4ms/ascend-torch4ms-unified50-preflight-20260918 && /media/main/whj/miniconda3/envs/mstorch/bin/python -'
if ($LASTEXITCODE -ne 0) { throw 'Remote monitoring probe failed' }
$snapshot=$raw | ConvertFrom-Json
$raw | Set-Content -Encoding utf8 (Join-Path $auditDir 'monitor_latest_snapshot.json')
$raw | Add-Content -Encoding utf8 (Join-Path $auditDir 'parent_monitor_history.jsonl')
$stateFile=Join-Path $auditDir 'monitor_state.json'
$state=Get-Content -LiteralPath $stateFile -Raw | ConvertFrom-Json
$updates=@{
    owner='root'
    monitor_handoff_status='Subagent stop acknowledged and verified idle/completed; parent owns monitoring. Existing 10-minute heartbeat active for parent only.'
    checked_at=$snapshot.checked_at
    finished=$snapshot.finished
    pending=$snapshot.pending
    running=@($snapshot.active).Count
    needs_inspection=$snapshot.needs_inspection
    scheduler_pid=$snapshot.scheduler_pid
    scheduler_alive=$snapshot.scheduler_alive
    active_workers_alive=(@($snapshot.active | Where-Object {-not $_.process_alive}).Count -eq 0)
    all_four_workers_alive=(@($snapshot.active).Count -eq 4 -and @($snapshot.active | Where-Object {-not $_.process_alive}).Count -eq 0)
    active_jobs=$snapshot.active
    status_file_age_seconds=$snapshot.status_file_age_seconds
    blocked_methods=$snapshot.blocked_methods
    global_api_pause=$snapshot.global_api_pause
    response_errors=$snapshot.response_errors
    recorded_response_files=$snapshot.recorded_response_files
    observed_usage=$snapshot.observed_provider_usage
    phases_finished=@{main=$snapshot.phases.main.finished;cross_language=$snapshot.phases.cross_language.finished;plugin=$snapshot.phases.plugin.finished;ablation=$snapshot.phases.ablation.finished}
    latest_check_summary='Parent checked remote status, actual process liveness, file activity, receipts and provider records.'
}
foreach ($key in $updates.Keys) { $state | Add-Member -Force -NotePropertyName $key -NotePropertyValue $updates[$key] }
$state | ConvertTo-Json -Depth 20 | Set-Content -Encoding utf8 $stateFile
$snapshot | Select-Object checked_at,finished,pending,needs_inspection,scheduler_alive,response_errors,blocked_methods,phases,@{n='active';e={$_.active | Select-Object job,pid,process_alive,latest_file_age_seconds,latest_response_age_seconds}} | ConvertTo-Json -Depth 6
