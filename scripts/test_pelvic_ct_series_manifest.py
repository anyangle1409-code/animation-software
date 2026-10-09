"""Fail-closed tests for a source-bound contiguous pelvic CT series manifest."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE / "anatomy_fit"))

import pelvic_ct_series_manifest as series


def manifest():
    rows = []
    for index, scanner_s in enumerate((6.0, 3.0, 0.0, -3.0, -6.0), start=1):
        rows.append({
            "source_id": f"slice-{index:04d}",
            "source_png_sha256": f"{index:x}" * 64,
            "source_header_sha256": f"{index + 5:x}" * 64,
            "source_png_bytes": 200000 + index,
            "scanner_centre_RAS_mm": [-2.0, 61.0, scanner_s],
            "scanner_grid": [512, 512],
            "pixel_spacing_mm": [0.898438, 0.898438],
            "slice_thickness_mm": 3.0,
            "slice_normal_RAS": [0.0, 0.0, 1.0],
        })
    return {
        "schema_version": 1,
        "kind": "CANDIDATE_PELVIC_CT_CONTIGUOUS_SERIES_MANIFEST",
        "series_uid_sha256": "a" * 64,
        "coordinate_frame": "SCANNER_RAS_MM",
        "slice_order": "SUPERIOR_TO_INFERIOR",
        "expected_step_S_mm": -3.0,
        "required_scanner_S_centre_range_mm": [6.0, -6.0],
        "source_bytes_committed": False,
        "patient_identifiers_exported": False,
        "anatomical_coverage_verified": False,
        "canonical_promotion_allowed": False,
        "source_skeleton_governs_geometry": True,
        "slices": rows,
    }


def bundle():
    superior = manifest()
    superior["series_uid_sha256"] = "a" * 64
    superior["slices"] = superior["slices"][:3]
    superior["required_scanner_S_centre_range_mm"] = [6.0, 0.0]
    inferior = manifest()
    inferior["series_uid_sha256"] = "b" * 64
    inferior["required_scanner_S_centre_range_mm"] = [-1.0, -7.0]
    inferior["slices"] = inferior["slices"][:3]
    for index, (row, scanner_s) in enumerate(
            zip(inferior["slices"], (-1.0, -4.0, -7.0)), start=1):
        row["source_id"] = f"inferior-{index:04d}"
        row["scanner_centre_RAS_mm"][2] = scanner_s
    return {
        "schema_version": 1,
        "kind": "CANDIDATE_PELVIC_CT_SERIES_BUNDLE",
        "coordinate_frame": "SCANNER_RAS_MM",
        "source_bytes_committed": False,
        "patient_identifiers_exported": False,
        "anatomical_coverage_verified": False,
        "canonical_promotion_allowed": False,
        "source_skeleton_governs_geometry": True,
        "series": [superior, inferior],
    }


class CandidateSeriesManifest(unittest.TestCase):
    def test_valid_manifest_verifies_geometry_not_anatomy(self):
        result = series.validate_series_manifest(manifest())
        self.assertEqual(result["status"], "CONTIGUOUS_SOURCE_SERIES_VERIFIED_NOT_ANATOMICAL")
        self.assertEqual(result["slice_count"], 5)
        self.assertTrue(result["scanner_geometry_contiguous"])
        self.assertTrue(result["declared_scanner_range_covered"])
        self.assertFalse(result["anatomical_coverage_verified"])
        self.assertFalse(result["canonical_promotion_allowed"])
        self.assertTrue(result["source_skeleton_governs_geometry"])

    def test_missing_or_malformed_hash_fails(self):
        value = manifest()
        del value["slices"][2]["source_header_sha256"]
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            series.validate_series_manifest(value)

    def test_source_id_must_be_privacy_safe(self):
        value = manifest()
        value["slices"][0]["source_id"] = "Patient Name: NEVER-EXPORT"
        with self.assertRaisesRegex(ValueError, "privacy-safe source_id"):
            series.validate_series_manifest(value)

    def test_duplicate_source_id_or_scanner_position_fails(self):
        value = manifest()
        value["slices"][2]["source_id"] = value["slices"][1]["source_id"]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            series.validate_series_manifest(value)
        value = manifest()
        value["slices"][2]["scanner_centre_RAS_mm"][2] = 3.0
        with self.assertRaisesRegex(ValueError, "duplicate"):
            series.validate_series_manifest(value)

    def test_reversed_or_discontinuous_slices_fail(self):
        value = manifest()
        value["slices"].reverse()
        with self.assertRaisesRegex(ValueError, "order"):
            series.validate_series_manifest(value)
        value = manifest()
        value["slices"][3]["scanner_centre_RAS_mm"][2] = -4.0
        with self.assertRaisesRegex(ValueError, "contiguous"):
            series.validate_series_manifest(value)

    def test_mixed_grid_spacing_thickness_or_normal_fails(self):
        fields_and_values = (
            ("scanner_grid", [256, 256]),
            ("pixel_spacing_mm", [1.0, 1.0]),
            ("slice_thickness_mm", 2.0),
            ("slice_normal_RAS", [0.0, 1.0, 0.0]),
        )
        for field, changed in fields_and_values:
            with self.subTest(field=field):
                value = manifest()
                value["slices"][3][field] = changed
                with self.assertRaisesRegex(ValueError, "mixed scanner geometry"):
                    series.validate_series_manifest(value)

    def test_ambiguous_coordinate_frame_fails(self):
        value = manifest()
        value["coordinate_frame"] = "SCANNER_MM"
        with self.assertRaisesRegex(ValueError, "SCANNER_RAS_MM"):
            series.validate_series_manifest(value)

    def test_partial_declared_scanner_range_fails(self):
        value = manifest()
        value["slices"].pop()
        with self.assertRaisesRegex(ValueError, "declared scanner range"):
            series.validate_series_manifest(value)

    def test_private_source_and_nonpromotion_flags_fail_closed(self):
        for field in ("source_bytes_committed", "patient_identifiers_exported",
                      "anatomical_coverage_verified", "canonical_promotion_allowed"):
            with self.subTest(field=field):
                value = manifest()
                value[field] = True
                with self.assertRaisesRegex(ValueError, "unsupported claim or source handling"):
                    series.validate_series_manifest(value)
        value = manifest()
        value["source_skeleton_governs_geometry"] = False
        with self.assertRaisesRegex(ValueError, "source skeleton"):
            series.validate_series_manifest(value)

    def test_source_rows_are_not_mutated(self):
        value = manifest()
        before = copy.deepcopy(value)
        series.validate_series_manifest(value)
        self.assertEqual(value, before)

    def test_cli_writes_only_sanitized_evidence_and_never_overwrites(self):
        value = manifest()
        value["untrusted_note"] = "NEVER-EXPORT-PATIENT-DATA"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "private-manifest.json"
            output = root / "safe-report.json"
            source.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(series.main([str(source), "--out", str(output)]), 0)
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result["slice_count"], 5)
            self.assertNotIn("NEVER-EXPORT", json.dumps(result))
            with self.assertRaises(FileExistsError):
                series.main([str(source), "--out", str(output)])


class CandidateSeriesBundle(unittest.TestCase):
    def test_committed_real_source_bundle_is_two_groups_noncanonical(self):
        path = (ROOT / "ORIGINAL_V1_WORK" / "anatomy" / "audit"
                / "nlm_pelvic_ct_full_series_candidate_bundle_20261009.json")
        value = json.loads(path.read_text(encoding="utf-8"))
        result = series.validate_series_bundle(value)
        self.assertEqual(result["series_count"], 2)
        self.assertEqual(result["slice_count"], 72)
        self.assertEqual(result["scanner_S_centre_range_mm"], [-342.0, -553.0])
        self.assertEqual(result["boundary_evidence"][0]["overlap_mm"], 2.0)
        self.assertFalse(result["single_uniform_stack_claimed"])
        self.assertFalse(result["anatomical_coverage_verified"])
        self.assertFalse(result["canonical_promotion_allowed"])
        pinned = json.loads((ROOT / "ORIGINAL_V1_WORK" / "anatomy" / "audit"
                             / "nlm_contiguous_ct_windows_pinned_20261009.json")
                            .read_text(encoding="utf-8"))
        rows = {row["source_id"]: row for group in value["series"]
                for row in group["slices"]}
        for anchor in pinned["exact_png_and_scanner_header_sha256"]:
            row = rows[f"cvm{anchor['source_id']}f"]
            self.assertEqual(row["source_png_sha256"], anchor["png_sha256"])
            self.assertEqual(row["source_header_sha256"], anchor["scanner_header_sha256"])
            self.assertEqual(row["source_png_bytes"], anchor["png_bytes"])
            self.assertEqual(row["scanner_centre_RAS_mm"][2], anchor["scanner_S_mm"])
        encoded = json.dumps(value)
        self.assertNotRegex(encoded, r"[A-Za-z]:\\")
        self.assertNotIn("Patient", encoded)
        self.assertNotIn("raw_header", encoded)

    def test_two_groups_preserve_boundary_overlap_without_flattening(self):
        result = series.validate_series_bundle(bundle())
        self.assertEqual(result["status"], "CONTIGUOUS_MULTI_GROUP_SOURCE_VOLUME_NOT_ANATOMICAL")
        self.assertEqual(result["series_count"], 2)
        self.assertEqual(result["slice_count"], 6)
        self.assertEqual(result["boundary_evidence"][0]["overlap_mm"], 2.0)
        self.assertFalse(result["single_uniform_stack_claimed"])
        self.assertFalse(result["anatomical_coverage_verified"])
        self.assertFalse(result["canonical_promotion_allowed"])

    def test_inter_group_physical_gap_fails(self):
        value = bundle()
        inferior = value["series"][1]
        for row, scanner_s in zip(inferior["slices"], (-5.0, -8.0, -11.0)):
            row["scanner_centre_RAS_mm"][2] = scanner_s
        inferior["required_scanner_S_centre_range_mm"] = [-5.0, -11.0]
        with self.assertRaisesRegex(ValueError, "physical gap"):
            series.validate_series_bundle(value)

    def test_duplicate_sources_or_reversed_group_order_fail(self):
        value = bundle()
        value["series"][1]["slices"][0]["source_id"] = "slice-0001"
        with self.assertRaisesRegex(ValueError, "duplicate source"):
            series.validate_series_bundle(value)
        value = bundle()
        value["series"].reverse()
        with self.assertRaisesRegex(ValueError, "series group order"):
            series.validate_series_bundle(value)

    def test_bundle_claims_fail_closed(self):
        for field in ("source_bytes_committed", "patient_identifiers_exported",
                      "anatomical_coverage_verified", "canonical_promotion_allowed"):
            with self.subTest(field=field):
                value = bundle()
                value[field] = True
                with self.assertRaisesRegex(ValueError, "unsupported bundle claim"):
                    series.validate_series_bundle(value)

    def test_committed_blender_occupancy_review_stays_non_anatomical(self):
        audit = ROOT / "ORIGINAL_V1_WORK" / "anatomy" / "audit"
        path = audit / "nlm_pelvic_ct_full_series_blender_review_20261009.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        source_bundle = json.loads((
            audit / "nlm_pelvic_ct_full_series_candidate_bundle_20261009.json"
        ).read_text(encoding="utf-8"))
        result = series.validate_occupancy_review(value, source_bundle)
        self.assertEqual(result["status"], "STORED_SCALAR_OCCUPANCY_VERIFIED_NOT_SEGMENTATION")
        self.assertEqual(result["slice_count"], 72)
        self.assertEqual(result["candidate_block_count"], 13273)
        self.assertEqual(
            value["kind"],
            "PELVIC_CT_STORED_SCALAR_OCCUPANCY_REVIEW_NOT_SEGMENTATION",
        )
        self.assertEqual(value["source_bundle"]["series_count"], 2)
        self.assertEqual(value["source_bundle"]["slice_count"], 72)
        self.assertEqual(value["source_bundle"]["boundary_overlap_mm"], 2.0)
        self.assertFalse(value["source_bundle"]["single_uniform_stack_claimed"])
        self.assertEqual(value["review_observation_count"], 10)
        self.assertEqual(value["stored_scalar_threshold"], 1200)
        self.assertEqual(value["candidate_block_count"], 13273)
        self.assertEqual(value["mesh_vertex_count"], 106184)
        self.assertEqual(value["mesh_quad_count"], 79638)
        self.assertFalse(value["values_are_calibrated_HU"])
        self.assertFalse(value["anatomical_bone_segmentation_verified"])
        self.assertFalse(value["patient_scanner_to_HGPT_world_verified"])
        self.assertTrue(value["source_skeleton_governs_geometry"])
        self.assertFalse(value["skeleton_geometry_modified"])
        self.assertFalse(value["canonical_promotion_allowed"])
        self.assertFalse(value["source_images_packed"])
        self.assertTrue(value["private_outputs_must_remain_untracked"])
        self.assertRegex(value["blend_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(value["render_sha256"], r"^[0-9a-f]{64}$")
        encoded = json.dumps(value)
        self.assertNotRegex(encoded, r"[A-Za-z]:\\")
        self.assertNotIn("source_validations", encoded)

    def test_occupancy_review_rejects_promoted_claims_and_bad_totals(self):
        audit = ROOT / "ORIGINAL_V1_WORK" / "anatomy" / "audit"
        review = json.loads((
            audit / "nlm_pelvic_ct_full_series_blender_review_20261009.json"
        ).read_text(encoding="utf-8"))
        source_bundle = json.loads((
            audit / "nlm_pelvic_ct_full_series_candidate_bundle_20261009.json"
        ).read_text(encoding="utf-8"))
        for field in ("values_are_calibrated_HU",
                      "anatomical_bone_segmentation_verified",
                      "patient_scanner_to_HGPT_world_verified",
                      "skeleton_geometry_modified",
                      "canonical_promotion_allowed", "source_images_packed"):
            with self.subTest(field=field):
                changed = copy.deepcopy(review)
                changed[field] = True
                with self.assertRaisesRegex(ValueError, "unsupported occupancy claim"):
                    series.validate_occupancy_review(changed, source_bundle)
        changed = copy.deepcopy(review)
        changed["source_skeleton_governs_geometry"] = False
        with self.assertRaisesRegex(ValueError, "source skeleton"):
            series.validate_occupancy_review(changed, source_bundle)
        for field in ("candidate_block_count", "mesh_vertex_count", "mesh_quad_count"):
            with self.subTest(field=field):
                changed = copy.deepcopy(review)
                changed[field] += 1
                with self.assertRaisesRegex(ValueError, "group totals"):
                    series.validate_occupancy_review(changed, source_bundle)

    def test_occupancy_review_must_match_validated_source_bundle(self):
        audit = ROOT / "ORIGINAL_V1_WORK" / "anatomy" / "audit"
        review = json.loads((
            audit / "nlm_pelvic_ct_full_series_blender_review_20261009.json"
        ).read_text(encoding="utf-8"))
        source_bundle = json.loads((
            audit / "nlm_pelvic_ct_full_series_candidate_bundle_20261009.json"
        ).read_text(encoding="utf-8"))
        for field, changed_value in (("series_count", 3), ("slice_count", 71),
                                     ("boundary_overlap_mm", 0.0)):
            with self.subTest(field=field):
                changed = copy.deepcopy(review)
                changed["source_bundle"][field] = changed_value
                with self.assertRaisesRegex(ValueError, "source bundle evidence"):
                    series.validate_occupancy_review(changed, source_bundle)


if __name__ == "__main__":
    unittest.main()
