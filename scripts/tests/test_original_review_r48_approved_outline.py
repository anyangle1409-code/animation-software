"""Hold the actual owner-approved R47 outline, not the old outward-fill target."""
import os,unittest
import numpy as np

def posed(z,delta,index=25):
    return z['base'][index]+np.einsum('nij,nj->ni',z['mat'][index],
        np.einsum('kn,knj->nj',z['weight'][index],delta))

def outline(points,faces):
    edges=np.unique(np.sort(np.concatenate((faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]])),axis=1),axis=0)
    a,b=points[edges[:,0]],points[edges[:,1]]
    result=[]
    for side in (-1,1):
        for n in (np.array([side,0.,0.]),np.array([side,-1.,0.])/np.sqrt(2.)):
            for level in np.arange(1.18,1.62,.005):
                mask=((a[:,2]<=level)&(b[:,2]>level))|((b[:,2]<=level)&(a[:,2]>level))
                aa,bb=a[mask],b[mask]
                t=(level-aa[:,2])/(bb[:,2]-aa[:,2])
                p=aa+t[:,None]*(bb-aa)
                p=p[p[:,0]*side>.08]
                if not len(p):raise ValueError('Missing outline station')
                result.append(float((p@n).max()))
    return np.array(result)

class ApprovedOutline(unittest.TestCase):
    def test_marked_rear_and_three_quarter_outlines_stay_within_one_mm(self):
        with np.load(os.environ['HGPT_R48_RESPONSE']) as z:
            old=np.load(os.environ['HGPT_R48_APPROVED_SOLUTION'])['delta']
            current=np.load(os.environ['HGPT_R48_SOLUTION'])['delta']
            error=float(abs(outline(posed(z,current),z['faces'])-outline(posed(z,old),z['faces'])).max()*1000)
            print('R48_APPROVED_OUTLINE_MAX_ERROR_MM',error,flush=True)
            self.assertLessEqual(error,1.)

if __name__=='__main__':unittest.main()
