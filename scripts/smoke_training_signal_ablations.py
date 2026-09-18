"""Check visible stopping and hidden final scoring through a fake transport."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys

source = Path(sys.argv[1]).resolve()
output = source.parent / 'training_signal16_offline_smoke'
output.mkdir()
shutil.copy2(source / 'plan.json', output / 'plan.json')
runner_path = source / 'run_training_signal_ablations.py'
spec = importlib.util.spec_from_file_location('signal_runner', runner_path)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
sys.path.insert(0, str(source / 'execution/code_snapshot'))
from autofix.autonomous import agent


def fake_client(request, timeout):
    return {'model': 'offline-fake-transport', 'choices': [{'message': {'role': 'assistant', 'content': json.dumps({
        'diagnosis': {'observations': ['Offline lifecycle check'], 'locations': [], 'evidence': [],
                      'uncertainty': 'No actual model diagnosis'}, 'summary': 'No repair attempted'})},
        'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}}


class FakeAgent(agent.AutonomousAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, client=fake_client, **kwargs)


agent.AutonomousAgent = FakeAgent
rows = []
for variant in ('execution', 'all_observations'):
    shutil.copytree(source / variant, output / variant,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    row = runner.worker(output / variant, 'task_004')
    assert row['status'] == 'completed' and row['accepted'] is False
    assert row['controller_accepted'] == (variant == 'execution')
    assert len(row['full_final_confirmation']) == 3
    assert row['budget']['usage']['total_tokens'] == 0
    rows.append({'variant': variant, 'controller_accepted': row['controller_accepted'],
                 'full_accepted': row['accepted'], 'status': row['status'], 'api_calls': 0})
(output / 'smoke_result.json').write_text(json.dumps(rows, indent=2) + '\n')
print(json.dumps(rows))
