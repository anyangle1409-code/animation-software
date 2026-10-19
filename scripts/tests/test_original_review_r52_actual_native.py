"""Original numerical limits applied to actual dense native geometry."""
import os,sys,json,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_original_review_r48_approved_outline import outline
class Native(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.root=Path(os.environ['HGPT_R52_REPORT_DIR']);cls.d=np.load(os.environ['HGPT_R52_RESPONSE']);cls.p=np.load(cls.root/'native_final.json.points.npz')['points'];cls.n=json.loads((cls.root/'native_final.json').read_text())
 def test_actual_marked_outline_with_unchanged_one_mm_guard(self):
  error=float(abs(outline(self.p[25],self.d['faces'])-outline(self.d['r48_profile_target_points'],self.d['faces'])).max()*1000)
  print('R52_ACTUAL_NATIVE_OUTLINE_ERROR_MM',error);self.assertLessEqual(error,1.)
 def test_actual_marked_normals_with_unchanged_zero_guard(self):
  f=self.d['faces'];a=self.d['base'][25,f];b=self.p[25,f];ca=np.cross(a[:,1]-a[:,0],a[:,2]-a[:,0]);cb=np.cross(b[:,1]-b[:,0],b[:,2]-b[:,0]);self.assertEqual(int(((ca*cb).sum(1)<=0).sum()),0)
 def test_original_native83_surface_motion_and_crease_guards(self):
  self.assertEqual(len(self.n['samples']),83);self.assertFalse(self.n['contacts']);self.assertTrue(all(x['passed'] for x in self.n['samples']));self.assertLessEqual(self.n['back_motion_excess_mm'],.5);self.assertLessEqual(self.n['posterior_crease_excess_degrees'],2.)
 def test_additional161_motion_and_integer_step_guards(self):
  z=json.loads((self.root/'dense_motion.json').read_text());self.assertEqual(z['samples'],161);self.assertLessEqual(z['original40_step_equivalent_excess_mm'],.5);self.assertTrue(z['oscillation']['passed']);self.assertLessEqual(z['early_outward_increment_mm'],.05)
if __name__=='__main__':unittest.main()
