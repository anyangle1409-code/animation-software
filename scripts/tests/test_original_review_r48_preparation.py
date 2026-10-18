"""R48 changes target interpretation, never the source data or safety coverage."""
import os,unittest
import numpy as np

class Preparation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with np.load(os.environ['HGPT_R48_PARENT_RESPONSE']) as z:cls.parent={k:z[k] for k in z.files}
        with np.load(os.environ['HGPT_R48_RESPONSE']) as z:cls.current={k:z[k] for k in z.files}

    def test_parent_arrays_and_full_posterior_coverage_are_unchanged(self):
        for name,expected in self.parent.items():
            np.testing.assert_array_equal(self.current[name],expected,err_msg=name)

    def test_editable_scope_is_exactly_owner_authorized_r47_scope(self):
        np.testing.assert_array_equal(self.current['r48_allowed'],self.parent['r47_allowed'])

    def test_new_target_is_actual_approved_r47_pose(self):
        z=self.parent
        old=np.load(os.environ['HGPT_R48_APPROVED_SOLUTION'])['delta']
        expected=z['base'][25]+np.einsum('nij,nj->ni',z['mat'][25],np.einsum('kn,knj->nj',z['weight'][25],old))
        np.testing.assert_allclose(self.current['r48_profile_target_points'],expected,rtol=0,atol=1e-14)

if __name__=='__main__':unittest.main()
