"""Offline context regression tests. All completions use an in-process fake client.

Run from the implementation checkout: python scripts/test_repository_context.py.
The module path is derived here, never from historical experiment constants.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from autofix.autonomous.repository import RepositoryAgent,RepositoryTools,serialized
from autofix.autonomous.agent import AgentConfig,BudgetExhausted
from autofix.autonomous.tools import ToolError


def answer(content=None,tools=None,reasoning='retained provider reasoning'):
    message={'role':'assistant','content':content,'reasoning_content':reasoning}
    if tools:message['tool_calls']=tools
    return {'choices':[{'finish_reason':'tool_calls' if tools else 'stop','message':message}],
            'usage':{'prompt_tokens':7,'completion_tokens':3,'completion_tokens_details':{'reasoning_tokens':1}}}


def final():
    return answer(json.dumps({'diagnosis':{'evidence':['observed mismatch'],
        'locations':[],'observations':['numeric failed'],'hypotheses':['check interface']},'summary':'remaining mismatch'}))


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name)
        self.ws=self.base/'workspace'
        for name in ('source','target','scratch_tests'):(self.ws/name).mkdir(parents=True)
        (self.ws/'task.json').write_text('{}')
        for name in ('a.py','b.py'):
            (self.ws/'source'/name).write_text('x = 1\n')
            (self.ws/'target'/name).write_text('x = 1\n')
        self.result={'accepted':False,'numeric':{'accepted':False,'checks':{'update':False},
                                               'measurements':{'update_relative_l2':.05866}}}
        self.tools=RepositoryTools(self.ws,lambda _:copy.deepcopy(self.result),
            state_path=self.base/'state.json',named_tests=('paired','workflow'))
        self.requests=[];self.responses=[]
        def client(request,timeout):
            self.assertTrue(RepositoryAgent._balanced(request['messages']))
            self.assertLessEqual(len(serialized(request['messages'])),self.agent.config.max_context_chars)
            self.requests.append(copy.deepcopy(request))
            return self.responses.pop(0) if self.responses else final()
        self.agent=RepositoryAgent(self.tools,self.base/'agent',client=client,
            config=AgentConfig(max_calls=80,max_output_tokens=480000,per_call_output_tokens=32768,
                               max_context_chars=18000,diagnosis_calls_per_stage=3,repair_calls_per_stage=3))
        self.plan=[{'id':name,'paths':['target/'+name+'.py'],'depends_on':[],
                    'goal':'migrate public module','tests':[]} for name in ('a','b')]

    def tearDown(self):self.temp.cleanup()

    def send(self):
        return self.agent.complete(self.agent.history,tool_schemas=self.tools.schemas(),stage='repair')

    def test_stable_prefix_within_unit_and_reasoning_tool_pair(self):
        self.tools.execute('plan_units',{'units':self.plan})
        self.tools.execute('focus_unit',{'id':'a'})
        self.send();prefix=copy.deepcopy(self.requests[-1]['messages'])
        call={'id':'test-1','type':'function','function':{'name':'repository_map','arguments':'{}'}}
        self.agent.history.extend([answer('inspect',tools=[call])['choices'][0]['message'],
                                   {'role':'tool','tool_call_id':'test-1','content':'{}'}])
        self.send()
        self.assertEqual(prefix,self.requests[-1]['messages'][:len(prefix)])
        self.assertEqual(self.requests[-1]['messages'][-2]['reasoning_content'],'retained provider reasoning')
        self.tools.execute('focus_unit',{'id':'a'})
        self.assertIsNone(self.agent.context_pending)

    def test_capacity_rebuild_preserves_failures_without_tool_orphans(self):
        self.tools.record_test('paired',self.result)
        call={'id':'long','type':'function','function':{'name':'read','arguments':'{}'}}
        self.agent.history.extend([answer('hypothesis: interface mismatch',tools=[call])['choices'][0]['message'],
            {'role':'tool','tool_call_id':'long','content':'notebook old output '*3000}])
        self.send()
        sent=serialized(self.requests[-1]['messages'])
        self.assertIn('0.05866',sent);self.assertIn('"update": false',self.requests[-1]['messages'][1]['content'])
        self.assertIn('hypothesis: interface mismatch',sent)
        self.assertLess(sent.count('notebook old output'),100)
        self.assertTrue(self.agent._balanced(self.requests[-1]['messages']))
        record=self.agent.context_archives[-1]
        text=(self.tools.evidence_dir/(record['id']+'.json')).read_text()
        self.assertIn('notebook old output',text)
        self.assertIn('retained provider reasoning',text)

    def test_pending_tool_batch_cannot_be_compacted(self):
        call={'id':'pending','type':'function','function':{'name':'read','arguments':'{}'}}
        self.agent.history.append(answer('pending',tools=[call])['choices'][0]['message'])
        self.agent.context_checkpoint()
        with self.assertRaisesRegex(BudgetExhausted,'unpaired'):self.send()
        self.assertEqual(self.agent.calls,0)

    def test_focus_boundary_keeps_edit_error_from_same_tool_batch(self):
        self.tools.execute('plan_units',{'units':self.plan})
        self.tools.execute('focus_unit',{'id':'b'})
        self.tools.execute('focus_unit',{'id':'a'})
        call={'id':'bad-edit','type':'function','function':{'name':'edit','arguments':'{}'}}
        error={'ok':False,'error':'Production edit requires matching active unit: target/b.py in unit b'}
        self.agent.history.extend([answer('applying patch',tools=[call])['choices'][0]['message'],
            {'role':'tool','tool_call_id':'bad-edit','content':json.dumps(error)}])
        self.send();state=json.loads(self.requests[-1]['messages'][1]['content'])
        self.assertEqual(state['latest_tool_batch'][0]['observation'],error)

    def test_latest_failure_replaces_pass_and_edit_marks_stale(self):
        self.tools.record_test('paired',{'accepted':True})
        self.tools.record_test('paired',self.result)
        self.tools.execute('plan_units',{'units':self.plan})
        self.tools.execute('focus_unit',{'id':'a'})
        self.tools.execute('edit',{'edits':[{'path':'target/a.py','old':'x = 1','new':'x = 2'}]})
        self.agent.context_checkpoint('explicit_test_boundary')
        self.send();state=json.loads(self.requests[-1]['messages'][1]['content'])
        test=state['latest_tests']['paired']
        self.assertFalse(test['observation']['accepted']);self.assertFalse(test['current'])
        self.result={'accepted':True}
        self.tools.execute('run_test',{'test':'paired'})
        self.assertTrue(self.tools.evidence_state()['paired']['current'])
        self.assertTrue(self.tools.evidence_state()['paired']['observation']['accepted'])

    def test_archive_paginated_pointer_read_is_exact_and_readonly(self):
        record=self.tools.archive_evidence('public',{'failure':False,'array':list(range(100))})
        before=(self.tools.evidence_dir/(record['id']+'.json')).read_bytes()
        parts=[];offset=0
        while True:
            result=self.tools.execute('repository_evidence',{'id':record['id'],'pointer':'/value/array',
                'offset':offset,'limit':37},readonly=True)
            parts.append(result['text'])
            if result['next_offset'] is None:break
            offset=result['next_offset']
        self.assertEqual(json.loads(''.join(parts)),list(range(100)))
        self.assertEqual(before,(self.tools.evidence_dir/(record['id']+'.json')).read_bytes())
        for args in ({'id':'../../task.json'},{'id':record['id'],'write':'oops'},
                     {'id':record['id'],'pointer':'/value/array/-1'}):
            with self.assertRaises(ToolError):self.tools.execute('repository_evidence',args)
        with self.assertRaises(ToolError):self.tools.execute('edit',{'edits':[
            {'path':'../state_evidence/'+record['id']+'.json','old':'','new':'changed'}]})

    def test_real_diagnosis_handoff_and_repair_stages_keep_latest_evidence(self):
        self.agent.set_generation_state({'written':['a.py'],'unattempted':['b.py']})
        self.agent.diagnose(self.result)
        self.agent.repair(self.result,attempt=1)
        first_calls=self.agent.calls;first_outputs=self.agent.output_tokens
        updated={'accepted':False,'numeric':{'checks':{'loss':False},'measurements':{'loss':.125}}}
        self.agent.repair(updated,attempt=2)
        sent=self.requests[-1]['messages']
        self.assertEqual(self.agent.verifier_findings['evidence'],['observed mismatch'])
        self.assertEqual(self.agent.generation_state['observation']['unattempted'],['b.py'])
        self.assertEqual(self.tools.evidence_state()['external_acceptance']['observation'],updated)
        self.assertEqual(self.agent.context_stage['attempt'],2)
        self.assertTrue(any('Repair attempt 2:' in (message.get('content') or '') for message in sent))
        self.assertGreater(self.agent.calls,first_calls);self.assertGreater(self.agent.output_tokens,first_outputs)
        self.assertEqual(self.agent.calls,len(self.requests));self.assertEqual(self.agent.output_tokens,3*len(self.requests))

    def test_budget_and_time_are_not_reset_by_boundaries(self):
        self.agent.calls=5;self.agent.output_tokens=900;self.agent.prompt_tokens=7000
        started=self.agent.started
        self.agent.context_checkpoint('controller',self.result);self.send()
        self.assertEqual((self.agent.calls,self.agent.output_tokens,self.agent.prompt_tokens),(6,903,7007))
        self.assertEqual(self.agent.started,started)

    def test_actionable_edit_scope_error_contains_legal_unit(self):
        self.tools.execute('plan_units',{'units':self.plan});self.tools.execute('focus_unit',{'id':'a'})
        with self.assertRaises(ToolError) as error:self.tools.execute('edit',{'edits':[
            {'path':'target/b.py','old':'x = 1','new':'x = 2'}]})
        self.assertIn('planned_units_for_path',str(error.exception));self.assertIn('target/a.py',str(error.exception))
        self.assertIn('"b"',str(error.exception));self.assertEqual((self.ws/'target/b.py').read_text(),'x = 1\n')

    def test_final_summary_instruction_survives_capacity_boundary(self):
        self.agent.history.append({'role':'user','content':'x'*25000})
        self.agent.history.append({'role':'assistant','content':'archived old analysis'})
        instruction='This is the final model call available in this stage. Tool execution is now disabled.'
        self.agent.history.append({'role':'user','content':instruction})
        self.send();self.assertEqual(self.requests[-1]['messages'][-1]['content'],instruction)

    def test_bootstrap_prompt_is_not_rewritten(self):
        messages=[{'role':'system','content':'generate file'},{'role':'user','content':'public code'}]
        self.agent.context_checkpoint('pending')
        self.agent.complete(messages,stage='repository_translation')
        self.assertEqual(self.requests[-1]['messages'],messages)

    def test_archive_hash_detects_external_corruption(self):
        record=self.tools.archive_evidence('test',{'accepted':False})
        (self.tools.evidence_dir/(record['id']+'.json')).write_text('{}')
        with self.assertRaisesRegex(ToolError,'integrity'):
            self.tools.execute('repository_evidence',{'id':record['id']})

    def test_archive_keeps_all_numeric_checks(self):
        result={'accepted':False,'checks':{'p'+str(i):False for i in range(120)},
                'measurements':{'p'+str(i):i*.001 for i in range(120)},'stdout':'z'*90000}
        self.tools.record_test('paired',result);self.agent.context_checkpoint();self.send()
        state=json.loads(self.requests[-1]['messages'][1]['content'])
        observed=state['latest_tests']['paired']['observation']
        self.assertEqual(observed['checks'],result['checks'])
        self.assertEqual(observed['measurements'],result['measurements'])


if __name__=='__main__':
    print('Implementation:',sys.modules['autofix.autonomous.repository'].__file__)
    unittest.main()
