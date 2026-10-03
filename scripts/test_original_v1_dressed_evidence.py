"""Dressed evidence is candidate-bound, matched and non-promotional."""
from __future__ import annotations

import copy
import math
import unittest

import original_v1_dressed_evidence as d


class DressedEvidenceTests(unittest.TestCase):
    def fixture(self):
        sha = "a" * 64
        import original_v1_locked_rig as locked
        rig=locked.load_locked_rig()
        lock_receipt={"revision":rig["revision"],"rig_structure_sha256":rig["rig_structure_sha256"],
                      "bone_count":rig["bone_count"],"deform_bone_count":rig["deform_bone_count"],
                      "lock":rig["lock"],"payload":rig["payload"]}
        manifest = {"candidate": "HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r30.blend", "candidate_sha256": sha}
        raw = {"status": "EVIDENCE_ONLY", "phase_complete": False, "production_approved": False, "candidate_sha256": sha,
               "locked_rig":copy.deepcopy(lock_receipt)}
        poses = []
        for pose in sorted(d.POSES):
            poses.append({
                "pose": pose,
                "pose_state_sha256": "b" * 64,
                "source_body_metrics": {"pose": pose, "volume_ratio": 1.0},
                "body_vertex_count_evaluated": 100,
                "garment_vertex_count_evaluated": 20,
                "body_face_count_evaluated": 200,
                "garment_face_count_evaluated": 40,
                "body_garment_intersecting_face_pairs": 0,
                "body_to_garment_min_vertex_surface_distance_mm": 1.25,
                "garment_to_body_min_vertex_surface_distance_mm": 1.20,
                "garment_lowest_z_mm": 10.0,
                "garment_vertices_below_floor": 0,
            })
        files = []
        for pose, view in sorted(d.REVIEW_KEYS):
            key = {"camera_matrix_world": [[1, 0, 0, 0]], "orthographic_scale": 2.0, "resolution": [900, 900, 100]}
            for presentation in ("bare", "dressed"):
                files.append({
                    "pose": pose, "view": view, "kind": "full", "presentation": presentation,
                    "file": f"review/{pose}_{view}_{presentation}.png", "sha256": "c" * 64,
                    "capture_key": copy.deepcopy(key),
                })
        report = {
            "status": "EVIDENCE_ONLY", "phase_complete": False, "production_approved": False,
            "candidate_revision": "r30", "candidate": manifest["candidate"], "candidate_sha256": sha,
            "rig_id": rig["identity"], "locked_rig":copy.deepcopy(lock_receipt), "poses": poses,
            "review": {"owner_review": "pending", "blocking": False, "files": files},
            "unresolved_checks": ["continuous_dressed_motion"],
        }
        return report, raw, manifest

    def test_valid_report_summarises_without_pass(self):
        report, raw, manifest = self.fixture()
        result = d.validate(report, raw, manifest)
        self.assertEqual(result["status"], "EVIDENCE_ONLY")
        self.assertFalse(result["phase_complete"])
        self.assertEqual(result["pose_count"], len(d.POSES))
        self.assertEqual(result["review_pair_count"], len(d.REVIEW_KEYS))

    def test_stale_locked_rig_receipt_refused(self):
        report, raw, manifest = self.fixture()
        report["locked_rig"]["bone_count"] = 63
        with self.assertRaisesRegex(ValueError, "static dressed locked rev2c rig identity differs"):
            d.validate(report, raw, manifest)

    def test_raw_pair_locked_rig_drift_refused(self):
        report, raw, manifest = self.fixture()
        raw["locked_rig"]["rig_structure_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "raw garment pair locked rev2c rig identity differs"):
            d.validate(report, raw, manifest)

    def test_candidate_mismatch_refused(self):
        report, raw, manifest = self.fixture(); raw["candidate_sha256"] = "d" * 64
        with self.assertRaisesRegex(ValueError, "candidate identity"):
            d.validate(report, raw, manifest)

    def test_missing_pose_refused(self):
        report, raw, manifest = self.fixture(); report["poses"].pop()
        with self.assertRaisesRegex(ValueError, "coverage"):
            d.validate(report, raw, manifest)

    def test_approval_claim_refused(self):
        report, raw, manifest = self.fixture(); report["production_approved"] = True
        with self.assertRaisesRegex(ValueError, "approval"):
            d.validate(report, raw, manifest)

    def test_mismatched_pair_camera_refused(self):
        report, raw, manifest = self.fixture()
        target = next(r for r in report["review"]["files"] if r["presentation"] == "dressed")
        target["capture_key"]["orthographic_scale"] = 3.0
        with self.assertRaisesRegex(ValueError, "camera"):
            d.validate(report, raw, manifest)

    def test_duplicate_presentation_refused(self):
        report, raw, manifest = self.fixture(); report["review"]["files"].append(copy.deepcopy(report["review"]["files"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            d.validate(report, raw, manifest)

    def test_negative_clearance_refused(self):
        report, raw, manifest = self.fixture(); report["poses"][0]["body_to_garment_min_vertex_surface_distance_mm"] = -1
        with self.assertRaisesRegex(ValueError, "clearance"):
            d.validate(report, raw, manifest)

    def test_nonfinite_metric_refused(self):
        report, raw, manifest = self.fixture(); report["poses"][0]["garment_lowest_z_mm"] = math.nan
        with self.assertRaises(ValueError):
            d.validate(report, raw, manifest)


if __name__ == "__main__":
    unittest.main()
