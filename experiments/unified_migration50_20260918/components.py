"""Final-method component controls and a read-only investigation plugin."""

import copy
from dataclasses import replace


VARIANTS = ('continuous_role', 'without_repair_history', 'without_progress_prompt')


def component_agent(base, variant):
    if variant not in VARIANTS:
        raise ValueError(variant)

    class ComponentAgent(base):
        def _handoff_to_fixer(self):
            if variant == 'continuous_role':
                self.verifier_history = copy.deepcopy(self.history)
                self.active_role = 'continuous_agent'
                self._event('ablation_continuous_role', {'history_preserved': True})
                self._snapshot()
                return
            super()._handoff_to_fixer()
            if variant == 'without_repair_history':
                old = 'Your conversation persists across repair attempts.'
                new = ('Each repair attempt starts from the initial verifier investigation and the latest observation. '
                       'Earlier repair conversations are not retained; the current workspace is retained.')
                assert self.history[0]['content'].count(old) == 1
                self.history[0]['content'] = self.history[0]['content'].replace(old, new)

        def repair(self, observation, attempt=1):
            if variant == 'without_repair_history':
                if not hasattr(self, 'initial_handoff'):
                    self._handoff_to_fixer()
                    self.initial_handoff = copy.deepcopy((self.history, self.handoff_tool_records, self.last_diagnosis))
                elif attempt > 1:
                    self.history, self.handoff_tool_records, self.last_diagnosis = copy.deepcopy(self.initial_handoff)
                    self._event('ablation_history_reset', {'attempt': attempt, 'lifetime_budget_reset': False})
            return super().repair(observation, attempt)

        def _event(self, kind, value):
            if variant == 'without_progress_prompt' and kind == 'stage_progress_checkpoint':
                assert self.history[-1] == {'role': 'user', 'content': value['feedback']}
                self.history.pop()
                return super()._event('ablation_progress_prompt_omitted', value)
            return super()._event(kind, value)

    return ComponentAgent


def investigate(host, observation):
    """Use the host's actual call/token/time ledger; restore native host history."""
    from autofix.autonomous import agent
    from autofix.autonomous.evaluation import snapshot
    saved = {name: copy.deepcopy(getattr(host, name)) for name in (
        'history', 'tool_records', 'handoff_tool_records', 'verifier_history', 'last_diagnosis', 'active_role')}
    config = host.config
    before = snapshot(host.tools.root, host.log_dir / 'plugin_before')
    host.config = replace(config, method='layered', memory_policy='evidence',
                          workflow_policy='progress_loop', diagnosis_policy='evidence')
    host.history = [{'role': 'system', 'content': agent.EVIDENCE_SYSTEM_PROMPT}]
    host.active_role = 'verifier'
    host.verifier_history = None
    start = host.calls
    try:
        stage = host.diagnose(observation)
        transcript = []
        for message in host.history:
            if message['role'] != 'system':
                transcript.append({key: value for key, value in message.items() if key != 'reasoning_content'})
        evidence = {'status': stage.status, 'diagnosis': stage.diagnosis, 'records': transcript,
                    'scope': 'Read-only investigation using public inputs and observations.'}
        host._write('plugin_evidence.json', evidence)
        after = snapshot(host.tools.root, host.log_dir / 'plugin_after')
        if before != after:
            raise RuntimeError('Investigation modified production files')
        host._event('plugin_completed', {'calls': host.calls - start, 'lifetime_budget_reset': False,
                                        'production_unchanged': True})
        return dict(observation, independent_investigation=evidence)
    finally:
        host.config = config
        for name, value in saved.items():
            setattr(host, name, value)
        host._snapshot()
