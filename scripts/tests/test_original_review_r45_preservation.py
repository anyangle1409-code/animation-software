"""R45 permits body controls110/156, preserving original arm/elbow and166.

R42 endpoint test remains unchanged for its original study. R45 extends only
body support to avoid an abrupt appearance/disappearance of the correction.
"""
import os,unittest
import numpy as np
class Preservation(unittest.TestCase):
 def test_only_authorized_body_coordinates_change(self):
  with np.load(os.environ['HGPT_R45_RESPONSE']) as d,np.load(os.environ['HGPT_R45_SOLUTION']) as s:
   delta=s['delta'];self.assertTrue(np.isfinite(delta).all());self.assertEqual(delta.shape,(7,len(d['rest']),3))
   np.testing.assert_array_equal(delta[6],0.)
   np.testing.assert_array_equal(delta[d['frozen_arm']],0.)
   np.testing.assert_array_equal(delta[~d['free']],0.)
   mirror=int(np.argmin(np.linalg.norm(d['rest']-d['rest'][18633]*[-1,1,1],axis=1)))
   np.testing.assert_array_equal(delta[:,[18633,mirror]],0.)
   self.assertLessEqual(float(np.linalg.norm(delta,axis=2).max()*1000),45.)
   dense=np.einsum('dk,knj->dnj',d['sampling_basis'],delta)
   self.assertLessEqual(float(np.linalg.norm(dense,axis=2).max()*1000),45.)
if __name__=='__main__':unittest.main()
