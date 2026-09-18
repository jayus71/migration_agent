"""Common evaluator injection into the frozen controller; paid execution is locked."""

import argparse
import hashlib
import json
from contextlib import ExitStack
from pathlib import Path
import subprocess
from unittest.mock import patch


def require_approval(run):
    manifest_path = run / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    approval = run / 'review_approval.json'
    if not approval.is_file():
        raise RuntimeError('Formal execution requires the user review receipt; preparation makes no model calls.')
    receipt = json.loads(approval.read_text())
    if (receipt.get('manifest_sha256') != hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            or receipt.get('approved_by_user') is not True):
        raise RuntimeError('Approval does not match this frozen manifest')
    for filename, expected in manifest.get('frozen_files', {}).items():
        if hashlib.sha256(Path(filename).read_bytes()).hexdigest() != expected:
            raise RuntimeError('Frozen file changed: ' + filename)
    for name, baseline in manifest.get('native_baselines', {}).items():
        command = ['git', '-C', baseline['root']]
        if subprocess.check_output(command + ['rev-parse', 'HEAD'], text=True).strip() != baseline['commit']:
            raise RuntimeError('Baseline revision changed: ' + name)
        if not baseline['use_pinned_git_archive'] and subprocess.check_output(command + ['diff', 'HEAD', '--']):
            raise RuntimeError('Baseline source was modified: ' + name)
    for image, expected in manifest.get('container_images', {}).items():
        if subprocess.check_output(['docker', 'image', 'inspect', image, '--format', '{{.Id}}'], text=True).strip() != expected:
            raise RuntimeError('Runtime image changed: ' + image)
    return manifest


def run_repair(run, task, method, python, *, variant=None, plugin=False):
    manifest = require_approval(run)
    if manifest.get('variant') != variant or manifest.get('plugin', False) != plugin:
        raise ValueError('Requested treatment differs from the reviewed manifest')
    if isinstance(manifest.get('methods'), dict) and method not in {
            value.get('adapter') for value in manifest['methods'].values()}:
        raise ValueError('Method is not included in this reviewed condition group')
    if manifest.get('translation_reuse') and task not in {g['tasks'][0] for g in manifest['translation_reuse']}:
        raise ValueError('Run only the declared representative of an identical input group')
    from autofix.autonomous import experiment
    from experiments.unified_migration50_20260918.evaluator import UnifiedEvaluator
    from experiments.unified_migration50_20260918.domain import declared_domain
    def evaluator_for(root, task_id, workspace, evidence, interpreter, current_manifest):
        row = next(row for row in current_manifest['tasks'] if row['anonymous_id'] == task_id)
        if manifest.get('benchmark') == 'unified_cross_language':
            from experiments.unified_migration50_20260918.extensions import CrossLanguageEvaluator
            return CrossLanguageEvaluator(workspace, evidence, interpreter,
                task=row['original_id'], reference=row['reference_root'])
        return UnifiedEvaluator(workspace, evidence, interpreter, kind=row['input_form'],
            runtime=manifest['runtime'], references=run / 'private_references' / task_id)
    with ExitStack() as stack:
        stack.enter_context(patch.object(experiment, 'evaluator_for', evaluator_for))
        if variant:
            if method != 'autonomous_layered' or plugin:
                raise ValueError('Component controls apply only to LaDiM')
            from autofix.autonomous import agent
            from experiments.unified_migration50_20260918.components import component_agent
            stack.enter_context(patch.object(agent, 'AutonomousAgent', component_agent(agent.AutonomousAgent, variant)))
        if plugin:
            from autofix.autonomous.baselines import MatchFixFullOrchestration
            from autofix.autonomous.swe_upstream import SWEAgentNative
            from experiments.unified_migration50_20260918.components import investigate
            cls = {'swe_native_isolated': SWEAgentNative,
                   'matchfix_full_orchestration': MatchFixFullOrchestration}[method]
            initialize, repair = cls.initialize, cls.repair
            def with_evidence(adapter, observation):
                enriched = investigate(adapter.agent, observation)
                adapter.plugin_evidence = enriched['independent_investigation']
                return initialize(adapter, enriched)
            def repair_with_evidence(adapter, observation, attempt=1):
                return repair(adapter, dict(observation, independent_investigation=adapter.plugin_evidence), attempt)
            stack.enter_context(patch.object(cls, 'initialize', with_evidence))
            stack.enter_context(patch.object(cls, 'repair', repair_with_evidence))
        with declared_domain(manifest.get('source_framework', 'PyTorch'),
                             manifest.get('target_framework', 'MindSpore')):
            return experiment.run_condition(run, task, method, python)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--task', required=True)
    parser.add_argument('--method', choices=['autonomous_layered', 'swe_native_isolated',
                                           'matchfix_full_orchestration'], required=True)
    parser.add_argument('--python', type=Path, required=True)
    parser.add_argument('--variant', choices=['continuous_role', 'without_repair_history', 'without_progress_prompt'])
    parser.add_argument('--plugin', action='store_true')
    args = parser.parse_args()
    print(json.dumps(run_repair(args.run, args.task, args.method, args.python, variant=args.variant, plugin=args.plugin)))


if __name__ == '__main__':
    main()
