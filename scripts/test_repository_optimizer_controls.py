"""Offline optimizer-interface checks using isolated tiny native fixtures.

No model API calls and no changes to historical candidates. Numerical fixtures
exercise the actual candidate worker with MindSpore on CPU; the source comparison
uses already saved measurements. Fixture code is never supplied to an agent.
"""
from __future__ import annotations
import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
WORKER=ROOT/'scripts/repository_twotower_candidate_worker.py'
OLD=Path('/media/main/whj/projects/torch4ms/ascend-torch4ms-repository-pilot-20260920')
REFERENCE=OLD/'experiments/repository_twotower_20260920/references/101.json'
EVIDENCE={}

MODEL='''import mindspore as ms
from mindspore import nn, Parameter, Tensor
class TwoTowerBaseRetrieval(nn.Cell):
    def __init__(self,mips_module):
        super().__init__()
        self.weight=Parameter(Tensor([1.0],ms.float32),name='weight')
        self.mips_module=mips_module
    def construct(self,user_id,user_features,user_history):
        return Tensor([[0]],ms.int32)
    def compute_user_embedding(self,*args):return self.weight
    def compute_item_embeddings(self,*args):return self.weight
    def train_forward(self,user_id,user_features,user_history,item_id,item_features,position,labels):
        return (self.weight*self.weight).sum()
'''
TRAINER='''import json
from pathlib import Path
import mindspore as ms
from mindspore import nn, Tensor
from src.baseline_mips_module import BaselineMIPSModule
from src.two_tower_base_retrieval import TwoTowerBaseRetrieval
MARKER=Path(__file__).with_name('fixture_marker.json')
LAST_OPTIMIZER=None
def mark(key):
    value=json.loads(MARKER.read_text()) if MARKER.exists() else {}
    value[key]=value.get(key,0)+1
    MARKER.write_text(json.dumps(value))
FACTORY
def train_one_epoch(model,dataloader,optimizer,device):
    if optimizer is not LAST_OPTIMIZER:raise RuntimeError('Candidate factory optimizer was replaced')
    mark('returned_optimizer_used')
    gradient=ms.value_and_grad(model.train_forward,None,model.trainable_params())
    loss=None
    for batch in dataloader:
        loss,grads=gradient(*batch)
        optimizer(grads)
    return float(loss.asnumpy())
if __name__=='__main__':
    model=TwoTowerBaseRetrieval(BaselineMIPSModule(1,1))
    CLI_OPTIMIZER
    batch=(Tensor([0],ms.int32),Tensor([[1.]],ms.float32),Tensor([[0]],ms.int32),Tensor([0],ms.int32),Tensor([[1.]],ms.float32),Tensor([0],ms.int32),Tensor([[1.]],ms.float32))
    for _ in range(2):train_one_epoch(model,[batch],optimizer,'CPU')
'''
FACTORY='''def make_optimizer(model,learning_rate=.001):
    global LAST_OPTIMIZER
    mark('factory_called')
    LAST_OPTIMIZER=nn.SGD(model.trainable_params(),learning_rate=learning_rate)
    return LAST_OPTIMIZER
'''


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


class OptimizerControls(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='optimizer-interface-controls-')
        self.base=Path(self.tmp.name);self.repo=self.base/'candidate'
        for folder in ('src','train'):
            p=self.repo/folder;p.mkdir(parents=True);(p/'__init__.py').write_text('')
        (self.repo/'src/two_tower_base_retrieval.py').write_text(MODEL)
        (self.repo/'src/baseline_mips_module.py').write_text('import mindspore as ms\nclass BaselineMIPSModule:\n    def __init__(self,*args):self.corpus=ms.Tensor([1.],ms.float32)\n')
        (self.repo/'parameter_map.json').write_text(json.dumps({'shared':{'weight':'weight'}}))
        batch={'user_id':[0],'user_features':[[1.]],'user_history':[[0]],'item_id':[0],
               'item_features':[[1.]],'position':[0],'labels':[[1.]]}
        request={'seed':101,'batches':[batch,batch,batch],
                 'cases':{'base':{'initial_state':{'weight':[1.]},'corpus':[1.]}}}
        self.request=self.base/'input.json';self.request.write_text(json.dumps(request))
        self.write_trainer()

    def tearDown(self):self.tmp.cleanup()

    def write_trainer(self,factory=FACTORY,cli='optimizer=make_optimizer(model,learning_rate=.001)'):
        (self.repo/'train/train.py').write_text(TRAINER.replace('FACTORY',factory).replace('CLI_OPTIMIZER',cli))

    def invoke(self,mode='numeric'):
        out=self.base/('result_'+mode+'.json')
        args=[sys.executable,str(WORKER),'--repository',str(self.repo),'--mode',mode,'--output',str(out)]
        if mode=='numeric':args+=['--case','base','--input',str(self.request)]
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
        process=subprocess.run(args,capture_output=True,text=True,timeout=90,env=env)
        self.assertEqual(process.returncode,0,process.stdout+process.stderr)
        self.assertTrue(out.exists(),process.stdout+process.stderr)
        return json.loads(out.read_text())

    def test_candidate_factory_and_returned_optimizer_are_used(self):
        result=self.invoke();training=result['cases']['base']['training']
        self.assertEqual(training['status'],'ok');self.assertEqual(training['native_autodiff_calls'],3)
        self.assertLess(training['steps'][0]['state']['weight'][0],1.)
        marker=json.loads((self.repo/'train/fixture_marker.json').read_text())
        self.assertEqual(marker,{'factory_called':1,'returned_optimizer_used':3})
        EVIDENCE['numeric_factory']={'passed':True,'marker':marker,'native_autodiff_calls':3,
                                     'first_updated_parameter':training['steps'][0]['state']['weight']}

    def test_missing_factory_is_observable(self):
        self.write_trainer(factory='')
        case=self.invoke()['cases']['base']
        self.assertEqual(case['status'],'error');self.assertEqual(case['error_type'],'AttributeError')
        self.assertIn('make_optimizer',case['error'])
        EVIDENCE['missing_factory']={'passed':True,'error_type':case['error_type'],'error':case['error']}

    def test_raising_factory_is_observable(self):
        self.write_trainer(factory="def make_optimizer(model,learning_rate=.001):\n    raise RuntimeError('fixture factory failure')\n")
        case=self.invoke()['cases']['base']
        self.assertEqual(case['status'],'error');self.assertEqual(case['error_type'],'RuntimeError')
        self.assertEqual(case['error'],'fixture factory failure')
        EVIDENCE['raising_factory']={'passed':True,'error_type':case['error_type'],'error':case['error']}

    def test_cli_records_real_factory_and_autodiff_calls(self):
        result=self.invoke('cli')
        self.assertTrue(result['accepted']);self.assertEqual(result['candidate_optimizer_factory_calls'],1)
        self.assertEqual(result['native_autodiff_calls'],2)
        EVIDENCE['cli_factory']={'passed':True,'result':result}

    def test_cli_without_factory_is_rejected_even_with_autodiff(self):
        self.write_trainer(cli="optimizer=nn.SGD(model.trainable_params(),learning_rate=.001); LAST_OPTIMIZER=optimizer")
        result=self.invoke('cli')
        self.assertFalse(result['accepted']);self.assertEqual(result['candidate_optimizer_factory_calls'],0)
        self.assertEqual(result['native_autodiff_calls'],2)
        EVIDENCE['cli_factory_bypass']={'passed':True,'result':result}

    def test_source_adam_branch_and_numeric_inputs_are_unchanged(self):
        def optimizer_branch(path):
            tree=ast.parse(path.read_text())
            node=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign)
                      and any(isinstance(t,ast.Name) and t.id=='optimizer' for t in n.targets)
                      and isinstance(n.value,ast.IfExp))
            return ast.dump(node.value.test),ast.dump(node.value.body)
        self.assertEqual(optimizer_branch(WORKER),optimizer_branch(OLD/'scripts/repository_twotower_worker.py'))
        EVIDENCE['source_optimizer_unchanged']={'passed':True,'check':'AST equality of source condition and source Adam construction'}

    def test_saved_source_identity_and_corrupted_loss_update(self):
        # Import only the compare function via its actual source definition to
        # avoid historical module globals and any runtime initialization.
        path=ROOT/'scripts/run_repository_twotower.py'
        tree=ast.parse(path.read_text())
        selected=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='compare'
                  or isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='THRESHOLDS' for t in node.targets)]
        import numpy as np
        namespace={'np':np}
        exec(compile(ast.Module(body=selected,type_ignores=[]),str(path),'exec'),namespace)
        record=json.loads(REFERENCE.read_text());target=copy.deepcopy(record['cases'])
        for case in target.values():
            if case.get('training',{}).get('status')=='ok':case['training']['native_autodiff_calls']=3
        compare=namespace['compare']
        identity=compare(record['cases'],target,record['request'])
        self.assertTrue(identity['accepted'])
        wrong_loss=copy.deepcopy(target);wrong_loss['base']['training']['steps'][0]['loss']+=1.
        loss=compare(record['cases'],wrong_loss,record['request'])
        self.assertFalse(loss['accepted']);self.assertFalse(loss['checks']['base_step1_loss'])
        wrong_update=copy.deepcopy(target)
        name=sorted(wrong_update['base']['training']['steps'][0]['state'])[0]
        value=np.asarray(wrong_update['base']['training']['steps'][0]['state'][name]);value.flat[0]+=1.
        wrong_update['base']['training']['steps'][0]['state'][name]=value.tolist()
        update=compare(record['cases'],wrong_update,record['request'])
        self.assertFalse(update['accepted']);self.assertFalse(update['checks']['base_step1_update'])
        EVIDENCE['comparison_controls']={'passed':True,'identity_checks':len(identity['checks']),
            'source_identity_accepted':identity['accepted'],'corrupt_loss_rejected':not loss['checks']['base_step1_loss'],
            'corrupt_update_rejected':not update['checks']['base_step1_update'],'reference_sha256':sha(REFERENCE)}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--report',type=Path,
        default=ROOT/'experiments/repository_migration_20260921/optimizer_controls.json')
    args=parser.parse_args()
    historical=OLD/'experiments/repository_twotower_20260920/continuation/workspace/target/train/train.py'
    before=sha(historical)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(OptimizerControls))
    unchanged=before==sha(historical)
    report={'passed':result.wasSuccessful() and unchanged,'tests_run':result.testsRun,'model_api_calls':0,
            'checks':EVIDENCE,'historical_target_unchanged':unchanged,'historical_target_sha256':before,
            'file_hashes':{str(p.relative_to(ROOT)):sha(p) for p in (WORKER,Path(__file__).resolve(),ROOT/'scripts/run_repository_twotower.py')},
            'scope':'Actual native MindSpore execution on isolated tiny temporary fixtures, never supplied to any agent; saved-source numerical comparison controls. No historical candidate edited or experiment rerun.'}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'report':str(args.report)}))
    sys.exit(not report['passed'])


if __name__=='__main__':main()
