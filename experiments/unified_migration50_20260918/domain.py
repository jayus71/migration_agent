"""Adapt public source/target names while keeping the frozen repair procedure."""

from contextlib import contextmanager


@contextmanager
def declared_domain(source_framework, target_framework):
    from autofix.autonomous import agent
    names = ('SYSTEM_PROMPT', 'FIXER_PROMPT', 'EVIDENCE_SYSTEM_PROMPT', 'EVIDENCE_FIXER_PROMPT')
    original = {name: getattr(agent, name) for name in names}
    for name, value in original.items():
        value = value.replace('torch4ms/MindSpore for\nthis task', target_framework + ' for\nthis task')
        if source_framework != 'PyTorch':
            value = value.replace('Native PyTorch serves as the reference and cannot replace target\ntraining.',
                                  'The supplied ' + source_framework + ' source defines intended behavior.')
        setattr(agent, name, value)
    try:
        yield
    finally:
        for name, value in original.items():
            setattr(agent, name, value)
