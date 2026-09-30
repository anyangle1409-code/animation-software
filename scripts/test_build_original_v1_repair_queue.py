from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("build_original_v1_repair_queue.py")
SPEC = importlib.util.spec_from_file_location("repair_queue", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

ROOT = Path(__file__).resolve().parents[1]


class RepairQueueTests(unittest.TestCase):
    def test_region_failure_requires_matching_region_and_pose(self):
        priority = {"poses": ["press_top"], "regions": ["shoulder"]}
        self.assertTrue(
            mod.owns_failure(
                priority,
                {"pose": "press_top", "region": "shoulder", "metric": "region_max_ratio"},
            )
        )
        self.assertFalse(
            mod.owns_failure(
                priority,
                {"pose": "press_top", "region": "hand", "metric": "region_max_ratio"},
            )
        )
        self.assertFalse(
            mod.owns_failure(
                priority,
                {"pose": "curl_peak", "region": "shoulder", "metric": "region_max_ratio"},
            )
        )

    def test_global_pose_failure_is_owned_by_matching_priority(self):
        priority = {"poses": ["press_top_rhythm"], "regions": ["shoulder", "torso"]}
        self.assertTrue(
            mod.owns_failure(
                priority,
                {"pose": "press_top_rhythm", "region": None, "metric": "volume_ratio"},
            )
        )

    def test_grip_side_is_owned_by_hand_priority(self):
        priority = {"poses": ["curl_handle"], "regions": ["hand", "finger", "thumb"]}
        self.assertTrue(
            mod.owns_failure(
                priority,
                {"pose": "curl_handle", "region": "grip_l", "metric": "grip_max_penetration_mm"},
            )
        )

    def test_real_r2_baseline_has_complete_repair_ownership(self):
        spec = mod.deval.load_json(ROOT / "ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json")
        poses = mod.deval.load_json(ROOT / "ORIGINAL_V1_WORK/candidates/pose_test_report_r2.json")
        result = mod.build_queue(poses, poses, spec, "development_blocker")

        self.assertEqual(result["acceptance_failure_count"], 54)
        self.assertEqual(result["next_priority"], 1)
        self.assertTrue(result["ownership_complete"])
        self.assertEqual(result["unmapped_failure_count"], 0)

        by_priority = {item["priority"]: item for item in result["queue"]}
        self.assertEqual(by_priority[1]["owned_failure_count"], 15)
        self.assertEqual(by_priority[2]["owned_failure_count"], 38)
        self.assertEqual(by_priority[3]["owned_failure_count"], 3)
        self.assertEqual(by_priority[4]["owned_failure_count"], 1)
        self.assertEqual(by_priority[5]["owned_failure_count"], 0)


if __name__ == "__main__":
    unittest.main()
