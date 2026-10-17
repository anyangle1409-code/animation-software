import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r41_checks import bounded_s7_update
class BoundedUpdates(unittest.TestCase):
 def test_small_end_key_update_allowed_and_large_update_rejected(self):
  a={'key166':np.zeros((3,3))};b={'key166':np.zeros((3,3))};b['key166'][0,0]=.0007
  self.assertTrue(bounded_s7_update(a,b,.75)[0]);b['key166'][0,1]=.0007
  self.assertFalse(bounded_s7_update(a,b,.75)[0])
 def test_missing_keys_and_nonfinite_updates_rejected(self):
  a={'key166':np.zeros((3,3))}
  self.assertFalse(bounded_s7_update(a,{},.75)[0]);b={'key166':np.full((3,3),np.nan)}
  self.assertFalse(bounded_s7_update(a,b,.75)[0])
if __name__=='__main__':unittest.main()
