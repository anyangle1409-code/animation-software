#!/usr/bin/env python3
"""Tests for direct NLM GE raw-to-PNG numeric calibration evidence."""
import copy
import json
import struct
import sys
import unittest
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE / "anatomy_fit"))

import nlm_ct_raw_png_calibration as calibration


def chunk(kind, payload):
    return (struct.pack(">I", len(payload)) + kind + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff))


def png_with_values(values):
    rows = []
    for row in range(512):
        start = row * 512
        rows.append(b"\0" + struct.pack(">512H", *values[start:start + 512]))
    header = struct.pack(">IIBBBBB", 512, 512, 16, 0, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(b"".join(rows))) + chunk(b"IEND", b""))


def evidence():
    path = (ROOT / "ORIGINAL_V1_WORK" / "anatomy" / "audit"
            / "nlm_pelvic_ct_full_series_hu_calibration_20261009.json")
    return json.loads(path.read_text(encoding="utf-8"))


def source_bundle():
    path = (ROOT / "ORIGINAL_V1_WORK" / "anatomy" / "audit"
            / "nlm_pelvic_ct_full_series_candidate_bundle_20261009.json")
    return json.loads(path.read_text(encoding="utf-8"))


class RawPngCalibration(unittest.TestCase):
    def test_identical_raw_and_png_samples_are_verified(self):
        values = [1200] * (512 * 512)
        raw = b"\0" * 3416 + struct.pack(">262144H", *values)
        result = calibration.compare_ge_raw_to_png(raw, png_with_values(values))
        self.assertEqual(result["sample_count"], 262144)
        self.assertTrue(result["all_samples_identical_in_file_order"])
        self.assertEqual(result["different_sample_count"], 0)
        self.assertEqual(result["maximum_absolute_sample_difference"], 0)

    def test_numeric_difference_is_reported_not_hidden(self):
        raw_values = [1200] * (512 * 512)
        png_values = list(raw_values)
        png_values[12345] = 1199
        raw = b"\0" * 3416 + struct.pack(">262144H", *raw_values)
        result = calibration.compare_ge_raw_to_png(raw, png_with_values(png_values))
        self.assertFalse(result["all_samples_identical_in_file_order"])
        self.assertEqual(result["different_sample_count"], 1)
        self.assertEqual(result["maximum_absolute_sample_difference"], 1)

    def test_wrong_raw_size_fails(self):
        with self.assertRaisesRegex(ValueError, "GE file size"):
            calibration.compare_ge_raw_to_png(b"short", png_with_values([0] * (512 * 512)))

    def test_committed_full_series_calibration_is_source_bound(self):
        result = calibration.validate_calibration_evidence(evidence(), source_bundle())
        self.assertEqual(result["status"], "FULL_SERIES_PNG_TO_HU_CALIBRATION_VERIFIED")
        self.assertEqual(result["slice_count"], 72)
        self.assertEqual(result["sample_count"], 18874368)
        self.assertEqual(result["stored_pixel_value_addend_for_HU"], -1024)
        self.assertEqual(result["stored_threshold_1200_in_HU"], 176)
        self.assertFalse(result["anatomical_bone_segmentation_verified"])
        self.assertFalse(result["canonical_promotion_allowed"])

    def test_calibration_claims_fail_closed(self):
        base = evidence()
        mutations = (
            ("slice_count", 71),
            ("sample_count", 18874367),
            ("all_samples_identical_in_file_order", False),
            ("different_sample_count", 1),
            ("maximum_absolute_sample_difference", 1),
            ("stored_pixel_value_addend_for_HU", -1000),
            ("HU_conversion_from_png_verified", False),
            ("source_bytes_committed", True),
            ("patient_identifiers_exported", True),
            ("canonical_promotion_allowed", True),
        )
        for field, changed_value in mutations:
            with self.subTest(field=field):
                changed = copy.deepcopy(base)
                changed[field] = changed_value
                with self.assertRaises(ValueError):
                    calibration.validate_calibration_evidence(changed, source_bundle())

    def test_private_paths_and_unpinned_identity_fail(self):
        changed = evidence()
        changed["private_path"] = r"C:\private\ct"
        with self.assertRaisesRegex(ValueError, "private"):
            calibration.validate_calibration_evidence(changed, source_bundle())
        changed = evidence()
        changed["ordered_source_identity_sha256"] = "a" * 64
        with self.assertRaisesRegex(ValueError, "identity"):
            calibration.validate_calibration_evidence(changed, source_bundle())


if __name__ == "__main__":
    unittest.main()
