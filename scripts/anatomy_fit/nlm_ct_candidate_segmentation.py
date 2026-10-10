#!/usr/bin/env python3
"""Validate bounded, manually reviewed candidate CT sparse-mask volumes.

The result is evidence for inspection only. It is not a verified bone surface,
does not use CT intensity/HU values, and cannot promote canonical geometry.
"""
import copy
import math

import nlm_ct_anatomical_review as anatomical_review
import nlm_ct_pixel_ras_envelope as pixel_ras
from nlm_contiguous_pelvis_ct_windows import TRIPLETS


MAX_SLICES = 3
MAX_RUNS = 4096
MAX_VOXELS = 500_000


def _is_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def _validate_scanners(source_ids, scanner_by_source):
    if not isinstance(scanner_by_source, dict) or set(scanner_by_source) != set(source_ids):
        raise ValueError("scanner records must match exactly one mask triplet")
    spacings = []
    scanners = []
    for source_id in source_ids:
        scanner = scanner_by_source[source_id]
        if (not isinstance(scanner, dict)
                or scanner.get("source_id") != source_id
                or scanner.get("image_dimensions") != [512, 512]
                or scanner.get("slice_thickness_mm") != 3):
            raise ValueError("scanner records require exact 512 grid and 3 mm slices")
        spacing = scanner.get("pixel_spacing_mm")
        if (not isinstance(spacing, list) or len(spacing) != 2
                or any(not _is_number(value) or value <= 0 for value in spacing)):
            raise ValueError("invalid scanner pixel spacing")
        spacings.append(tuple(spacing))
        scanners.append(scanner)
    if any(any(abs(a - b) > 1e-9 for a, b in zip(spacings[0], spacing))
           for spacing in spacings[1:]):
        raise ValueError("mixed pixel spacing is not a single scanner group")
    centres = [pixel_ras.place_pixel(scanner, 0, 0)["source_slice_centre_RAS_S_mm"]
               for scanner in scanners]
    if any(abs(abs(a - b) - 3) > 1e-6 for a, b in zip(centres, centres[1:])):
        raise ValueError("slice centres must be strictly contiguous at 3 mm")
    return centres


def _validated_runs(slices):
    run_count = 0
    for item in slices:
        if not isinstance(item, dict) or not isinstance(item.get("runs"), list):
            raise ValueError("each slice needs sparse-mask runs")
        run_count += len(item["runs"])
    if run_count > MAX_RUNS:
        raise ValueError("sparse-mask run cap exceeded")
    validated = []
    voxel_count = 0
    for item in slices:
        runs = item["runs"]
        if not runs:
            raise ValueError("each slice needs non-empty sparse-mask runs")
        prior = None
        clean = []
        for run in runs:
            if (not isinstance(run, list) or len(run) != 3
                    or any(type(value) is not int for value in run)):
                raise ValueError("runs must be [row, first_col, last_col] integers")
            row, first_col, last_col = run
            if not (0 <= row < 512 and 0 <= first_col <= last_col < 512):
                raise ValueError("runs must remain inside the 512 grid")
            if prior is not None:
                prior_row, _, prior_last = prior
                if row < prior_row or (row == prior_row and first_col <= prior_last):
                    raise ValueError("runs must be sorted, unique, and non-overlapping")
            prior = run
            clean.append(list(run))
            voxel_count += last_col - first_col + 1
            if voxel_count > MAX_VOXELS:
                raise ValueError("expanded voxel cap exceeded")
        validated.append(clean)
    return validated, voxel_count


def component_sizes_6_neighbour(voxels):
    """Return descending component sizes without selecting or filtering any."""
    remaining = set(voxels)
    sizes = []
    while remaining:
        size = 1
        stack = [remaining.pop()]
        while stack:
            z, row, col = stack.pop()
            for neighbour in ((z - 1, row, col), (z + 1, row, col),
                              (z, row - 1, col), (z, row + 1, col),
                              (z, row, col - 1), (z, row, col + 1)):
                if neighbour in remaining:
                    remaining.remove(neighbour)
                    stack.append(neighbour)
                    size += 1
        sizes.append(size)
    return sorted(sizes, reverse=True)


def validate_candidate_segmentation(packet: dict, review_result: dict,
                                    scanner_by_source: dict) -> dict:
    """Validate one manually authored sparse mask on one pinned triplet."""
    if (not isinstance(packet, dict)
            or packet.get("schema_version") != 1
            or packet.get("kind") != "NLM_CT_CANDIDATE_SPARSE_MASK_VOLUME"):
        raise ValueError("unsupported candidate segmentation packet")
    if (packet.get("mask_origin") != "manual_source_review"
            or packet.get("intensity_derived") is not False
            or packet.get("source_HU_used") is not False):
        raise ValueError("intensity-derived or HU segmentation claims are prohibited")
    for field in ("coverage_complete", "bone_surface_segmentation_verified",
                  "canonical_promotion_allowed"):
        if packet.get(field) is not False:
            raise ValueError(f"{field} must remain explicitly false")

    label = packet.get("candidate_label")
    if label not in anatomical_review.LABELS:
        raise ValueError("unsupported candidate label")
    if (not isinstance(review_result, dict)
            or review_result.get("anatomical_status") != "CANDIDATE"
            or review_result.get("source_skeleton_governs_geometry") is not True
            or review_result.get("canonical_promotion_allowed") is not False):
        raise ValueError("validated candidate anatomical review is required")
    reviewed = {item.get("observation_id"): item
                for item in review_result.get("observations", [])
                if isinstance(item, dict)}

    slices = packet.get("slices")
    if not isinstance(slices, list) or len(slices) != MAX_SLICES:
        raise ValueError("exactly one three-slice volume is required")
    source_ids = tuple(item.get("source_id") for item in slices
                       if isinstance(item, dict))
    if len(source_ids) != MAX_SLICES or source_ids not in TRIPLETS:
        raise ValueError("mask must use one pinned contiguous triplet")
    matched_observations = []
    for item in slices:
        observation = reviewed.get(item.get("review_observation_id"))
        if (observation is None
                or observation.get("source_id") != item.get("source_id")
                or observation.get("candidate_label") != label):
            raise ValueError("each mask slice needs a matching review observation")
        matched_observations.append(observation)

    centres_s = _validate_scanners(source_ids, scanner_by_source)
    if any(abs(centre - observation.get("scanner_S_mm", float("inf"))) > 1e-9
           for centre, observation in zip(centres_s, matched_observations)):
        raise ValueError("scanner centre differs from reviewed scanner coordinate")
    runs, voxel_count = _validated_runs(slices)
    voxels = set()
    points = []
    for z, (source_id, slice_runs) in enumerate(zip(source_ids, runs)):
        scanner = scanner_by_source[source_id]
        for row, first_col, last_col in slice_runs:
            for col in range(first_col, last_col + 1):
                voxels.add((z, row, col))
                points.append(pixel_ras.place_pixel(scanner, row, col)[
                    "candidate_pixel_centre_RAS_mm_if_outer_FOV_corners"
                ])
    if len(voxels) != voxel_count:
        raise ValueError("sparse-mask runs produce duplicate voxels")

    result = copy.deepcopy(packet)
    result["source_ids"] = list(source_ids)
    result["validated_runs"] = runs
    result["voxel_count"] = voxel_count
    component_sizes = component_sizes_6_neighbour(voxels)
    result["connected_component_count_6_neighbour"] = len(component_sizes)
    result["component_voxel_counts_6_neighbour"] = component_sizes
    result["largest_component_voxel_fraction"] = component_sizes[0] / voxel_count
    result["automatic_component_filter_applied"] = False
    result["voxel_index_bounds"] = {
        "min": [min(value[i] for value in voxels) for i in range(3)],
        "max": [max(value[i] for value in voxels) for i in range(3)],
    }
    result["sample_centre_bounds_RAS_mm"] = {
        "min": [min(point[i] for point in points) for i in range(3)],
        "max": [max(point[i] for point in points) for i in range(3)],
    }
    result["source_slice_centres_RAS_S_mm"] = centres_s
    result["coverage_complete"] = False
    result["bone_surface_segmentation_verified"] = False
    result["canonical_promotion_allowed"] = False
    result["coverage_gaps"] = [
        "OUTSIDE_REVIEWED_THREE_SLICE_WINDOW",
        "BETWEEN_PINNED_TRIPLETS_NOT_REVIEWED",
        "FULL_PELVIC_BONE_SURFACE_NOT_COVERED",
    ]
    result["unmet_gates"] = [
        "FULL_CONTIGUOUS_CT_COVERAGE_REQUIRED",
        "INDEPENDENT_BONE_SURFACE_VALIDATION_REQUIRED",
        "PATIENT_SCANNER_TO_HGPT_WORLD_NOT_VERIFIED",
        "CANONICAL_GEOMETRY_PROMOTION_PROHIBITED",
    ]
    return result
