"""Pure provisional shape-to-control attachment contract.

The anatomical guides remain in the 206-bone rest frame.  Runtime controls
only supply pose deltas; this mapping never moves anatomical joint centres to
fit the legacy skin and never implies one-to-one anatomical correspondence.
"""

import math


MAJOR_ATTACHMENT_MAPPING = {
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

THORAX_ATTACHMENT_MAPPING = {
    **{
        f"anat_rib_{number:02d}_{side}": "spine_02"
        for number in range(1, 13)
        for side in ("left", "right")
    },
    "anat_sternum": "spine_02",
}

ATTACHMENT_MAPPING = {**MAJOR_ATTACHMENT_MAPPING, **THORAX_ATTACHMENT_MAPPING}

EVIDENCE_VIEWS = {
    "full_front": {"scope": "full_body", "offset": (0.0, -4.0, 0.0)},
    "full_side": {"scope": "full_body", "offset": (4.0, 0.0, 0.0)},
    "full_rear": {"scope": "full_body", "offset": (0.0, 4.0, 0.0)},
    "shoulder_front": {"scope": "shoulder", "offset": (0.0, -3.0, 0.0)},
    "shoulder_side": {"scope": "shoulder", "offset": (3.0, 0.0, 0.0)},
    "shoulder_rear": {"scope": "shoulder", "offset": (0.0, 3.0, 0.0)},
}


def _point(value):
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        raise ValueError("expected finite 3D point")
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x)
           for x in value):
        raise ValueError("expected finite 3D point")
    return tuple(float(x) for x in value)


def _sub(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def _add(a, b):
    return tuple(a[i] + b[i] for i in range(3))


def _mul(a, scalar):
    return tuple(x * scalar for x in a)


def _dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def _cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _norm(a):
    return math.sqrt(_dot(a, a))


def _unit(a):
    length = _norm(a)
    if length <= 1e-12:
        raise ValueError("collapsed axis")
    return tuple(x / length for x in a), length


def _rotate_shortest(value, source_axis, target_axis):
    cross = _cross(source_axis, target_axis)
    sine = _norm(cross)
    cosine = max(-1.0, min(1.0, _dot(source_axis, target_axis)))
    if sine > 1e-12:
        axis = _mul(cross, 1.0 / sine)
        return _add(
            _add(_mul(value, cosine), _mul(_cross(axis, value), sine)),
            _mul(axis, _dot(axis, value) * (1.0 - cosine)),
        )
    if cosine > 0:
        return value
    seed = (1.0, 0.0, 0.0) if abs(source_axis[0]) < 0.9 else (0.0, 1.0, 0.0)
    axis, _ = _unit(_cross(source_axis, seed))
    return _add(_mul(value, -1.0), _mul(axis, 2.0 * _dot(axis, value)))


def fit_segment_similarity(points, source_head, source_tail, target_head, target_tail):
    """Uniformly fit authored points from one directed segment to another."""
    points = [_point(point) for point in points]
    source_head, source_tail = _point(source_head), _point(source_tail)
    target_head, target_tail = _point(target_head), _point(target_tail)
    source_vector = _sub(source_tail, source_head)
    source_length = _norm(source_vector)
    if source_length <= 1e-12:
        raise ValueError("collapsed source segment")
    source_axis = _mul(source_vector, 1.0 / source_length)
    target_vector = _sub(target_tail, target_head)
    target_length = _norm(target_vector)
    if target_length <= 1e-12:
        raise ValueError("collapsed target segment")
    target_axis = _mul(target_vector, 1.0 / target_length)
    scale = target_length / source_length
    if not math.isfinite(scale):
        raise ValueError("unsafe non-finite similarity scale")
    fitted = []
    for point in points:
        if point == source_head:
            fitted.append(target_head)
        elif point == source_tail:
            fitted.append(target_tail)
        else:
            relative = _mul(_sub(point, source_head), scale)
            fitted.append(_add(target_head, _rotate_shortest(relative, source_axis, target_axis)))
        if any(not math.isfinite(value) for value in fitted[-1]):
            raise ValueError("similarity fit produced non-finite coordinate")
    return fitted


def validate_attachment_inventory(anatomical_bones, runtime_bones):
    """Validate the selected attachment subset, not either armature's full inventory."""
    anatomical_bones = set(anatomical_bones)
    runtime_bones = set(runtime_bones)
    expected_anatomical = set(ATTACHMENT_MAPPING)
    expected_runtime = set(ATTACHMENT_MAPPING.values())
    errors = []
    missing_anatomical = sorted(expected_anatomical - anatomical_bones)
    unexpected_anatomical = sorted(anatomical_bones - expected_anatomical)
    missing_runtime = sorted(expected_runtime - runtime_bones)
    unexpected_runtime = sorted(runtime_bones - expected_runtime)
    if missing_anatomical:
        errors.append("missing anatomical attachment bones: " + ", ".join(missing_anatomical))
    if unexpected_anatomical:
        errors.append("unexpected anatomical attachment bones: " + ", ".join(unexpected_anatomical))
    if missing_runtime:
        errors.append("missing runtime attachment bones: " + ", ".join(missing_runtime))
    if unexpected_runtime:
        errors.append("unexpected runtime attachment bones: " + ", ".join(unexpected_runtime))
    return {
        "errors": errors,
        "attachment_count": len(ATTACHMENT_MAPPING),
        "anatomy_approved": False,
        "attachment_scope": "provisional rigid guide attachment",
        "non_bijective": len(expected_runtime) < len(expected_anatomical),
    }
