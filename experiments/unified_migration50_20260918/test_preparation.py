"""Check deduplication, guarded generation, native extraction and budget variants."""

import json
from pathlib import Path
import sys

import pytest

from experiments.unified_migration50_20260918 import translation
from experiments.unified_migration50_20260918.integration import require_approval
from experiments.unified_migration50_20260918.components import component_agent, investigate
from autofix.autonomous.agent import AgentConfig, AutonomousAgent
from autofix.autonomous.tools import WorkspaceTools


def response(content, calls=None):
    message = {'role': 'assistant', 'content': content}
    if calls:
        message['tool_calls'] = calls
    return {'model': 'offline-script', 'choices': [{'message': message, 'finish_reason': 'stop'}],
            'usage': {'prompt_tokens': 5, 'completion_tokens': 3, 'total_tokens': 8}}


def test_review_is_required_before_client_creation(tmp_path):
    (tmp_path / 'manifest.json').write_text('{}')
    with pytest.raises(RuntimeError, match='user review'):
        require_approval(tmp_path)


def test_direct_failure_receipt_and_no_second_attempt(tmp_path):
    folder = tmp_path / 'generation'
    def fail(request):
        raise TimeoutError('offline transport interruption')
    with pytest.raises(TimeoutError):
        translation.generate({'model': 'deepseek-v4-flash'}, folder, method='direct', group='g', client=fail)
    receipt = json.loads((folder / 'generation.json').read_text())
    assert receipt['usage'] is None and receipt['transport_calls'] == 1
    with pytest.raises(FileExistsError):
        translation.generate({}, folder, method='direct', group='g', client=fail)


def test_native_cte_protobuf_and_terminal_extraction():
    batch = translation.cte_request('def f(x): return x', {'target_framework': 'MindSpore'}, 'synthetic')
    assert list(batch.translation_requests[0].used_languages) == ['PyTorch', 'Python']
    assert len(batch.translation_requests[0].test_suite.unit_test_suite) == 1
    from intertrans import protos_pb2 as pb
    from google.protobuf.json_format import MessageToDict
    edge = pb.ResponseTranslationEdge(edge_id=7, target_language='Python',
        source_code='DO_NOT_SELECT_SOURCE', extracted_source_code='NATIVE_EXTRACTED', status='TRANSLATION_FOUND')
    answer = pb.BatchTranslationResponse(translation_responses=[pb.TranslationResponse(
        translation_request=batch.translation_requests[0],
        paths=[pb.ResponseTranslationPath(translation_edges=[edge])])])
    data = MessageToDict(answer, preserving_proto_field_name=True)
    assert translation.cte_candidate(data) == 'NATIVE_EXTRACTED'
    data['translation_responses'][0]['paths'][0]['translation_edges'][0].pop('extracted_source_code')
    assert translation.cte_candidate(data) == ''


def make_agent(tmp_path, cls=AutonomousAgent, method='layered'):
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    (workspace / 'scratch_tests').mkdir()
    (workspace / 'candidate.py').write_text('VALUE = 1\n')
    (workspace / 'source.py').write_text('VALUE = 1\n')
    (workspace / 'task.json').write_text('{}')
    client = lambda request, timeout: response('{"diagnosis":{"observations":["public observation"]},"summary":"complete"}')
    return cls(WorkspaceTools(workspace, run_test=lambda request: {'accepted': False}),
        tmp_path / 'logs', config=AgentConfig(method=method), client=client)


@pytest.mark.parametrize('variant', ['continuous_role', 'without_repair_history', 'without_progress_prompt'])
def test_final_component_preserves_shared_budget(tmp_path, variant):
    agent = make_agent(tmp_path, component_agent(AutonomousAgent, variant))
    agent.diagnose({'accepted': False})
    agent.repair({'accepted': False}, 1)
    calls = agent.calls
    agent.repair({'accepted': False}, 2)
    assert agent.calls > calls and agent.usage()['completion_tokens'] == agent.calls * 3
    assert agent.config.repair_calls_per_stage == 8
    if variant == 'without_repair_history':
        assert 'Your conversation persists' not in agent.history[0]['content']
        assert sum('Repair attempt 1' in str(item) for item in agent.history) == 0
    if variant == 'continuous_role':
        assert agent.active_role == 'continuous_agent'


def test_plugin_readonly_charges_host_and_restores_native_history(tmp_path):
    agent = make_agent(tmp_path, method='single')
    history, started = list(agent.history), agent.started
    initial = (agent.tools.root / 'candidate.py').read_bytes()
    result = investigate(agent, {'accepted': False})
    assert result['independent_investigation']['records']
    assert agent.calls == 1 and agent.usage()['completion_tokens'] == 3
    assert agent.started == started and agent.config.memory_policy == 'native'
    assert agent.history == history
    assert (agent.tools.root / 'candidate.py').read_bytes() == initial


def test_plugin_rejects_production_edit(tmp_path):
    agent = make_agent(tmp_path, method='single')
    calls = [{'id': 'edit1', 'type': 'function', 'function': {'name': 'edit',
        'arguments': json.dumps({'edits': [{'path': 'candidate.py', 'old': 'VALUE = 1', 'new': 'VALUE = 9'}]})}}]
    answers = iter([response('', calls), response('{"summary":"done"}')])
    agent.client = lambda request, timeout: next(answers)
    investigate(agent, {'accepted': False})
    assert (agent.tools.root / 'candidate.py').read_text() == 'VALUE = 1\n'
    assert agent.calls == 2


def test_usage_includes_failures_and_retains_unknown():
    from experiments.unified_migration50_20260918.cte_service import aggregate
    result = aggregate([{'usage': {'prompt_tokens': 5, 'completion_tokens': 2, 'total_tokens': 7}}, {'usage': None}])
    assert result['calls'] == 2 and result['usage'] is None
    assert result['known_usage_lower_bound']['total_tokens'] == 7
    assert result['unknown_usage_calls'] == 1


def test_materialization_preserves_candidate_and_reference_hashes(tmp_path):
    from experiments.unified_migration50_20260918.materialize import assemble
    from experiments.unified_migration50_20260918.prepare_review import sha
    public = tmp_path / 'bundle/public/task_001'
    public.mkdir(parents=True)
    (public / 'source.py').write_text('SOURCE = 1\n')
    (public / 'task.json').write_text('{}')
    (tmp_path / 'bundle/manifest.json').write_text('{}')
    group = {'group': 'group_001', 'tasks': ['task_001'], 'source_sha256': sha(public / 'source.py'),
             'contract_sha256': sha(public / 'task.json')}
    review = tmp_path / 'review'
    review.mkdir()
    (review / 'manifest.json').write_text(json.dumps({'translation_reuse': [group],
        'source_manifest_sha256': sha(tmp_path / 'bundle/manifest.json')}))
    generations = tmp_path / 'generations'
    directory = generations / 'group_001/direct'
    directory.mkdir(parents=True)
    (directory / 'candidate.py').write_text('CANDIDATE = 1\n')
    (directory / 'generation.json').write_text(json.dumps({'status': 'generated',
        'candidate_sha256': sha(directory / 'candidate.py')}))
    for seed in (101, 202, 303):
        trace = tmp_path / 'references/group_001/torch' / str(seed)
        trace.mkdir(parents=True)
        (trace / 'measurement.json').write_text(json.dumps({'status': 'completed', 'seed': seed}))
    for _ in range(2):
        assert assemble(review, tmp_path / 'bundle', tmp_path / 'references', generations)[0]['status'] == 'materialized'
    (review / 'private_inputs/task_001/candidate.py').write_text('CHANGED = 1\n')
    with pytest.raises(ValueError, match='existing input changed'):
        assemble(review, tmp_path / 'bundle', tmp_path / 'references', generations)


def test_native_ordinary_repair_preserves_visible_stop_and_four_round_policy(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from experiments.unified_migration50_20260918 import ordinary_repair
    n18 = tmp_path / 'native'
    (n18 / 'sources').mkdir(parents=True)
    (n18 / 'sources/manifest.json').write_text(json.dumps({'sources': [{'task_id': 'example'}]}))
    monkeypatch.setattr(ordinary_repair, 'N18', n18)
    for mode in ('visible_pass', 'always_fail'):
        review = tmp_path / mode
        public = review / 'private_inputs/task_001'
        public.mkdir(parents=True)
        (public / 'candidate.py').write_text('VALUE = 1\n')
        (public / 'task.json').write_text(json.dumps({'interface': 'public interface', 'public_context': {}}))
        manifest = {'tasks': [{'anonymous_id': 'task_001', 'original_id': 'example', 'reference_root': 'unused'}]}
        monkeypatch.setattr(ordinary_repair, 'require_approval', lambda path: manifest)
        calls = []
        def save(path, value):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value))
        def evaluate(candidate, reference, output, task, seed):
            return {'passed': mode == 'visible_pass' and seed == 101, 'stage': 'forward', 'error': 'public failure'}
        def call(messages, destination):
            calls.append(messages)
            destination.mkdir(parents=True)
            (destination / 'candidate.py').write_text('VALUE = 1\n')
            return {'status': 'generated'}
        module = SimpleNamespace(translation_prompt=lambda item, source: 'SOURCE', source_text=lambda item: 'source',
                                 digest=lambda path: 'unchanged', save=save, evaluate=evaluate, call=call)
        monkeypatch.setattr(ordinary_repair, 'native_module', lambda: module)
        result = ordinary_repair.run(review, 'task_001')
        assert result['accepted'] is False
        assert len(calls) == (0 if mode == 'visible_pass' else 4)
        assert all('"stage"' not in str(request) for request in calls)
