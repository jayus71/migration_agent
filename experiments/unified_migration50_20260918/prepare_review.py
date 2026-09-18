"""Freeze public requests and a review matrix; never import an inference client."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess


METHODS = {
    'ladim': {'label': 'LaDiM', 'mode': 'shared_initial_then_repair',
              'adapter': 'autonomous_layered', 'runtime': 'mindspore',
              'memory_policy': 'evidence', 'workflow_policy': 'progress_loop'},
    'direct': {'label': 'Direct LLM', 'mode': 'shared_initial_only', 'runtime': 'mindspore'},
    'swe': {'label': 'SWE-agent', 'mode': 'shared_initial_then_repair',
            'adapter': 'swe_native_isolated', 'runtime': 'mindspore',
            'memory_policy': 'native', 'workflow_policy': 'standard'},
    'matchfix': {'label': 'MatchFixAgent', 'mode': 'shared_initial_then_repair',
                 'adapter': 'matchfix_full_orchestration', 'runtime': 'mindspore',
                 'memory_policy': 'native', 'workflow_policy': 'standard'},
    'msadapter': {'label': 'MSAdapter', 'mode': 'native_import_conversion', 'runtime': 'msadapter'},
    'cte': {'label': 'CodeTransEngine (direct translation)', 'mode': 'native_direct_translation',
            'runtime': 'mindspore', 'full_intertrans_search': False},
}

GENERATION = {'model': 'deepseek-v4-flash', 'temperature': 0,
              'thinking': {'type': 'enabled'}, 'reasoning_effort': 'high',
              'max_tokens': 131072}
REPAIR = {'model': 'deepseek-v4-flash', 'temperature': 0, 'thinking_mode': 'enabled',
          'reasoning_effort': 'high', 'max_calls': 40, 'max_output_tokens': 120000,
          'max_seconds': 1800, 'max_repair_attempts': 4, 'per_call_output_tokens': 16384,
          'diagnosis_calls_per_stage': 8, 'repair_calls_per_stage': 8}
SYSTEM = ('Translate the complete Python module from PyTorch to native MindSpore. '
          'Preserve its public interfaces and behavior, including differentiation and training. '
          'Use the supplied source and public task contract. Return only the complete Python module. '
          'Keep model parameter names and shapes so the common evaluator can supply identical initial values. '
          'The candidate must execute its tensor computations with MindSpore on CPU.')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--implementation', type=Path)
    parser.add_argument('--references', type=Path)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    bundle = json.loads((args.bundle / 'manifest.json').read_text())
    by_task = {row['task']: row for row in bundle['tasks']}
    assert len(by_task) == 50
    for task, row in by_task.items():
        public = args.bundle / 'public' / task
        assert sha(public / 'source.py') == row['source_sha256']
        assert sha(public / 'task.json') == row['contract_sha256']
    matrix, translations = [], []
    for index, group in enumerate(bundle['shared_translation_groups'], 1):
        group_id = f'group_{index:03d}'
        representative = group['tasks'][0]
        public = args.bundle / 'public' / representative
        contract = json.loads((public / 'task.json').read_text())
        request = {**GENERATION, 'messages': [
            {'role': 'system', 'content': SYSTEM},
            {'role': 'user', 'content': json.dumps(contract, ensure_ascii=False) +
             '\n\nsource.py:\n' + (public / 'source.py').read_text()}]}
        request_path = args.out / 'requests' / group_id / 'direct.json'
        dump(request_path, request)
        translations.append({'group': group_id, 'tasks': group['tasks'],
                             'source_sha256': group['source_sha256'],
                             'contract_sha256': group['contract_sha256'],
                             'request_sha256': sha(request_path)})
        for method, settings in METHODS.items():
            for task in group['tasks']:
                matrix.append({'task': task, 'group': group_id, 'representative': representative,
                    'method': method, 'runtime': settings['runtime'], 'status': 'awaiting_review',
                    'input_form': by_task[task]['input_form'], 'initial_generation': group_id
                    if settings['mode'].startswith('shared_initial') else None,
                    'previous_repair_results': 'retained_in_repair_analysis_not_relabelled_end_to_end',
                    'proposed_reuse_key': group_id + '/' + method})
    manifest = {'formal_execution_authorized': False, 'real_model_calls': 0,
        **REPAIR, 'runtime': 'mindspore', 'task_kind': 'framework_migration',
        'tasks': [dict(row, anonymous_id=row['task']) for row in bundle['tasks']],
        'memory_policy': {item['adapter']: item['memory_policy'] for item in METHODS.values() if 'adapter' in item},
        'workflow_policy': {item['adapter']: item['workflow_policy'] for item in METHODS.values() if 'adapter' in item},
        'status': 'review_candidate', 'implementation_commit': '694f6920ac89de66492d556e00dacb42fcd47154',
        'task_count': 50, 'unique_source_count': bundle['unique_source_bytes'],
        'unique_source_contract_groups': len(translations), 'methods': METHODS,
        'repair_budget': REPAIR, 'generation_configuration': GENERATION,
        'source_manifest_sha256': sha(args.bundle / 'manifest.json'),
        'source_bundle': str(args.bundle.resolve()),
        'reference_directory': str(args.references.resolve()) if args.references else None,
        'candidate_initialization': 'One Direct native MindSpore module per source-and-contract group',
        'translation_reuse': translations, 'table_cells': len(matrix),
        'unique_method_conditions': len(translations) * len(METHODS),
        'proposed_episode_reuse': 'Reuse only identical source, contract, initial candidate, method configuration and acceptance fingerprints. Preserve all 50 task IDs and report 29 distinct input groups.',
        'cost': {'actual_ledger': 'Every actual call, including failures and interrupted attempts, exactly once.',
                 'method_end_to_end': 'Charge shared initial translation once to each applicable method/group; shared physical calls retain a common call ID.',
                 'alias_rows': 'Do not count repeated table aliases as additional physical calls.',
                 'missing_usage': 'null; do not substitute zero or mix estimates with provider usage.'},
        'public_visibility': ['source.py', 'task.json', 'candidate.py', 'public evaluation observations',
                              'scratch tests and unmodified public runtime library'],
        'private': ['source traces', 'reference calibration targets', 'fault labels and injected locations',
                    'legacy candidate history', 'other method trajectories', 'provider credentials'],
        'acceptance': {'seeds': [101, 202, 303], 'training_steps': 2,
                       'all_required_measurements': True, 'same_initial_values': True,
                       'dtype_and_shape': 'exact', 'backend_required': True,
                       'missing_after_execution_failure': None},
        'review_decisions': ['New source semantics and four native adapter interface mappings',
                             '29 input groups under the 50 preserved task identifiers',
                             'Common native MindSpore initial translation and method integration',
                             'CodeTransEngine direct-translation configuration label',
                             'Generation and repair budgets; identical-condition reuse']}
    implementation = (args.implementation or Path(__file__).resolve().parents[2]).resolve()
    frozen = list(Path(__file__).resolve().parent.glob('*.py')) + list(Path(__file__).resolve().parent.glob('*.yaml'))
    frozen += list(Path(__file__).resolve().parent.glob('*.Dockerfile'))
    frozen += list(Path(__file__).resolve().parent.joinpath('bin').glob('*'))
    frozen += [Path(__file__).with_name('cte-native'), Path(__file__).with_name('upstream_python_script')]
    frozen += list((implementation / 'autofix/autonomous').glob('*.py'))
    frozen += [args.bundle / 'manifest.json']
    frozen += [path for path in (args.bundle / 'public').rglob('*') if path.is_file() and path.suffix in ('.py', '.json')]
    if args.references:
        traces = list(args.references.glob('group_*/torch/*/measurement.json'))
        assert len(traces) == len(translations) * 3
        frozen += traces
    manifest['frozen_files'] = {str(path.resolve()): sha(path) for path in sorted(set(frozen))}
    manifest['implementation_head'] = subprocess.check_output(['git', '-C', str(implementation), 'rev-parse', 'HEAD'], text=True).strip()
    base = Path('/media/main/whj/projects/torch4ms')
    manifest['native_baselines'] = {}
    for method, root in [('cte', base / 'third_party/CodeTransEngine-native-unified50-20260918'),
                         ('matchfix', base / 'external_baselines/MatchFixAgent-66a52a5'),
                         ('msadapter', base / 'third_party/MSAdapter-native-e-20260918'),
                         ('swe', base / 'external_baselines/SWE-agent-v1.1.0')]:
        manifest['native_baselines'][method] = {'root': str(root), 'use_pinned_git_archive': method == 'swe',
            'commit': subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()}
    manifest['container_images'] = {'unified50/cte-python:20260918': subprocess.check_output(
        ['docker', 'image', 'inspect', 'unified50/cte-python:20260918', '--format', '{{.Id}}'], text=True).strip()}
    manifest['statistical_unit'] = {'preserved_task_ids': 50, 'independent_input_groups': len(translations),
        'primary_display': 'accepted task identifiers / 50',
        'sensitivity': 'accepted distinct input groups / 29',
        'inference': 'Aliases are not independent trials. No independent-test or significance claim.'}
    manifest['feedback'] = 'All repair methods can obtain the same complete public measurements and errors. No supplied fault category or repair location.'
    manifest['cte_configuration_sha256'] = sha(Path(__file__).with_name('cte_config.yaml'))
    dump(args.out / 'manifest.json', manifest)
    dump(args.out / 'matrix.json', matrix)
    dump(args.out / 'checks.json', {'passed': True, 'real_model_calls': 0,
        'task_hashes_checked': 100, 'source_contract_groups': len(translations),
        'method_cells': dict(Counter(row['method'] for row in matrix)),
        'request_count': len(translations), 'request_inputs': 'public source and contract only'})
    treatments = {}
    for variant in ('continuous_role', 'without_repair_history', 'without_progress_prompt'):
        treatments[variant] = dict(manifest, variant=variant, methods={'ladim': METHODS['ladim']})
    for host in ('swe', 'matchfix'):
        treatments[host + '_investigation'] = dict(manifest, plugin=True, methods={host: METHODS[host]})
    additional = []
    for name, treatment in treatments.items():
        treatment['parent_manifest_sha256'] = sha(args.out / 'manifest.json')
        treatment['unique_method_conditions'] = len(translations)
        treatment['table_cells'] = 50
        dump(args.out / 'analyses' / name / 'manifest.json', treatment)
        additional += [{'analysis': name, 'group': group['group'], 'tasks': group['tasks'],
                        'representative': group['tasks'][0], 'action': 'awaiting_review',
                        'initial_translation': 'reuse_main_direct'} for group in translations]
    dump(args.out / 'analysis_matrix.json', additional)
    dump(args.out / 'budgets.json', {
        'all_values_are_upper_bounds_not_estimated_spending': True,
        'main': {'unique_method_conditions': len(translations) * 6,
                 'generation_calls': len(translations) * 2, 'repair_episodes': len(translations) * 3,
                 'maximum_calls': len(translations) * (8 + 3 * REPAIR['max_calls']),
                 'maximum_output_tokens': len(translations) * (8 * GENERATION['max_tokens'] + 3 * REPAIR['max_output_tokens'])},
        'plugin_optional': {'new_episodes': len(translations) * 2,
                            'maximum_calls': len(translations) * 2 * REPAIR['max_calls'],
                            'maximum_output_tokens': len(translations) * 2 * REPAIR['max_output_tokens']},
        'final_component_controls_optional': {'new_episodes': len(translations) * 3,
                            'maximum_calls': len(translations) * 3 * REPAIR['max_calls'],
                            'maximum_output_tokens': len(translations) * 3 * REPAIR['max_output_tokens']},
        'input_tokens': 'Measured from provider usage; not estimated from output-token caps.',
        'cte_native_retries': 'One edge per task; upstream retains up to six transport retries (seven provider attempts). The generation_calls field is nominal; maximum_calls and output caps include all seven.',
        'authorization': 'No group has execution approval.'})
    print(json.dumps({'manifest_sha256': sha(args.out / 'manifest.json'),
                      'table_cells': len(matrix), 'requests': len(translations), 'real_model_calls': 0}))


if __name__ == '__main__':
    main()
