"""Constraint helpers for the skeleton-first shoulder-girdle target.

This module deliberately does not select a production coordinate. It keeps
measurement definitions separate and exposes only geometry that is valid
before the scapular local frame is frozen.
"""
from __future__ import annotations

from math import hypot, isfinite
from numbers import Real
from typing import Iterable, Tuple


def _require_finite(*values):
    if not all(isinstance(v, Real) and not isinstance(v, bool) and isfinite(v) for v in values):
        raise ValueError("finite numeric anatomical measurements required")


def bilateral_ac_breadth_from_transverse_offset(
    biacromial_mm: float,
    transverse_lateral_acromion_to_ac_mm: float,
) -> float:
    """Return bilateral AC breadth from a *transverse* medial offset.

    Important: the commonly cited lateral-acromion->AC measurement in the
    source register is a 3-D Euclidean distance. It may be used as an upper
    bound on this transverse component, but not substituted as if identical.
    """
    _require_finite(biacromial_mm, transverse_lateral_acromion_to_ac_mm)
    value = biacromial_mm - 2.0 * transverse_lateral_acromion_to_ac_mm
    if value <= 0.0:
        raise ValueError("AC breadth must remain positive")
    if transverse_lateral_acromion_to_ac_mm < 0.0:
        raise ValueError("transverse offset cannot be negative")
    return value


def ac_breadth_bounds_from_outer_and_3d_distance(
    biacromial_band: Tuple[float, float],
    ac_3d_distance_band: Tuple[float, float],
) -> Tuple[float, float]:
    """Conservative AC-breadth bounds from outer breadth and 3-D offset bands.

    If d is a 3-D acromion-to-AC distance, transverse medial offset t obeys
    0 < t <= d. Thus lower bound is outer_low - 2*d_high, while the upper
    bound is strictly less than outer_high. The returned high value is the
    numeric outer-high ceiling; callers must enforce strict inequality.
    """
    b_lo, b_hi = biacromial_band
    d_lo, d_hi = ac_3d_distance_band
    _require_finite(b_lo, b_hi, d_lo, d_hi)
    if not (0 < b_lo <= b_hi and 0 <= d_lo <= d_hi):
        raise ValueError("invalid bands")
    lo = b_lo - 2.0 * d_hi
    if lo <= 0.0:
        raise ValueError("derived lower bound is non-positive")
    return lo, b_hi


def required_transverse_acromion_to_ac_offset(
    biacromial_mm: float,
    bilateral_ac_breadth_mm: float,
) -> float:
    """Return the per-side transverse medial offset implied by two breadths."""
    _require_finite(biacromial_mm, bilateral_ac_breadth_mm)
    if not (0.0 < bilateral_ac_breadth_mm < biacromial_mm):
        raise ValueError("AC breadth must be positive and less than biacromial breadth")
    return (biacromial_mm - bilateral_ac_breadth_mm) / 2.0


def chord_length_mm(a: Iterable[float], b: Iterable[float]) -> float:
    """3-D Euclidean landmark distance in millimetres."""
    ax, ay, az = a
    bx, by, bz = b
    _require_finite(ax, ay, az, bx, by, bz)
    length = hypot(ax - bx, ay - by, az - bz)
    _require_finite(length)
    return length


def minimum_bilateral_sc_breadth_for_lateral_only_chord(
    bilateral_ac_breadth_mm: float,
    clavicle_endpoint_length_mm: float,
) -> float:
    """Symmetric SC breadth if the entire clavicle chord were mediolateral.

    This is a lower-bound/consistency helper only. Any AP or vertical
    separation increases the 3-D chord, so real geometry generally requires
    greater SC breadth or smaller AC breadth for the same endpoint length.
    """
    _require_finite(bilateral_ac_breadth_mm, clavicle_endpoint_length_mm)
    if bilateral_ac_breadth_mm <= 0:
        raise ValueError("AC breadth must be positive")
    if clavicle_endpoint_length_mm <= 0:
        raise ValueError("clavicle endpoint length must be positive")
    value = bilateral_ac_breadth_mm - 2.0 * clavicle_endpoint_length_mm
    return max(0.0, value)


def endpoint_chord_is_anatomically_possible(
    sc_xyz_mm: Iterable[float],
    ac_xyz_mm: Iterable[float],
    curved_centerline_length_mm: float,
) -> bool:
    """Hard invariant: the straight endpoint chord cannot exceed curve length."""
    try:
        _require_finite(curved_centerline_length_mm)
        chord = chord_length_mm(sc_xyz_mm, ac_xyz_mm)
        return 0 < chord <= curved_centerline_length_mm
    except (ValueError, TypeError):
        return False


def a003_outer_breadth_failure(current_biac_mm: float, outer_biacromial_mm: float) -> bool:
    """Return True when AC centres are wider than lateral acromial landmarks.

    This invariant does not require any disputed AC-offset measurement.
    """
    _require_finite(current_biac_mm, outer_biacromial_mm)
    if min(current_biac_mm, outer_biacromial_mm) <= 0:
        raise ValueError("positive breadths required")
    return current_biac_mm >= outer_biacromial_mm
