import json
from pathlib import Path
import tempfile
import unittest
from repository_bootstrap import generation_order,parse_files,bootstrap
from autofix.autonomous.agent import AgentConfig


class BootstrapTests(unittest.TestCase):
    def test_public_import_dependency_order(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'src').mkdir()
            (p/'src/a.py').write_text('import torch\nfrom src.z import Z\n')
            (p/'src/z.py').write_text('import torch\nclass Z: pass\n')
            (p/'setup.py').write_text('x = 1\n')
            order,deps=generation_order(p)
            self.assertEqual(order,['src/z.py','src/a.py']);self.assertEqual(deps['src/a.py'],['src/z.py'])
    def test_generation_payload_rejects_paths_and_invalid_files(self):
        def r(files):return {'choices':[{'message':{'content':json.dumps({'files':files})},'finish_reason':'stop'}]}
        self.assertEqual(parse_files(r({'target/a.py':'x=1'}),['a.py']),{'a.py':'x=1'})
        for value in ({'../a.py':'x=1'},{'a.py':'x=('},{'a.py':'x=1','b.py':'x=2'}):
            with self.assertRaises((ValueError,SyntaxError)):parse_files(r(value),['a.py'])
    def test_translation_retains_source_and_lifetime_usage(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            for folder in ('source','target'):(p/folder).mkdir()
            (p/'source/a.py').write_text('import torch\nx=1\n');(p/'source/README.md').write_text('source')
            (p/'target/a.py').write_text('import torch\nx=1\n')
            class Agent:
                config=AgentConfig(per_call_output_tokens=16384);calls=7;output_tokens=100
                def _budget_status(self):return None
                def complete(self,messages,**kwargs):
                    self.calls+=1;self.output_tokens+=10
                    payload=json.loads(messages[-1]['content'])
                    files={name:('{}' if name.endswith('.json') else 'x=2' if name.endswith('.py') else 'mindspore') for name in payload['files_to_generate']}
                    return {'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'files':files})}}]}
            def save(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))
            agent=Agent();result=bootstrap(agent,p,{'source_parameter_metadata':{}},save,p/'evidence',max_calls=1)
            self.assertEqual(agent.calls,8);self.assertEqual(result['written_units'],1)
            self.assertEqual((p/'source/a.py').read_text(),'import torch\nx=1\n')
            self.assertEqual((p/'target/a.py').read_text(),'x=2')
            self.assertEqual(agent.config.per_call_output_tokens,16384)

if __name__=='__main__':unittest.main()
