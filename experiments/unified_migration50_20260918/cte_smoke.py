"""Exercise the native CodeTransEngine server against a loopback fake provider."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket
import subprocess
from threading import Thread
from unittest.mock import patch

import yaml
from google.protobuf.json_format import MessageToDict

from experiments.unified_migration50_20260918.translation import cte_request, cte_candidate, BASE
from experiments.unified_migration50_20260918.cte_service import native_engine, aggregate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=False)
    batch = cte_request('import torch\ndef workload(value):\n    return torch.relu(value)\n',
                        {'target_framework': 'MindSpore', 'public_interfaces': ['workload']}, 'offline')
    import grpc
    requests = []
    code = 'import mindspore as ms\ndef workload(value):\n    return ms.ops.relu(value)\n'
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            request = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append(request)
            body = json.dumps({'id': 'offline', 'object': 'chat.completion', 'created': 0,
                'model': 'deepseek-v4-flash', 'choices': [{'index': 0, 'finish_reason': 'stop',
                    'message': {'role': 'assistant', 'content': '```python\n' + code + '```'}}],
                'usage': {'prompt_tokens': 10, 'completion_tokens': 20, 'total_tokens': 30}}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with patch.dict(os.environ, AUTOFIX_LLM_API_KEY='offline-placeholder',
                        AUTOFIX_LLM_BASE_URL=f'http://127.0.0.1:{server.server_port}/v1'), \
             native_engine(output / 'native') as (endpoint, ledger):
            from intertrans import protos_pb2_grpc
            with grpc.insecure_channel(endpoint) as channel:
                answer = protos_pb2_grpc.TranslationServiceStub(channel).BatchTranslate(batch, timeout=45)
            data = MessageToDict(answer, preserving_proto_field_name=True)
            (output / 'native_response.json').write_text(json.dumps(data, indent=2))
            (output / 'provider_requests.json').write_text(json.dumps(requests, indent=2))
            assert cte_candidate(data).strip() == code.strip(), data
            edges = [edge for item in data['translation_responses'] for path in item['paths']
                     for edge in path['translation_edges']]
            assert all(test.get('passed') is True for edge in edges for test in edge.get('unit_tests', [])), data
            assert any(edge.get('unit_tests') for edge in edges), data
            assert len(requests) == 1, requests
            assert requests[0]['model'] == 'deepseek-v4-flash'
            assert aggregate(ledger)['usage']['total_tokens'] == 30
            report = {'passed': True, 'native_server': True, 'native_parser': True,
                      'scripted_provider_calls': len(requests), 'real_model_calls': 0,
                      'usage_recording_proxy': True,
                      'native_public_tests_passed': True,
                      'provider_request_fields': sorted(requests[0])}
            (output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
            print(json.dumps(report))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


if __name__ == '__main__':
    main()
