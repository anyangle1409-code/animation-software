import sys,unittest
from pathlib import Path
import numpy as np
from scipy import sparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r46_lp import step
class FeasibilityLP(unittest.TestCase):
 def test_smallest_repair_leaves_unneeded_coordinates_fixed(self):
  A=sparse.csr_matrix([[1.,0.,0.],[-1.,0.,0.]])
  x,z=step(A,np.array([-.5,.6]),1.)
  self.assertLess(z,1e-8);np.testing.assert_allclose(x,[-.5,0,0],atol=2e-7)
 def test_feasibility_takes_priority_over_smaller_step(self):
  x,z=step(sparse.csr_matrix([[1.,0.]]),np.array([-2.]),1.)
  self.assertAlmostEqual(z,1.);self.assertAlmostEqual(x[0],-1.,places=6)
 def test_small_projected_rows_are_not_ignored(self):
  x,z=step(sparse.csr_matrix([[1e-10,0.],[0.,-1.]]),np.array([-5e-11,-.2]),1.,relaxed=np.zeros(2))
  self.assertLess(z,1e-8);np.testing.assert_allclose(x,[-.5,.2],atol=2e-7)
 def test_profile_objective_budget_does_not_relax_hard_rows(self):
  A=sparse.csr_matrix([[1.,0.],[-1.,0.],[0.,1.]])
  rhs=np.array([-2.,3.,.2]);relaxed=np.array([1.,0.,0.])
  x,z=step(A,rhs,1.,relaxed=relaxed,profile_opt_tolerance=.001)
  self.assertAlmostEqual(z,1.);self.assertAlmostEqual(x[0],-.999,places=6)
  self.assertTrue((A@x<=rhs+relaxed*(z+.001)+2e-7).all())
if __name__=='__main__':unittest.main()
