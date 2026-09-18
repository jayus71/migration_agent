"""Exercise the frozen condition lifecycle with a fake transport and no API."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys


source = Path(sys.argv[1]).resolve()
run = source.parent / "offline_agent_smoke"
run.mkdir()
for name in ("code_snapshot", "private_inputs", "private_reference", "public_backend"):
    shutil.copytree(source / name, run / name)
manifest = json.loads((source / "manifest.json").read_text())
manifest["max_repair_attempts"] = 1
(run / "manifest.json").write_text(json.dumps(manifest, indent=2))
spec = importlib.util.spec_from_file_location("jax_runner", source / "runner.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
experiment = runner.runtime(run)
from autofix.autonomous import agent


def fake_client(request, timeout):
    return {"model": "offline-fake-transport", "choices": [{"message": {"role": "assistant", "content": json.dumps({
        "diagnosis": {"observations": ["Offline lifecycle smoke test"], "locations": [], "evidence": [], "uncertainty": "No real diagnosis"},
        "summary": "Offline transport; no repair attempted"})}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}


original = agent.AutonomousAgent


class FakeAgent(original):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, client=fake_client, **kwargs)


agent.AutonomousAgent = FakeAgent
results = [experiment.run_condition(run, "task_001", method, Path(sys.executable))
           for method in ("autonomous_layered", "direct_shared_tools")]
assert all(row["status"] == "completed" and row["accepted"] is False for row in results), results
print(json.dumps({"transport": "fake; zero API calls", "methods": [row["method"] for row in results], "statuses": [row["status"] for row in results]}))
