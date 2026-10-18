"""Combined repair must not let one worst residual monopolize the proposal."""
import sys,unittest
from pathlib import Path
import numpy as np
from scipy import sparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r50_lp import step

class RepairProposal(unittest.TestCase):
    def test_repair_reduces_total_violation_instead_of_only_the_worst(self):
        A=sparse.csr_matrix([[-1.],[-1.],[1.],[1.]])
        x,_=step(A,np.array([-3.,-3.,0.,4.]),4.,['contact','contact','contact','profile_upper'],np.ones(4))
        self.assertAlmostEqual(float(x[0]),3.,places=5)

    def test_outline_and_material_bounds_cannot_be_relaxed(self):
        A=sparse.csr_matrix([[-1.],[1.],[1.]])
        x,_=step(A,np.array([-3.,1.,.5]),4.,['contact','profile_upper','material_bound'],np.ones(3))
        self.assertLessEqual(float(x[0]),.500001)
        self.assertGreaterEqual(float(x[0]),.499999)

if __name__=='__main__':unittest.main()
