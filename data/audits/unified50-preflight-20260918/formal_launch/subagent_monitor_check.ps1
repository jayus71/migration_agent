$dest='data/audits/unified50-preflight-20260918/formal_launch'
$routeFile=Join-Path $dest 'parent_route_check_20260919.txt'
if (Test-Path -LiteralPath $routeFile) {
    $routeText=Get-Content -LiteralPath $routeFile -Raw
    if ($routeText.Contains('STOP REQUEST 2026-09-18T17:23:36Z')) {
        throw 'User stopped this subagent. Parent /root has taken over. Leave all remote experiment processes running, stop monitoring and edits, and end this subagent turn.'
    }
    if ($routeText.Contains('PARENT APP RECEIPT') -and -not $routeText.Contains('CHILD CONFIRMS ROUND2 RECEIVED')) {
        Write-Warning "Pending parent acknowledgement: read $routeFile and respond to ACK-APP-ROUND2-1713 through the verified parent app route. Keep checking the parent file between waits; the user is waiting for a verified two-way acknowledgement."
    }
}
$raw = Get-Content "$dest/subagent_probe.py" -Raw | ssh -i 'C:\Users\jayus71\.ssh\whj_ed25519' -p 40902 -o BatchMode=yes -o ConnectTimeout=15 whj@218.194.42.215 'cd /media/main/whj/projects/torch4ms/ascend-torch4ms-unified50-preflight-20260918 && /media/main/whj/miniconda3/envs/mstorch/bin/python -'
if ($LASTEXITCODE -ne 0) { throw 'Remote monitoring probe failed' }
$s=$raw | ConvertFrom-Json
$raw | Set-Content -Encoding utf8 "$dest/monitor_latest_snapshot.json"
$raw | Add-Content -Encoding utf8 "$dest/subagent_monitor_history.jsonl"
$m=Get-Content "$dest/monitor_state.json" -Raw | ConvertFrom-Json
$values=@{owner='formal_experiment_monitor';notification_policy='Only report once all 391 conditions are complete, or a blocker requires user decision';checked_at=$s.checked_at;finished=$s.finished;running=$s.active.Count;pending=$s.pending;needs_inspection=$s.needs_inspection;scheduler_pid=$s.scheduler_pid;scheduler_alive=$s.scheduler_alive;all_four_workers_alive=(@($s.active | Where-Object {-not $_.process_alive}).Count -eq 0);status_file_age_seconds=$s.status_file_age_seconds;recorded_response_files=$s.recorded_response_files;response_errors=$s.response_errors;global_api_pause=$s.global_api_pause;blocked_methods=$s.blocked_methods;active_jobs=$s.active;observed_usage=$s.observed_provider_usage;phases_finished=@{main=$s.phases.main.finished;cross_language=$s.phases.cross_language.finished;plugin=$s.phases.plugin.finished;ablation=$s.phases.ablation.finished};latest_check_summary='Read-only SSH check completed; see monitor_latest_snapshot.json for process, response, file-age, receipt and phase evidence.'}
foreach($k in $values.Keys) {$m | Add-Member -Force -NotePropertyName $k -NotePropertyValue $values[$k]}
$m | ConvertTo-Json -Depth 20 | Set-Content -Encoding utf8 "$dest/monitor_state.json"
$s | ConvertTo-Json -Depth 15
