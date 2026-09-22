import unittest
import numpy as np
from formal_validation import compare_arrays,compare_named_arrays


class ShapeAndVectorTests(unittest.TestCase):
    def test_flatten_equal_wrong_shape_rejected(self):
        a=np.array([[1.,2.]])
        self.assertFalse(compare_arrays(a,a.reshape(2))['accepted'])
    def test_gradient_rotation_rejected(self):
        self.assertFalse(compare_arrays([1.,0.],[0.,1.])['accepted'])
    def test_missing_key_rejected(self):
        self.assertFalse(compare_named_arrays({'w':np.ones(2)}, {})['accepted'])
    def test_near_zero_roundoff_accepted(self):
        self.assertTrue(compare_arrays([1e-18],[-2e-18])['accepted'])
    def test_nan_rejected(self):
        self.assertFalse(compare_arrays([np.nan],[np.nan])['accepted'])


if __name__=='__main__': unittest.main()
