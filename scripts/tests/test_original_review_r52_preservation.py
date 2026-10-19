import os,sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r52_projection import allowed_dense
from original_review_r52_temporal import SOURCE
class Preservation(unittest.TestCase):
 def test_all_dense_controls_preserve_authorized_material_and_caps(self):
  with np.load(os.environ['HGPT_R52_RESPONSE']) as z,np.load(os.environ['HGPT_R52_SOLUTION']) as s:
   dense=s['dense_delta'];allowed=allowed_dense(z)
   self.assertEqual(dense.shape,(72,len(z['rest']),3));self.assertTrue(np.isfinite(dense).all())
   np.testing.assert_array_equal(dense[~allowed],0.);np.testing.assert_array_equal(dense[[0,15,71]],0.)
   np.testing.assert_array_equal(s['delta'],dense[SOURCE]);self.assertLessEqual(float(np.linalg.norm(dense,axis=2).max()),.045+1e-10)
   anchors=[18633,int(np.argmin(np.linalg.norm(z['rest']-z['rest'][18633]*[-1,1,1],axis=1)))]
   np.testing.assert_array_equal(dense[:,anchors],0.)
if __name__=='__main__':unittest.main()
