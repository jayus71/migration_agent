"""Single-factor removal of automatic public repository structure extraction."""
import copy
from autofix.autonomous.repository import RepositoryTools, RepositoryAgent

MAP_GUIDANCE = 'Use repository_map to inspect public interfaces, imports and notebook structure.'
NO_MAP_GUIDANCE = ('Use read, search and notebook to inspect public interfaces, imports and notebook structure. '
                   'repository_map returns only your current work-unit graph; automatic structure extraction is disabled.')


class NoAutomaticMapTools(RepositoryTools):
    def inventory(self):
        # Do not invoke the parent scanner: even the unassigned-file list is
        # automatic structure information. Preserve the agent's own plan.
        return {'units': copy.deepcopy(self.units), 'active': self.active,
                'index_basis': 'Automatic structure extraction is disabled. Inspect public code with read, search and notebook.',
                'completion_rule': 'Unit checkpoints record local evidence only. External repository acceptance remains authoritative.'}

    def schemas(self, readonly=False):
        result = super().schemas(readonly=readonly)
        for schema in result:
            if schema['function']['name'] == 'repository_map':
                schema['function']['description'] = ('Read your current work-unit graph. Automatic file, symbol, import and notebook-cell inventory is disabled; ordinary read, search and notebook tools remain available.')
        return result


class NoAutomaticMapAgent(RepositoryAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._adapt_guidance()

    def _adapt_guidance(self):
        self.history[0]['content'] = self.history[0]['content'].replace(MAP_GUIDANCE, NO_MAP_GUIDANCE)

    def _stage(self, stage, observation, *, attempt):
        # Independent handoff creates a new system message before entering here.
        self._adapt_guidance()
        return super()._stage(stage, observation, attempt=attempt)
