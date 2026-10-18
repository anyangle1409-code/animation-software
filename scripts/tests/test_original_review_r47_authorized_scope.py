"""R47 authorized arm-root release; all prior candidate tests remain unchanged."""
import os,sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from author_original_review_r47 import author

class AuthorizedScope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with np.load(os.environ['HGPT_R47_RESPONSE']) as z:cls.data={k:z[k] for k in z.files}
        cls.delta,cls.allowed,cls.report=author(cls.data)
        if 'HGPT_R47_SOLUTION' in os.environ:
            cls.delta=np.load(os.environ['HGPT_R47_SOLUTION'])['delta']
            cls.allowed=cls.data['r47_allowed']

    def test_previously_locked_root_can_move_inward(self):
        ids=np.array([15575,19050,8712,21318])
        self.assertTrue(self.allowed[2:4,ids].all())
        d=self.data
        change=np.einsum('nij,nj->ni',d['mat'][25],np.einsum('kn,knj->nj',d['weight'][25],self.delta))
        self.assertGreater(float(change[ids,0].min()),.003)

    def test_elbow_and_distal_arm_are_preserved(self):
        d=self.data
        protected=np.zeros(len(d['rest']),bool)
        for k in range(7):
            for sign,bones in zip((-1,1),d['key_bones'][k]):
                gh,el=bones;axis=el-gh;axis/=np.linalg.norm(axis)
                p=d['key_base'][k]
                distal=(p[:,0]*sign>0)&((p-gh)@axis>=.16)
                protected|=distal
                np.testing.assert_array_equal(self.delta[k,distal],0.)
        np.testing.assert_array_equal(self.delta[:,protected],0.)

    def test_top_and_anchors_and_outside_scope_are_preserved(self):
        d=self.data;rest=d['rest']
        mirror=int(np.argmin(np.linalg.norm(rest-rest[18633]*[-1,1,1],axis=1)))
        np.testing.assert_array_equal(self.delta[6],0.)
        np.testing.assert_array_equal(self.delta[:,[18633,mirror]],0.)
        np.testing.assert_array_equal(self.delta[~self.allowed],0.)

    def test_source_and_dense_displacement_caps_are_unchanged(self):
        self.assertTrue(np.isfinite(self.delta).all())
        self.assertLessEqual(float(np.linalg.norm(self.delta,axis=2).max()),.045)
        dense=np.einsum('dk,knj->dnj',self.data['sampling_basis'],self.delta)
        self.assertLessEqual(float(np.linalg.norm(dense,axis=2).max()),.045)

if __name__=='__main__':unittest.main()
