#!/usr/bin/env python3
"""Validate mask-supported candidate CT landmarks without canonical promotion."""
import copy

import nlm_ct_pixel_ras_envelope as pixel_ras


SEMANTICS = {
    ("ASIS", "left"): "iliac_blade",
    ("ASIS", "right"): "iliac_blade",
    ("pubic_region", "midline"): "pubic_region",
    ("S1_endplate", "midline"): "sacrum",
    ("acetabular", "left"): "acetabulum_left",
    ("acetabular", "right"): "acetabulum_right",
    ("femoral_head", "left"): "femoral_head_left",
    ("femoral_head", "right"): "femoral_head_right",
}


def _contains_world_coordinate(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"HomeGymPT_world_coordinate_m", "HomeGymPT_world_coordinate_mm"}:
                return True
            if _contains_world_coordinate(child):
                return True
    elif isinstance(value, list):
        return any(_contains_world_coordinate(child) for child in value)
    return False


def _mask_voxels(segmentation_result):
    source_ids = segmentation_result.get("source_ids")
    runs = segmentation_result.get("validated_runs")
    if (not isinstance(source_ids, list) or not isinstance(runs, list)
            or len(source_ids) != len(runs)):
        raise ValueError("validated candidate segmentation is required")
    voxels = set()
    for source_id, slice_runs in zip(source_ids, runs):
        for row, first_col, last_col in slice_runs:
            for col in range(first_col, last_col + 1):
                voxels.add((source_id, row, col))
    return voxels


def _citations(review_result):
    citations = review_result.get("citations")
    if (not isinstance(citations, list) or not citations
            or any(not isinstance(item, dict)
                   or not isinstance(item.get("url"), str)
                   or not item["url"].startswith("https://")
                   for item in citations)):
        raise ValueError("independent HTTPS citation evidence is required")
    return citations


def validate_landmarks(packet: dict, review_result: dict,
                       segmentation_result: dict, scanner_by_source: dict) -> dict:
    """Return bounded landmark observations that remain explicitly unverified."""
    if (not isinstance(packet, dict)
            or packet.get("schema_version") != 1
            or packet.get("kind") != "NLM_CT_CANDIDATE_LANDMARK_PACKET"):
        raise ValueError("unsupported candidate landmark packet")
    if (packet.get("source_skeleton_governs_geometry") is not True
            or packet.get("canonical_promotion_allowed") is not False):
        raise ValueError("source skeleton governs; canonical promotion is prohibited")
    if (packet.get("exact_point_claimed") is not False
            or packet.get("submillimetre_accuracy_claimed") is not False):
        raise ValueError("exact or submillimetre landmark claims are prohibited")
    if (packet.get("HomeGymPT_world_transform_applied") is not False
            or _contains_world_coordinate(packet)):
        raise ValueError("Home Gym PT world coordinates are not established")

    if (not isinstance(review_result, dict)
            or review_result.get("anatomical_status") != "CANDIDATE"
            or review_result.get("canonical_promotion_allowed") is not False):
        raise ValueError("validated candidate source review is required")
    citations = _citations(review_result)
    observations = {item.get("observation_id"): item
                    for item in review_result.get("observations", [])
                    if isinstance(item, dict)}

    if (not isinstance(segmentation_result, dict)
            or segmentation_result.get("canonical_promotion_allowed") is not False
            or segmentation_result.get("coverage_complete") is not False
            or segmentation_result.get("bone_surface_segmentation_verified") is not False):
        raise ValueError("noncanonical incomplete candidate segmentation is required")
    voxels = _mask_voxels(segmentation_result)
    segmentation_label = segmentation_result.get("candidate_label")

    items = packet.get("landmarks")
    if not isinstance(items, list):
        raise ValueError("candidate landmarks must be a list")
    seen = set()
    output = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("each landmark must be an object")
        landmark_id = item.get("landmark_id")
        if (not isinstance(landmark_id, str) or not landmark_id.strip()
                or landmark_id in seen):
            raise ValueError("candidate landmark IDs must be unique")
        seen.add(landmark_id)

        expected_label = SEMANTICS.get((item.get("semantic"), item.get("side")))
        if expected_label is None or item.get("candidate_label") != expected_label:
            raise ValueError("landmark semantic, side, and structure are inconsistent")
        if expected_label != segmentation_label:
            raise ValueError("landmark structure differs from candidate segmentation")

        source_id = item.get("source_id")
        row, col = item.get("row"), item.get("column")
        if source_id not in scanner_by_source:
            raise ValueError("landmark source slice is absent from segmentation")
        if type(row) is not int or type(col) is not int:
            raise ValueError("landmark pixel indices must be integers")
        observation = observations.get(item.get("review_observation_id"))
        if (observation is None
                or observation.get("source_id") != source_id
                or observation.get("candidate_label") != expected_label):
            raise ValueError("matching review observation is required")
        if item.get("reviewer_id") != observation.get("reviewer_id"):
            raise ValueError("landmark reviewer conflicts with source review")
        if (source_id, row, col) not in voxels:
            raise ValueError("landmark must be supported by an included mask voxel")
        if item.get("claimed_accuracy_mm") is not None:
            raise ValueError("exact or submillimetre landmark accuracy is prohibited")

        envelope = pixel_ras.place_pixel(scanner_by_source[source_id], row, col)
        candidate = copy.deepcopy(item)
        candidate.update({
            "validation_status": "CANDIDATE_SOURCE_OBSERVATION",
            "source_png_sha256": observation["source_png_sha256"],
            "source_header_sha256": observation["source_header_sha256"],
            "citations": copy.deepcopy(citations),
            "candidate_pixel_centre_RAS_mm_if_outer_FOV_corners":
                envelope["candidate_pixel_centre_RAS_mm_if_outer_FOV_corners"],
            "pixel_cell_four_corners_RAS_mm":
                envelope["candidate_cell_four_corners_RAS_mm_if_outer_FOV_corners"],
            "source_slab_S_range_mm": envelope["source_slab_S_range_mm"],
            "voxel_index_to_physical_sample_centre_convention_verified": False,
            "HomeGymPT_world_transform_applied": False,
            "canonical_promotion_allowed": False,
        })
        output.append(candidate)

    return {
        "schema_version": 1,
        "kind": "NLM_CT_CANDIDATE_LANDMARK_VALIDATION",
        "landmarks": output,
        "source_skeleton_governs_geometry": True,
        "canonical_promotion_allowed": False,
        "all_landmarks_verified": False,
        "unmet_gates": [
            "PIXEL_CENTRE_CONVENTION_NOT_INDEPENDENTLY_VERIFIED",
            "PATIENT_SCANNER_TO_HGPT_WORLD_NOT_VERIFIED",
            "FULL_BONE_SURFACE_NOT_VALIDATED",
            "INDEPENDENT_SECOND_LANDMARK_REVIEW_REQUIRED",
            "CANONICAL_GEOMETRY_PROMOTION_PROHIBITED",
        ],
    }
