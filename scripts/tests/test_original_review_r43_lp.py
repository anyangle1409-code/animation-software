import sys,unittest
from pathlib import Path
import numpy as np
from scipy import sparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r43_lp import step
class FeasibilityLP(unittest.TestCase):
 def test_smallest_repair_leaves_unneeded_coordinates_fixed(self):
  A=sparse.csr_matrix([[1.,0.,0.],[-1.,0.,0.]])
  x,z=step(A,np.array([-.5,.6]),1.)
  self.assertLess(z,1e-8);np.testing.assert_allclose(x,[-.5,0,0],atol=2e-7)
 def test_feasibility_takes_priority_over_smaller_step(self):
  x,z=step(sparse.csr_matrix([[1.,0.]]),np.array([-2.]),1.)
  self.assertAlmostEqual(z,1.);self.assertAlmostEqual(x[0],-1.,places=6)
if __name__=='__main__':unittest.main()
