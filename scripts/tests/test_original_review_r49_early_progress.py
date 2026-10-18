"""A short preflight must make useful actual-outline progress, not merely run."""
import os,sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from test_original_review_r48_approved_outline import outline,posed

class EarlyProgress(unittest.TestCase):
    def test_three_step_preflight_reduces_actual_outline_error_by_one_mm(self):
        with np.load(os.environ['HGPT_R49_RESPONSE']) as z:
            target=outline(z['r49_profile_target_points'],z['faces'])
            before=float(abs(outline(z['base'][25],z['faces'])-target).max())
            delta=np.load(os.environ['HGPT_R49_SOLUTION'])['delta']
            after=float(abs(outline(posed(z,delta),z['faces'])-target).max())
            improvement=(before-after)*1000
            print('R49_THREE_STEP_OUTLINE_IMPROVEMENT_MM',improvement,flush=True)
            self.assertGreaterEqual(improvement,1.)

if __name__=='__main__':unittest.main()
