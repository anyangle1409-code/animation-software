#!/usr/bin/env python3
"""Validate a private, source-bound contiguous pelvic CT series manifest.

This validates source identity and scanner geometry only. It deliberately does
not infer anatomy, segmentation quality, landmarks, registration, or canonical
fitness from a geometrically continuous stack.
"""
import argparse
import json
import math
import re
from pathlib import Path


_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SAFE_SOURCE_ID = re.compile(r"[A-Za-z0-9._-]{1,128}\Z")
_TOLERANCE = 1e-6


def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be a finite number")
    return result


def _numeric_vector(value, length, label):
    if not isinstance(value, list) or len(value) != length:
        raise ValueError(f"{label} must have {length} values")
    return tuple(_number(item, label) for item in value)


def _same_vector(left, right):
    return len(left) == len(right) and all(
        abs(a - b) <= _TOLERANCE for a, b in zip(left, right)
    )


def _valid_hash(value):
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def validate_series_manifest(manifest):
    """Return sanitized continuity evidence or fail closed on any ambiguity."""
    if not isinstance(manifest, dict):
        raise ValueError("series manifest must be an object")
    if (manifest.get("schema_version") != 1 or
            manifest.get("kind") != "CANDIDATE_PELVIC_CT_CONTIGUOUS_SERIES_MANIFEST"):
        raise ValueError("unsupported pelvic CT series manifest schema")
    if manifest.get("coordinate_frame") != "SCANNER_RAS_MM":
        raise ValueError("coordinate frame must be explicit SCANNER_RAS_MM")
    if manifest.get("slice_order") != "SUPERIOR_TO_INFERIOR":
        raise ValueError("slice order must be explicit superior-to-inferior")
    if not _valid_hash(manifest.get("series_uid_sha256")):
        raise ValueError("series identity requires a lowercase SHA-256")
    if (manifest.get("source_bytes_committed") is not False or
            manifest.get("patient_identifiers_exported") is not False or
            manifest.get("anatomical_coverage_verified") is not False or
            manifest.get("canonical_promotion_allowed") is not False):
        raise ValueError("unsupported claim or source handling in candidate manifest")
    if manifest.get("source_skeleton_governs_geometry") is not True:
        raise ValueError("source skeleton must govern geometry")

    expected_step = _number(manifest.get("expected_step_S_mm"), "expected step")
    if expected_step >= 0:
        raise ValueError("superior-to-inferior slice order requires a negative step")
    required_range = _numeric_vector(
        manifest.get("required_scanner_S_centre_range_mm"), 2,
        "required scanner range",
    )
    if required_range[0] <= required_range[1]:
        raise ValueError("required scanner range must be superior-to-inferior")

    rows = manifest.get("slices")
    if not isinstance(rows, list) or len(rows) < 2:
        raise ValueError("at least two source slices are required")

    source_ids = set()
    scanner_positions = set()
    normalized = []
    baseline = None
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each source slice must be an object")
        source_id = row.get("source_id")
        if (not isinstance(source_id, str) or
                _SAFE_SOURCE_ID.fullmatch(source_id) is None):
            raise ValueError("each source slice requires a privacy-safe source_id")
        if source_id in source_ids:
            raise ValueError("duplicate source_id in series manifest")
        source_ids.add(source_id)
        if (not _valid_hash(row.get("source_png_sha256")) or
                not _valid_hash(row.get("source_header_sha256"))):
            raise ValueError("every source slice requires lowercase SHA-256 identities")
        byte_count = row.get("source_png_bytes")
        if isinstance(byte_count, bool) or not isinstance(byte_count, int) or byte_count <= 0:
            raise ValueError("source PNG byte count must be a positive integer")

        centre = _numeric_vector(row.get("scanner_centre_RAS_mm"), 3,
                                 "scanner centre RAS")
        scanner_s = centre[2]
        if scanner_s in scanner_positions:
            raise ValueError("duplicate scanner position in series manifest")
        scanner_positions.add(scanner_s)

        grid_value = row.get("scanner_grid")
        if (not isinstance(grid_value, list) or len(grid_value) != 2 or
                any(isinstance(item, bool) or not isinstance(item, int) or item <= 0
                    for item in grid_value)):
            raise ValueError("scanner grid must contain two positive integers")
        grid = tuple(grid_value)
        spacing = _numeric_vector(row.get("pixel_spacing_mm"), 2, "pixel spacing")
        thickness = _number(row.get("slice_thickness_mm"), "slice thickness")
        normal = _numeric_vector(row.get("slice_normal_RAS"), 3, "slice normal RAS")
        if any(value <= 0 for value in spacing) or thickness <= 0:
            raise ValueError("scanner spacing and thickness must be positive")
        if abs(math.sqrt(sum(value * value for value in normal)) - 1.0) > _TOLERANCE:
            raise ValueError("slice normal RAS must be a unit vector")

        geometry = (centre[:2], grid, spacing, thickness, normal)
        if baseline is None:
            baseline = geometry
        elif (not _same_vector(geometry[0], baseline[0]) or
              geometry[1] != baseline[1] or
              not _same_vector(geometry[2], baseline[2]) or
              abs(geometry[3] - baseline[3]) > _TOLERANCE or
              not _same_vector(geometry[4], baseline[4])):
            raise ValueError("mixed scanner geometry in source series")
        normalized.append((source_id, scanner_s))

    steps = [normalized[index + 1][1] - normalized[index][1]
             for index in range(len(normalized) - 1)]
    if any(step >= 0 for step in steps):
        raise ValueError("slice order is not superior-to-inferior")
    if any(abs(step - expected_step) > _TOLERANCE for step in steps):
        raise ValueError("source series is not physically contiguous")

    actual_superior = normalized[0][1]
    actual_inferior = normalized[-1][1]
    if (actual_superior + _TOLERANCE < required_range[0] or
            actual_inferior - _TOLERANCE > required_range[1]):
        raise ValueError("source slices do not cover declared scanner range")

    return {
        "status": "CONTIGUOUS_SOURCE_SERIES_VERIFIED_NOT_ANATOMICAL",
        "slice_count": len(normalized),
        "source_ids": [source_id for source_id, _ in normalized],
        "scanner_S_centre_range_mm": [actual_superior, actual_inferior],
        "measured_step_S_mm": expected_step,
        "slice_thickness_mm": baseline[3],
        "scanner_geometry_contiguous": True,
        "declared_scanner_range_covered": True,
        "anatomical_coverage_verified": False,
        "canonical_promotion_allowed": False,
        "source_skeleton_governs_geometry": True,
    }


def validate_series_bundle(bundle):
    """Validate multiple uniform groups without flattening their boundaries."""
    if not isinstance(bundle, dict):
        raise ValueError("series bundle must be an object")
    if (bundle.get("schema_version") != 1 or
            bundle.get("kind") != "CANDIDATE_PELVIC_CT_SERIES_BUNDLE"):
        raise ValueError("unsupported pelvic CT series bundle schema")
    if bundle.get("coordinate_frame") != "SCANNER_RAS_MM":
        raise ValueError("bundle coordinate frame must be explicit SCANNER_RAS_MM")
    if (bundle.get("source_bytes_committed") is not False or
            bundle.get("patient_identifiers_exported") is not False or
            bundle.get("anatomical_coverage_verified") is not False or
            bundle.get("canonical_promotion_allowed") is not False):
        raise ValueError("unsupported bundle claim or source handling")
    if bundle.get("source_skeleton_governs_geometry") is not True:
        raise ValueError("source skeleton must govern bundle geometry")
    groups = bundle.get("series")
    if not isinstance(groups, list) or len(groups) < 2:
        raise ValueError("multi-group bundle requires at least two source series")

    reports = []
    seen_source_ids = set()
    for group in groups:
        report = validate_series_manifest(group)
        duplicates = seen_source_ids.intersection(report["source_ids"])
        if duplicates:
            raise ValueError("duplicate source identity across series groups")
        seen_source_ids.update(report["source_ids"])
        reports.append(report)

    boundaries = []
    for superior, inferior in zip(reports, reports[1:]):
        superior_last = superior["scanner_S_centre_range_mm"][1]
        inferior_first = inferior["scanner_S_centre_range_mm"][0]
        if superior_last <= inferior_first:
            raise ValueError("series group order must be superior-to-inferior")
        superior_bottom = superior_last - superior["slice_thickness_mm"] / 2.0
        inferior_top = inferior_first + inferior["slice_thickness_mm"] / 2.0
        overlap = inferior_top - superior_bottom
        if overlap < -_TOLERANCE:
            raise ValueError("physical gap between source series groups")
        boundaries.append({
            "superior_group_last_centre_S_mm": superior_last,
            "inferior_group_first_centre_S_mm": inferior_first,
            "overlap_mm": max(0.0, overlap),
            "flattened_to_uniform_stack": False,
        })

    return {
        "status": "CONTIGUOUS_MULTI_GROUP_SOURCE_VOLUME_NOT_ANATOMICAL",
        "series_count": len(reports),
        "slice_count": sum(report["slice_count"] for report in reports),
        "scanner_S_centre_range_mm": [
            reports[0]["scanner_S_centre_range_mm"][0],
            reports[-1]["scanner_S_centre_range_mm"][1],
        ],
        "boundary_evidence": boundaries,
        "single_uniform_stack_claimed": False,
        "source_series_group_boundaries_preserved": True,
        "anatomical_coverage_verified": False,
        "canonical_promotion_allowed": False,
        "source_skeleton_governs_geometry": True,
    }


def validate_occupancy_review(review, source_bundle):
    """Bind a coarse Blender occupancy review to verified source geometry.

    The accepted evidence remains explicitly non-anatomical. This gate rejects
    attempts to reinterpret stored PNG values as calibrated HU, call the block
    mesh a bone segmentation, modify the source skeleton, or allow promotion.
    """
    if not isinstance(review, dict):
        raise ValueError("occupancy review must be an object")
    if (review.get("schema_version") != 1 or review.get("kind") !=
            "PELVIC_CT_STORED_SCALAR_OCCUPANCY_REVIEW_NOT_SEGMENTATION"):
        raise ValueError("unsupported pelvic CT occupancy review schema")

    false_claims = (
        "values_are_calibrated_HU",
        "anatomical_bone_segmentation_verified",
        "patient_scanner_to_HGPT_world_verified",
        "skeleton_geometry_modified",
        "canonical_promotion_allowed",
        "source_images_packed",
    )
    if any(review.get(field) is not False for field in false_claims):
        raise ValueError("unsupported occupancy claim or source handling")
    if review.get("source_skeleton_governs_geometry") is not True:
        raise ValueError("source skeleton must govern occupancy geometry")
    if review.get("private_outputs_must_remain_untracked") is not True:
        raise ValueError("private occupancy outputs must remain untracked")
    if (not _valid_hash(review.get("blend_sha256")) or
            not _valid_hash(review.get("render_sha256"))):
        raise ValueError("occupancy artifacts require lowercase SHA-256 identities")

    bundle_report = validate_series_bundle(source_bundle)
    claimed_bundle = review.get("source_bundle")
    if not isinstance(claimed_bundle, dict):
        raise ValueError("occupancy review requires source bundle evidence")
    boundary_values = bundle_report["boundary_evidence"]
    if len(boundary_values) != 1:
        raise ValueError("occupancy review supports exactly one group boundary")
    expected_overlap = boundary_values[0]["overlap_mm"]
    if (claimed_bundle.get("series_count") != bundle_report["series_count"] or
            claimed_bundle.get("slice_count") != bundle_report["slice_count"] or
            claimed_bundle.get("scanner_S_centre_range_mm") !=
            bundle_report["scanner_S_centre_range_mm"] or
            claimed_bundle.get("boundary_overlap_mm") != expected_overlap or
            claimed_bundle.get("single_uniform_stack_claimed") is not False or
            claimed_bundle.get("group_boundaries_preserved") is not True):
        raise ValueError("occupancy source bundle evidence does not match manifest")

    groups = review.get("group_summaries")
    if not isinstance(groups, list) or len(groups) != bundle_report["series_count"]:
        raise ValueError("occupancy group summaries do not match source bundle")
    total_fields = ("candidate_block_count", "mesh_vertex_count", "mesh_quad_count")
    totals = {field: 0 for field in total_fields}
    slice_total = 0
    for index, group in enumerate(groups, start=1):
        if not isinstance(group, dict) or group.get("group_index") != index:
            raise ValueError("occupancy groups must retain source order")
        for field in ("source_slice_count",) + total_fields:
            value = group.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError("occupancy group counts must be positive integers")
        slice_total += group["source_slice_count"]
        for field in total_fields:
            totals[field] += group[field]
        component_sizes = group.get("component_block_counts_6_neighbour")
        if (not isinstance(component_sizes, list) or not component_sizes or
                any(isinstance(value, bool) or not isinstance(value, int) or value <= 0
                    for value in component_sizes) or
                component_sizes != sorted(component_sizes, reverse=True) or
                sum(component_sizes) != group["candidate_block_count"] or
                group.get("connected_component_count_6_neighbour") !=
                len(component_sizes) or
                group.get("automatic_component_filter_applied") is not False):
            raise ValueError("occupancy component audit is incomplete or inconsistent")
        largest_fraction = _number(
            group.get("largest_component_block_fraction"),
            "largest component block fraction",
        )
        expected_fraction = component_sizes[0] / group["candidate_block_count"]
        if abs(largest_fraction - expected_fraction) > _TOLERANCE:
            raise ValueError("occupancy component audit has inconsistent fraction")
    if slice_total != bundle_report["slice_count"]:
        raise ValueError("occupancy group slice totals do not match source bundle")
    if any(review.get(field) != total for field, total in totals.items()):
        raise ValueError("occupancy group totals do not match reported totals")

    threshold = _number(review.get("stored_scalar_threshold"), "stored scalar threshold")
    if threshold <= 0:
        raise ValueError("stored scalar threshold must be positive")
    block_size = review.get("candidate_block_size_pixels")
    if (not isinstance(block_size, list) or len(block_size) != 2 or
            any(isinstance(value, bool) or not isinstance(value, int) or value <= 0
                for value in block_size)):
        raise ValueError("candidate block size must contain two positive integers")
    observations = review.get("review_observation_count")
    if (isinstance(observations, bool) or not isinstance(observations, int) or
            observations < 0):
        raise ValueError("review observation count must be a non-negative integer")

    visual = review.get("visual_review")
    if (not isinstance(visual, dict) or
            visual.get("candidate_volume_visible") is not True or
            visual.get("group_boundary_visible") is not True or
            visual.get("disconnected_threshold_islands_visible") is not True or
            visual.get("surface_suitable_for_anatomical_use") is not False):
        raise ValueError("visual review must preserve non-anatomical limitations")
    encoded = json.dumps(review)
    if re.search(r"[A-Za-z]:\\\\", encoded) or "source_validations" in encoded:
        raise ValueError("occupancy review contains private source detail")

    return {
        "status": "STORED_SCALAR_OCCUPANCY_VERIFIED_NOT_SEGMENTATION",
        "series_count": bundle_report["series_count"],
        "slice_count": bundle_report["slice_count"],
        "candidate_block_count": totals["candidate_block_count"],
        "values_are_calibrated_HU": False,
        "anatomical_bone_segmentation_verified": False,
        "canonical_promotion_allowed": False,
        "source_skeleton_governs_geometry": True,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("kind") == "CANDIDATE_PELVIC_CT_SERIES_BUNDLE":
        safe = validate_series_bundle(manifest)
    else:
        safe = validate_series_manifest(manifest)
    result = json.dumps(safe, indent=2) + "\n"
    if args.out:
        with args.out.open("x", encoding="utf-8") as handle:
            handle.write(result)
    else:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
