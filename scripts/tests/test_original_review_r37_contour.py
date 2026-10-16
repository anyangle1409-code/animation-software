"""Fixed R37 goals, additional to every prior deformation check.

Input is a read-only native Blender probe NPZ. The marked frame is 135.625
degrees. A 10mm tangent span is sampled at 2mm spacing below the shoulder.
"""
import os
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from original_review_contour import section_profile, corner_degrees

class ArmToSideContourTests(unittest.TestCase):
    def test_marked_frame_has_smoother_bilateral_rear_outline(self):
        with np.load(os.environ['HGPT_CONTOUR_NPZ']) as z:
            for side in ('l', 'r'):
                with self.subTest(side=side):
                    y,h=section_profile(z['all_135.625'],z['faces'],z[f'gh_{side}_135.625'],'back',side)
                    peak=corner_degrees(y,h)
                    print('R37_REAR_CORNER',side,peak,flush=True)
                    self.assertLess(peak,12.5)

    def test_marked_frame_three_quarter_outline_does_not_worsen(self):
        with np.load(os.environ['HGPT_CONTOUR_NPZ']) as z:
            for side,limit in (('l',35.407937),('r',53.426476)):
                with self.subTest(side=side):
                    y,h=section_profile(z['all_135.625'],z['faces'],z[f'gh_{side}_135.625'],'three_quarter',side)
                    peak=corner_degrees(y,h)
                    print('R37_THREE_QUARTER_CORNER',side,peak,flush=True)
                    self.assertLessEqual(peak,limit+0.001)

if __name__=='__main__':
    unittest.main()

