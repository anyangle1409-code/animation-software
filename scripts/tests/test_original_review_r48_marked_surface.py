"""Regression: R47 folds at the very pose whose outline the owner approved."""
import os
import unittest
import numpy as np

class MarkedSurface(unittest.TestCase):
    def test_no_new_triangle_normal_reversals_at_approved_pose(self):
        with np.load(os.environ['HGPT_R48_RESPONSE']) as z:
            b=z['base'][25];faces=z['faces']
            with np.load(os.environ['HGPT_R48_SOLUTION']) as s:
                p=b+np.einsum('nij,nj->ni',z['mat'][25],
                    np.einsum('kn,knj->nj',z['weight'][25],s['delta']))
            def normals(v):
                t=v[faces]
                return np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
            reversals=int(np.sum(np.einsum('ni,ni->n',normals(b),normals(p))<=0))
            print('R48_MARKED_NORMAL_REVERSALS',reversals,flush=True)
            self.assertEqual(reversals,0)

if __name__=='__main__':unittest.main()
