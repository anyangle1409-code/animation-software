import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from optimize_original_review_r39 import objective,solve,separating_plane
class OptimizerTests(unittest.TestCase):
 def data(self):
  p=.01*np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])
  mat=np.tile(np.eye(3),(2,4,1,1));mat[1,:,0,1]=.2
  return dict(rest=p,faces=np.array([[0,1,2],[0,1,3]]),base=np.array([p,p]),mat=mat,
              weight=np.array([np.ones((1,4)),np.ones((1,4))*.8]),delta=np.array([[[0.,0.,0.],[.02,0.,0.],[0.,0.,0.],[0.,0.,0.]]]),
              free=np.array([[False,True,True,False]]),constraint_normal=np.array([[[0.,0.,0.],[0.,1.,0.],[0.,0.,0.],[0.,0.,0.]]]),
              constraint_mask=np.array([[False,True,False,False]]),constraint_value=np.zeros((1,4)))
 def test_coupled_analytic_gradient_matches_finite_difference(self):
  fun,expand,safe,shape=objective(self.data());x=np.random.default_rng(7).normal(0,.1,size=np.prod(shape));_,g=fun(x)
  for i in range(len(x)):
   xp=x.copy();xm=x.copy();xp[i]+=1e-5;xm[i]-=1e-5
   numeric=(fun(xp)[0]-fun(xm)[0])/2e-5
   self.assertAlmostEqual(g[i],numeric,places=7)
 def test_fixed_vertices_and_zero_line_component_stay_exact(self):
  d=self.data();out,report=solve(d,epochs=200)
  np.testing.assert_array_equal(out[~d['free']],d['delta'][~d['free']])
  self.assertEqual(float(out[0,1,1]),0.)
  self.assertTrue(report['constraints_satisfied'])
 def contact_data(self):
  a=np.array([[0.,0.,0.],[.01,0.,0.],[0.,.01,0.]])
  p=np.vstack((a,a+[0,0,.002]));delta=np.zeros((1,6,3));delta[0,3:,2]=-.0025
  return dict(rest=p,faces=np.array([[0,1,2],[3,4,5]]),base=np.array([p]),mat=np.tile(np.eye(3),(1,6,1,1)),
              weight=np.ones((1,1,6)),delta=delta,free=np.array([[False]*3+[True]*3]),
              constraint_normal=np.zeros_like(delta),constraint_mask=np.zeros((1,6),bool),constraint_value=np.zeros((1,6)),
              contacts=[dict(sample=0,a=0,b=1)])
 def test_native_contact_plane_gradient_matches_finite_difference(self):
  fun,_,_,shape=objective(self.contact_data());x=np.random.default_rng(11).normal(0,.01,size=np.prod(shape));_,g=fun(x)
  for i in range(len(x)):
   xp=x.copy();xm=x.copy();xp[i]+=1e-6;xm[i]-=1e-6
   self.assertAlmostEqual(g[i],(fun(xp)[0]-fun(xm)[0])/2e-6,places=6)
 def test_contact_is_resolved_without_moving_fixed_triangle(self):
  d=self.contact_data();out,report=solve(d,epochs=200)
  self.assertTrue(report['constraints_satisfied'])
  np.testing.assert_array_equal(out[0,:3],d['delta'][0,:3])
  p=d['base'][0]+out[0];axis,margin=separating_plane(d['base'][0,:3],d['base'][0,3:])
  self.assertGreaterEqual(float((p[3:]@axis).min()-(p[:3]@axis).max()),.9*margin)
 def test_nonfinite_input_rejected(self):
  d=self.data();d['delta'][0,1,0]=np.nan
  with self.assertRaises(ValueError):solve(d)
if __name__=='__main__':unittest.main()
