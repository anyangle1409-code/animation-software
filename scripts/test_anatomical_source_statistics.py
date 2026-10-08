import importlib.util
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('stats',Path(__file__).parent/'anatomy_fit/source_statistics.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class SourceStatisticsTests(unittest.TestCase):
 def test_published_pl1_error_rejected(self):
  errors=m.check_summary(26.30,26.30,[20.,30.],46)
  self.assertTrue(any('bounded sample' in e for e in errors))
 def test_valid_summary_and_exact_two_point_sample(self):
  self.assertEqual(m.check_summary(25.23,1.97,[21.,30.],46),[])
  self.assertEqual(m.check_summary(5.,50**.5,[0.,10.],2),[])
 def test_population_sd_bound_would_wrongly_reject_two_point_sample(self):
  self.assertGreater(50**.5,5.)
  self.assertEqual(m.check_summary(5.,50**.5,[0.,10.],2),[])
 def test_nonfinite_negative_mean_outside_range_and_bad_n(self):
  for args in [(float('nan'),1,[0,10],46),(5,-1,[0,10],46),(11,1,[0,10],46),(5,1,[10,0],46),(5,1,[0,10],1),(5,1,[0,10],True)]:
   self.assertTrue(m.check_summary(*args))
 def test_committed_source_quarantines_impossible_sd(self):
  import json
  r=json.loads((Path(__file__).resolve().parents[1]/'ORIGINAL_V1_WORK/anatomy/canonical_lumbar_edge_height_crosscheck_v1.json').read_text())
  p=r['body_edge_heights']['L1']
  self.assertIsNone(p['posterior_SD_mm'])
  self.assertTrue(m.check_summary(p['posterior_mean_mm'],p['posterior_printed_SD_mm'],p['posterior_printed_range_mm'],r['source']['male_n']))
  self.assertFalse(r['freeze_ready'])
  self.assertEqual(r['source']['posture'],'supine with flexed hips and knees')
  self.assertEqual(len(r['body_edge_heights']),5)
  self.assertEqual(len(r['disc_edge_gaps']),5)
if __name__=='__main__':unittest.main()
