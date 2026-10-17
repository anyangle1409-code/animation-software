import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from optimize_original_review_r41 import objective,solve
class BoundedStrain(unittest.TestCase):
 def data(self):
  rest=np.array([[0.,0.,0.],[.01,0.,0.],[0.,.01,0.]])
  base=rest.copy();base[1,0]=.023
  return dict(rest=rest,faces=np.array([[0,1,2]]),base=np.tile(base,(82,1,1)),mat=np.tile(np.eye(3),(82,3,1,1)),
              weight=np.ones((82,1,3)),delta=np.zeros((1,3,3)),free=np.array([[False,True,False]]),
              constraint_normal=np.array([[[0.,0.,0.],[1.,1.,1.],[0.,0.,0.]]])/np.sqrt(3),constraint_mask=np.array([[False,True,False]]),constraint_value=np.zeros((1,3)),strain_mode=np.array(1),max_delta_mm=np.array(.70))
 def test_strain_chain_gradient_matches_finite_difference(self):
  fun,_,_,shape=objective(self.data());x=np.random.default_rng(4).normal(0,.01,size=np.prod(shape));_,g=fun(x)
  for i in range(len(x)):
   a=x.copy();b=x.copy();a[i]+=1e-6;b[i]-=1e-6
   self.assertAlmostEqual(g[i],(fun(a)[0]-fun(b)[0])/2e-6,delta=max(1e-5,abs(g[i])*1e-6))
 def test_material_cap_line_and_fixed_vertices_hold(self):
  d=self.data();delta,r=solve(d,epochs=30)
  self.assertLessEqual(np.linalg.norm(delta,axis=2).max()*1000,.700001)
  self.assertGreater(np.linalg.norm(delta[0,1]),0.)
  np.testing.assert_array_equal(delta[~d['free']],0.)
  self.assertAlmostEqual(float((delta*d['constraint_normal']).sum()),0.,places=12)
if __name__=='__main__':unittest.main()
