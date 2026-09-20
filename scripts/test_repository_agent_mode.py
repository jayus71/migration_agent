import copy
import json
from pathlib import Path
import tempfile
import unittest
import sys
from repository_timeseries_pilot import ROOT
sys.path.insert(0,str(ROOT))
from autofix.autonomous.repository import RepositoryTools,RepositoryAgent,inspect_python
from autofix.autonomous.agent import AgentConfig
from autofix.autonomous.tools import ToolError


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name);self.ws=self.base/'workspace'
        for name in ('source','target','scratch_tests'):(self.ws/name).mkdir(parents=True)
        (self.ws/'task.json').write_text('{}')
        for name in ('a.py','b.py'):
            (self.ws/'source'/name).write_text('x = 1\n')
            (self.ws/'target'/name).write_text('x = 1\n')
        nb={'nbformat':4,'nbformat_minor':5,'metadata':{},'cells':[
            {'id':'a','cell_type':'code','metadata':{},'source':['x = 1\n'],'outputs':[{'output_type':'stream','name':'stdout','text':['stale']}],'execution_count':1},
            {'id':'b','cell_type':'code','metadata':{},'source':['print(x)\n'],'outputs':[],'execution_count':2}]}
        (self.ws/'target/demo.ipynb').write_text(json.dumps(nb))
        self.tools=RepositoryTools(self.ws,lambda _: {'accepted':True,'numeric':{'accepted':True}},state_path=self.base/'state.json',validate_syntax=True)
    def tearDown(self):self.temp.cleanup()
    def plan(self):
        return [{'id':'a','paths':['target/a.py'],'depends_on':[],'goal':'first module','tests':[]},
                {'id':'b','paths':['target/b.py','target/demo.ipynb'],'depends_on':['a'],'goal':'dependent module','tests':[]}]
    def ready(self):
        self.tools.execute('plan_units',{'units':self.plan()})
        self.tools.execute('focus_unit',{'id':'a'})
        self.tools.execute('checkpoint_unit',{})
        self.tools.execute('focus_unit',{'id':'b'})
        self.tools.execute('checkpoint_unit',{})
    def test_unknown_and_cyclic_plans_are_transactional(self):
        self.tools.execute('plan_units',{'units':self.plan()});before=copy.deepcopy(self.tools.units)
        plan=self.plan();plan[0]['depends_on']=['b']
        with self.assertRaises(ToolError):self.tools.execute('plan_units',{'units':plan})
        self.assertEqual(before,self.tools.units)
        plan=self.plan();plan[1]['depends_on']=['missing']
        with self.assertRaises(ToolError):self.tools.execute('plan_units',{'units':plan})
    def test_source_and_unfocused_files_cannot_change(self):
        self.tools.execute('plan_units',{'units':self.plan()})
        for path in ('source/a.py','target/a.py'):
            with self.assertRaises(ToolError):self.tools.execute('edit',{'edits':[{'path':path,'old':'x = 1','new':'x = 2'}]})
        self.tools.execute('focus_unit',{'id':'a'})
        with self.assertRaises(ToolError):self.tools.execute('edit',{'edits':[{'path':'target/b.py','old':'x = 1','new':'x = 2'}]})
        self.assertEqual((self.ws/'target/b.py').read_text(),'x = 1\n')
    def test_dependency_edit_invalidates_transitive_checkpoints(self):
        self.ready();self.tools.execute('focus_unit',{'id':'a'})
        self.tools.execute('edit',{'edits':[{'path':'target/a.py','old':'x = 1','new':'x = 2'}]})
        self.assertEqual(self.tools.units['a']['status'],'stale')
        self.assertEqual(self.tools.units['b']['status'],'stale')
        with self.assertRaises(ToolError):self.tools.execute('focus_unit',{'id':'b'})
    def test_notebook_cell_edit_keeps_payload_small_and_clears_outputs(self):
        self.ready()
        edits=[{'path':'target/demo.ipynb','cell':0,'old':'x = 1','new':'x = 2'}]
        result=self.tools.execute('edit',{'edits':edits})
        nb=json.loads((self.ws/'target/demo.ipynb').read_text())
        self.assertEqual(''.join(nb['cells'][0]['source']),'x = 2\n')
        self.assertTrue(all(c['outputs']==[] and c['execution_count'] is None for c in nb['cells']))
        self.assertEqual(result['edits'],edits)
        self.assertNotIn('stale',json.dumps(result))
    def test_bad_cell_edit_does_not_apply_other_file_edits(self):
        self.ready();before=(self.ws/'target/demo.ipynb').read_bytes()
        with self.assertRaises(ToolError):self.tools.execute('edit',{'edits':[
            {'path':'target/b.py','old':'x = 1','new':'x = 2'},
            {'path':'target/demo.ipynb','cell':0,'old':'x = 1','new':'x = ('}]})
        self.assertEqual((self.ws/'target/b.py').read_text(),'x = 1\n')
        self.assertEqual((self.ws/'target/demo.ipynb').read_bytes(),before)
    def test_invalid_whole_notebook_rejects_the_entire_transaction(self):
        self.ready();path=self.ws/'target/demo.ipynb';before=path.read_text()
        with self.assertRaises(ToolError):self.tools.execute('edit',{'edits':[
            {'path':'target/b.py','old':'x = 1','new':'x = 2'},
            {'path':'target/demo.ipynb','old':before,'new':r'{\"nbformat\":4}'}]})
        self.assertEqual(path.read_text(),before)
        self.assertEqual((self.ws/'target/b.py').read_text(),'x = 1\n')
    def test_whole_notebook_rejects_invalid_cell_source(self):
        self.ready();path=self.ws/'target/demo.ipynb';before=path.read_text()
        bad=json.loads(before);bad['cells'][0]['source']=['x = (']
        with self.assertRaises(ToolError):self.tools.execute('edit',{'edits':[
            {'path':'target/demo.ipynb','old':before,'new':json.dumps(bad)}]})
        self.assertEqual(path.read_text(),before)
    def test_local_check_never_claims_repository_acceptance(self):
        self.ready();result=self.tools.execute('checkpoint_unit',{})
        self.assertTrue(result['local_checkpoint_passed'])
        self.assertFalse(result['repository_accepted'])
        self.assertEqual(result['validation_level'],'syntax_only')
    def test_revising_checked_prerequisite_invalidates_dependents(self):
        self.ready();plan=self.plan();plan[0]['goal']='new interface contract'
        self.tools.execute('plan_units',{'units':plan})
        self.assertEqual(self.tools.units['b']['status'],'stale')
    def test_symbol_inventory_records_parse_failures_without_guessing(self):
        r=inspect_python('from other import f\nclass C:\n def run(self): pass\n')
        self.assertEqual(r['imports'],['other']);self.assertEqual(r['symbols'][0]['methods'],['run'])
        self.assertIsNotNone(inspect_python('x = (')['syntax_error'])
    def test_diagnosis_cannot_edit_notebook(self):
        self.ready()
        with self.assertRaises(ToolError):self.tools.execute('edit',{'edits':[{'path':'target/demo.ipynb','cell':0,'old':'x = 1','new':'x = 2'}]},readonly=True)
    def test_handoff_resets_old_focus_boundary(self):
        def client(req,timeout):
            return {'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':json.dumps({'diagnosis':{'observations':['public evidence'],'evidence':['public evidence'],'locations':[]},'summary':'observed'})}}],
                    'usage':{'prompt_tokens':1,'completion_tokens':1,'total_tokens':2}}
        agent=RepositoryAgent(self.tools,self.base/'agent',config=AgentConfig(max_calls=8),client=client)
        agent.diagnose({'execution':'failed'})
        self.tools.context_start=100
        agent._handoff_to_fixer()
        self.assertEqual(self.tools.context_start,0)
        self.assertEqual(agent.active_role,'fixer')
        self.assertIn('repository_map',agent.history[0]['content'])
        self.assertEqual(agent.verifier_findings['evidence'],['public evidence'])


if __name__=='__main__':unittest.main()
