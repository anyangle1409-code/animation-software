import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r43_sampling import hats,basis,KEYS,DENSE
class Sampling(unittest.TestCase):
 def test_dense_baseline_keeps_original_arm_for_every_angle(self):
  angles=np.linspace(85,175,1801)
  np.testing.assert_allclose(hats(angles,DENSE)@hats(DENSE,KEYS),hats(angles,KEYS),atol=1e-14)
 def test_old_controls_are_retained(self):
  for j,a in enumerate(KEYS):np.testing.assert_allclose(basis()[np.flatnonzero(DENSE==a)[0]],np.eye(7)[j],atol=1e-14)
if __name__=='__main__':unittest.main()
