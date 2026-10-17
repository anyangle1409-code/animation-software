"""New owner-approved straight-line goals; no earlier test is changed."""
import unittest,os,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r41_line import errors

class ApprovedLineGoals(unittest.TestCase):
    def test_upper_arm_reaches_shoulder_without_the_early_bend(self):
        with np.load(os.environ['HGPT_CONTOUR_NPZ']) as current,np.load(os.environ['HGPT_LINE_PARENT_NPZ']) as parent:
            for side in ('l','r'):
                a,j=errors(current,parent,side);print('R41_APPROVED_LINE',side,a,j,flush=True)
                with self.subTest(side=side):self.assertLess(a,2.)
    def test_line_meets_body_without_the_inward_notch(self):
        with np.load(os.environ['HGPT_CONTOUR_NPZ']) as current,np.load(os.environ['HGPT_LINE_PARENT_NPZ']) as parent:
            for side in ('l','r'):
                with self.subTest(side=side):self.assertLess(errors(current,parent,side)[1],2.)

if __name__=='__main__':unittest.main()
