import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
try:from original_review_r52_projection import allowed_dense,project,motion,motion_adjoint
except ImportError:allowed_dense=project=motion=motion_adjoint=None
try:from original_review_r52_projection import normal_response,normal_adjoint
except ImportError:normal_response=normal_adjoint=None
from original_review_r52_temporal import decode
from original_review_r43_sampling import hats,basis,DENSE
class Projection(unittest.TestCase):
 def test_scope_never_releases_frozen_source_or_material(self):
  self.assertIsNotNone(allowed_dense)
  old=np.ones((7,8),bool);old[[0,6]]=False;old[:,0]=False;old[2,3]=False
  a=allowed_dense({'r47_allowed':old})
  self.assertFalse(a[:,0].any());self.assertFalse(a[[0,15,71]].any());self.assertFalse(a[35,3]);self.assertTrue(a[34,3])
 def test_ball_mask_and_marked_boundary_projection(self):
  self.assertIsNotNone(project)
  rng=np.random.default_rng(52);x=rng.normal(size=(72,4,3))*.08;allowed=np.ones((72,4),bool);allowed[[0,15,71]]=False;allowed[:,0]=False
  lo=np.array([40,40,40,40]);t=np.full(4,.625);pin=np.array([False,True,False,False]);target=np.zeros((4,3));target[1]=[.03,0,0]
  y=project(x,allowed,(lo,lo+1,t),pin,target)
  self.assertLessEqual(np.linalg.norm(y,axis=2).max(),.045+1e-9);self.assertEqual(abs(y[~allowed]).max(),0)
  np.testing.assert_allclose((1-t[1])*y[40,1]+t[1]*y[41,1],target[1],atol=1e-9)
 def test_motion_adjoint_with_skinning(self):
  self.assertIsNotNone(motion)
  rng=np.random.default_rng(532);w=np.repeat((hats(np.linspace(96,166,11),DENSE)@basis())[:,:,None],4,axis=2);m=decode(w);a=rng.normal(size=(11,4,3,3));x=rng.normal(size=(72,4,3));y=rng.normal(size=(9,4,3))
  self.assertAlmostEqual(float((motion(x,a,m)*y).sum()),float((x*motion_adjoint(y,a,m)).sum()),places=9)
 def test_outward_halfspace_adjoint_and_inactive_frames(self):
  self.assertIsNotNone(normal_response)
  rng=np.random.default_rng(42);w=np.repeat((hats(np.linspace(96,166,8),DENSE)@basis())[:,:,None],3,axis=2);m=decode(w);a=rng.normal(size=(8,3,3,3));x=rng.normal(size=(72,3,3));y=rng.normal(size=(8,3));normal=np.zeros((8,3,3));normal[:4,:,0]=[-1.,1.,-1.]
  value=normal_response(x,a,m,normal);self.assertEqual(abs(value[4:]).max(),0.)
  self.assertAlmostEqual(float((value*y).sum()),float((x*normal_adjoint(y,a,m,normal)).sum()),places=9)
if __name__=='__main__':unittest.main()
