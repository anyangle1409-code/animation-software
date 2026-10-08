import importlib.util
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('stats',Path(__file__).parent/'anatomy_fit/source_statistics.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class SourceStatisticsTests(unittest.TestCase):
 def test_pooled_correlation_bound_handles_between_group_covariance(self):
  # Two groups with identical within-group scatter but opposite means:
  # within-group r=0, yet pooled r=8/9. A simple max(r_group) rule is wrong.
  self.assertAlmostEqual(m.two_group_correlation_upper_bound(8,4,(36/7)**.5,(36/7)**.5,0,4,4),8/9)
  self.assertEqual(m.two_group_correlation_upper_bound(8,4,1,1,.6,0,4),.6)
 def test_fontana_reported_summaries_cannot_support_printed_pooled_r(self):
  # Both overall and Japanese CL means round to 143.7 mm; allow 0.1 mm
  # difference before inferring the other group's mean. Allow all 50 cm
  # of the published height range as a between-group mean difference.
  limit=m.two_group_correlation_upper_bound(350,102,10.7,11,.679,350/248*.1,50)
  self.assertLess(limit,.692)
  self.assertGreater(.968,limit)
 def test_bound_contains_correlations_of_independent_synthetic_samples(self):
  import math
  groups=[[(0,2),(2,0),(1,1)],[(5,7),(8,6),(6,9),(9,10)]]
  def stats(points):
   n=len(points); mx=sum(p[0] for p in points)/n; my=sum(p[1] for p in points)/n
   xx=sum((x-mx)**2 for x,y in points); yy=sum((y-my)**2 for x,y in points)
   r=sum((x-mx)*(y-my) for x,y in points)/math.sqrt(xx*yy)
   return mx,my,math.sqrt(xx/(n-1)),math.sqrt(yy/(n-1)),r
  a,b=[stats(g) for g in groups]; total=stats(sum(groups,[]))
  bound=m.two_group_correlation_upper_bound(7,3,total[2],total[3],max(0,a[4],b[4]),abs(a[0]-b[0]),abs(a[1]-b[1]))
  self.assertLessEqual(total[4],bound+1e-12)
 def test_bound_rejects_undefined_or_nonfinite_summaries(self):
  for args in [(4,0,1,1,.5,1,1),(4,4,1,1,.5,1,1),(True,1,1,1,.5,1,1),(4,1,0,1,.5,1,1),(4,1,1,1,1.1,1,1),(4,1,1,1,-.1,1,1),(4,1,1,1,.5,-1,1),(4,1,1,1,.5,float('inf'),1),(4,1,True,1,.5,1,1)]:
   with self.assertRaises(ValueError):m.two_group_correlation_upper_bound(*args)
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
