"""Remove explicit work-unit planning while preserving the frozen transaction.

The _edit body is copied from the frozen RepositoryTools method, with only the
active-unit guard and dependent-checkpoint propagation removed. Tests attest
this exact source transformation; shared runtime code is never modified.
"""
import copy
import json
from autofix.autonomous.repository import RepositoryTools, RepositoryAgent, REPOSITORY_GUIDANCE
from autofix.autonomous.tools import WorkspaceTools, ToolError

REMOVED_TOOLS = {'plan_units', 'focus_unit', 'checkpoint_unit'}
NO_UNIT_GUIDANCE = """\nThis is a repository migration. Use repository_map to inspect public interfaces, imports and notebook structure. Inspect cross-file interfaces from the supplied code and actual observations; no fault classes or repair locations are supplied. Explicit work-unit planning, focus constraints and unit checkpoints are disabled. Edit any legitimate target/ path directly using the ordinary transaction and syntax checks; source/ and task.json remain immutable. Use notebook to read cells and edit with a cell index to change plain cell code, avoiding full notebook regeneration. Use run_test for measured validation. Final acceptance requires the unchanged complete-repository verifier, including actual execution of all declared entrypoints. The lifetime budget covers investigation, edits and validation for the whole repository. Use existing execution evidence to decide what needs further investigation, and reserve calls for integration tests. Keep edits incremental and preserve implemented behavior across every entry point.\n"""


class NoWorkUnitTools(RepositoryTools):
    def schemas(self, readonly=False):
        schemas = [x for x in super().schemas(readonly=readonly)
                   if x['function']['name'] not in REMOVED_TOOLS]
        for entry in schemas:
            tool = entry['function']
            if tool['name'] == 'edit':
                tool['description'] = tool['description'].replace(' Production edits must belong to the active work unit.', '')
            elif tool['name'] == 'repository_map':
                tool['description'] = 'Read the public file, symbol, import and notebook inventory. It supplies no fault categories or correct target code.'
        return schemas

    def execute(self, name, arguments, readonly=False, remaining_seconds=None):
        if name in REMOVED_TOOLS:
            raise ToolError('Explicit work-unit planning is disabled; use ordinary edit and run_test tools.')
        return super().execute(name, arguments, readonly=readonly, remaining_seconds=remaining_seconds)

    def inventory(self):
        inventory = super().inventory()
        for name in ('units', 'active', 'unassigned_target_code_files'):
            inventory.pop(name, None)
        inventory['completion_rule'] = 'External complete-repository acceptance remains authoritative.'
        return inventory

    def _edit(self,edits,readonly=False):
        if not isinstance(edits,list) or not edits:raise ToolError('edits must be nonempty')
        notebooks={};regular=[]
        for edit in edits:
            if not isinstance(edit,dict):raise ToolError('Invalid edit object')
            if 'cell' not in edit:regular.append(edit);continue
            if set(edit)!={'path','old','new','cell'}:raise ToolError('Invalid notebook edit fields')
            path=self._path(edit['path'],write=True)
            if path.suffix!='.ipynb' or type(edit['cell']) is not int or edit['cell']<0:raise ToolError('Expected notebook path and nonnegative cell index')
            if path not in notebooks:
                raw=path.read_text();notebooks[path]=(raw,json.loads(raw))
            raw,notebook=notebooks[path]
            try:cell=notebook['cells'][edit['cell']]
            except (KeyError,IndexError):raise ToolError('Notebook cell does not exist')
            if cell['cell_type']!='code':raise ToolError('Cell edits are limited to code cells')
            current=''.join(cell['source']);old,new=edit['old'],edit['new']
            if not isinstance(old,str) or not isinstance(new,str) or not old or current.count(old)!=1:raise ToolError('old must occur exactly once in the specified code cell')
            updated=current.replace(old,new,1)
            python='\n'.join(line for line in updated.splitlines() if not line.lstrip().startswith(('!','%')))
            try:compile(python,edit['path']+':cell_'+str(edit['cell']),'exec')
            except SyntaxError as exc:raise ToolError('Notebook edit has invalid Python syntax: '+str(exc))
            cell['source']=updated.splitlines(keepends=True);cell['outputs']=[];cell['execution_count']=None
        for path,(raw,notebook) in notebooks.items():
            for cell in notebook['cells']:
                if cell.get('cell_type')=='code':
                    cell['outputs']=[];cell['execution_count']=None
            regular.append({'path':path.relative_to(self.root).as_posix(),'old':raw,'new':json.dumps(notebook,ensure_ascii=False,indent=1)+'\n'})
        # Whole-file notebook edits are legal, but they need the same transaction
        # validation as cell edits. In particular, reject doubly escaped JSON
        # before writing any other file in the batch.
        staged_notebooks={}
        for edit in regular:
            if not edit.get('path','').endswith('.ipynb'):continue
            path=self._path(edit['path'],write=True)
            current=staged_notebooks.get(path,path.read_text() if path.exists() else None)
            old,new=edit.get('old'),edit.get('new')
            if not isinstance(old,str) or not isinstance(new,str):raise ToolError('Notebook old/new must be strings')
            if current is None:
                if old:raise ToolError('New notebook requires old empty')
                updated=new
            else:
                if not old or current.count(old)!=1:raise ToolError('old must occur exactly once in the notebook')
                updated=current.replace(old,new,1)
            try:
                document=json.loads(updated)
                if not isinstance(document,dict) or document.get('nbformat')!=4 or not isinstance(document.get('cells'),list):
                    raise ValueError('Expected a version 4 notebook with a cells array')
                for cell in document['cells']:
                    if not isinstance(cell,dict) or cell.get('cell_type') not in ('code','markdown','raw'):
                        raise ValueError('Malformed notebook cell')
                    source=cell.get('source')
                    if not isinstance(source,str) and not (isinstance(source,list) and all(isinstance(v,str) for v in source)):
                        raise ValueError('Notebook source must be text or an array of text lines')
                    if cell['cell_type']=='code':
                        code=''.join(source)
                        code='\n'.join(line for line in code.splitlines() if not line.lstrip().startswith(('!','%')))
                        compile(code,edit['path'],'exec')
            except (ValueError,SyntaxError,TypeError) as exc:
                raise ToolError('Notebook edit transaction was rejected: '+str(exc)) from None
            staged_notebooks[path]=updated
        result=WorkspaceTools._edit(self,regular,readonly=readonly)
        # Keep cell-sized tool observations; full file hashes still attest the transaction.
        result['edits']=copy.deepcopy(edits);self.edit_records[-1]['edits']=copy.deepcopy(edits)
        changed={r['path'] for r in result['files'] if r['path'].startswith('target/')
                 and r['before_sha256']!=r['after_sha256']}
        if changed:self.content_revision+=1
        self.revision+=1;self._persist()
        result['invalidated_units']=[]
        return result


class NoWorkUnitAgent(RepositoryAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._adapt_guidance()

    def _adapt_guidance(self):
        self.history[0]['content'] = self.history[0]['content'].replace(REPOSITORY_GUIDANCE, NO_UNIT_GUIDANCE)

    def _stage(self, stage, observation, *, attempt):
        self._adapt_guidance()
        return super()._stage(stage, observation, attempt=attempt)
