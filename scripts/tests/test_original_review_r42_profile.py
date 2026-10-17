"""Owner confirmed the green arm-to-side transition on17Oct2026.

Relative to the unchanged upper-arm line, the torso begins its turn earlier.
The target is a shape relation; the owner's image is not included in the repo.
"""
import os,sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
# Existing measurement implementation, unchanged.
from original_review_r41_line import profile,guide
class OwnerConfirmedTransition(unittest.TestCase):
 def test_side_turns_into_body_at_confirmed_junction(self):
  with np.load(os.environ['HGPT_CONTOUR_NPZ']) as z,np.load(os.environ['HGPT_LINE_PARENT_NPZ']) as ref:
   stations=np.array([-.12,-.10,-.08,-.06]);lower=np.array([20.,12.,6.,0.]);upper=np.array([31.,24.,17.,9.])
   for side in ('l','r'):
    gh=ref[f'gh_{side}_135.625'];el=ref[f'elbow_{side}_135.625'];f=ref['faces']
    line=guide(ref['all_135.625'],f,gh,el,side)
    measured=(profile(z['all_135.625'],f,gh,el,side,stations)-np.polyval(line,stations))*1000
    print('R42_CONFIRMED_JUNCTION',side,measured.tolist(),flush=True)
    for s,value,lo,hi in zip(stations,measured,lower,upper):
     with self.subTest(side=side,station=s):self.assertGreaterEqual(value,lo);self.assertLessEqual(value,hi)
if __name__=='__main__':unittest.main()
