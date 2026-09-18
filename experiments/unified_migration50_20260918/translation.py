"""One generation per frozen input fingerprint; formal calls require review."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from experiments.unified_migration50_20260918.integration import require_approval


BASE = Path('/media/main/whj/projects/torch4ms')


def extract(text):
    blocks = re.findall(r'```(?:python|py)?\s*\n(.*?)```', text, re.S)
    return ('\n\n'.join(blocks) if blocks else text).strip() + '\n'


def cte_request(source, contract, task):
    sys.path[:0] = [str(BASE / 'ascend-torch4ms-exp-e-final-5f3351f/.experiment_deps/cte_client'),
                   str(BASE / 'third_party/CodeTransEngine-native-unified50-20260918/client')]
    from intertrans import protos_pb2 as pb
    request = pb.TranslationRequest(seed_language='PyTorch', target_language='Python',
        seed_code=source + '\n\n# Public task contract:\n' +
                  '\n'.join('# ' + line for line in json.dumps(contract, indent=2).splitlines()),
        prompt_template_name='prompt_codenet_mindspore', regex_template_name='temperature',
        model_name='deepseek-v4-flash', id=task)
    request.used_languages.extend(['PyTorch', 'Python'])
    test = ('import unittest\nclass PublicInterfaceTest(unittest.TestCase):\n'
            '    def test_public_interfaces(self):\n'
            f'        for name in {contract.get("public_interfaces", [])!r}:\n'
            '            self.assertIn(name, globals())\n'
            '            self.assertTrue(callable(globals()[name]))\n'
            'if __name__ == "__main__":\n    unittest.main()\n')
    request.test_suite.unit_test_suite.append(pb.UnitTestCase(language='Python', test_case=test))
    batch = pb.BatchTranslationRequest()
    batch.translation_requests.append(request)
    return batch


def cte_candidate(response):
    translations = response.get('translation_responses', [])
    if len(translations) != 1:
        raise ValueError('Expected one native translation response')
    paths = translations[0].get('paths', [])
    edges = {edge['edge_id']: edge for path in paths
             for edge in path.get('translation_edges', [])}
    target_edges = [edge for edge in edges.values()
                    if edge.get('target_language') == 'Python'
                    and edge.get('extracted_source_code')]
    if len(target_edges) > 1:
        raise ValueError('Direct translation produced multiple candidates; selection is not declared')
    return target_edges[0]['extracted_source_code'] if target_edges else ''


def generate(request, output, *, method, group, client):
    """Archive every attempted transport, including errors, before returning."""
    if output.exists():
        raise FileExistsError('A prior attempt exists; failures are not regenerated')
    output.mkdir(parents=True)
    (output / 'request.json').write_text(json.dumps(request, indent=2) + '\n')
    record = {'method': method, 'group': group, 'status': 'started', 'transport_calls': 1,
              'real_model_calls': 1 if method == 'direct' else None,
              'usage': None, 'usage_kind': 'unavailable'}
    try:
        response = client(request)
        (output / 'response.json').write_text(json.dumps(response, indent=2) + '\n')
        if method == 'direct':
            choice = response['choices'][0]
            content = choice['message'].get('content') or ''
            code = extract(content)
            record.update(usage=response.get('usage'), finish_reason=choice.get('finish_reason'))
            record['usage_kind'] = 'provider' if record['usage'] is not None else 'unavailable'
        else:
            code = cte_candidate(response)
            if '_provider_ledger' in response:
                record.update(real_model_calls=response['_provider_ledger']['calls'],
                              usage=response['_provider_ledger']['usage'],
                              provider_ledger=response['_provider_ledger'])
                record['usage_kind'] = 'provider' if record['usage'] is not None else 'partial_provider'
        (output / 'candidate.py').write_text(code)
        record.update(status='generated' if code.strip() else 'generation_failed',
                      candidate_sha256=hashlib.sha256(code.encode()).hexdigest())
    except Exception as exc:
        record.update(status='transport_or_protocol_error', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        (output / 'generation.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--group', required=True)
    parser.add_argument('--method', choices=['direct', 'cte'], required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    manifest = require_approval(args.review)
    group = next(row for row in manifest['translation_reuse'] if row['group'] == args.group)
    if args.out.exists():
        raise FileExistsError('A prior attempt exists; completed failures are not regenerated')
    public = args.bundle / 'public' / group['tasks'][0]
    assert hashlib.sha256((public / 'source.py').read_bytes()).hexdigest() == group['source_sha256']
    assert hashlib.sha256((public / 'task.json').read_bytes()).hexdigest() == group['contract_sha256']
    if args.method == 'direct':
        from autofix.autonomous.agent import OpenAICompatibleClient
        request_path = args.review / 'requests' / args.group / 'direct.json'
        assert hashlib.sha256(request_path.read_bytes()).hexdigest() == group['request_sha256']
        request = json.loads(request_path.read_text())
        client = OpenAICompatibleClient()
        call = lambda request: client(request, 1800)
    else:
        from google.protobuf.json_format import MessageToDict
        batch = cte_request((public / 'source.py').read_text(), json.loads((public / 'task.json').read_text()), args.group)
        from intertrans.utils import submit_request
        request = MessageToDict(batch, preserving_proto_field_name=True)
        from experiments.unified_migration50_20260918.cte_service import native_engine, aggregate
        def call(request):
            with native_engine(args.out.resolve() / 'provider') as (server, ledger):
                response = MessageToDict(submit_request(batch, server), preserving_proto_field_name=True)
            response['_provider_ledger'] = aggregate(ledger)
            return response
    generate(request, args.out, method=args.method, group=args.group, client=call)


if __name__ == '__main__':
    main()
