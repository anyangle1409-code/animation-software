#!/usr/bin/env python3
import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE / "anatomy_fit"))
sys.path.insert(0, str(HERE))

import nlm_ct_pelvis_workflow as workflow
from test_nlm_ct_landmark_validation import (
    landmark_packet, manifest, reviewed, scanners, segmented,
)


def inputs():
    review_result = reviewed()
    return {
        "pinned_manifest": manifest(),
        "review_packet": review_result,
        "segmentation_packet": segmented(review_result=review_result),
        "landmark_packet": landmark_packet(),
        "scanner_by_source": scanners(),
        "canonical_output_requested": False,
        "private_source_directory": "D:/private/never-echo-this",
    }


class EndToEndWorkflow(unittest.TestCase):
    def test_committed_live_candidate_report_is_source_bound_and_noncanonical(self):
        path = (ROOT / "ORIGINAL_V1_WORK" / "anatomy" / "audit"
                / "codex_pelvis_ct_candidate_review_20261009"
                / "candidate_sacrum_report.json")
        result = json.loads(path.read_text(encoding="utf-8"))
        expected = {row["source_id"]: row
                    for row in manifest()["exact_png_and_scanner_header_sha256"]}
        self.assertEqual(result["status"], "CANDIDATE_EVIDENCE_ONLY")
        self.assertEqual(result["canonical_promotions"], 0)
        self.assertFalse(result["canonical_promotion_allowed"])
        self.assertTrue(result["source_skeleton_governs_geometry"])
        self.assertTrue(result["missing_full_volume_coverage"])
        self.assertFalse(result["source_image_or_header_bytes_copied"])
        observations = result["stage_evidence"]["anatomical_review"]["observations"]
        self.assertEqual([item["source_id"] for item in observations], [1797, 1800, 1803])
        for item in observations:
            pin = expected[item["source_id"]]
            self.assertEqual(item["source_png_sha256"], pin["png_sha256"])
            self.assertEqual(item["source_header_sha256"], pin["scanner_header_sha256"])
            self.assertEqual(item["candidate_label"], "sacrum")
        segmented = result["stage_evidence"]["candidate_segmentation"]
        self.assertEqual(segmented["voxel_count"], 27)
        self.assertEqual(segmented["connected_component_count_6_neighbour"], 1)
        self.assertFalse(segmented["coverage_complete"])
        self.assertFalse(segmented["bone_surface_segmentation_verified"])
        landmarks = result["stage_evidence"]["candidate_landmarks"]
        self.assertEqual(landmarks["count"], 0)
        self.assertFalse(landmarks["all_landmarks_verified"])
        encoded = json.dumps(result)
        self.assertNotRegex(encoded, r"[A-Za-z]:\\")
        self.assertNotIn("raw_headers", encoded)
        self.assertNotIn("raw_pixels", encoded)

    def test_workflow_accepts_no_defensible_landmark_candidates(self):
        value = inputs()
        value["landmark_packet"]["landmarks"] = []
        result = workflow.run_workflow(value)
        self.assertEqual(result["status"], "CANDIDATE_EVIDENCE_ONLY")
        self.assertEqual(result["stage_evidence"]["candidate_landmarks"]["count"], 0)
        self.assertFalse(result["stage_evidence"]["candidate_landmarks"]
                         ["all_landmarks_verified"])
        self.assertEqual(result["canonical_promotions"], 0)

    def test_happy_path_is_candidate_evidence_only(self):
        result = workflow.run_workflow(inputs())
        self.assertEqual(result["status"], "CANDIDATE_EVIDENCE_ONLY")
        self.assertEqual(result["canonical_promotions"], 0)
        self.assertTrue(result["missing_full_volume_coverage"])
        self.assertIn("anatomical_review", result["stage_evidence"])
        self.assertIn("candidate_segmentation", result["stage_evidence"])
        self.assertIn("candidate_landmarks", result["stage_evidence"])
        self.assertEqual(
            result["stage_evidence"]["candidate_segmentation"]["voxel_count"], 3
        )
        encoded = json.dumps(result, sort_keys=True)
        self.assertNotIn("never-echo-this", encoded)
        self.assertNotIn("private_source_directory", encoded)
        self.assertNotIn("raw_pixels", encoded)
        self.assertNotIn("raw_headers", encoded)

    def test_stage_failure_propagates(self):
        value = inputs()
        value["segmentation_packet"]["slices"][0]["runs"] = [[10, 11, 10]]
        with self.assertRaisesRegex(ValueError, "runs"):
            workflow.run_workflow(value)

    def test_canonical_output_request_is_refused(self):
        value = inputs()
        value["canonical_output_requested"] = True
        with self.assertRaisesRegex(ValueError, "canonical output"):
            workflow.run_workflow(value)


class WorkflowCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="nlm_ct_workflow_")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write_input(self, value=None):
        path = self.root / "input.json"
        path.write_text(json.dumps(value or inputs()), encoding="utf-8")
        return path

    def test_cli_exclusive_creates_sanitized_output(self):
        source = self.write_input()
        out = self.root / "report.json"
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(workflow.main(["--input", str(source), "--out", str(out)]), 0)
        original = out.read_bytes()
        report = json.loads(original.decode("utf-8"))
        self.assertEqual(report["status"], "CANDIDATE_EVIDENCE_ONLY")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(workflow.main(["--input", str(source), "--out", str(out)]), 2)
        self.assertEqual(out.read_bytes(), original)

    def test_cli_rejects_malformed_json(self):
        source = self.root / "bad.json"
        source.write_text("{", encoding="utf-8")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(workflow.main(["--input", str(source)]), 2)

    def test_cli_refuses_canonical_flag(self):
        source = self.write_input()
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(workflow.main([
                "--input", str(source), "--request-canonical-output"
            ]), 2)


if __name__ == "__main__":
    unittest.main()
