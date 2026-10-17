"""R42 study must not obtain its contour by moving the newer arm or endpoints."""
import os,unittest
import numpy as np
class Preservation(unittest.TestCase):
 def test_native_control_coordinates_remain_in_scope(self):
  with np.load(os.environ['HGPT_R42_RESPONSE']) as d,np.load(os.environ['HGPT_R42_SOLUTION']) as s:
   delta=s['delta'];self.assertTrue(np.isfinite(delta).all())
   self.assertEqual(delta.shape,(7,len(d['rest']),3))
   np.testing.assert_array_equal(delta[[0,5,6]],0.)
   np.testing.assert_array_equal(delta[d['frozen_arm']],0.)
   np.testing.assert_array_equal(delta[~d['free']],0.)
   mirror=int(np.argmin(np.linalg.norm(d['rest']-d['rest'][18633]*[-1,1,1],axis=1)))
   np.testing.assert_array_equal(delta[:,[18633,mirror]],0.)
   self.assertLessEqual(float(np.linalg.norm(delta,axis=2).max()*1000),45.)
if __name__=='__main__':unittest.main()
