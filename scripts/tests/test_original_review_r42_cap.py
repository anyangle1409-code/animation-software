"""Hard absolute material cap must preserve contour components and gradients."""
import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r42_cap import bounded_material
class MaterialCap(unittest.TestCase):
 def test_preserves_normal_component_and_bounds_final_vector(self):
  initial=np.array([[[.035,.008,0.],[0.,0.,0.]]]);n=np.array([[[1.,0.,0.],[0.,0.,0.]]]);free=np.array([[True,False]])
  actual,pullback=bounded_material(np.array([[[100.,100.,100.],[100.,100.,100.]]]),initial,free,n,.045)
  self.assertAlmostEqual(actual[0,0,0],.035,places=12)
  self.assertLessEqual(np.linalg.norm(actual,axis=2).max(),.045000000001)
  np.testing.assert_array_equal(actual[0,1],initial[0,1])
 def test_nonlinear_pullback_matches_finite_difference(self):
  rng=np.random.default_rng(42);initial=rng.normal(0,.003,(2,3,3));free=np.array([[1,1,0],[1,1,1]],bool)
  n=np.zeros_like(initial);n[0,0]=[1.,0.,0.];n[1,2]=[0.,1.,0.]
  x=rng.normal(0,8,initial.shape);g=rng.normal(size=x.shape)
  _,back=bounded_material(x,initial,free,n,.045);analytic=back(g)
  for i in np.ndindex(x.shape):
   a=x.copy();b=x.copy();a[i]+=1e-5;b[i]-=1e-5
   va=bounded_material(a,initial,free,n,.045)[0];vb=bounded_material(b,initial,free,n,.045)[0]
   self.assertAlmostEqual(float(((va-vb)*g).sum()/2e-5),analytic[i],delta=1e-9)
 def test_coupled_objective_gradient_through_active_cap(self):
  from test_original_review_r42_bounded_optimizer import BoundedStrain
  from optimize_original_review_r42 import objective
  data=BoundedStrain().data();data['absolute_material_limit_mm']=2.
  fun,_,_,shape=objective(data);x=np.random.default_rng(44).normal(0,2,np.prod(shape));_,g=fun(x)
  for i in range(len(x)):
   a=x.copy();b=x.copy();a[i]+=1e-6;b[i]-=1e-6
   numeric=(fun(a)[0]-fun(b)[0])/2e-6
   self.assertAlmostEqual(g[i],numeric,delta=max(1e-5,abs(g[i])*1e-5))
if __name__=='__main__':unittest.main()
