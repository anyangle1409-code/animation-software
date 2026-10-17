"""Whole-motion back check added after owner rejected R42's moving back."""
import os,sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
class BackMotion(unittest.TestCase):
 def test_back_frame_acceleration_stays_near_r41(self):
  with np.load(os.environ['HGPT_R43_RESPONSE']) as z,np.load(os.environ['HGPT_R43_SOLUTION']) as s:
   rest=z['rest'];base=z['base'][:41];a=z['mat'][:41];w=z['weight'][:41]
   mask=(abs(rest[:,0])>.08)&(abs(rest[:,0])<.25)&(rest[:,2]>1.27)&(rest[:,2]<1.49)&(rest[:,1]>.025)
   now=base+np.einsum('snij,snj->sni',a,np.einsum('skn,knj->snj',w,s['delta']))
   before=np.linalg.norm(np.diff(base[:,mask],n=2,axis=0),axis=2)
   after=np.linalg.norm(np.diff(now[:,mask],n=2,axis=0),axis=2)
   excess=float((after-before).max()*1000)
   print('R43_BACK_MOTION_EXCESS_MM',excess,flush=True)
   self.assertLessEqual(excess,.5)
if __name__=='__main__':unittest.main()
