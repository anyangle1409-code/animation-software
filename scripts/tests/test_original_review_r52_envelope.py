import sys,unittest,numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
try:from original_review_r52_envelope import clip_marked
except ImportError:clip_marked=None
class Envelope(unittest.TestCase):
 def test_moves_only_active_material_inside_boundary(self):
  self.assertIsNotNone(clip_marked)
  x=np.zeros((72,2,3));x[40,0,0]=20;x[41,0,0]=20;x[:,1]=5
  lo=np.array([40,40]);t=np.array([.5,.5]);allowed=np.ones((72,2),bool);allowed[:,1]=False
  base=np.array([[100.,0,1400.],[-100.,0,1400.]]);mat=np.repeat(np.eye(3)[None],2,axis=0)
  envelopes=[(1,np.array([1.,0,0]),np.array([1200.,1600.]),np.array([110.,110.]))]
  y=clip_marked(x.copy(),allowed,(lo,lo+1,t),base,mat,envelopes)
  self.assertLessEqual(float(base[0,0]+.5*(y[40,0,0]+y[41,0,0])),110.000001)
  np.testing.assert_array_equal(y[:,1],x[:,1])
if __name__=='__main__':unittest.main()
