"""Replay saved native outputs affected by missing runtime packages; no inference."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys

BASE = Path('/media/main/whj/projects/torch4ms')
ROOT = BASE / 'intertrans-completion-20260918'
REPO = BASE / 'ascend-torch4ms-intertrans-completion-20260918'
N18 = REPO / 'experiments/experiment_request_20260820/14_experiment_N_real_cross_language/n18'
ENGINE = BASE / 'intertrans-completion-engine-20260918/intertrans'
IMAGE = 'intertrans-n/python:n18-completion-20260918'
sys.path[:0] = [str(REPO), str(N18 / 'pairing'),
    '/media/main/whj/.autofix-intertrans/client-env/lib/python3.9/site-packages',
    str(BASE / 'external_baselines/InterTrans-84d2d43/client')]
import grpc
import yaml
from google.protobuf.json_format import MessageToDict
from intertrans import protos_pb2 as pb, protos_pb2_grpc as rpc
from autofix.backends.visible_service import serve
from external_method_adapters import ordinary
from verify_candidate import evaluate, prepare, save


def select_and_verify(task, edges, reference, *, replay_root=None):
    destination = (replay_root or ROOT / 'environment_replay') / task
    selected_path = destination / 'selection.json'
    if selected_path.exists():
        return
    for edge in edges:
        if edge.get('target_language') != 'Python':
            continue
        saved = destination / str(edge['edge_id']) / 'native_response.json'
        effective = json.loads(saved.read_text())['verification_responses'][0] if saved.exists() else edge
        tests = effective.get('unit_tests', [])
        if not tests or not all(t.get('passed', False) for t in tests):
            continue
        code = effective.get('extracted_source_code') or edge.get('extracted_source_code')
        assert code, 'Native successful edge must retain extracted source'
        destination.mkdir(parents=True, exist_ok=True)
        (destination / 'candidate.py').write_text(code)
        original = json.loads((ROOT / 'intertrans_visible_assets/public' / task / 'fixture.json').read_text())
        fixture = prepare(reference, destination / 'host_contract', task, 101)
        for name, path in fixture['context']['assets'].items():
            code = code.replace(original['context']['assets'][name], path)
        candidate = destination / 'host_candidate.py'
        candidate.write_text(code)
        scores = [evaluate(candidate, reference, destination / f'seed_{seed}', task, seed)
                  for seed in (101, 202, 303)]
        save(selected_path, dict(task=task, selected_edge_id=edge['edge_id'],
            passed=all(r['passed'] for r in scores),
            seeds=[dict(seed=r['seed'], passed=r['passed'], stage=r['stage']) for r in scores],
            real_model_calls=0, selection_order='original native response path order',
            full_program_certified=False))
        return


def replay(task, edge, reference, *, replay_root=None):
    out = (replay_root or ROOT / 'environment_replay') / task / str(edge['edge_id'])
    if (out / 'native_response.json').exists():
        return json.loads((out / 'native_response.json').read_text())['verification_responses'][0]
    out.mkdir(parents=True, exist_ok=False)
    service_dir = out / 'visible_service'
    service_dir.mkdir()
    shutil.copy2(N18 / 'intertrans/n18_check.py', service_dir / 'n18_check.py')
    calls = []
    def visible(code):
        folder = out / ('visible_' + str(len(calls)))
        folder.mkdir()
        candidate = folder / 'candidate.py'
        candidate.write_text(code)
        measured = evaluate(candidate, reference, folder / 'measurement', task, 101)
        calls.append(measured)
        return ordinary(measured)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    config = dict(numExecutionWorkers=1, numInferenceWorkers=1, serverAddress='127.0.0.1',
        serverPort=port, executionContainers={'Python': IMAGE},
        regexTemplates={'temperature': r'(?s)```(?:python|java|javascript|js)?\s*(.*?)```'},
        applyRegexInferenceOnly=True, cacheDatabasePath=str(out / 'cache'))
    (out / 'config.yaml').write_text(yaml.safe_dump(config))
    env = os.environ.copy()
    env.update(INTERTRANS_EXECUTOR='docker', INTERTRANS_N18_ASSET_ROOT=str(service_dir))
    env.pop('AUTOFIX_LLM_API_KEY', None)
    channel = grpc.insecure_channel('127.0.0.1:' + str(port),
        options=[('grpc.max_receive_message_length', 64 * 1024 * 1024)])
    with serve(service_dir, visible), (out / 'server.log').open('w') as log:
        process = subprocess.Popen([str(ENGINE), 'runserver', str(out / 'config.yaml')],
            cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            grpc.channel_ready_future(channel).result(timeout=30)
            request = pb.BatchVerificationRequest(id=task, verification_requests=[pb.VerificationRequest(
                id=task, inferenceOutput=edge['inference_output'], targetLanguage='Python',
                sourceLanguage=edge['input_language'], test_suite=pb.TestSuite(unit_test_suite=[
                    pb.UnitTestCase(language='Python', test_case=t['source_code']) for t in edge['unit_tests']]))])
            response = rpc.TranslationServiceStub(channel).BatchRunVerification(request, timeout=600)
            result = MessageToDict(response, preserving_proto_field_name=True)
            save(out / 'native_response.json', result)
        finally:
            channel.close()
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    save(out / 'audit.json', dict(real_model_calls=0, source_result=str(ROOT / 'intertrans' / task / 'response.json'),
        edge_id=edge['edge_id'], image=IMAGE, original_inference_reused=True,
        candidate_modified=False, visible_calls=len(calls)))
    return result['verification_responses'][0]


def main():
    os.environ['AUTOFIX_CANDIDATE_IMAGE'] = IMAGE
    index = json.loads((BASE / 'ascend-torch4ms-n18-348e8cd/artifacts/evidence_index.json').read_text())
    rows = []
    for path in sorted((ROOT / 'intertrans').glob('*/response.json')):
        task = path.parent.name
        response = json.loads(path.read_text())
        reference = Path(index['tasks'][task]['reference_root'])
        for record in response['translation_responses']:
            for route in record['paths']:
                for edge in route['translation_edges']:
                    if edge['target_language'] != 'Python':
                        continue
                    errors = '\n'.join(t.get('actual_output', '') for t in edge.get('unit_tests', []))
                    if 'ModuleNotFoundError' in errors and any(name in errors for name in ('torchvision', 'PIL')):
                        result = replay(task, edge, reference)
                        passed = bool(result.get('unit_tests')) and all(t.get('passed', False) for t in result['unit_tests'])
                        rows.append(dict(task=task, edge_id=edge['edge_id'], passed=passed,
                                         native_status=result.get('status')))
        edges = [edge for record in response['translation_responses']
                 for route in record['paths'] for edge in route['translation_edges']]
        outcome = json.loads((path.parent / 'result.json').read_text())
        if outcome['status'] != 'evaluated':
            select_and_verify(task, edges, reference)
    save(ROOT / 'environment_replay_summary.json', dict(real_model_calls=0, rows=rows))
    print(json.dumps(rows, indent=2))


if __name__ == '__main__':
    main()
