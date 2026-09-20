import copy
from dataclasses import replace
import tempfile
import unittest
from pathlib import Path
from continue_repository_twotower import CachedContinuationAgent, RepositoryTools, AgentConfig
from autofix.autonomous.agent import AutonomousAgent


class ContinuationTests(unittest.TestCase):
    def test_exact_request_replay_and_append_only_prefix(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);ws=root/'workspace';ws.mkdir()
            for name in ('source','target','scratch_tests'):(ws/name).mkdir()
            calls=[]
            def client(request,timeout):
                calls.append(copy.deepcopy(request))
                return {'model':'deepseek-flash','usage':{'prompt_tokens':3,'completion_tokens':4},
                        'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':'ok'}}]}
            tools=RepositoryTools(ws,lambda args:{'accepted':False},named_tests=('public',),state_path=root/'state.json')
            agent=CachedContinuationAgent(tools,root/'logs',config=AgentConfig(per_call_output_tokens=100),client=client)
            history=[{'role':'system','content':'unchanged system'},{'role':'user','content':'unchanged task'}]
            agent.history=copy.deepcopy(history)
            AutonomousAgent.complete(agent,history,tool_schemas=tools.schemas(readonly=False))
            original=copy.deepcopy(calls[-1])
            agent.replay_request=copy.deepcopy(original)
            agent.config=replace(agent.config,per_call_output_tokens=32768)
            agent.complete(history+[{'role':'user','content':'stage setup must not enter replay'}])
            retried=copy.deepcopy(calls[-1]);self.assertEqual(retried.pop('max_tokens'),32768)
            expected=copy.deepcopy(original);expected.pop('max_tokens');self.assertEqual(retried,expected)
            self.assertEqual(agent.calls,2);self.assertEqual(agent.output_tokens,8)
            agent.history.append({'role':'assistant','content':'ok'})
            agent.complete(agent.history)
            self.assertEqual(calls[-1]['messages'][:len(history)],history)
            with self.assertRaises(ValueError):agent.complete([{'role':'system','content':'changed'}])


if __name__=='__main__':unittest.main()
