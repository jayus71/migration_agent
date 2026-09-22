import copy
import unittest
from runner import compare


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        step = {'loss':1.0,'logits':[1.0,2.0], 'gradients':{'w':[1.0,0.0]},
                'updates':{'w':[-0.1,0.0]},'parameters':{'w':[0.9,2.0]}}
        self.ref={'initial':{'w':[1.0,2.0]},'steps':[copy.deepcopy(step) for _ in range(3)]}
        self.target=copy.deepcopy(self.ref); self.target['status']='ok'
        for step in self.target['steps']: step['jax_arrays']=True
        self.thresholds={'loss_abs':2e-5,**{k+'_rel_l2':2e-4 for k in ('logits','gradients','updates','parameters')}}

    def accepted(self): return compare(self.ref,self.target,self.thresholds)[0]
    def test_exact_control_passes(self): self.assertTrue(self.accepted())
    def test_same_norm_wrong_gradient_fails(self):
        self.target['steps'][0]['gradients']['w']=[0.0,1.0]
        self.assertFalse(self.accepted())
    def test_late_update_error_fails(self):
        self.target['steps'][2]['updates']['w']=[0.0,-0.1]
        self.assertFalse(self.accepted())
    def test_changed_initial_state_fails(self):
        self.target['initial']['w'][0]+=0.01
        self.assertFalse(self.accepted())
    def test_nonfinite_fails(self):
        self.target['steps'][0]['gradients']['w'][0]=float('nan')
        self.assertFalse(self.accepted())
    def test_missing_parameter_fails(self):
        self.target['steps'][0]['gradients']={}
        self.assertFalse(self.accepted())
    def test_execution_failure_fails(self):
        self.target={'status':'failed'}
        self.assertFalse(self.accepted())


if __name__=='__main__': unittest.main()
