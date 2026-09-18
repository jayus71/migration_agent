"""Run the unchanged native engine with a local provider-usage recording proxy."""

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket
import subprocess
from threading import Thread, Lock
import urllib.error
import urllib.request

import yaml

from experiments.unified_migration50_20260918.translation import BASE


@contextmanager
def native_engine(output):
    import grpc
    key = os.environ['AUTOFIX_LLM_API_KEY']
    base = os.environ.get('AUTOFIX_LLM_BASE_URL', 'https://api.deepseek.com').rstrip('/')
    endpoint = base if base.endswith('/chat/completions') else base + '/chat/completions'
    output.mkdir(parents=True, exist_ok=False)
    lock, records = Lock(), []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            data = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data)
            with lock:
                folder = output / f'call_{len(records) + 1:04d}'
                folder.mkdir()
                record = {'usage': None, 'http_status': None, 'response_received': False}
                records.append(record)
            (folder / 'request.json').write_text(json.dumps(request, indent=2))
            if request.get('model') != 'deepseek-v4-flash':
                self.send_error(400, 'Only the frozen DeepSeek model is allowed')
                return
            outgoing = urllib.request.Request(endpoint, data=data, headers={
                'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key})
            try:
                with urllib.request.urlopen(outgoing, timeout=1800) as result:
                    body, status = result.read(), result.status
            except urllib.error.HTTPError as exc:
                body, status = exc.read(), exc.code
            except Exception as exc:
                body, status = json.dumps({'error': {'message': type(exc).__name__}}).encode(), 502
            record.update(http_status=status, response_received=True)
            (folder / 'response.json').write_bytes(body)
            try:
                record['usage'] = json.loads(body).get('usage')
            except (ValueError, AttributeError):
                pass
            (folder / 'ledger.json').write_text(json.dumps(record, indent=2))
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *args):
            pass
    proxy = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=proxy.serve_forever, daemon=True)
    thread.start()
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    configuration = yaml.safe_load(Path(__file__).with_name('cte_config.yaml').read_text())
    configuration.update(serverPort=str(port), inferenceApiBaseUrls=[f'http://127.0.0.1:{proxy.server_port}/v1'],
                         inferenceApiToken='local-proxy', cacheDatabasePath=str(output / 'cache'))
    config = output / 'config.yaml'
    config.write_text(yaml.safe_dump(configuration, sort_keys=False))
    process = None
    try:
        with (output / 'engine.log').open('w') as stream:
            environment = {name: value for name, value in os.environ.items()
                           if not any(word in name.upper() for word in ('API_KEY', 'TOKEN', 'SECRET', 'PASSWORD'))}
            environment['PATH'] = str(Path(__file__).with_name('bin')) + os.pathsep + environment.get('PATH', '')
            process = subprocess.Popen([str(Path(__file__).with_name('cte-native')), 'runserver', str(config)],
                                       cwd=output, env=environment, stdout=stream, stderr=subprocess.STDOUT)
            address = f'127.0.0.1:{port}'
            with grpc.insecure_channel(address) as channel:
                grpc.channel_ready_future(channel).result(timeout=30)
            yield address, records
    finally:
        if process is not None:
            process.terminate()
            process.wait(timeout=15)
        proxy.shutdown()
        proxy.server_close()
        thread.join(timeout=5)
        (output / 'ledger.json').write_text(json.dumps({'calls': len(records), 'records': records}, indent=2) + '\n')


def aggregate(records):
    fields = ('prompt_tokens', 'completion_tokens', 'total_tokens')
    known = {field: sum(row['usage'][field] for row in records
                       if isinstance((row.get('usage') or {}).get(field), int)) for field in fields}
    complete = all(all(isinstance((row.get('usage') or {}).get(field), int) for field in fields) for row in records)
    return {'calls': len(records), 'usage': known if complete else None, 'known_usage_lower_bound': known,
            'unknown_usage_calls': sum(not all(isinstance((row.get('usage') or {}).get(f), int) for f in fields) for row in records)}
