"""Independent mathematical checks of the accepted distal rib segment only."""
import importlib.util,json,math,pathlib,unittest
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('spiral',ROOT/'scripts/anatomy_fit/rib_spiral_reconstruction.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
class DistalRibTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.model=json.loads((ROOT/'ORIGINAL_V1_WORK/anatomy/rib_demographic_model_holcombe2017_v1.json').read_text())
 def test_export_is_reproducible_and_keeps_floating_rib_exceptions(self):
  import sys
  sys.path.insert(0,str(ROOT/'scripts/anatomy_fit'));sys.path.insert(0,str(ROOT/'scripts'))
  import build_rib_distal_source_curves as b
  from report_compare import report_differences
  stored=json.loads(b.OUT.read_text());self.assertEqual(report_differences(stored,b.build()),[])
  self.assertFalse(stored['freeze_ready'])
  for k,v in stored['levels'].items():
   self.assertEqual(v['costotransverse_joint_permitted'],int(k)<=10)
   self.assertIsNone(v['rib_head']);self.assertIsNone(v['tubercle'])
   self.assertFalse(v['full_rib_reconstructed'])
 def test_primary_pdf_access_does_not_silently_accept_conflicted_proximal_equations(self):
  d=json.loads((ROOT/'ORIGINAL_V1_WORK/anatomy/rib_inplane_derivation_holcombe2016_v1.json').read_text())
  review=d['primary_visual_review_2026_10_08']
  self.assertTrue(review['original_pdf_acquired'])
  self.assertFalse(review['printed_second_constraint_accepted'])
  self.assertFalse(review['proximal_branch_accepted'])
  self.assertIn('BLOCKED',d['implementation_status']['proximal_branch_selection'])
 def test_all_published_level_means_have_correct_endpoints_and_no_loops(self):
  for level in self.model['levels'].values():
   p=level['population_mean'];curve=np.array(r.distal_curve(p['Xpk'],p['Ypk'],p['Bd']))
   np.testing.assert_allclose(curve[0],[p['Xpk'],p['Ypk']],atol=1e-12)
   np.testing.assert_allclose(curve[-1],[1,0],atol=1e-12)
   self.assertTrue(np.isfinite(curve).all());self.assertTrue((np.diff(curve[:,0])>0).all())
   self.assertGreaterEqual(curve[:,1].min(),-1e-12)
 def test_peak_is_independently_stationary_and_maximum(self):
  for bd in [-2.5,-.51,0,1,2.5]:
   t=r.distal_theta_peak(bd)
   self.assertAlmostEqual(t,math.pi/2+math.atan(bd),places=12)
   self.assertAlmostEqual(bd*math.sin(t)+math.cos(t),0,places=12)
   self.assertGreater(r.distal_unscaled(t,bd)[1],r.distal_unscaled(t-.001,bd)[1])
   self.assertGreater(r.distal_unscaled(t,bd)[1],r.distal_unscaled(t+.001,bd)[1])
 def test_zero_spiral_rate_matches_independent_circle_solution(self):
  x,y=.3,.4;t=r.distal_transform(x,y,0)
  # (sin(t)-1)/(negative cos(t)) = -y/(1-x), and tangent half-angle identity.
  delta=2*math.atan(y/(1-x))
  self.assertAlmostEqual(t['theta_end']-t['theta_pk'],delta,places=10)
 def test_physical_scale_and_length_are_not_endpoint_chord(self):
  c=np.array(r.physical_distal_curve(200,.3,.4,-.5,samples=401))
  np.testing.assert_allclose(c[-1],[200,0],atol=1e-10)
  self.assertGreater(np.linalg.norm(np.diff(c,axis=0),axis=1).sum(),np.linalg.norm(c[-1]-c[0]))
 def test_dense_and_sparse_sampling_preserve_same_curve(self):
  a=np.array(r.distal_curve(.3,.4,-.5,samples=11));b=np.array(r.distal_curve(.3,.4,-.5,samples=101))
  np.testing.assert_allclose(a,b[::10],atol=1e-12)
 def test_nonfinite_parameters_and_span_rejected(self):
  for value in [float('nan'),float('inf'),-float('inf')]:
   for idx in range(3):
    args=[.3,.4,-.5];args[idx]=value
    with self.assertRaises(ValueError):r.distal_curve(*args)
   with self.assertRaises(ValueError):r.physical_distal_curve(value,.3,.4,-.5)
 def test_bad_samples_and_degenerate_peak_rejected(self):
  for samples in [1,0,-1,2.5,True]:
   with self.assertRaises(ValueError):r.distal_curve(.3,.4,-.5,samples=samples)
  for x,y in [(0,.4),(1,.4),(.3,0)]:
   with self.assertRaises(ValueError):r.distal_curve(x,y,-.5)
if __name__=='__main__':unittest.main()
