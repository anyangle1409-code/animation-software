import importlib.util,json,unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('glenoid',ROOT/'scripts/anatomy_fit/glenoid_rim_frame.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class GlenoidRimTests(unittest.TestCase):
 def fixture(self):
  p=np.zeros((29,3));p[14]=[0,-20,0];p[17]=[0,20,0];p[15]=[-15,0,0];p[16]=[15,0,0];p[18]=[0,0,-3];return p
 def test_analytic_rim_is_not_gh_centre(self):
  r=m.derive(self.fixture());np.testing.assert_allclose(r['axes_local'],np.eye(3),atol=1e-12)
  self.assertAlmostEqual(r['rim_plane_rms_mm'],0)
  self.assertAlmostEqual(r['landmark_19_signed_offset_mm'],-3)
  self.assertIsNone(r['GH_centre_local_mm'])
 def test_translation_and_tilt_covariance(self):
  p=self.fixture();angle=np.radians(20);R=np.array([[np.cos(angle),0,np.sin(angle)],[0,1,0],[-np.sin(angle),0,np.cos(angle)]])
  r=m.derive(p@R.T+[2,3,4]);np.testing.assert_allclose(r['axes_local'],R,atol=1e-12)
  np.testing.assert_allclose(r['rim_centroid_local_mm'],[2,3,4],atol=1e-12)
 def test_rank_deficiency_nonfinite_and_mirror_rejected(self):
  p=self.fixture()
  for q in [np.zeros((29,3)),p*np.array([-1,1,1]),p*np.nan]:
   with self.assertRaises(ValueError):m.derive(q)
 def test_nonplanarity_reported_and_frame_still_proper(self):
  p=self.fixture();p[14,2]=2;r=m.derive(p);self.assertGreater(r['rim_plane_rms_mm'],0)
  R=np.array(r['axes_local']);np.testing.assert_allclose(R.T@R,np.eye(3),atol=1e-12);self.assertAlmostEqual(np.linalg.det(R),1)
 def test_bilateral_outward_normals_and_proper_pose_rotations(self):
  b=m.bilateral(m.derive(self.fixture()))
  right=np.array(b['right']['axes_HGPT']);left=np.array(b['left']['axes_HGPT'])
  self.assertAlmostEqual(np.linalg.det(right),1);self.assertAlmostEqual(np.linalg.det(left),1)
  self.assertLess(right[0,2],0);self.assertGreater(left[0,2],0)
  M=np.diag([-1,1,1])
  np.testing.assert_allclose(left[:,2],M@right[:,2],atol=1e-12)
  np.testing.assert_allclose(-left[:,0],M@right[:,0],atol=1e-12)
  self.assertEqual(b['left']['axis_columns'][0],'posterior_tangent')
 def test_isotropic_rim_has_no_unique_plane_and_must_fail(self):
  p=self.fixture();p[[14,15,16,17]]=[[-1,-1,-1],[-1,1,1],[1,-1,1],[1,1,-1]]
  with self.assertRaises(ValueError):m.derive(p)
 def test_measured_report_reproduction(self):
  saved=json.loads((ROOT/'ORIGINAL_V1_WORK/anatomy/canonical_glenoid_rim_frame_v1.json').read_text())
  self.assertEqual(saved,m.build());self.assertFalse(saved['freeze_ready']);self.assertEqual(saved['subject_count'],34)
if __name__=='__main__':unittest.main()
