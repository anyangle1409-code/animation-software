"""Sampled dressed range evidence is deterministic, source-bound and non-promotional."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import unittest

import original_v1_dressed_range_evidence as r


class DressedRangeEvidenceTests(unittest.TestCase):
    def plan(self):
        return {
            "sample_policy": {"samples_per_segment": 3, "deduplicate_shared_waypoints": True},
            "paths": [{"id": "demo", "waypoints": ["neutral", "squat_bottom", "neutral"]}],
        }

    def fixture(self):
        sha = "a" * 64
        manifest = {"candidate": "HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r30.blend", "candidate_sha256": sha}
        static = {"status": "EVIDENCE_ONLY", "phase_complete": False, "production_approved": False, "candidate_sha256": sha}
        plan = self.plan()
        rows = []
        for exp in r.expected_samples(plan):
            pairs = [[1, 2]] if exp["path_sample_index"] == 2 else []
            rows.append({
                **exp,
                "pose_state_sha256": "b" * 64,
                "body_garment_intersecting_face_pairs": len(pairs),
                "body_garment_face_pairs": pairs,
                "body_garment_face_pairs_sha256": hashlib.sha256(json.dumps(pairs, separators=(",", ":")).encode()).hexdigest(),
                "body_to_garment_min_vertex_surface_distance_mm": 1.2,
                "garment_to_body_min_vertex_surface_distance_mm": 1.1,
                "body_lowest_z_mm": 0.0,
                "garment_lowest_z_mm": 5.0,
                "body_vertices_below_floor": [],
                "garment_vertices_below_floor": [3] if exp["path_sample_index"] == 3 else [],
                "body_vertices_within_2mm_floor": [4],
                "garment_vertices_within_2mm_floor": [],
            })
        report = {
            "status": "EVIDENCE_ONLY", "phase_complete": False, "production_approved": False,
            "candidate_revision": "r30", "candidate": manifest["candidate"], "candidate_sha256": sha,
            "rig_id": "hgpt_canonical_v4_original", "samples": rows,
            "classification_status": "UNCLASSIFIED", "unresolved_checks": ["per_sample_legitimate_contact_classification"],
        }
        return report, static, manifest, plan

    def test_expected_sample_deduplication(self):
        rows = r.expected_samples(self.plan())
        self.assertEqual(len(rows), 5)
        self.assertEqual([x["path_sample_index"] for x in rows], list(range(5)))
        self.assertEqual(rows[2]["segment_t"], 1.0)
        self.assertEqual(rows[3]["segment_t"], 0.5)

    def test_valid_report_preserves_unresolved_findings(self):
        report, static, manifest, plan = self.fixture()
        result = r.validate_report(report, static, manifest, plan)
        self.assertEqual(result["sample_count"], 5)
        self.assertEqual(result["samples_with_raw_contact_findings"], 2)
        self.assertFalse(result["classification_complete"])
        self.assertFalse(result["production_approved"])

    def test_missing_sample_refused(self):
        report, static, manifest, plan = self.fixture(); report["samples"].pop()
        with self.assertRaisesRegex(ValueError, "coverage"):
            r.validate_report(report, static, manifest, plan)

    def test_changed_time_refused(self):
        report, static, manifest, plan = self.fixture(); report["samples"][1]["segment_t"] = .6
        with self.assertRaisesRegex(ValueError, "time"):
            r.validate_report(report, static, manifest, plan)

    def test_pair_hash_mismatch_refused(self):
        report, static, manifest, plan = self.fixture(); report["samples"][2]["body_garment_face_pairs_sha256"] = "c" * 64
        with self.assertRaisesRegex(ValueError, "pair hash"):
            r.validate_report(report, static, manifest, plan)

    def test_nonfinite_metric_refused(self):
        report, static, manifest, plan = self.fixture(); report["samples"][0]["body_lowest_z_mm"] = math.nan
        with self.assertRaises(ValueError):
            r.validate_report(report, static, manifest, plan)

    def test_template_marks_findings_unclassified(self):
        report, static, manifest, plan = self.fixture()
        template = r.classification_template(report)
        by_key = {x["sample_key"]: x for x in template["rows"]}
        self.assertEqual(by_key["demo:2"]["body_garment"]["classification"], "UNCLASSIFIED")
        self.assertEqual(by_key["demo:0"]["body_garment"]["classification"], "NO_FINDING")
        self.assertEqual(by_key["demo:3"]["garment_floor"]["classification"], "UNCLASSIFIED")

    def test_classification_requires_source_hash(self):
        report, static, manifest, plan = self.fixture()
        template = r.classification_template(report); template["candidate_sha256"] = report["candidate_sha256"]; template["range_report_sha256"] = "x"
        with self.assertRaisesRegex(ValueError, "source identity"):
            r.validate_classification(template, report, "d" * 64)

    def test_legitimate_contact_requires_note(self):
        report, static, manifest, plan = self.fixture()
        template = r.classification_template(report)
        template["candidate_sha256"] = report["candidate_sha256"]; template["range_report_sha256"] = "d" * 64
        row = next(x for x in template["rows"] if x["sample_key"] == "demo:2")
        row["body_garment"]["classification"] = "LEGITIMATE_CONTACT"
        with self.assertRaisesRegex(ValueError, "evidence note"):
            r.validate_classification(template, report, "d" * 64)

    def test_explicit_classification_summarises_without_pass(self):
        report, static, manifest, plan = self.fixture()
        template = r.classification_template(report)
        template["candidate_sha256"] = report["candidate_sha256"]; template["range_report_sha256"] = "d" * 64
        for row in template["rows"]:
            for domain in ("body_garment", "body_floor", "garment_floor"):
                item = row[domain]
                if item["classification"] == "UNCLASSIFIED":
                    item["classification"] = "UNEXPLAINED_DEFECT"
                    item["evidence_note"] = "test fixture classification"
        result = r.validate_classification(template, report, "d" * 64)
        self.assertTrue(result["classification_complete"])
        self.assertGreater(result["unexplained_defects"], 0)
        self.assertFalse(result["production_pass_inferred"])


if __name__ == "__main__":
    unittest.main()
