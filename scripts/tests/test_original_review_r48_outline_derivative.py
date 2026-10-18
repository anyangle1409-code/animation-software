"""Analytic derivatives must match actual silhouette changes, both review views."""
import os,sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r48_outline import silhouette

class OutlineDerivative(unittest.TestCase):
    def test_active_edge_derivative_in_both_review_views(self):
        with np.load(os.environ['HGPT_R48_RESPONSE']) as z:
            # The fitter adds float64 increments. Finite differences must use
            # that same precision, not quantize 0.1-micron probes to float32.
            points=z['base'][25].astype(np.float64);faces=z['faces']
        for side,sign in [('l',-1),('r',1)]:
            for n in [np.array([sign,0.,0.]),np.array([sign,-1.,0.])/np.sqrt(2.)]:
                for height in [1.2813,1.3517,1.4311]:
                    _,ids,grad=silhouette(points,faces,side,n,height)
                    for local,i in enumerate(ids):
                        for axis in range(3):
                            plus=points.copy();minus=points.copy();plus[i,axis]+=1e-7;minus[i,axis]-=1e-7
                            numerical=(silhouette(plus,faces,side,n,height)[0]-silhouette(minus,faces,side,n,height)[0])/2e-7
                            self.assertAlmostEqual(float(grad[local,axis]),float(numerical),places=5)

if __name__=='__main__':unittest.main()
