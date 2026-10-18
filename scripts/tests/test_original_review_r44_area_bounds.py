"""Regression: below2x must still obey the unchanged parent-relative1% ceiling."""
import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r44_area import upper_bounds
class NativeAreaAgreement(unittest.TestCase):
 def test_no_stretched_faces_still_obey_parent_severity_limit(self):
  a=np.ones(3);parent=np.array([[1.80,1.9338163335375886,1.2]])
  b=upper_bounds(a,parent,np.array([parent.max()]))
  self.assertTrue((b<=parent.max()*1.01).all(),b)
  self.assertTrue((b>=parent).all())
 def test_count_and_severity_limits_both_apply(self):
  a=np.ones(3);parent=np.array([[1.8,2.2,4.]])
  b=upper_bounds(a,parent,np.array([4.]))
  self.assertLessEqual(b[0,0],2.);self.assertLessEqual(b.max(),4.04)
  self.assertTrue((b>=parent).all())
if __name__=='__main__':unittest.main()
