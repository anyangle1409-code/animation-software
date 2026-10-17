import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r41_strain import area_log_penalty,area_safety
class StrainMath(unittest.TestCase):
 def test_gradient_matches_finite_difference_for_stretch_and_crush(self):
  a=np.array([[3.,1.,.05]])*1e-5;ref=np.ones(3)*1e-5
  value,gradient=area_log_penalty(a,ref)
  self.assertGreater(value,0.)
  for i in range(3):
   plus=a.copy();minus=a.copy();plus[0,i]+=1e-11;minus[0,i]-=1e-11
   numeric=(area_log_penalty(plus,ref)[0]-area_log_penalty(minus,ref)[0])/2e-11
   self.assertAlmostEqual(gradient[0,i],numeric,delta=max(1e-3,abs(numeric)*1e-6))
 def test_rest_area_has_no_quality_penalty(self):
  value,g=area_log_penalty(np.ones((2,3)),np.ones(3));self.assertEqual(value,0.);np.testing.assert_array_equal(g,0.)
 def test_final_area_gate_rejects_count_and_severity_regression(self):
  rest=np.array([[0.,0,0],[1,0,0],[0,1,0]]);faces=np.array([[0,1,2]])
  parent=rest.copy();parent[1]*=3
  worse=parent.copy();worse[1]*=1.02
  self.assertFalse(area_safety(worse,parent,rest,faces)['passed'])
  self.assertFalse(area_safety(parent,rest,rest,faces)['passed'])
  self.assertTrue(area_safety(rest,parent,rest,faces)['passed'])
if __name__=='__main__':unittest.main()
