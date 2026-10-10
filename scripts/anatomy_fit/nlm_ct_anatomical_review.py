#!/usr/bin/env python3
"""Validate candidate anatomical observations against exact pinned NLM CT bytes.

This module records review evidence; it does not identify canonical anatomy,
segment bone, alter skeleton geometry, or permit canonical promotion.
"""
import copy
import json
from pathlib import Path

import pelvic_ct_series_manifest as series_manifest


LABELS = frozenset({
    "iliac_blade",
    "sacrum",
    "acetabulum_left",
    "acetabulum_right",
    "femoral_head_left",
    "femoral_head_right",
    "pubic_region",
    "other",
    "unverified",
})

UNMET_GATES = (
    "INDEPENDENT_SECOND_REVIEWER_REQUIRED",
    "FULL_ANATOMICAL_COVERAGE_NOT_ESTABLISHED",
    "SOURCE_CT_HU_CALIBRATION_NOT_VERIFIED",
    "SOURCE_SEGMENTED_BONE_SURFACES_NOT_VERIFIED",
    "PATIENT_SCANNER_TO_HGPT_WORLD_NOT_VERIFIED",
    "CANONICAL_GEOMETRY_PROMOTION_PROHIBITED",
)


def load_json_object(path: Path) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("expected a JSON object")
    return value


def _promotion_requested(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "canonical_promotion_allowed" and child is not False:
                return True
            if _promotion_requested(child):
                return True
    elif isinstance(value, list):
        return any(_promotion_requested(child) for child in value)
    return False


def _pinned_rows(manifest):
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ValueError("pinned manifest does not preserve non-anatomical source status")
    kind = manifest.get("kind")
    if kind == "PINNED_NLM_SIX_ADJACENT_ORIGINAL_CT_FRAMES":
        if (manifest.get("anatomical_features_identified") is not False or
                manifest.get("canonical_promotion_allowed") is not False):
            raise ValueError("pinned manifest does not preserve non-anatomical source status")
        rows = manifest.get("exact_png_and_scanner_header_sha256")
        if not isinstance(rows, list) or len(rows) != 6:
            raise ValueError("pinned manifest must contain six source identities")
        by_id = {row.get("source_id"): row for row in rows if isinstance(row, dict)}
        if len(by_id) != 6:
            raise ValueError("pinned manifest source IDs must be unique")
        return by_id
    if kind == "CANDIDATE_PELVIC_CT_SERIES_BUNDLE":
        evidence = series_manifest.validate_series_bundle(manifest)
        rows = [row for group in manifest["series"] for row in group["slices"]]
        by_id = {}
        for row in rows:
            by_id[row["source_id"]] = {
                "source_id": row["source_id"],
                "png_sha256": row["source_png_sha256"],
                "scanner_header_sha256": row["source_header_sha256"],
                "scanner_S_mm": row["scanner_centre_RAS_mm"][2],
            }
        if len(by_id) != evidence["slice_count"]:
            raise ValueError("pinned manifest source IDs must be unique")
        return by_id
    raise ValueError("pinned manifest does not preserve non-anatomical source status")


def _validate_citations(citations):
    if not isinstance(citations, list) or not citations:
        raise ValueError("at least one independent HTTPS anatomical citation is required")
    for citation in citations:
        if (not isinstance(citation, dict)
                or not isinstance(citation.get("title"), str)
                or not citation["title"].strip()
                or not isinstance(citation.get("url"), str)
                or not citation["url"].startswith("https://")):
            raise ValueError("each independent HTTPS anatomical citation needs title and URL")


def validate_review_packet(packet: dict, pinned_manifest: dict) -> dict:
    """Return normalized candidate evidence or fail closed on any mismatch."""
    if (not isinstance(packet, dict)
            or packet.get("schema_version") != 1
            or packet.get("kind") != "NLM_CT_ANATOMICAL_REVIEW_PACKET"):
        raise ValueError("unsupported anatomical review packet schema")
    if packet.get("canonical_promotion_allowed") is not False or _promotion_requested(packet):
        raise ValueError("canonical promotion must remain explicitly false")
    if packet.get("source_skeleton_governs_geometry") is not True:
        raise ValueError("source skeleton must govern geometry")
    if packet.get("source_manifest_kind") != pinned_manifest.get("kind"):
        raise ValueError("review packet source manifest kind mismatch")

    pinned = _pinned_rows(pinned_manifest)
    reviewer = packet.get("reviewer")
    if not isinstance(reviewer, dict):
        raise ValueError("reviewer identity is required")
    reviewer_id = reviewer.get("id")
    if not isinstance(reviewer_id, str) or not reviewer_id.strip():
        raise ValueError("reviewer identity is required")
    if reviewer.get("conflict_of_interest") is not False:
        raise ValueError("reviewer conflict must be explicitly false")

    _validate_citations(packet.get("citations"))
    observations = packet.get("observations")
    if not isinstance(observations, list) or not observations:
        raise ValueError("at least one candidate observation is required")

    seen = set()
    for observation in observations:
        if not isinstance(observation, dict):
            raise ValueError("each observation must be an object")
        observation_id = observation.get("observation_id")
        if (not isinstance(observation_id, str) or not observation_id.strip()
                or observation_id in seen):
            raise ValueError("each observation needs a unique observation_id")
        seen.add(observation_id)

        source_id = observation.get("source_id")
        if source_id not in pinned:
            raise ValueError("unknown source frame")
        expected = pinned[source_id]
        if (observation.get("source_png_sha256") != expected.get("png_sha256")
                or observation.get("source_header_sha256")
                != expected.get("scanner_header_sha256")):
            raise ValueError("source-byte identity mismatch")
        if observation.get("scanner_S_mm") != expected.get("scanner_S_mm"):
            raise ValueError("source scanner coordinate mismatch")

        pixel = observation.get("pixel")
        if not isinstance(pixel, dict):
            raise ValueError("pixel row/column must be integer indices in the 512 grid")
        row, column = pixel.get("row"), pixel.get("column")
        if (not isinstance(row, int) or isinstance(row, bool) or not 0 <= row < 512
                or not isinstance(column, int) or isinstance(column, bool)
                or not 0 <= column < 512):
            raise ValueError("pixel row/column must be integer indices in the 512 grid")

        if observation.get("candidate_label") not in LABELS:
            raise ValueError("unsupported candidate label")
        confidence = observation.get("confidence")
        if (not isinstance(confidence, (int, float)) or isinstance(confidence, bool)
                or not 0 <= confidence <= 1):
            raise ValueError("confidence must be numeric and in [0, 1]")
        if observation.get("reviewer_id") != reviewer_id:
            raise ValueError("observation reviewer identity must match packet reviewer")

    result = copy.deepcopy(packet)
    result["anatomical_status"] = "CANDIDATE"
    result["source_skeleton_governs_geometry"] = True
    result["canonical_promotion_allowed"] = False
    result["unmet_gates"] = list(UNMET_GATES)
    return result
