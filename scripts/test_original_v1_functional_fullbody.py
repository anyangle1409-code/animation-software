"""Fail-closed contract for the source-skeleton/original-body evidence bridge."""
import unittest

import original_v1_functional_fullbody as bridge


class FunctionalFullBodyBridgeTests(unittest.TestCase):
    def test_review_views_cover_required_orthogonal_directions(self):
        self.assertEqual(set(bridge.REVIEW_VIEWS), {"front", "side", "rear"})
        self.assertEqual(bridge.REVIEW_VIEWS["front"], (0, -4, 0))
        self.assertEqual(bridge.REVIEW_VIEWS["rear"], (0, 4, 0))

    def test_major_mapping_is_bilateral_and_inventory_bound(self):
        self.assertEqual(bridge.MAJOR_BONE_MAPPING["anat_humerus_left"], "upperarm_r")
        self.assertEqual(bridge.MAJOR_BONE_MAPPING["anat_scapula_right"], "scapula_l")
        anatomical = set(bridge.MAJOR_BONE_MAPPING)
        anatomical.update(f"anatomy_extra_{i}" for i in range(206 - len(anatomical)))
        runtime = set(bridge.MAJOR_BONE_MAPPING.values())
        runtime.update(f"runtime_extra_{i}" for i in range(67 - len(runtime)))
        result = bridge.validate_inventory(anatomical, runtime, 17946)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["mapped_bones"], 16)
        self.assertFalse(result["anatomy_approved"])

        anatomical.remove("anat_femur_right")
        errors = "\n".join(bridge.validate_inventory(anatomical, runtime, 17946)["errors"])
        self.assertIn("anat_femur_right", errors)

    def test_wrong_body_or_runtime_inventory_is_refused(self):
        anatomical = set(bridge.MAJOR_BONE_MAPPING)
        anatomical.update(f"anatomy_extra_{i}" for i in range(206 - len(anatomical)))
        runtime = set(bridge.MAJOR_BONE_MAPPING.values())
        runtime.update(f"runtime_extra_{i}" for i in range(67 - len(runtime)))
        runtime.remove("scapula_l")
        errors = "\n".join(bridge.validate_inventory(anatomical, runtime, 42)["errors"])
        self.assertIn("scapula_l", errors)
        self.assertIn("17946", errors)
        self.assertIn("67", errors)

    def test_full_body_frame_uses_pose_bounds_instead_of_torso_closeup(self):
        centre, scale = bridge.frame_from_bounds(
            (-0.72, -0.24, 0.0), (0.72, 0.22, 2.06)
        )
        self.assertEqual(centre, (0.0, -0.01, 1.03))
        self.assertAlmostEqual(scale, 2.06 * 1.12)
        for padding in (float("nan"), float("inf"), -float("inf")):
            with self.assertRaises(ValueError):
                bridge.frame_from_bounds((0, 0, 0), (1, 1, 1), padding)
        with self.assertRaises(ValueError):
            bridge.frame_from_bounds((0, 0, 0), (2, 2, 2), 1e308)


if __name__ == "__main__":
    unittest.main()
