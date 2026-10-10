#!/usr/bin/env python3
"""Verify NLM GE raw samples against PNG samples without exposing source data."""
import hashlib
import json
import re
import struct

from ct_pelvis_window_geometry import decode_png_gray16
from pelvic_ct_series_manifest import validate_series_bundle


GRID = 512
GE_HEADER_BYTES = 3416
SAMPLE_COUNT = GRID * GRID
EXPECTED_ORDERED_IDENTITY = "76d08c3821b4d848682e5f103af996d73201f778461cfe4cc5c91c970ba0d208"
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def compare_ge_raw_to_png(raw_blob, png_blob):
    """Compare one decompressed GE payload with one decoded 16-bit PNG."""
    expected_bytes = GE_HEADER_BYTES + SAMPLE_COUNT * 2
    if not isinstance(raw_blob, bytes) or len(raw_blob) != expected_bytes:
        raise ValueError("unexpected decompressed GE file size")
    width, height, png_values = decode_png_gray16(png_blob)
    raw_values = struct.unpack(">262144H", raw_blob[GE_HEADER_BYTES:])
    different = 0
    maximum = 0
    for raw_value, png_value in zip(raw_values, png_values):
        difference = abs(raw_value - png_value)
        if difference:
            different += 1
            maximum = max(maximum, difference)
    return {
        "width_pixels": width,
        "height_pixels": height,
        "sample_count": SAMPLE_COUNT,
        "all_samples_identical_in_file_order": different == 0,
        "different_sample_count": different,
        "maximum_absolute_sample_difference": maximum,
        "raw_file_sha256": hashlib.sha256(raw_blob).hexdigest(),
        "png_file_sha256": hashlib.sha256(png_blob).hexdigest(),
    }


def validate_calibration_evidence(evidence, source_bundle):
    """Bind an aggregate raw/PNG comparison to the validated 72-slice bundle."""
    if not isinstance(evidence, dict):
        raise ValueError("calibration evidence must be an object")
    if (evidence.get("schema_version") != 1 or evidence.get("kind") !=
            "NLM_PELVIC_CT_FULL_SERIES_GE_RAW_PNG_CALIBRATION"):
        raise ValueError("unsupported raw-to-PNG calibration schema")
    bundle = validate_series_bundle(source_bundle)
    expected_samples = bundle["slice_count"] * SAMPLE_COUNT
    if (evidence.get("slice_count") != bundle["slice_count"] or
            evidence.get("sample_count") != expected_samples or
            evidence.get("all_samples_identical_in_file_order") is not True or
            evidence.get("different_sample_count") != 0 or
            evidence.get("maximum_absolute_sample_difference") != 0):
        raise ValueError("raw-to-PNG comparison is incomplete or non-identical")
    if (evidence.get("ordered_source_identity_sha256") !=
            EXPECTED_ORDERED_IDENTITY):
        raise ValueError("raw-to-PNG ordered source identity is not pinned")
    if (evidence.get("scanner_header_count") != bundle["slice_count"] or
            evidence.get("stored_pixel_value_addend_for_HU") != -1024 or
            evidence.get("scanner_header_HU_addend_consistent") is not True or
            evidence.get("PNG_numeric_identity_to_scanner_pixels_verified") is not True or
            evidence.get("HU_conversion_from_png_verified") is not True or
            evidence.get("HU_formula") != "HU = PNG_stored_value - 1024" or
            evidence.get("stored_threshold_1200_in_HU") != 176):
        raise ValueError("PNG-to-HU calibration claim is incomplete")
    if (evidence.get("source_bytes_committed") is not False or
            evidence.get("patient_identifiers_exported") is not False or
            evidence.get("anatomical_bone_segmentation_verified") is not False or
            evidence.get("canonical_promotion_allowed") is not False):
        raise ValueError("calibration evidence contains an unsupported claim")
    sources = evidence.get("official_sources")
    if (not isinstance(sources, dict) or
            not sources.get("raw_GE_base", "").startswith(
                "https://data.lhncbc.nlm.nih.gov/public/Visible-Human/") or
            not sources.get("PNG_base", "").startswith(
                "https://data.lhncbc.nlm.nih.gov/public/Visible-Human/") or
            not sources.get("scanner_header_base", "").startswith(
                "https://data.lhncbc.nlm.nih.gov/public/Visible-Human/") or
            sources.get("NLM_data_documentation") !=
                "https://www.nlm.nih.gov/research/visible/getting_data.html"):
        raise ValueError("calibration evidence requires official NLM source URLs")
    encoded = json.dumps(evidence)
    if re.search(r"[A-Za-z]:\\\\", encoded) or "private_path" in encoded:
        raise ValueError("calibration evidence contains a private path")
    return {
        "status": "FULL_SERIES_PNG_TO_HU_CALIBRATION_VERIFIED",
        "slice_count": bundle["slice_count"],
        "sample_count": expected_samples,
        "stored_pixel_value_addend_for_HU": -1024,
        "stored_threshold_1200_in_HU": 176,
        "anatomical_bone_segmentation_verified": False,
        "canonical_promotion_allowed": False,
    }
