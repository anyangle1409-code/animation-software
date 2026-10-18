"""Contour progress must never buy slack in a hard safety inequality."""
import sys,unittest
from pathlib import Path
import numpy as np
from scipy import sparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r48_lp import step

class FeasibilityStep(unittest.TestCase):
    def test_shape_slack_cannot_relax_safety(self):
        # Desired x>=1 and y>=1 conflict with hard x+y<=0.2.
        A=sparse.csr_matrix([[1.,1.],[-1.,0.],[0.,-1.]])
        movement,slack=step(A,np.array([.2,-1.,-1.]),.5,np.array([0.,1.,1.]))
        self.assertLessEqual(float(movement.sum()),.2+1e-7)
        self.assertAlmostEqual(slack,.9,places=6)
        self.assertTrue(np.all(abs(movement)<=.5+1e-8))
        self.assertLessEqual(float((A@movement-np.array([.2,-1.,-1.])-np.array([0.,1.,1.])*slack).max()),1e-7)

if __name__=='__main__':unittest.main()
