from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("evaluate_original_v1_deformation_report.py")
SPEC = importlib.util.spec_from_file_location("deformation_eval", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


LIMITS = {
    "volume_ratio_min": 0.9,
    "volume_ratio_max": 1.1,
    "edge_ratio_p01_min": 0.4,
    "edge_ratio_p99_max": 2.0,
    "region_min_ratio_min": 0.15,
    "region_max_ratio_max": 5.0,
    "self_intersecting_face_pairs_max": 200,
    "lowest_z_min_m": -0.002,
    "grip_max_penetration_mm": 2.0,
    "grip_min_contact_vertices_within_2mm": 20,
}


def pose(**overrides):
    data = {
        "pose": "neutral",
        "volume_ratio": 1.0,
        "edge_ratio_p01": 1.0,
        "edge_ratio_p99": 1.0,
        "compressed_edges_lt_0_6": 0,
        "stretched_edges_gt_1_6": 0,
        "self_intersecting_face_pairs": 0,
        "self_intersection_by_region": {},
        "by_region": {
            "shoulder": {
                "compressed": 0,
                "stretched": 0,
                "min_ratio": 1.0,
                "max_ratio": 1.0,
            }
        },
        "lowest_z": 0.0,
    }
    data.update(overrides)
    return data


class DeformationEvaluatorTests(unittest.TestCase):
    def test_clean_pose_passes(self):
        self.assertEqual(mod.evaluate_pose(pose(), LIMITS), [])

    def test_extreme_region_stretch_and_collapse_fail(self):
        p = pose(
            pose="press_top",
            by_region={
                "shoulder": {
                    "compressed": 10,
                    "stretched": 10,
                    "min_ratio": 0.1,
                    "max_ratio": 8.0,
                }
            },
        )
        failures = mod.evaluate_pose(p, LIMITS)
        metrics = {f["metric"] for f in failures}
        self.assertIn("region_min_ratio", metrics)
        self.assertIn("region_max_ratio", metrics)

    def test_grip_penetration_fails_without_hiding_contact(self):
        report = [
            {
                "pose": "curl_handle",
                "grip_l": {
                    "max_penetration_mm": 5.93,
                    "contact_vertices_within_2mm": 178,
                },
                "grip_r": {
                    "max_penetration_mm": 0.8,
                    "contact_vertices_within_2mm": 40,
                },
            }
        ]
        failures = mod.evaluate_grip(report, LIMITS)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["region"], "grip_l")
        self.assertEqual(failures[0]["metric"], "grip_max_penetration_mm")

    def test_required_pose_group_detects_missing_pose(self):
        spec = {
            "asset": "test",
            "rig": "test",
            "profiles": {"development_blocker": LIMITS},
            "required_pose_groups": {"core": ["neutral", "press_top"]},
        }
        summary = mod.make_summary(
            [pose()],
            None,
            spec,
            "development_blocker",
            "core",
        )
        self.assertEqual(summary["status"], "FAIL")
        self.assertEqual(summary["missing_required_poses"], ["press_top"])

    def test_json_loader_accepts_utf8_bom(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            path.write_bytes(b"\xef\xbb\xbf" + json.dumps([pose()]).encode("utf-8"))
            self.assertEqual(mod.load_json(path)[0]["pose"], "neutral")


if __name__ == "__main__":
    unittest.main()
