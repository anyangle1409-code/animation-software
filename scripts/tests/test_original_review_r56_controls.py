"""Synthetic scope tests for R56. No Blender model changed."""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r52_temporal import SOURCE
from audit_original_review_r56_controls import checked_permissions, source_key_rows


class R56Scope(unittest.TestCase):
    def test_ghost_source_110_and_166_are_zero(self):
        allowed=np.ones((7,4),bool)
        frozen=np.zeros_like(allowed)
        got=checked_permissions(allowed,frozen)
        self.assertEqual(got.shape,(72,4))
        self.assertFalse(got[[0,15,71]].any())
        for k in range(1,6):
            np.testing.assert_array_equal(got[int(SOURCE[k])],allowed[k])

    def test_source_specific_masks_do_not_become_union_at_source_knots(self):
        allowed=np.zeros((7,3),bool)
        allowed[1,0]=True
        allowed[3,1]=True
        dense=checked_permissions(allowed,np.zeros_like(allowed))
        self.assertFalse(dense[110-95,0])
        self.assertTrue(dense[120-95,0])
        self.assertFalse(dense[130-95,0])
        self.assertTrue(dense[118-95,1])
        self.assertFalse(dense[136-95,0])

    def test_source_frozen_and_allowed_kept_independently(self):
        allowed=np.zeros((7,2),bool)
        frozen=np.zeros_like(allowed)
        allowed[1,0]=True
        frozen[0,0]=True
        dense=checked_permissions(allowed,frozen)
        self.assertTrue(dense[118-95,0])
        vals=source_key_rows(0,allowed,frozen,allowed,dense,np.zeros((72,2,3)))
        self.assertTrue(vals[0]["source_frozen_arm"])
        self.assertFalse(vals[0]["actual_R52_dense_control_allowed"])
        self.assertTrue(vals[1]["actual_R52_dense_control_allowed"])

    def test_reject_bad_or_nonboolean_masks(self):
        good=np.zeros((7,3),bool)
        for allowed,frozen in [
            (good.astype(int),good),
            (good,good[:-1]),
            (good[:6],good[:6])]:
            with self.assertRaises(ValueError):
                checked_permissions(allowed,frozen)

    def test_original_controls_have_no_dense_permission_leakage(self):
        a=np.zeros((7,5),bool)
        a[2,2]=True
        out=checked_permissions(a,np.zeros_like(a))
        self.assertTrue(out[130-95,2])
        self.assertFalse(out[120-95,2])
        self.assertFalse(out[136-95,2])
        self.assertFalse(out[:,0].any())


if __name__=="__main__":
    unittest.main()
