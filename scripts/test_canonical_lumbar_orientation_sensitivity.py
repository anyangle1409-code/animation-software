import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('sensitivity',ROOT/'scripts/anatomy_fit/build_lumbar_orientation_sensitivity.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class LumbarSensitivityTests(unittest.TestCase):
 def test_independent_known_source_difference(self):
  r=m.build();self.assertAlmostEqual(r['maximum_abs_difference_deg'],1.06)
  self.assertAlmostEqual(r['families']['Been_mixed_sex_standing_body']['inferior_frames']['L1']['slope_deg'],-18.5)
  self.assertAlmostEqual(r['Bailey_minus_Been_inferior_slope_deg']['L5'],.01)
 def test_common_superior_chain_but_distinct_body_disc_families(self):
  r=m.build();a,b=r['families'].values()
  self.assertEqual(a['superior_frames'],b['superior_frames'])
  self.assertNotEqual(a['disc_wedges_deg'],b['disc_wedges_deg'])
  for k in ['L1','L2','L3','L4','L5']:
   self.assertIsNone(b['inferior_frames'][k]['centre_m'])
  self.assertFalse(r['freeze_ready'])
 def test_report_exact_reproduction(self):
  saved=json.loads((ROOT/'ORIGINAL_V1_WORK/anatomy/canonical_lumbar_orientation_sensitivity_p1.json').read_text())
  self.assertEqual(m.build(),saved)
if __name__=='__main__':unittest.main()
