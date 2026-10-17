"""Material-field construction must preserve scope and bounded control motion."""
import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r43_field import material_field
class SmoothMaterialField(unittest.TestCase):
 def test_separate_sides_and_bounded_nonnegative_partition(self):
  r=np.array([[x,y,z] for x in [-.15,-.1,-.05,.05,.1,.15] for y in [0,.02,.04] for z in [1.3,1.32,1.34]])
  f=np.array([(abs(r[:,0])>.05)&(r[:,1]>.0)])
  b=material_field(r,f);self.assertEqual(b.shape[0],f.sum()*3);self.assertGreater(b.shape[1],0)
  self.assertTrue((b.data>=0).all());self.assertLessEqual(float(np.max(b.sum(axis=1))),1.+1e-12)
  vertex=np.repeat(np.flatnonzero(f[0]),3);negative=np.flatnonzero(r[vertex,0]<0);positive=np.flatnonzero(r[vertex,0]>0)
  self.assertFalse(set(b[negative].indices)&set(b[positive].indices))
  full=np.zeros((len(r),3));full[f[0]]=(b@np.ones(b.shape[1])).reshape(-1,3)
  np.testing.assert_array_equal(full[~f[0]],0.)
if __name__=='__main__':unittest.main()
