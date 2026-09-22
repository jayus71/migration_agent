import copy,json,unittest
from dataclasses import replace
from test_repository_context import ContextTests,answer
from autofix.autonomous.repository import serialized

class ContextFixTests(unittest.TestCase):
    setUp=ContextTests.setUp
    tearDown=ContextTests.tearDown
    send=ContextTests.send
    def test_first_focus_keeps_entire_prefix(self):
        self.agent.config=replace(self.agent.config,max_context_chars=100000)
        self.agent.history.append({'role':'user','content':'observed source '+('code '*6000)})
        self.send(); before=copy.deepcopy(self.agent.history)
        self.tools.execute('plan_units',{'units':self.plan})
        self.tools.execute('focus_unit',{'id':'a'})
        self.assertIsNone(self.agent.context_pending)
        self.send();self.assertEqual(before,self.requests[-1]['messages'])

    def test_next_repair_stage_continues_prefix(self):
        self.agent.config=replace(self.agent.config,max_context_chars=100000)
        self.agent.repair(self.result,attempt=1)
        before=copy.deepcopy(self.agent.history);generation=self.agent.context_generation
        self.agent.repair(self.result,attempt=2)
        self.assertEqual(generation,self.agent.context_generation)
        self.assertEqual(before,self.requests[-1]['messages'][:len(before)])

    def test_measurement_currency_tracks_only_target_changes(self):
        self.tools.record_test('paired',self.result)
        self.tools.execute('plan_units',{'units':self.plan})
        self.tools.execute('focus_unit',{'id':'a'})
        self.assertTrue(self.tools.evidence_state()['paired']['current'])
        (self.ws/'scratch_tests'/'trial.py').write_text('x = 1\n')
        for path,new in [('scratch_tests/trial.py','x = 2'),('target/a.py','x = 1')]:
            self.tools.execute('edit',{'edits':[{'path':path,'old':'x = 1','new':new}]})
            self.assertTrue(self.tools.evidence_state()['paired']['current'])
        self.tools.execute('edit',{'edits':[{'path':'target/a.py','old':'x = 1','new':'x = 3'}]})
        self.assertFalse(self.tools.evidence_state()['paired']['current'])
        self.assertEqual(self.tools.content_revision,1)

    def retrieve(self,record,pointer):
        chunks=[];offset=0
        while True:
            result=self.tools.execute('repository_evidence',{'id':record['id'],'pointer':pointer,'offset':offset,'limit':12000})
            chunks.append(result['text']);offset=result['next_offset']
            if offset is None:return json.loads(''.join(chunks))

    def test_switch_and_capacity_preserve_current_read_views(self):
        self.agent.config=replace(self.agent.config,max_context_chars=100000)
        self.tools.execute('plan_units',{'units':self.plan})
        self.tools.execute('focus_unit',{'id':'a'})
        a=self.tools.execute('read',{'path':'target/a.py'})
        b=self.tools.execute('read',{'path':'target/b.py'})
        self.tools.execute('focus_unit',{'id':'b'});self.send()
        state=json.loads(self.requests[-1]['messages'][1]['content'])
        reads=state['working_set']['read_results']
        self.assertEqual([r['path'] for r in reads],['target/b.py']);self.assertEqual(reads[0]['result'],b)
        self.assertEqual(self.retrieve(reads[0],'/value/result'),b)
        omitted=self.tools.working_set(0)['omitted_current_reads']
        self.assertEqual(self.retrieve(omitted[0],'/value/result'),b)
        self.agent.history.append({'role':'user','content':'old evidence '*8000})
        self.agent.history.append({'role':'assistant','content':'boundary'})
        self.send();state=json.loads(self.requests[-1]['messages'][1]['content'])
        self.assertEqual(state['reason'],'context_capacity')
        self.assertEqual(state['working_set']['read_results'][0]['result'],b)
        self.tools.execute('edit',{'edits':[{'path':'target/b.py','old':'x = 1','new':'x = 4'}]})
        self.assertEqual(self.tools.working_set(10000)['read_results'],[])

    def test_full_final_fields_and_note_pointers(self):
        self.agent.config=replace(self.agent.config,max_context_chars=150000)
        final={'diagnosis':{'evidence':['observed']},'hypotheses':[{'mechanism':'m'*1800,'evidence':'e'*1600,'falsification_test':'run test','status':'open'} for _ in range(5)],'summary':'next action '*300,'arbitrary_future_field':{'x':[1,2,3]}}
        self.responses.append(answer(serialized(final)));response=self.send()
        self.agent.history.append(response['choices'][0]['message'])
        self.agent.context_checkpoint('explicit');self.send()
        state=json.loads(self.requests[-1]['messages'][1]['content'])
        public=state['latest_public_finals'][self.agent.active_role]
        self.assertEqual(public['observation'],final);self.assertEqual(self.retrieve(public,public['pointer']),final)
        note=state['recent_agent_notes'][-1]
        self.assertEqual(note['observation'],final);self.assertEqual(self.retrieve(note,note['pointer']),final)

if __name__=='__main__':unittest.main()

