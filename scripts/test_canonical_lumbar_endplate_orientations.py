import importlib.util
import json
from pathlib import Path
import unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('lumbar',ROOT/'scripts/anatomy_fit/lumbar_endplate_orientations.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class LumbarEndplateTests(unittest.TestCase):
 def test_global_endpoint_and_independent_direction(self):
  r=m.derive(40.9,{'L1/L2':1.34019801980198,'L2/L3':6.589306930693069,'L3/L4':10.163168316831682,'L4/L5':14.183762376237622,'L5/S1':24.123564356435644})
  self.assertAlmostEqual(r['L1']['slope_deg'],-15.5)
  self.assertGreater(r['S1']['normal'][2],0);self.assertLess(r['S1']['normal'][1],0)
  self.assertGreater(r['L1']['normal'][1],0)
  for f in r.values():
   R=np.array([f['left_axis'],f['AP_axis'],f['normal']]).T
   np.testing.assert_allclose(R.T@R,np.eye(3),atol=1e-12)
   self.assertAlmostEqual(np.linalg.det(R),1)
   self.assertIsNone(f['centre_m'])
 def test_wrong_sign_is_detectable_by_global_endpoint(self):
  r=m.derive(40.9,{k:0 for k in m.LEVELS})
  self.assertNotAlmostEqual(r['L1']['slope_deg'],-15.5)
 def test_missing_nonfinite_or_impossible_input_fails(self):
  for levels in [{},{k:float('nan') for k in m.LEVELS},{k:100 for k in m.LEVELS}]:
   with self.assertRaises(ValueError):m.derive(40.9,levels)
  with self.assertRaises(ValueError):m.derive(float('inf'),{k:1 for k in m.LEVELS})
 def test_source_semantics_forbid_using_full_segment_as_disc_wedge(self):
  p=json.loads((ROOT/'ORIGINAL_V1_WORK/anatomy/canonical_spine_reference_pose_p1.json').read_text())
  s=p['lumbar_distribution'].get('measurement_semantics',{})
  self.assertEqual(s.get('endplates'),'superior-to-superior')
  self.assertFalse(s.get('disc_only_angle',True))
  self.assertIn('vertebral body',s.get('includes',''))
if __name__=='__main__':unittest.main()
