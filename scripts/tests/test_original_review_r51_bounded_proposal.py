"""A bounded approximate proposal is never reported as an optimal/model result."""
import sys,unittest
from pathlib import Path
import numpy as np
from scipy import sparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r51_bounded import propose

class BoundedProposal(unittest.TestCase):
 def test_reduces_combined_loss_and_retains_hard_bounds(self):
  A=sparse.csr_matrix([[-1.],[-1.],[1.],[1.]])
  x,report=propose(A,np.array([-3.,-3.,0.,2.]),np.array([1.,1.,1.]),np.array([0,1,2]),4.,iterations=800)
  self.assertLessEqual(float(x[0]),2.000001)
  self.assertGreater(float(x[0]),1.98)
  self.assertLessEqual(report['hard_violation'],1e-6)
  self.assertFalse(report['proposal_optimal'])
  self.assertLess(report['objective'],report['initial_objective'])

 def test_rejects_infeasible_hard_bounds(self):
  with self.assertRaises(RuntimeError):
   propose(sparse.csr_matrix([[-1.]]),np.array([-2.]),np.array([]),np.array([],int),1.,iterations=10)

 def test_rejects_nonfinite_input(self):
  with self.assertRaises(ValueError):
   propose(sparse.csr_matrix([[1.]]),np.array([np.nan]),np.array([]),np.array([],int),1.,iterations=10)

if __name__=='__main__':unittest.main()
