"""R49 must not change R48 source data, target, editable mask or coverage."""
import os,unittest
import numpy as np

class Preparation(unittest.TestCase):
    def test_all_parent_arrays_and_exact_scope_and_target_are_preserved(self):
        with np.load(os.environ['HGPT_R49_PARENT_RESPONSE']) as z:parent={k:z[k] for k in z.files}
        with np.load(os.environ['HGPT_R49_RESPONSE']) as z:
            for name,expected in parent.items():np.testing.assert_array_equal(z[name],expected,err_msg=name)
            np.testing.assert_array_equal(z['r49_allowed'],parent['r48_allowed'])
            np.testing.assert_array_equal(z['r49_profile_target_points'],parent['r48_profile_target_points'])

if __name__=='__main__':unittest.main()
