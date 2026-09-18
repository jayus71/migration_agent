"""Record extension identity and generation settings without loading credentials."""

import hashlib
import json
from pathlib import Path


BASE = Path('/media/main/whj/projects/torch4ms')
PACKAGE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def request_configuration(value, prefix=''):
    found = {}
    fields = {'model', 'model_name', 'temperature', 'max_tokens', 'max_completion_tokens',
              'max_output_tokens', 'thinking', 'reasoning_effort', 'seed'}
    if isinstance(value, dict):
        for key, child in value.items():
            if key in fields:
                found[prefix + key] = child
            elif isinstance(child, dict) and key not in ('messages', 'response', 'headers'):
                found.update(request_configuration(child, prefix + key + '.'))
    return found


def main():
    current = BASE / 'ascend-torch4ms-n18-remediation-3eb9150/artifacts/n18_prepared_20260917'
    rows = []
    for path in sorted((current / 'direct_llm').glob('*/initial/request.json')):
        request = read(path)
        response = read(path.with_name('response.json'))
        generation = read(path.with_name('generation.json'))
        rows.append({'task': path.parent.parent.name, 'request_keys': sorted(request),
                     'settings': request_configuration(request),
                     'finish_reasons': [choice.get('finish_reason') for choice in response.get('choices', [])],
                     'usage_matches': response.get('usage') == generation.get('usage'),
                     'usage': response.get('usage'), 'request_sha256': sha(path)})
    assert len(rows) == 18
    jax = BASE / 'experiments/maintext_jax_autonomous_20260918/formal_v5'
    old_agent = jax / 'code_snapshot/autofix/autonomous/agent.py'
    new_agent = PACKAGE.parents[1] / 'autofix/autonomous/agent.py'
    import difflib
    diff = ''.join(difflib.unified_diff(old_agent.read_text().splitlines(True),
        new_agent.read_text().splitlines(True), fromfile='jax_historical_agent.py', tofile='current_agent.py'))
    (PACKAGE / 'jax_implementation.diff').write_text(diff)
    old = read(jax / 'manifest.json')
    report = {'real_model_calls': 0, 'cross_language_direct': rows,
        'jax': {'manifest_sha256': sha(jax / 'manifest.json'),
                'old_agent_sha256': sha(old_agent), 'current_agent_sha256': sha(new_agent),
                'agent_bytes_equal': old_agent.read_bytes() == new_agent.read_bytes(),
                'method_rows': len(old['tasks']) * len(old['methods']),
                'direct_action': 'retain six completed current-task results',
                'ladim_action': 'preserve original configuration evidence; six current-configuration conditions remain optional and unlaunched',
                'converter_action': 'retain fault-input evidence separately; no healthy-source end-to-end claim'},
        'cross_language_matrix': {'reused': 36, 'new_protocol_conditions': 72,
                                 'new_generation_calls_for_shared_initials': 0}}
    (PACKAGE / 'extension_configuration_audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'direct_requests': len(rows), 'configurations': sorted({json.dumps(r['settings'], sort_keys=True) for r in rows}),
                      'usage_matches': sum(row['usage_matches'] for row in rows), 'jax': report['jax']}, indent=2))


if __name__ == '__main__':
    main()
