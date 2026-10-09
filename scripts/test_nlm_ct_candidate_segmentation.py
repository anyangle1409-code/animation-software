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
import nlm_ct_pixel_ras_envelope as pixel_ras


MANIFEST_PATH = (
    ROOT / "ORIGINAL_V1_WORK" / "anatomy" / "audit"
    / "nlm_contiguous_ct_windows_pinned_20261009.json"
)


def manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def review_result(source_ids=(1749, 1752, 1755)):
    rows = {r["source_id"]: r for r in manifest()["exact_png_and_scanner_header_sha256"]}
    observations = []
    for source_id in source_ids:
        source = rows[source_id]
        observations.append({
            "observation_id": f"obs-{source_id}-left-ilium",
            "source_id": source_id,
            "source_png_sha256": source["png_sha256"],
            "source_header_sha256": source["scanner_header_sha256"],
            "scanner_S_mm": source["scanner_S_mm"],
            "pixel": {"row": 10, "column": 10},
            "candidate_label": "iliac_blade",
            "confidence": 0.7,
            "reviewer_id": "reviewer-01",
        })
    packet = {
        "schema_version": 1,
        "kind": "NLM_CT_ANATOMICAL_REVIEW_PACKET",
        "source_manifest_kind": "PINNED_NLM_SIX_ADJACENT_ORIGINAL_CT_FRAMES",
        "source_skeleton_governs_geometry": True,
        "canonical_promotion_allowed": False,
        "reviewer": {"id": "reviewer-01", "conflict_of_interest": False},
        "citations": [{"title": "Independent anatomy", "url": "https://example.org/anatomy"}],
        "observations": observations,
    }
    return review.validate_review_packet(packet, manifest())


def scanner(source_id, s_mm):
    return {
        "source_id": source_id,
        "image_dimensions": [512, 512],
        "pixel_spacing_mm": [0.898438, 0.898438],
        "slice_thickness_mm": 3,
        "plane_TL_RAS_mm": [-230, -230, s_mm],
        "plane_TR_RAS_mm": [230, -230, s_mm],
        "plane_BR_RAS_mm": [230, 230, s_mm],
    }


def scanners(source_ids=(1749, 1752, 1755), positions=(-357, -360, -363)):
    return {source_id: scanner(source_id, s_mm)
            for source_id, s_mm in zip(source_ids, positions)}


def packet(source_ids=(1749, 1752, 1755)):
    runs = (
        [[10, 10, 11]],
        [[10, 10, 11]],
        [[10, 11, 11]],
    )
    return {
        "schema_version": 1,
        "kind": "NLM_CT_CANDIDATE_SPARSE_MASK_VOLUME",
        "candidate_label": "iliac_blade",
        "mask_origin": "manual_source_review",
        "intensity_derived": False,
        "source_HU_used": False,
        "coverage_complete": False,
        "bone_surface_segmentation_verified": False,
        "canonical_promotion_allowed": False,
        "slices": [
            {
                "source_id": source_id,
                "review_observation_id": f"obs-{source_id}-left-ilium",
                "runs": run_rows,
            }
            for source_id, run_rows in zip(source_ids, runs)
        ],
    }


class CandidateSegmentation(unittest.TestCase):
    def test_bounded_sparse_mask_has_deterministic_geometry(self):
        source_scanners = scanners()
        result = segmentation.validate_candidate_segmentation(
            packet(), review_result(), source_scanners
        )
        self.assertEqual(result["voxel_count"], 5)
        self.assertEqual(result["connected_component_count_6_neighbour"], 1)
        self.assertEqual(result["source_ids"], [1749, 1752, 1755])
        centres = [
            pixel_ras.place_pixel(source_scanners[1749], 10, 10)[
                "candidate_pixel_centre_RAS_mm_if_outer_FOV_corners"
            ],
            pixel_ras.place_pixel(source_scanners[1755], 10, 11)[
                "candidate_pixel_centre_RAS_mm_if_outer_FOV_corners"
            ],
        ]
        for axis in range(3):
            self.assertAlmostEqual(
                result["sample_centre_bounds_RAS_mm"]["min"][axis],
                min(point[axis] for point in centres),
            )
            self.assertAlmostEqual(
                result["sample_centre_bounds_RAS_mm"]["max"][axis],
                max(point[axis] for point in centres),
            )
        self.assertFalse(result["coverage_complete"])
        self.assertFalse(result["bone_surface_segmentation_verified"])
        self.assertFalse(result["canonical_promotion_allowed"])
        self.assertIn("OUTSIDE_REVIEWED_THREE_SLICE_WINDOW", result["coverage_gaps"])

    def test_disconnected_voxel_is_counted(self):
        value = packet()
        value["slices"][2]["runs"].append([100, 100, 100])
        result = segmentation.validate_candidate_segmentation(value, review_result(), scanners())
        self.assertEqual(result["connected_component_count_6_neighbour"], 2)

    def test_cross_gap_volume_fails(self):
        source_ids = (1749, 1752, 1797)
        with self.assertRaisesRegex(ValueError, "one pinned contiguous triplet"):
            segmentation.validate_candidate_segmentation(
                packet(source_ids), review_result(source_ids),
                scanners(source_ids, (-357, -360, -405)),
            )

    def test_non_three_mm_steps_fail(self):
        with self.assertRaisesRegex(ValueError, "3 mm"):
            segmentation.validate_candidate_segmentation(
                packet(), review_result(), scanners(positions=(-357, -360, -364))
            )

    def test_scanner_centres_must_match_source_review(self):
        shifted = scanners(positions=(-347, -350, -353))
        with self.assertRaisesRegex(ValueError, "reviewed scanner coordinate"):
            segmentation.validate_candidate_segmentation(
                packet(), review_result(), shifted
            )

    def test_mixed_spacing_fails(self):
        source_scanners = scanners()
        source_scanners[1755]["pixel_spacing_mm"] = [1, 1]
        with self.assertRaisesRegex(ValueError, "mixed pixel spacing"):
            segmentation.validate_candidate_segmentation(
                packet(), review_result(), source_scanners
            )

    def test_duplicate_reversed_or_overlapping_runs_fail(self):
        mutations = (
            [[10, 10, 11], [10, 10, 11]],
            [[10, 12, 11]],
            [[10, 10, 12], [10, 12, 13]],
        )
        for runs in mutations:
            with self.subTest(runs=runs):
                value = packet()
                value["slices"][0]["runs"] = runs
                with self.assertRaisesRegex(ValueError, "runs"):
                    segmentation.validate_candidate_segmentation(
                        value, review_result(), scanners()
                    )

    def test_malformed_runs_fail_as_validation_errors(self):
        value = packet()
        value["slices"][0]["runs"] = 3
        with self.assertRaisesRegex(ValueError, "runs"):
            segmentation.validate_candidate_segmentation(value, review_result(), scanners())

    def test_excessive_run_count_fails_before_expansion(self):
        value = packet()
        value["slices"][0]["runs"] = [[row % 512, 0, 0]
                                            for row in range(segmentation.MAX_RUNS + 1)]
        with self.assertRaisesRegex(ValueError, "run cap"):
            segmentation.validate_candidate_segmentation(value, review_result(), scanners())

    def test_missing_review_observation_fails(self):
        value = packet()
        value["slices"][0]["review_observation_id"] = "not-reviewed"
        with self.assertRaisesRegex(ValueError, "review observation"):
            segmentation.validate_candidate_segmentation(value, review_result(), scanners())

    def test_out_of_grid_mask_fails(self):
        value = packet()
        value["slices"][0]["runs"] = [[512, 0, 0]]
        with self.assertRaisesRegex(ValueError, "512 grid"):
            segmentation.validate_candidate_segmentation(value, review_result(), scanners())

    def test_intensity_or_hu_claims_fail(self):
        for field in ("intensity_derived", "source_HU_used"):
            with self.subTest(field=field):
                value = packet()
                value[field] = True
                with self.assertRaisesRegex(ValueError, "intensity|HU"):
                    segmentation.validate_candidate_segmentation(
                        value, review_result(), scanners()
                    )

    def test_nonpromotion_flags_must_be_explicitly_false(self):
        for field in ("coverage_complete", "bone_surface_segmentation_verified",
                      "canonical_promotion_allowed"):
            for mode in ("true", "missing"):
                with self.subTest(field=field, mode=mode):
                    value = packet()
                    if mode == "true":
                        value[field] = True
                    else:
                        del value[field]
                    with self.assertRaises(ValueError):
                        segmentation.validate_candidate_segmentation(
                            value, review_result(), scanners()
                        )


if __name__ == "__main__":
    unittest.main()
