"""Additional owner-mark goals; prior R34/R37 tests remain unchanged."""
import os,sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_contour import section_profile

def measured(z,side):
    p=z['all_135.625'];gh=z[f'gh_{side}_135.625']
    y,h=section_profile(p,z['faces'],gh,'back',side,np.arange(-.12,.06001,.002))
    if not np.isfinite(h).all():raise ValueError('Missing broad contour')
    line=np.interp(y,[y[0],y[-1]],[h[0],h[-1]])
    bow=float(np.sqrt(np.mean((h-line)**2))*1000)
    d=p-gh;d[:,0]*=1 if side=='r' else -1
    q=d[(abs(d[:,0]-.045)<.04)&(abs(d[:,2]-.03)<.035)&(d[:,1]>.025)]
    if len(q)<30:raise ValueError('Missing marked posterior surface')
    x,y,v=q.T
    a=np.column_stack((np.ones(len(x)),x,v,x*x,x*v,v*v))
    residual=y-a@np.linalg.lstsq(a,y,rcond=None)[0]
    return bow,float(np.percentile(abs(residual),95)*1000)

class OwnerMarkGoals(unittest.TestCase):
    def test_bilateral_broad_bow_is_reduced(self):
        with np.load(os.environ['HGPT_CONTOUR_NPZ']) as z:
            for side in ('l','r'):
                bow,ridge=measured(z,side);print('R38_MARK_METRICS',side,bow,ridge,flush=True)
                with self.subTest(side=side):self.assertLess(bow,7.5)
    def test_bilateral_marked_surface_is_smoother(self):
        with np.load(os.environ['HGPT_CONTOUR_NPZ']) as z:
            for side in ('l','r'):
                with self.subTest(side=side):self.assertLess(measured(z,side)[1],2.0)

if __name__=='__main__':unittest.main()
