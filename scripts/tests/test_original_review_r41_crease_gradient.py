import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r41_front import crease_loss
class CreaseGradient(unittest.TestCase):
 def test_analytic_gradient_and_translation_invariance(self):
  p=np.array([[0.,0.,0.],[.01,0.,0.],[0.,.01,0.],[.01,.01,.012]])
  tri=np.array([[[0,1,2],[1,3,2]]]);limit=np.array([23.5]);value,g,peak=crease_loss(p,tri,limit)
  self.assertGreater(value,0.);self.assertGreater(peak,25.)
  for i in range(p.size):
   a=p.copy();b=p.copy();a.flat[i]+=1e-8;b.flat[i]-=1e-8
   numeric=(crease_loss(a,tri,limit)[0]-crease_loss(b,tri,limit)[0])/2e-8
   self.assertAlmostEqual(g.flat[i],numeric,delta=max(1e-3,abs(numeric)*1e-6))
  np.testing.assert_allclose(g.sum(0),0.,atol=1e-8)
 def test_flat_surface_has_no_penalty(self):
  p=np.array([[0.,0.,0.],[.01,0.,0.],[0.,.01,0.],[.01,.01,0.]])
  loss,g,peak=crease_loss(p,np.array([[[0,1,2],[1,3,2]]]),np.array([23.5]))
  self.assertEqual(loss,0.);np.testing.assert_array_equal(g,0.)
if __name__=='__main__':unittest.main()
