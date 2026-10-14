"""Native checks of the W3 option A diagnostic: stateless mid-elevation-reference helper drive (in memory only)."""
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import build_functional_shoulder_correction_blender as correction
import diagnose_shoulder_helper_deformer_blender as d
import build_original_shoulder_weight_refit_blender as w4


class ShoulderHelperReferenceDriveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res = correction.build_corrected_scene()
        for kb in cls.res["body"].data.shape_keys.key_blocks[1:]:
            kb.value = 0.0
        cls.before = w4.sweep_metrics(cls.res, angles=(145, 160))
        cls.info = d.add_helpers(cls.res)
        cls.after = w4.sweep_metrics(cls.res, angles=(145, 160))

    def test_contract_is_extended_only_in_memory(self):
        self.assertEqual(self.info["joints"], 69)
        self.assertEqual(d.DRIVE, "reference")
        self.assertEqual(len(self.res["body"].data.vertices), 17946)

    def test_helper_is_identity_at_rest_and_half_the_path_without_flip(self):
        rig = self.res["runtime"]
        correction.apply_corrected_pose(self.res, 0)
        self.assertLess(rig.pose.bones["deltoid_helper_r"].rotation_quaternion.angle, 1e-6)
        angles = []
        for e in range(90, 161, 5):
            correction.apply_corrected_pose(self.res, e)
            angles.append(math.degrees(rig.pose.bones["deltoid_helper_r"].rotation_quaternion.angle))
        steps = [b - a for a, b in zip(angles, angles[1:])]
        self.assertLess(max(abs(s) for s in steps), 10.0)      # no branch jump (a flip would be ~90 deg)
        correction.apply_corrected_pose(self.res, 0)

    def test_overhead_collision_and_collapse_reduced_volume_loss_smaller(self):
        for a in ("145", "160"):
            b, h = self.before[int(a)], self.after[int(a)]
            self.assertLess(h["self_intersecting_face_pairs_in_region"], 0.5 * b["self_intersecting_face_pairs_in_region"], a)
            self.assertLess(h["collapse_faces_ratio_lt_0_1"], b["collapse_faces_ratio_lt_0_1"], a)
            self.assertGreater(h["body_volume_change_pct"], b["body_volume_change_pct"], a)

    def test_known_cost_stretch_is_recorded_not_hidden(self):
        # retained failure signal: the helper increases stretched faces; this documents it rather than asserting it away
        self.assertGreater(self.after[160]["stretched_faces_ratio_gt_2"], self.before[160]["stretched_faces_ratio_gt_2"])


if __name__ == "__main__":
    unittest.main(argv=[__file__])
