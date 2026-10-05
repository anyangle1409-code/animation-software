"""Fail-closed validation for the r96 shoulder-yoke repair declaration."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


R95_SHA256 = "8a39a22d3fec36f82c1cd53f6d0a976748a8cf97de14d81e62b5789178403bdd"
R95_PATH = "ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r95.blend"
ALLOWED_BONES = {
    "clavicle_l", "clavicle_r", "scapula_l", "scapula_r",
    "upperarm_l", "upperarm_r", "spine_02", "spine_03",
}
REQUIRED_PROTECTED_ZONES = {
    "neck_boundary", "pelvis_boundary", "hands", "feet", "head",
    "clothing", "frozen_correctives",
}
REQUIRED_STOP_CONDITIONS = {
    "parent_identity_mismatch", "out_of_scope_edit",
    "critical_or_high_defect", "material_regression",
}


def _integer_ids(value: Any) -> list[int] | None:
    if not isinstance(value, list) or not value:
        return None
    if not all(isinstance(item, int) and not isinstance(item, bool) and item >= 0 for item in value):
        return None
    return value


def validate_declaration(data: dict[str, Any], root: Path | None = None) -> list[str]:
    """Return every declaration error; an empty list is the only valid result."""
    errors: list[str] = []
    if data.get("schema_version") != 1 or data.get("declared_before_edit") is not True:
        errors.append("declaration must use schema 1 and be recorded before edit")
    if data.get("target_revision") != "r96":
        errors.append("target revision must be r96")

    parent = data.get("parent")
    if not isinstance(parent, dict) or (
        parent.get("revision") != "r95"
        or parent.get("candidate_path") != R95_PATH
        or parent.get("sha256") != R95_SHA256
    ):
        errors.append("exact r95 parent revision, path and SHA-256 are required")

    issue_ids = data.get("issue_ids")
    if not isinstance(issue_ids, list) or not issue_ids or not all(
        isinstance(item, str) and re.fullmatch(r"WB-[A-Z]+-\d{3}", item) for item in issue_ids
    ):
        errors.append("one or more stable whole-body issue IDs are required")

    evidence_paths = data.get("evidence_paths")
    if not isinstance(evidence_paths, list) or not evidence_paths or not all(
        isinstance(item, str) and item.strip() for item in evidence_paths
    ):
        errors.append("one or more evidence paths are required")
    elif root is not None:
        resolved_root = root.resolve()
        for item in evidence_paths:
            target = (resolved_root / item).resolve()
            if not target.is_relative_to(resolved_root) or not target.is_file():
                errors.append("evidence path is missing or escapes the repository: " + item)

    zone = data.get("zone")
    if not isinstance(zone, dict):
        errors.append("declared mirror-closed zone is required")
    else:
        left = _integer_ids(zone.get("left_vertex_ids"))
        right = _integer_ids(zone.get("right_vertex_ids"))
        pairs = zone.get("mirror_pairs")
        if left is None or right is None:
            errors.append("zone vertex IDs must be non-empty non-negative integer lists")
        else:
            if len(set(left)) != len(left) or len(set(right)) != len(right):
                errors.append("zone vertex IDs must be unique on each side")
            if set(left) & set(right):
                errors.append("left and right zone vertex IDs must be disjoint")
            expected_pairs = set(zip(left, right)) if len(left) == len(right) else set()
            actual_pairs = {
                tuple(pair) for pair in pairs
                if isinstance(pair, list) and len(pair) == 2 and all(isinstance(item, int) for item in pair)
            } if isinstance(pairs, list) else set()
            if len(left) != len(right) or actual_pairs != expected_pairs or len(actual_pairs) != len(left):
                errors.append("zone mirror pairs must be complete and ordered left-to-right")
            if zone.get("maximum_existing_vertex_count") != len(set(left) | set(right)):
                errors.append("maximum existing vertex count must equal the declared zone size")
        regions = zone.get("permitted_regions")
        if not isinstance(regions, list) or not regions or not set(regions) <= {"shoulder", "torso", "arm"}:
            errors.append("zone permitted regions must be limited to shoulder, torso and arm")

    bones = data.get("permitted_bones")
    if not isinstance(bones, list) or not bones or len(set(bones)) != len(bones) or not set(bones) <= ALLOWED_BONES:
        errors.append("permitted bones must be a unique non-empty subset of the existing shoulder-yoke bones")

    topology = data.get("topology_intent")
    if not isinstance(topology, dict):
        errors.append("topology intent is required")
    else:
        max_vertices = topology.get("maximum_new_vertices")
        max_faces = topology.get("maximum_new_faces")
        if (
            topology.get("operation") != "local_support_loops"
            or not isinstance(max_vertices, int) or not 0 < max_vertices <= 960
            or not isinstance(max_faces, int) or not 0 < max_faces <= 960
        ):
            errors.append("maximum topology scope must be finite, local and explicitly bounded")
        for key in ("preserve_original_vertex_ids", "preserve_quads", "preserve_outward_normals"):
            if topology.get(key) is not True:
                errors.append("topology intent must require " + key)

    weights = data.get("weight_intent")
    if not isinstance(weights, dict) or weights.get("scope") != "declared_zone_only":
        errors.append("weight changes must be limited to the declared zone")
    elif (
        weights.get("maximum_influences") != 4
        or weights.get("normalized") is not True
        or weights.get("mirror_symmetric") is not True
    ):
        errors.append("weight intent must preserve four-influence normalized mirror symmetry")

    protected = data.get("protected_zones")
    if not isinstance(protected, list) or not REQUIRED_PROTECTED_ZONES <= set(protected):
        errors.append("all required protected zones must be explicit")
    stop_conditions = data.get("stop_conditions")
    if not isinstance(stop_conditions, list) or not REQUIRED_STOP_CONDITIONS <= set(stop_conditions):
        errors.append("all fail-closed stop conditions must be explicit")
    return errors
