import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from optimize_original_review_r39 import objective,solve
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
 def test_nonfinite_input_rejected(self):
  d=self.data();d['delta'][0,1,0]=np.nan
  with self.assertRaises(ValueError):solve(d)
if __name__=='__main__':unittest.main()
