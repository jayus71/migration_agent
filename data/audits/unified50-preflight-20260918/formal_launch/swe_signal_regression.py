"""Zero-model-call regression for post-SIGCONT re-stop and pidfd ownership.

Run from the remote implementation repository. The synthetic child deliberately
re-stops after continuation; it demonstrates the observed exception and cleanup
defect, not an assertion about the original unlogged child's exact stop reason.
"""
import importlib.util, os, subprocess, sys, time, json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import autofix.autonomous.swe_upstream as old

p=Path('experiments/unified_migration50_20260918/formal_control/recoveries/swe_continuation_bridge')
spec=importlib.util.spec_from_file_location('autofix.autonomous.swe_candidate',p/'swe_upstream.proposed.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
child='import os,signal,time;signal.signal(signal.SIGCONT,lambda *a:os.kill(os.getpid(),signal.SIGSTOP));print("ready",flush=True);os.kill(os.getpid(),signal.SIGSTOP);time.sleep(30)'
results=[]
real=old._pidfd_signal
def scheduled(fd,sig):
    real(fd,sig)
    time.sleep(.05)
for name,mod in [('before',old),('proposed',m)]:
    proc=subprocess.Popen([sys.executable,'-c',child],stdout=subprocess.PIPE,text=True)
    proc.stdout.readline()
    time.sleep(.05)
    obj=SimpleNamespace(_paused={proc.pid:old._pidfd_open(proc.pid)})
    error=None
    try:
        with patch.object(mod,'_pidfd_signal',scheduled):mod.SWEAgentNative.resume(obj)
    except Exception as exc:error=str(exc)
    stale=[]
    for pid,fd in obj._paused.items():
        try:os.fstat(fd)
        except OSError:stale.append(pid)
    proc.kill()
    proc.wait()
    results.append({'version':name,'error':error,'stale_closed_descriptors':len(stale),'owned_descriptors_after':len(obj._paused)})
assert results[0]['error']=='Native process did not acknowledge continuation'
assert results[0]['stale_closed_descriptors']==1
assert results[1]['error'] is None and results[1]['owned_descriptors_after']==0
print(json.dumps(results,indent=2))
