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
    "anat_clavicle_left": "clavicle_l",
    "anat_clavicle_right": "clavicle_r",
    "anat_scapula_left": "scapula_l",
    "anat_scapula_right": "scapula_r",
    "anat_humerus_left": "upperarm_l",
    "anat_humerus_right": "upperarm_r",
    "anat_radius_left": "forearm_l",
    "anat_radius_right": "forearm_r",
    "anat_ulna_left": "forearm_l",
    "anat_ulna_right": "forearm_r",
    "anat_femur_left": "thigh_l",
    "anat_femur_right": "thigh_r",
    "anat_tibia_left": "shin_l",
    "anat_tibia_right": "shin_r",
    "anat_fibula_left": "shin_l",
    "anat_fibula_right": "shin_r",
}

EXPECTED_BODY_VERTICES = 17_946


def frame_from_bounds(lo, hi, padding=1.12):
    """Return a square full-body orthographic frame from world-space bounds."""
    if len(lo) != 3 or len(hi) != 3 or padding <= 1.0:
        raise ValueError("expected 3D bounds and padding greater than one")
    values = tuple(float(v) for v in (*lo, *hi))
    if not all(math.isfinite(v) for v in values):
        raise ValueError("frame bounds must be finite")
    spans = tuple(values[i + 3] - values[i] for i in range(3))
    if any(span <= 0 for span in spans):
        raise ValueError("frame upper bounds must exceed lower bounds")
    centre = tuple(round((values[i] + values[i + 3]) / 2.0, 12) for i in range(3))
    return centre, max(spans) * padding


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

    return {
        "errors": errors,
        "mapped_bones": len(MAJOR_BONE_MAPPING),
        "anatomical_bone_count": len(anatomical_bones),
        "runtime_bone_count": len(runtime_bones),
        "body_vertex_count": body_vertices,
        "anatomy_approved": False,
        "mapping_scope": "diagnostic major-bone bridge only",
    }
