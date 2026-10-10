#!/usr/bin/env python3
import copy
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE / "anatomy_fit"))

import nlm_ct_anatomical_review as review
import nlm_ct_candidate_segmentation as segmentation
import nlm_ct_landmark_validation as landmarks
import nlm_ct_pixel_ras_envelope as pixel_ras


MANIFEST_PATH = (ROOT / "ORIGINAL_V1_WORK" / "anatomy" / "audit"
                 / "nlm_contiguous_ct_windows_pinned_20261009.json")
SOURCE_IDS = (1749, 1752, 1755)
POSITIONS = (-357, -360, -363)


def manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def scanners():
    return {
        source_id: {
            "source_id": source_id,
            "image_dimensions": [512, 512],
            "pixel_spacing_mm": [0.898438, 0.898438],
            "slice_thickness_mm": 3,
            "plane_TL_RAS_mm": [-230, -230, s_mm],
            "plane_TR_RAS_mm": [230, -230, s_mm],
            "plane_BR_RAS_mm": [230, 230, s_mm],
        }
        for source_id, s_mm in zip(SOURCE_IDS, POSITIONS)
    }


def reviewed(label="iliac_blade"):
    rows = {r["source_id"]: r for r in manifest()["exact_png_and_scanner_header_sha256"]}
    observations = []
    for source_id in SOURCE_IDS:
        source = rows[source_id]
        observations.append({
            "observation_id": f"obs-{source_id}-{label}",
            "source_id": source_id,
            "source_png_sha256": source["png_sha256"],
            "source_header_sha256": source["scanner_header_sha256"],
            "scanner_S_mm": source["scanner_S_mm"],
            "pixel": {"row": 10, "column": 10},
            "candidate_label": label,
            "confidence": 0.7,
            "reviewer_id": "reviewer-01",
        })
    return review.validate_review_packet({
        "schema_version": 1,
        "kind": "NLM_CT_ANATOMICAL_REVIEW_PACKET",
        "source_manifest_kind": "PINNED_NLM_SIX_ADJACENT_ORIGINAL_CT_FRAMES",
        "source_skeleton_governs_geometry": True,
        "canonical_promotion_allowed": False,
        "reviewer": {"id": "reviewer-01", "conflict_of_interest": False},
        "citations": [{"title": "Independent anatomy", "url": "https://example.org/anatomy"}],
        "observations": observations,
    }, manifest())


def segmented(label="iliac_blade", review_result=None):
    review_result = review_result or reviewed(label)
    value = {
        "schema_version": 1,
        "kind": "NLM_CT_CANDIDATE_SPARSE_MASK_VOLUME",
        "candidate_label": label,
        "mask_origin": "manual_source_review",
        "intensity_derived": False,
        "source_HU_used": False,
        "coverage_complete": False,
        "bone_surface_segmentation_verified": False,
        "canonical_promotion_allowed": False,
        "slices": [{
            "source_id": source_id,
            "review_observation_id": f"obs-{source_id}-{label}",
            "runs": [[10, 10, 10]],
        } for source_id in SOURCE_IDS],
    }
    return segmentation.validate_candidate_segmentation(value, review_result, scanners())


def landmark_packet(semantic="ASIS", side="left", label="iliac_blade"):
    return {
        "schema_version": 1,
        "kind": "NLM_CT_CANDIDATE_LANDMARK_PACKET",
        "source_skeleton_governs_geometry": True,
        "canonical_promotion_allowed": False,
        "exact_point_claimed": False,
        "submillimetre_accuracy_claimed": False,
        "HomeGymPT_world_transform_applied": False,
        "landmarks": [{
            "landmark_id": "candidate-landmark-01",
            "semantic": semantic,
            "side": side,
            "candidate_label": label,
            "source_id": 1749,
            "row": 10,
            "column": 10,
            "review_observation_id": f"obs-1749-{label}",
            "reviewer_id": "reviewer-01",
        }],
    }


class CandidateLandmarks(unittest.TestCase):
    def test_empty_packet_preserves_absence_instead_of_inventing_landmark(self):
        value = landmark_packet()
        value["landmarks"] = []
        result = landmarks.validate_landmarks(
            value, reviewed(), segmented(), scanners()
        )
        self.assertEqual(result["landmarks"], [])
        self.assertFalse(result["all_landmarks_verified"])
        self.assertFalse(result["canonical_promotion_allowed"])
        self.assertIn("INDEPENDENT_SECOND_LANDMARK_REVIEW_REQUIRED",
                      result["unmet_gates"])

    def test_mask_supported_point_retains_source_and_uncertainty(self):
        review_result = reviewed()
        scanner_records = scanners()
        result = landmarks.validate_landmarks(
            landmark_packet(), review_result, segmented(review_result=review_result),
            scanner_records,
        )
        point = result["landmarks"][0]
        envelope = pixel_ras.place_pixel(scanner_records[1749], 10, 10)
        observation = review_result["observations"][0]
        self.assertEqual(point["validation_status"], "CANDIDATE_SOURCE_OBSERVATION")
        self.assertNotEqual(point["validation_status"], "VERIFIED")
        self.assertEqual(point["pixel_cell_four_corners_RAS_mm"],
                         envelope["candidate_cell_four_corners_RAS_mm_if_outer_FOV_corners"])
        self.assertEqual(point["source_slab_S_range_mm"], [-358.5, -355.5])
        self.assertEqual(point["source_png_sha256"], observation["source_png_sha256"])
        self.assertEqual(point["source_header_sha256"], observation["source_header_sha256"])
        self.assertEqual(point["citations"], review_result["citations"])
        self.assertEqual(point["reviewer_id"], "reviewer-01")
        self.assertFalse(result["canonical_promotion_allowed"])
        self.assertTrue(result["unmet_gates"])

    def test_supported_candidate_semantics(self):
        cases = (
            ("ASIS", "left", "iliac_blade"),
            ("pubic_region", "midline", "pubic_region"),
            ("S1_endplate", "midline", "sacrum"),
            ("acetabular", "left", "acetabulum_left"),
            ("acetabular", "right", "acetabulum_right"),
            ("femoral_head", "left", "femoral_head_left"),
            ("femoral_head", "right", "femoral_head_right"),
        )
        for semantic, side, label in cases:
            with self.subTest(semantic=semantic, side=side, label=label):
                review_result = reviewed(label)
                result = landmarks.validate_landmarks(
                    landmark_packet(semantic, side, label), review_result,
                    segmented(label, review_result), scanners(),
                )
                self.assertEqual(result["landmarks"][0]["validation_status"],
                                 "CANDIDATE_SOURCE_OBSERVATION")

    def test_wrong_side_or_structure_fails(self):
        review_result = reviewed()
        for side, label in (("midline", "iliac_blade"), ("left", "pubic_region")):
            with self.subTest(side=side, label=label):
                value = landmark_packet("ASIS", side, label)
                with self.assertRaisesRegex(ValueError, "semantic|side|structure"):
                    landmarks.validate_landmarks(
                        value, review_result, segmented(review_result=review_result), scanners()
                    )

    def test_absent_mask_voxel_fails(self):
        value = landmark_packet()
        value["landmarks"][0]["row"] = 11
        with self.assertRaisesRegex(ValueError, "mask voxel"):
            landmarks.validate_landmarks(value, reviewed(), segmented(), scanners())

    def test_unreviewed_source_slice_fails(self):
        value = landmark_packet()
        value["landmarks"][0]["source_id"] = 1800
        with self.assertRaisesRegex(ValueError, "review observation|segmentation"):
            landmarks.validate_landmarks(value, reviewed(), segmented(), scanners())

    def test_conflicting_reviewer_fails(self):
        value = landmark_packet()
        value["landmarks"][0]["reviewer_id"] = "reviewer-02"
        with self.assertRaisesRegex(ValueError, "reviewer"):
            landmarks.validate_landmarks(value, reviewed(), segmented(), scanners())

    def test_missing_citation_fails(self):
        review_result = reviewed()
        review_result["citations"] = []
        with self.assertRaisesRegex(ValueError, "citation"):
            landmarks.validate_landmarks(
                landmark_packet(), review_result, segmented(), scanners()
            )

    def test_submillimetre_or_exact_claim_fails(self):
        for field in ("submillimetre_accuracy_claimed", "exact_point_claimed"):
            value = landmark_packet()
            value[field] = True
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "exact|submillimetre"):
                landmarks.validate_landmarks(value, reviewed(), segmented(), scanners())

    def test_home_gym_world_coordinate_fails(self):
        value = landmark_packet()
        value["landmarks"][0]["HomeGymPT_world_coordinate_m"] = [0, 0, 0]
        with self.assertRaisesRegex(ValueError, "Home Gym PT world"):
            landmarks.validate_landmarks(value, reviewed(), segmented(), scanners())


if __name__ == "__main__":
    unittest.main()
