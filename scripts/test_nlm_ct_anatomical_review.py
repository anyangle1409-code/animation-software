#!/usr/bin/env python3
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE / "anatomy_fit"))

import nlm_ct_anatomical_review as review


MANIFEST_PATH = (
    ROOT / "ORIGINAL_V1_WORK" / "anatomy" / "audit"
    / "nlm_contiguous_ct_windows_pinned_20261009.json"
)


def manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def packet():
    source = manifest()["exact_png_and_scanner_header_sha256"][0]
    return {
        "schema_version": 1,
        "kind": "NLM_CT_ANATOMICAL_REVIEW_PACKET",
        "source_manifest_kind": "PINNED_NLM_SIX_ADJACENT_ORIGINAL_CT_FRAMES",
        "source_skeleton_governs_geometry": True,
        "canonical_promotion_allowed": False,
        "reviewer": {
            "id": "independent-reviewer-01",
            "conflict_of_interest": False,
        },
        "citations": [{
            "title": "Independent pelvic CT anatomy reference",
            "url": "https://pubmed.ncbi.nlm.nih.gov/21210309/",
        }],
        "observations": [{
            "observation_id": "obs-1749-left-ilium-01",
            "source_id": source["source_id"],
            "source_png_sha256": source["png_sha256"],
            "source_header_sha256": source["scanner_header_sha256"],
            "scanner_S_mm": source["scanner_S_mm"],
            "pixel": {"row": 220, "column": 103},
            "candidate_label": "iliac_blade",
            "confidence": 0.72,
            "reviewer_id": "independent-reviewer-01",
        }],
    }


class ReviewPacketValidation(unittest.TestCase):
    def test_valid_packet_binds_candidate_label_to_exact_source_bytes(self):
        result = review.validate_review_packet(packet(), manifest())
        self.assertEqual(result["anatomical_status"], "CANDIDATE")
        self.assertTrue(result["source_skeleton_governs_geometry"])
        self.assertFalse(result["canonical_promotion_allowed"])
        self.assertEqual(result["observations"][0]["source_id"], 1749)
        self.assertEqual(
            result["observations"][0]["source_png_sha256"],
            manifest()["exact_png_and_scanner_header_sha256"][0]["png_sha256"],
        )
        self.assertEqual(
            result["observations"][0]["source_header_sha256"],
            manifest()["exact_png_and_scanner_header_sha256"][0]["scanner_header_sha256"],
        )
        self.assertTrue(result["unmet_gates"])

    def test_altered_png_or_header_hash_fails(self):
        for field in ("source_png_sha256", "source_header_sha256"):
            with self.subTest(field=field):
                value = packet()
                value["observations"][0][field] = "0" * 64
                with self.assertRaisesRegex(ValueError, "source-byte identity"):
                    review.validate_review_packet(value, manifest())

    def test_unknown_frame_fails(self):
        value = packet()
        value["observations"][0]["source_id"] = 9999
        with self.assertRaisesRegex(ValueError, "unknown source frame"):
            review.validate_review_packet(value, manifest())

    def test_duplicate_observation_id_fails(self):
        value = packet()
        value["observations"].append(copy.deepcopy(value["observations"][0]))
        with self.assertRaisesRegex(ValueError, "unique observation_id"):
            review.validate_review_packet(value, manifest())

    def test_malformed_row_or_column_fails(self):
        for field, bad in (("row", 512), ("column", -1), ("row", 2.5), ("column", True)):
            with self.subTest(field=field, bad=bad):
                value = packet()
                value["observations"][0]["pixel"][field] = bad
                with self.assertRaisesRegex(ValueError, "pixel row/column"):
                    review.validate_review_packet(value, manifest())

    def test_empty_or_non_https_citation_url_fails(self):
        for bad in ("", "http://example.org/reference"):
            with self.subTest(url=bad):
                value = packet()
                value["citations"][0]["url"] = bad
                with self.assertRaisesRegex(ValueError, "HTTPS anatomical citation"):
                    review.validate_review_packet(value, manifest())

    def test_unsupported_label_fails(self):
        value = packet()
        value["observations"][0]["candidate_label"] = "canonical_left_hip"
        with self.assertRaisesRegex(ValueError, "candidate label"):
            review.validate_review_packet(value, manifest())

    def test_reviewer_conflict_fails(self):
        value = packet()
        value["reviewer"]["conflict_of_interest"] = True
        with self.assertRaisesRegex(ValueError, "reviewer conflict"):
            review.validate_review_packet(value, manifest())

    def test_any_input_promotion_flag_fails(self):
        for mode in ("true", "missing"):
            with self.subTest(mode=mode):
                value = packet()
                if mode == "true":
                    value["canonical_promotion_allowed"] = True
                else:
                    del value["canonical_promotion_allowed"]
                with self.assertRaisesRegex(ValueError, "canonical promotion"):
                    review.validate_review_packet(value, manifest())

    def test_reviewer_identity_and_confidence_are_strict(self):
        value = packet()
        value["observations"][0]["reviewer_id"] = "someone-else"
        with self.assertRaisesRegex(ValueError, "reviewer identity"):
            review.validate_review_packet(value, manifest())
        for bad in (-0.01, 1.01, "0.7"):
            with self.subTest(confidence=bad):
                value = packet()
                value["observations"][0]["confidence"] = bad
                with self.assertRaisesRegex(ValueError, "confidence"):
                    review.validate_review_packet(value, manifest())

    def test_load_json_object_rejects_non_object(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "value.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "JSON object"):
                review.load_json_object(path)


if __name__ == "__main__":
    unittest.main()
