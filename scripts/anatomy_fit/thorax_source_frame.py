"""Matsumura 2020 / ISB thorax landmark frame, expressed in caller coordinates.

Inputs and mapped positions share a unit (metres in the canonical records).
Source columns are X anterior, Y superior, Z anatomical right; origin IJ.
This maps source points, not clinical Euler angles or joint centres. Landmark
identity and anatomical pose must be established by the caller. No global pose
or absolute SC/AC/GH coordinate is selected here.
Primary definition: doi:10.1186/s13018-020-01934-w, Methods/Figure 2.
"""
import math
from numbers import Real
import numpy as np


def _array(value, shape):
    try:
        raw = np.asarray(value, dtype=object)
    except (TypeError, ValueError) as exc:
        raise ValueError('finite numeric coordinates required') from exc
    if raw.shape != shape or not all(isinstance(v, Real) and not isinstance(v, (bool, np.bool_))
                                    and math.isfinite(v) for v in raw.flat):
        raise ValueError('finite numeric coordinates required')
    return raw.astype(float)


def _unit(vector):
    length = math.hypot(*vector)
    if not math.isfinite(length) or length == 0:
        raise ValueError('degenerate landmark axis')
    return vector / length


def thorax_frame(points):
    """Return IJ origin and proper source-to-caller rotation columns X/Y/Z."""
    if not isinstance(points, dict) or not all(k in points for k in ('IJ', 'C7', 'PX', 'T8')):
        raise ValueError('IJ/C7/PX/T8 landmarks required')
    ij, c7, px, t8 = (_array(points[k], (3,)) for k in ('IJ', 'C7', 'PX', 'T8'))
    lower = px / 2 + t8 / 2
    upper = ij / 2 + c7 / 2
    y = _unit(upper - lower)
    normal = np.cross(_unit(c7 - ij), _unit(lower - ij))
    # Relative angular conditioning guard, not an anatomical tolerance.
    if math.hypot(*normal) <= 1e-10:
        raise ValueError('collinear or ill-conditioned thorax plane')
    z = _unit(normal)
    x = _unit(np.cross(y, z))
    R = np.column_stack((x, y, z))
    if not np.allclose(R.T @ R, np.eye(3), atol=1e-10, rtol=0) or np.linalg.det(R) <= 0:
        raise ValueError('thorax frame is not proper')
    return ij, R


def map_source_point(origin, frame, point):
    """Map an anterior/superior/right source position into caller coordinates."""
    o, R, p = _array(origin, (3,)), _array(frame, (3, 3)), _array(point, (3,))
    if not np.allclose(R.T @ R, np.eye(3), atol=1e-10, rtol=0) or np.linalg.det(R) <= 0:
        raise ValueError('proper orthonormal source frame required')
    result = o + R @ p
    if not np.isfinite(result).all():
        raise ValueError('mapped coordinates overflow')
    return result


def map_between_thorax_frames(source_landmarks, target_landmarks, point):
    """Transfer a point between two IJ/C7/PX/T8 anatomical frames.

    The input point uses the source model's coordinate basis, which need not
    already equal its landmark-derived ISB basis. All coordinates must share
    a unit. This performs a rigid rotation/translation only; it neither scales
    source anatomy nor accepts its dimensions as canonical numerical targets.
    Anatomical landmark identities and poses remain caller prerequisites.
    """
    source_origin, source_frame = thorax_frame(source_landmarks)
    target_origin, target_frame = thorax_frame(target_landmarks)
    source_point = _array(point, (3,))
    local_point = source_frame.T @ (source_point - source_origin)
    return map_source_point(target_origin, target_frame, local_point)
