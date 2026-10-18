"""Early progress is an execution guard, never model or owner acceptance."""
import os,json,unittest
from pathlib import Path
class Preflight(unittest.TestCase):
 def test_three_retained_steps_improve_merit_while_holding_outline(self):
  d=json.loads(Path(os.environ['HGPT_R51_PREFLIGHT_HISTORY']).read_text());h=d['history']
  self.assertEqual(len(h),3)
  self.assertLessEqual(max(v['approved_outline_error_mm'] for v in h),.95)
  improvement=1-h[-1]['repair_score']/d['initial_repair_score'];print('R51_DIAGNOSTIC_REPAIR_REDUCTION_PCT',100*improvement,flush=True)
  self.assertGreaterEqual(improvement,.10)
  self.assertFalse(d['approved']);self.assertFalse(d['model_saved'])
if __name__=='__main__':unittest.main()
