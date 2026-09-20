"""Repository coordination for our agent: dependency plans, cell edits and local evidence.

All index information is extracted from the public workspace. Unit membership
and dependencies are proposed by the agent, not inferred from hidden failures.
"""
from __future__ import annotations
import ast
import copy
import hashlib
import json
from pathlib import Path

from autofix.autonomous.tools import WorkspaceTools,ToolError
from autofix.autonomous.agent import AutonomousAgent


def sha(text):return hashlib.sha256(text.encode()).hexdigest()


def inspect_python(text):
    try:tree=ast.parse(text)
    except SyntaxError as exc:return {'syntax_error':{'line':exc.lineno,'message':exc.msg},'symbols':[],'imports':[]}
    symbols=[];imports=[]
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            methods=[x.name for x in getattr(node,'body',[]) if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))]
            symbols.append({'name':node.name,'kind':type(node).__name__,'line':node.lineno,'end_line':node.end_lineno,'methods':methods})
        if isinstance(node,ast.Import):imports.extend(x.name for x in node.names)
        if isinstance(node,ast.ImportFrom):imports.append('.'*node.level+(node.module or ''))
    return {'syntax_error':None,'symbols':symbols,'imports':imports}


class RepositoryTools(WorkspaceTools):
    def __init__(self,*args,state_path,**kwargs):
        super().__init__(*args,**kwargs)
        self.state_path=Path(state_path)
        self.units={};self.active=None;self.checkpoints=[];self.revision=0
        self.focus_callback=None;self.context_start=0
        self._persist()

    def _persist(self):
        self.state_path.parent.mkdir(parents=True,exist_ok=True)
        self.state_path.write_text(json.dumps({'units':self.units,'active':self.active,'checkpoints':self.checkpoints,'revision':self.revision},indent=2))

    def inventory(self):
        rows={}
        for name in self._files():
            if not name.startswith(('source/','target/')):continue
            p=self.root/name
            if p.suffix not in ('.py','.ipynb'):continue
            text=p.read_text()
            if p.suffix=='.py':rows[name]={'sha256':sha(text),**inspect_python(text)}
            else:
                try:
                    cells=json.loads(text)['cells']
                    rows[name]={'sha256':sha(text),'cells':[{'index':i,'cell_type':c['cell_type'],
                         'lines':len(''.join(c['source']).splitlines())} for i,c in enumerate(cells)]}
                except (ValueError,KeyError,TypeError) as exc:rows[name]={'format_error':str(exc)}
        assigned={path for unit in self.units.values() for path in unit['paths']}
        return {'files':rows,'units':copy.deepcopy(self.units),'active':self.active,
                'unassigned_target_code_files':sorted(path for path in rows if path.startswith('target/') and path not in assigned),
                'index_basis':'Public syntax and imports only; dynamic dependencies are unresolved and must be investigated.',
                'completion_rule':'Unit checkpoints record local evidence only. External repository acceptance remains authoritative.'}

    def schemas(self,readonly=False):
        schemas=copy.deepcopy(super().schemas(readonly=readonly))
        edit=next(x['function'] for x in schemas if x['function']['name']=='edit')
        edit['parameters']['properties']['edits']['items']['properties']['cell']={'type':'integer','minimum':0}
        edit['description']+=' For an existing notebook code cell, optionally supply cell=<zero-based index>; old/new then refer to plain cell source, not serialized notebook JSON. Production edits must belong to the active work unit.'
        defs=[
          ('repository_map','Read the public symbol/import inventory and current work-unit graph. It supplies no fault categories or correct target code.',{},[]),
          ('notebook','Read notebook cells as plain text without execution outputs.',{'path':{'type':'string'},'start_cell':{'type':'integer','minimum':0},'max_cells':{'type':'integer','minimum':1,'maximum':20}},['path']),
          ('plan_units','Define or revise a bounded dependency plan. Choose semantic work units and justify their goals from public evidence. Dependencies must be acyclic. Revising a verified unit invalidates its prior checkpoint.',
           {'units':{'type':'array','minItems':1,'maxItems':12,'items':{'type':'object','properties':{
              'id':{'type':'string'},'paths':{'type':'array','minItems':1,'items':{'type':'string'}},
              'depends_on':{'type':'array','items':{'type':'string'}},'goal':{'type':'string'},
              'tests':{'type':'array','items':{'type':'string','enum':sorted(self.named_tests)}}},
              'required':['id','paths','depends_on','goal','tests'],'additionalProperties':False}}},['units']),
          ('focus_unit','Select a planned unit. Its declared dependencies must have current local checkpoints. Inspect cross-file interfaces before editing. Related evidence is retained when context changes.',{'id':{'type':'string'}},['id']),
          ('checkpoint_unit','Run syntax checks on the active unit and its declared public tests, then record measured evidence. It never declares final repository acceptance.',{},[])]
        for name,description,props,required in defs:
            schemas.append({'type':'function','function':{'name':name,'description':description,
                'parameters':{'type':'object','properties':props,'required':required,'additionalProperties':False}}})
        return schemas

    def execute(self,name,arguments,readonly=False,remaining_seconds=None):
        if name not in ('repository_map','notebook','plan_units','focus_unit','checkpoint_unit'):
            return super().execute(name,arguments,readonly=readonly,remaining_seconds=remaining_seconds)
        schema=next(x['function']['parameters'] for x in self.schemas(readonly=readonly) if x['function']['name']==name)
        if not isinstance(arguments,dict) or set(arguments)-set(schema['properties']) or set(schema['required'])-set(arguments):
            raise ToolError('Unknown or missing repository-tool arguments')
        if name=='repository_map':return self.inventory()
        if name=='notebook':
            path=self._path(arguments['path']);data=json.loads(path.read_text())
            start=self._integer(arguments,'start_cell',0,0,100000)
            count=self._integer(arguments,'max_cells',6,1,20)
            cells=[{'index':i,'cell_type':c['cell_type'],'source':''.join(c['source'])}
                   for i,c in enumerate(data['cells']) if start<=i<start+count]
            return {'path':arguments['path'],'cells':cells,'total_cells':len(data['cells']),'next_cell':start+count if start+count<len(data['cells']) else None}
        if name=='plan_units':return self._plan(arguments['units'])
        if name=='focus_unit':
            unit=self.units.get(arguments['id'])
            if unit is None:raise ToolError('Unknown work unit; use plan_units first')
            pending=[d for d in unit['depends_on'] if self.units[d]['status']!='checked']
            if pending:raise ToolError('Dependency checkpoints are missing or stale: '+', '.join(pending))
            self.active=arguments['id']
            if self.focus_callback:self.context_start=self.focus_callback()
            self._persist()
            return {'active':copy.deepcopy(unit),'prior_checkpoints':self.checkpoints[-6:]}
        if readonly:raise ToolError('Unit checkpoints belong to the repair role; diagnosis may use run_test')
        return self._checkpoint(remaining_seconds)

    def _plan(self,units):
        if not isinstance(units,list) or not 1<=len(units)<=12:raise ToolError('Plan requires 1 to 12 units')
        staged={}
        for unit in units:
            if not isinstance(unit,dict) or set(unit)!={'id','paths','depends_on','goal','tests'}:raise ToolError('Invalid unit fields')
            key=unit['id']
            if not isinstance(key,str) or not key or len(key)>80 or key in staged:raise ToolError('Invalid or duplicate unit id')
            if not isinstance(unit['paths'],list) or not unit['paths']:raise ToolError('Every unit requires explicit file paths')
            if not isinstance(unit['depends_on'],list) or not all(isinstance(x,str) for x in unit['depends_on']):raise ToolError('Invalid dependency list')
            if not isinstance(unit['goal'],str) or not unit['goal']:raise ToolError('Every unit requires a concrete goal')
            if not isinstance(unit['tests'],list) or any(t not in self.named_tests for t in unit['tests']):raise ToolError('Unknown public test in plan')
            for path in unit['paths']:
                self._path(path,write=True)
                if not path.startswith('target/'):raise ToolError('Work units contain target/ files only')
            old=self.units.get(key,{})
            same=all(old.get(k)==v for k,v in unit.items())
            staged[key]={**copy.deepcopy(unit),'status':old.get('status','pending') if same else 'pending'}
        visiting=set();visited=set()
        def visit(key):
            if key not in staged:raise ToolError('Unknown dependency: '+key)
            if key in visiting:raise ToolError('Work-unit dependencies contain a cycle')
            if key in visited:return
            visiting.add(key)
            for dep in staged[key]['depends_on']:visit(dep)
            visiting.remove(key);visited.add(key)
        for key in staged:visit(key)
        # A changed prerequisite invalidates downstream checks, even without a file edit.
        changed={k for k,v in staged.items() if v['status']!='checked'}
        while True:
            more={k for k,v in staged.items() if any(d in changed for d in v['depends_on'])}
            if more<=changed:break
            changed|=more
        for key in changed:
            if staged[key]['status']=='checked':staged[key]['status']='stale'
        self.units=staged
        if self.active not in staged:self.active=None
        self.revision+=1;self._persist()
        return {'units':copy.deepcopy(self.units),'active':self.active}

    def _edit(self,edits,readonly=False):
        if not isinstance(edits,list) or not edits:raise ToolError('edits must be nonempty')
        for edit in edits:
            path=edit.get('path','') if isinstance(edit,dict) else ''
            if path.startswith('target/') and not readonly:
                if self.active is None:raise ToolError('Create a plan and focus a unit before production edits')
                if path not in self.units[self.active]['paths']:raise ToolError('File is outside the active unit; revise the plan or focus the corresponding unit')
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
        result=super()._edit(regular,readonly=readonly)
        # Keep cell-sized tool observations; full file hashes still attest the transaction.
        result['edits']=copy.deepcopy(edits);self.edit_records[-1]['edits']=copy.deepcopy(edits)
        changed={r['path'] for r in result['files'] if r['path'].startswith('target/')}
        stale={key for key,unit in self.units.items() if changed.intersection(unit['paths'])}
        while True:
            extra={key for key,unit in self.units.items() if any(d in stale for d in unit['depends_on'])}
            if extra<=stale:break
            stale|=extra
        for key in stale:self.units[key]['status']='stale'
        self.revision+=1;self._persist()
        result['invalidated_units']=sorted(stale)
        return result

    def _checkpoint(self,remaining):
        if self.active is None:raise ToolError('No active unit')
        unit=self.units[self.active]
        errors=[]
        for name in unit['paths']:
            path=self._path(name)
            if not path.is_file():errors.append({'path':name,'error':'missing'});continue
            text=path.read_text()
            if path.suffix=='.py':
                error=inspect_python(text)['syntax_error']
                if error:errors.append({'path':name,**error})
            elif path.suffix=='.ipynb':
                try:
                    nb=json.loads(text)
                    if nb.get('nbformat')!=4:raise ValueError('Expected notebook format 4')
                    for index,cell in enumerate(nb['cells']):
                        if cell['cell_type']!='code':continue
                        code=''.join(cell['source']);code='\n'.join(s for s in code.splitlines() if not s.lstrip().startswith(('!','%')))
                        error=inspect_python(code)['syntax_error']
                        if error:errors.append({'path':name,'cell':index,**error})
                except (ValueError,KeyError,TypeError) as exc:errors.append({'path':name,'error':str(exc)})
        tests=[]
        if not errors:
            for name in unit['tests']:
                result=self.runner({'test':name,'timeout_seconds':min(self.max_test_seconds,remaining or self.max_test_seconds)})
                # A local numeric checkpoint excludes unrelated file-coverage failures.
                passed=result.get('numeric',{}).get('accepted',False) if name=='paired' else result.get('accepted',False)
                tests.append({'test':name,'passed':passed,'observation':result})
        passed=not errors and all(t['passed'] for t in tests)
        unit['status']='checked' if passed else 'needs_work'
        result={'unit':self.active,'local_checkpoint_passed':passed,'validation_level':'public_tests' if tests else 'syntax_only',
                'syntax_errors':errors,'tests':tests,'repository_accepted':False,'revision':self.revision}
        self.checkpoints.append(result);self._persist()
        return result


REPOSITORY_GUIDANCE='''\nThis is a repository migration. Use repository_map to inspect public interfaces, imports and notebook structure. Propose semantic work units using plan_units, preserving shared model and training interfaces. Infer unit membership and dependencies from the supplied code and actual observations; no fault classes or repair locations are supplied. Focus one ready unit before edits. Use notebook to read cells and edit with a cell index to change plain cell code, avoiding full notebook regeneration. Checkpoint completed work with declared local tests. Upstream changes invalidate dependent checkpoints. Local completion is provisional; final acceptance requires the unchanged complete-repository verifier, including actual execution of all declared entrypoints. The lifetime budget covers investigation, edits and validation for all units. Use existing execution evidence to decide when a unit is sufficiently understood, and reserve calls for dependent units and integration tests. Keep edits incremental and preserve implemented behavior across every entry point.\n'''


class RepositoryAgent(AutonomousAgent):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.history[0]['content']+=REPOSITORY_GUIDANCE
        self.tools.focus_callback=lambda:max(0,len(self.history)-1)
        self.initial_observation=None
        self.verifier_findings=None

    def diagnose(self,observation):
        self.initial_observation=copy.deepcopy(observation)
        result=super().diagnose(observation)
        self.verifier_findings=copy.deepcopy(result.diagnosis)
        return result

    def complete(self,messages,**kwargs):
        if self.tools.active and self.active_role=='fixer' and self.tools.context_start>0:
            start=min(self.tools.context_start,len(messages)-1)
            while start>0 and messages[start].get('role')=='tool':start-=1
            state={'active_unit':copy.deepcopy(self.tools.units[self.tools.active]),
                   'dependency_plan':copy.deepcopy(self.tools.units),'local_checkpoints':copy.deepcopy(self.tools.checkpoints[-6:]),
                   'independent_verifier_findings':self.verifier_findings,'initial_public_observation':self.initial_observation,
                   'context_note':'Prior unit tool transcripts remain in the audit log; inspect files or rerun a check when their details are needed. Numerical checkpoint observations above are unchanged.'}
            messages=[copy.deepcopy(messages[0]),{'role':'user','content':REPOSITORY_GUIDANCE+json.dumps(state,ensure_ascii=False)},*copy.deepcopy(messages[start:])]
            self._event('repository_context',{'active':self.tools.active,'history_start':start,'messages_sent':len(messages),'unit_count':len(self.tools.units)})
        return super().complete(messages,**kwargs)

    def _handoff_to_fixer(self):
        result=super()._handoff_to_fixer()
        self.tools.context_start=0
        self.history[0]['content']+=REPOSITORY_GUIDANCE
        return result
