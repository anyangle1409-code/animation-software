"""Fail-closed inventory contract for the provisional original-body bridge.

The mapping is deliberately diagnostic.  Shared runtime controls do not imply
one-to-one anatomical correspondence or anatomical approval.
"""

import math

REVIEW_VIEWS = {
    "front": (0, -4, 0),
    "side": (4, 0, 0),
    "rear": (0, 4, 0),
}

MAJOR_BONE_MAPPING = {
    "anat_clavicle_left": "clavicle_r",
    "anat_clavicle_right": "clavicle_l",
    "anat_scapula_left": "scapula_r",
    "anat_scapula_right": "scapula_l",
    "anat_humerus_left": "upperarm_r",
    "anat_humerus_right": "upperarm_l",
    "anat_radius_left": "forearm_r",
    "anat_radius_right": "forearm_l",
    "anat_ulna_left": "forearm_r",
    "anat_ulna_right": "forearm_l",
    "anat_femur_left": "thigh_r",
    "anat_femur_right": "thigh_l",
    "anat_tibia_left": "shin_r",
    "anat_tibia_right": "shin_l",
    "anat_fibula_left": "shin_r",
    "anat_fibula_right": "shin_l",
}

EXPECTED_BODY_VERTICES = 17_946
EXPECTED_ANATOMICAL_BONES = 206
EXPECTED_RUNTIME_BONES = 67


def frame_from_bounds(lo, hi, padding=1.12):
    """Return a square full-body orthographic frame from world-space bounds."""
    padding = float(padding)
    if len(lo) != 3 or len(hi) != 3 or not math.isfinite(padding) or padding <= 1.0:
        raise ValueError("expected 3D bounds and padding greater than one")
    values = tuple(float(v) for v in (*lo, *hi))
    if not all(math.isfinite(v) for v in values):
        raise ValueError("frame bounds must be finite")
    spans = tuple(values[i + 3] - values[i] for i in range(3))
    if any(not math.isfinite(span) or span <= 0 for span in spans):
        raise ValueError("frame upper bounds must exceed lower bounds")
    centre = tuple(round((values[i] + values[i + 3]) / 2.0, 12) for i in range(3))
    scale = max(spans) * padding
    if not all(math.isfinite(value) for value in centre) or not math.isfinite(scale):
        raise ValueError("computed frame must be finite")
    return centre, scale


def validate_inventory(anatomical_bones, runtime_bones, body_vertices):
    """Return a serialisable, fail-closed inventory validation result."""
    anatomical_bones = set(anatomical_bones)
    runtime_bones = set(runtime_bones)
    errors = []

    missing_anatomical = sorted(set(MAJOR_BONE_MAPPING) - anatomical_bones)
    if missing_anatomical:
        errors.append("missing anatomical bones: " + ", ".join(missing_anatomical))

    missing_runtime = sorted(set(MAJOR_BONE_MAPPING.values()) - runtime_bones)
    if missing_runtime:
        errors.append("missing runtime bones: " + ", ".join(missing_runtime))

    if body_vertices != EXPECTED_BODY_VERTICES:
        errors.append(
            f"original body vertex count must be {EXPECTED_BODY_VERTICES}, got {body_vertices}"
        )
    if len(anatomical_bones) != EXPECTED_ANATOMICAL_BONES:
        errors.append(
            f"anatomical armature must have {EXPECTED_ANATOMICAL_BONES} bones, "
            f"got {len(anatomical_bones)}"
        )
    if len(runtime_bones) != EXPECTED_RUNTIME_BONES:
        errors.append(
            f"runtime armature must have {EXPECTED_RUNTIME_BONES} bones, "
            f"got {len(runtime_bones)}"
        )

    return {
        "errors": errors,
        "mapped_bones": len(MAJOR_BONE_MAPPING),
        "anatomical_bone_count": len(anatomical_bones),
        "runtime_bone_count": len(runtime_bones),
        "body_vertex_count": body_vertices,
        "anatomy_approved": False,
        "mapping_scope": "diagnostic major-bone bridge only",
    }


def _matrix_is_identity(matrix, tolerance=1e-9):
    return all(
        abs(float(matrix[row][column]) - (1.0 if row == column else 0.0)) <= tolerance
        for row in range(4)
        for column in range(4)
    )


def validate_blender_bridge(anatomy, runtime, body):
    """Validate the named native objects before emitting bridge claims."""
    result = validate_inventory(
        {bone.name for bone in anatomy.data.bones},
        {bone.name for bone in runtime.data.bones},
        len(body.data.vertices),
    )
    errors = result["errors"]
    expected_names = {
        "anatomy": "HGPT_ANATOMICAL_MASTER",
        "runtime": "HGPT_CANONICAL_V4_ORIGINAL",
        "body": "HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE",
    }
    for label, obj in (("anatomy", anatomy), ("runtime", runtime), ("body", body)):
        if obj.name != expected_names[label]:
            errors.append(f"{label} object must be named {expected_names[label]}, got {obj.name}")

    active_targets = [
        modifier.object
        for modifier in body.modifiers
        if modifier.type == "ARMATURE"
        and modifier.show_viewport
        and modifier.show_render
        and modifier.object is not None
    ]
    if len(active_targets) != 1 or active_targets[0] is not runtime:
        errors.append(
            "body must have exactly one enabled viewport/render Armature modifier, targeting runtime rig"
        )

    nonrest = [
        pose_bone.name
        for pose_bone in anatomy.pose.bones
        if not _matrix_is_identity(pose_bone.matrix_basis)
    ]
    if nonrest:
        errors.append("anatomical master must be at rest; posed bones: " + ", ".join(nonrest[:8]))
    return result
