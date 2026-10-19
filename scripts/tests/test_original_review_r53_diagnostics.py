import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r53_diagnostics import *

class Diagnostics(unittest.TestCase):
    def test_protected_families_never_muted(self):
        names=['HGPT_S5_BAKE_l_110','HGPT_S7_DELT_r_130','HGPT_SHOULDER_l','HGPT_K1_ELBOW_l_90','Basis']
        self.assertEqual(muted_names(names,'all_shoulder_off'),names[:2])
        self.assertEqual(muted_names(names,'no_S7'),[names[1]])
        with self.assertRaises(ValueError):muted_names(names,'unknown')
    def test_jump_identifies_boundary(self):
        np.testing.assert_allclose(edge_weight_jumps([[1,0],[.5,.5],[0,1]],[[0,1],[0,2]]),[1,2])
        with self.assertRaises(ValueError):edge_weight_jumps([[float('nan')]],[[0,0]])
    def test_parent_motion_removed(self):
        m=np.repeat(np.eye(4)[None],2,axis=0);m[1,:2,:2]=[[0,-1],[1,0]]
        np.testing.assert_allclose(relative_rotation_degrees(m,None),[0,90],atol=1e-6)
        np.testing.assert_allclose(relative_rotation_degrees(m,m),[0,0],atol=1e-6)
    def test_metrics_rigid_rotation(self):
        r=np.array([[0.,0,0],[1,0,0],[0,1,0]])
        p=r[:,[1,0,2]]
        a=geometry_metrics(r,p,[[0,1,2]],[[0,1],[1,2],[2,0]],np.ones(3,dtype=bool))
        self.assertEqual(a['area_ratio_min'],1)
        self.assertEqual(a['edge_ratio_max'],1)
    def test_no_broadcasted_motion_identity(self):
        from original_review_r53_diagnostics import verify_clip_identity
        keys=('runtime','anatomy','basis','polygons','groups','weights','protected_keys')
        r=dict(samples=161,bone_names=['a'],protected_identity=dict.fromkeys(keys,True))
        reports={'r41':r,'r52':r}
        a=np.tile(np.eye(4),(161,1,1,1));b=a[:1]
        with self.assertRaises(ValueError):verify_clip_identity(reports,{'r41':a,'r52':b})
        self.assertEqual(verify_clip_identity(reports,{'r41':a,'r52':a}),0)

if __name__=='__main__':unittest.main()
