import importlib.util
import json
from pathlib import Path
import unittest
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('wedges', ROOT/'scripts/anatomy_fit/lumbar_wedge_decomposition.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
class LumbarWedgeTests(unittest.TestCase):
 def setUp(self):
  self.segments = {'L1/L2':1.34019801980198,'L2/L3':6.589306930693069,'L3/L4':10.163168316831682,'L4/L5':14.183762376237622,'L5/S1':24.123564356435644}
  self.body = dict(zip(['L1','L2','L3','L4','L5'],[-4.06,-1.28,.60,2.45,8.01]))
 def test_independent_known_signs_and_disc_values(self):
  r = m.derive(40.9,self.segments,self.body)
  self.assertAlmostEqual(r['inferior_frames']['L1']['slope_deg'],-19.56)
  self.assertAlmostEqual(r['inferior_frames']['L5']['slope_deg'],24.786435643564355)
  for segment,expected in zip(self.segments,[5.40019801980198,7.869306930693069,9.563168316831682,11.733762376237622,16.113564356435644]):
   self.assertAlmostEqual(r['disc_wedges_deg'][segment],expected)
 def test_each_body_and_disc_closes_independently(self):
  r=m.derive(40.9,self.segments,self.body)
  for segment,angle in self.segments.items():
   upper,lower=segment.split('/')
   si=r['inferior_frames'][upper]['slope_deg']; su=r['superior_frames'][upper]['slope_deg']
   self.assertAlmostEqual(si-su,self.body[upper])
   self.assertAlmostEqual(r['superior_frames'][lower]['slope_deg']-si,r['disc_wedges_deg'][segment])
   self.assertAlmostEqual(self.body[upper]+r['disc_wedges_deg'][segment],angle)
 def test_proper_frames_and_no_centres(self):
  for f in m.derive(40.9,self.segments,self.body)['inferior_frames'].values():
   R=np.array([f['left_axis'],f['AP_axis'],f['normal']]).T
   np.testing.assert_allclose(R.T@R,np.eye(3),atol=1e-12)
   self.assertAlmostEqual(np.linalg.det(R),1)
   self.assertIsNone(f['centre_m'])
 def test_positive_wedge_means_anterior_taller_in_posterior_frame(self):
  # Independent trapezoid: flat upper plate z=30, lower plate z=y*tan(10).
  # At anterior y=-20 the body is taller; inferior-minus-superior is +10.
  import math
  anterior_height=30+20*math.tan(math.radians(10))
  posterior_height=30-20*math.tan(math.radians(10))
  self.assertGreater(anterior_height,posterior_height)
  ss={k:15. for k in self.segments};body={k:10. for k in self.body}
  r=m.derive(75.,ss,body)
  self.assertAlmostEqual(r['superior_frames']['L1']['slope_deg'],0.)
  self.assertAlmostEqual(r['inferior_frames']['L1']['slope_deg'],10.)
  self.assertAlmostEqual(r['disc_wedges_deg']['L1/L2'],5.)
 def test_bad_body_values_and_kyphotic_discs_rejected(self):
  for b in [{}, {**self.body,'L3':float('nan')}, {**self.body,'L3':True}, {**self.body,'L5':99}]:
   with self.assertRaises(ValueError):m.derive(40.9,self.segments,b)
 def test_report_reproduction_and_se_not_sd(self):
  p=json.loads((ROOT/'ORIGINAL_V1_WORK/anatomy/canonical_spine_reference_pose_p1.json').read_text())
  e=json.loads((ROOT/'ORIGINAL_V1_WORK/anatomy/canonical_lumbar_wedge_evidence_v1.json').read_text())
  saved=json.loads((ROOT/'ORIGINAL_V1_WORK/anatomy/canonical_lumbar_body_disc_frames_p1.json').read_text())
  self.assertEqual(e['dispersion'],'standard_error_of_mean_not_population_SD')
  self.assertFalse(saved['freeze_ready'])
  self.assertEqual(saved['geometry'],m.derive(p['global_male_reference_deg']['sacral_slope'],p['lumbar_distribution']['provisional_scaled_levels_deg'],{k:v['mean_deg'] for k,v in e['male_body_wedges'].items()}))
 def test_ct_source_inconsistency_is_preserved_without_target_freeze(self):
  r=json.loads((ROOT/'ORIGINAL_V1_WORK/anatomy/canonical_lumbar_ct_source_review_v1.json').read_text())
  self.assertEqual(sum(r['male_counts']),r['table_totals']['male'])
  self.assertEqual(sum(r['female_counts']),r['table_totals']['female'])
  self.assertNotEqual(r['table_totals'],r['stated_totals'])
  self.assertFalse(r['freeze_ready'])
  self.assertIn('UNRESOLVED',r['width_semantics'])
 def test_source_subset_closure_is_not_silently_forced(self):
  e=json.loads((ROOT/'ORIGINAL_V1_WORK/anatomy/canonical_lumbar_wedge_evidence_v1.json').read_text())
  body=sum(x['mean_deg'] for x in e['male_body_wedges'].values())
  disc=sum(x['mean_deg'] for x in e['male_standing_disc_wedges'].values())
  self.assertAlmostEqual(e['source_mean_closure']['reported_standing_lordosis_deg']-body-disc,.5)
  self.assertIsNone(e['corridor_SD_deg'])
if __name__=='__main__':unittest.main()
