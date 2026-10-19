import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_arm_back_audit import muted_names,pose_difference_mm,temporal_metrics

class Audit(unittest.TestCase):
 def test_ablation_never_mutes_other_workstream(self):
  names=['HGPT_S5_BAKE_l_120','HGPT_S7_DELT_r_136','HGPT_SHOULDER_TEST','HGPT_K1_ELBOW_l_90','Basis']
  self.assertEqual(muted_names('r41_no_s5_s7',names),names[:2])
  self.assertEqual(muted_names('r41_no_s5',names),names[:1])
  self.assertEqual(muted_names('r52',names),[])
 def test_detects_posed_bone_translation(self):
  a=np.zeros((161,2,2,3));b=a.copy();b[80,1,0,0]=.001
  self.assertAlmostEqual(pose_difference_mm(a,b),1.)
 def test_dense_spike_cannot_hide_in_coarse_samples(self):
  a=np.zeros((161,1,3));b=a.copy();b[81,0,0]=.001
  z=temporal_metrics(a,b)
  self.assertAlmostEqual(z['coarse41_excess_mm'],0.)
  self.assertAlmostEqual(z['dense161_excess_mm'],2.)
  self.assertAlmostEqual(z['normalized_dense_excess_mm'],32.)
 def test_rejects_unknown_ablation(self):
  with self.assertRaises(ValueError):muted_names('all_keys',[])

if __name__=='__main__':unittest.main(verbosity=2)
