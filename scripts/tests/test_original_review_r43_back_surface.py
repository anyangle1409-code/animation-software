"""Do not restore the old posterior crumpling while matching the silhouette."""
import sys,os,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r41_front import edge_pairs,angles
class BackSurface(unittest.TestCase):
 def test_no_new_sharp_posterior_folds_over_full_motion(self):
  with np.load(os.environ['HGPT_R43_RESPONSE']) as z,np.load(os.environ['HGPT_R43_SOLUTION']) as s:
   e,ff=edge_pairs(z['faces']);r=z['rest'][e].mean(1)
   select=(abs(r[:,0])>.08)&(abs(r[:,0])<.35)&(r[:,1]>.025)&(r[:,2]>1.20)&(r[:,2]<1.51)&z['free'].any(0)[e].any(1);ft=z['faces'][ff[select]]
   base=z['base'];a=z['mat'];w=z['weight'];worst=0.
   for i,b in enumerate(base):
    p=b+np.einsum('nij,nj->ni',a[i],np.einsum('kn,knj->nj',w[i],s['delta']));worst=max(worst,float((angles(p,ft)-angles(b,ft)).max()))
   print('R43_NEW_POSTERIOR_CREASE_DEGREES',worst,flush=True);self.assertLessEqual(worst,2.)
if __name__=='__main__':unittest.main()
