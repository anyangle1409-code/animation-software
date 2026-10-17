"""Additional front smoothness goal; all prior tests stay unchanged."""
import os,sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
class FrontSmoothness(unittest.TestCase):
 def test_fixed_front_patch_stays_near_r38_smoothness(self):
  from original_review_r40_front import front_peak
  with np.load(os.environ['HGPT_CONTOUR_NPZ']) as z:
   for s in ('l','r'):
    peak=front_peak(z['all_130.0'],z['faces'],z[f'gh_{s}_130.0'],s)
    print('R40_FRONT_PEAK',s,peak,flush=True)
    with self.subTest(side=s):self.assertLessEqual(peak,25.)
if __name__=='__main__':unittest.main()
