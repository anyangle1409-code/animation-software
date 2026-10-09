"""Fail-closed tests for a source-bound contiguous pelvic CT series manifest."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
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


if __name__ == "__main__":
    unittest.main()
