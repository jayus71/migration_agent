# SWE continuation incident, 2026-09-18

The monitoring agent completed real SSH checks and recorded the takeover in `subagent_handoff.txt`. Scheduler PID 192058 and four worker processes were alive. At 14:59 UTC, 206 of 391 conditions were finished, one required inspection, and 180 were pending.

`main__group_012__swe` ended after 28 real model calls with `RuntimeError: Native process did not acknowledge continuation` in our process-control bridge. Its cleanup also encountered a closed pidfd. The scheduler automatically blocked new `swe` jobs while other methods continued. No candidate was regenerated and no result was modified.

The raw `accepted=true` value records the initially accepted candidate. The final saved public observation, `measurement_0007`, is `accepted=false`, after the native agent changed ReLU to sigmoid. The episode did not reach an external submission checkpoint. The raw result must remain intact, and a final comparison must separately identify this interrupted condition and its 428,811 observed tokens (418,238 input; 10,573 output).

A scripted integration probe using the existing synthetic fixture and the same public-test pipeline completed normally. A second probe with 29 consecutive identical pipelines also completed normally. These probes made no real model calls and did not modify the implementation. They did not reproduce the process-control failure.

The native worker has exited, so its in-memory episode cannot be resumed without new execution. The existing authorization forbids resampling interrupted conditions. The interrupted run and costs therefore remain preserved; new SWE conditions remain blocked pending a justified integration repair or an explicit decision about this interruption. Other authorized work is still running.
A third scripted probe added a 2.2-second verification delay to match the recorded measurement duration; all 19 consecutive public-test pipelines completed. The continuation failure remains unreproduced. The SWE bridge is included in the frozen manifest, so no speculative bridge modification or manifest change was made.

## Verified recovery

At 16:53 UTC, a deterministic Linux child-process probe reproduced the continuation error. A child can stop again immediately after successful `SIGCONT` delivery; the old bridge treated that subsequent stopped state as failed delivery and retained a closed process descriptor. The corrected bridge recognizes successful signal delivery and releases descriptor ownership only after success or process exit. The regression fails before the correction and passes after it. All six existing SWE integration tests passed with zero real model calls.

The dispatcher installs this correction in its SWE worker startup, with the correction file hash checked before use. The frozen manifests and native baseline files remain unchanged; prompts, parsing, retry policy and budgets were not changed. The complete proposal, regression, tests and recovery receipt are under remote `formal_control/recoveries/swe_continuation_bridge/`.

At 16:54 UTC, scheduler PID 801954 resumed the 34 never-started SWE conditions with four workers. The interrupted condition was not rerun: its result retains SHA-256 `dc01ceda726dfefd12c30875ab840daa5789b6af0ba8bcb7d2db595821b0e4d5`. Its original dispatch receipt is archived; the current receipt explicitly records the infrastructure interruption and `accepted=null`, preserving all 28 calls and preventing the stale initial acceptance field from being counted as final success.

The parent independently checked the regression, integration-test records, dispatcher diff, interruption receipt and result hash. At 17:19:32 UTC, 11 of the 34 resumed conditions had finished, four were running and 19 were pending. Their logs contained no recurrence of the continuation error, and no new infrastructure failures were recorded. This is a progress checkpoint, not full-batch completion.

## Verified recovery at 16:54 UTC

The process-control regression now reproduces the continuation exception and stale closed descriptor using a real Linux child that deliberately stops again immediately after successful SIGCONT delivery. A deterministic 50 ms observation delay exercises that scheduling case. The original failed process did not log its PID state, so the original child's exact reason for stopping remains unconfirmed.

The correction keeps descendant-first signal order, treats successful pidfd signal delivery as acknowledgement, and removes descriptor ownership as each continuation succeeds or its process has exited. It retains descriptors on unexpected signalling failure so cleanup can still own them. All six existing native SWE transport and isolation integration tests passed without skipping or real model calls. The targeted regression reproduces both defects before the correction and passes after it.

The dispatcher applies the audited resume method in memory for newly launched SWE workers. Original frozen files, approved manifests, upstream algorithm, prompts, parser, retries and budgets remain unchanged. The archived proposal hash is `aecf5a5fce2907d6c0b803af92a0509c290afc9202b9c49f9c7be095376d312f`. The original dispatcher and interrupted receipt are archived remotely under `formal_control/recoveries/swe_continuation_bridge`.

The interrupted result remains byte-identical (`dc01ceda726dfefd12c30875ab840daa5789b6af0ba8bcb7d2db595821b0e4d5`). Its dispatch receipt now records a terminal integration interruption with `accepted=null`, preserves the raw initial acceptance separately, and retains all 28 calls. No interrupted generation was rerun. The 34 previously unstarted SWE conditions were verified to have no start receipts and resumed with four workers under scheduler PID 801954. The first live check at 16:54:16 UTC confirmed all four workers and recent output files.
