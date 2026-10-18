"""Retained repair searches cannot silently become saved or approved models."""
import sys,json,unittest,tempfile
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from retain_original_review_r51 import retain
class Retention(unittest.TestCase):
 def test_missing_checkpoint_records_failure_before_raise(self):
  with tempfile.TemporaryDirectory() as t:
   with self.assertRaises(RuntimeError):retain(t,124)
   r=json.loads((Path(t)/'fit_status.json').read_text());self.assertFalse(r['has_retained_search_state']);self.assertFalse(r['model_saved'])
 def test_preflight_fallback_is_explicitly_unverified(self):
  with tempfile.TemporaryDirectory() as t:
   np.savez(Path(t)/'preflight.npz',delta=np.zeros((1,1,3)))
   r=retain(t,124);self.assertEqual(r['state_source'],'preflight_repair_search_only');self.assertFalse(r['shape_repair_complete']);self.assertFalse(r['approved']);self.assertEqual(r['retained_state_safety'],'UNVERIFIED_SEARCH_STATE')
 def test_main_progress_precedes_preflight(self):
  with tempfile.TemporaryDirectory() as t:
   np.savez(Path(t)/'preflight.npz',delta=np.zeros((1,1,3)));np.savez(Path(t)/'solved.npz.progress.npz',delta=np.ones((1,1,3)))
   r=retain(t,1);self.assertEqual(r['state_source'],'main_repair_search_progress');self.assertFalse(r['model_saved']);np.testing.assert_array_equal(np.load(Path(t)/'solved.npz')['delta'],1.)
if __name__=='__main__':unittest.main()
