"""Constraint helpers for the skeleton-first shoulder-girdle target.

This module deliberately does not select a production coordinate. It keeps
measurement definitions separate and exposes only geometry that is valid
before the scapular local frame is frozen.
"""
from __future__ import annotations

from math import sqrt
from typing import Iterable, Tuple


def bilateral_ac_breadth_from_transverse_offset(
    biacromial_mm: float,
    transverse_lateral_acromion_to_ac_mm: float,
) -> float:
    """Return bilateral AC breadth from a *transverse* medial offset.

    Important: the commonly cited lateral-acromion->AC measurement in the
    source register is a 3-D Euclidean distance. It may be used as an upper
    bound on this transverse component, but not substituted as if identical.
    """
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
    if not (0.0 < bilateral_ac_breadth_mm < biacromial_mm):
        raise ValueError("AC breadth must be positive and less than biacromial breadth")
    return (biacromial_mm - bilateral_ac_breadth_mm) / 2.0


def chord_length_mm(a: Iterable[float], b: Iterable[float]) -> float:
    """3-D Euclidean landmark distance in millimetres."""
    ax, ay, az = a
    bx, by, bz = b
    return sqrt((ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2)


def minimum_bilateral_sc_breadth_for_lateral_only_chord(
    bilateral_ac_breadth_mm: float,
    clavicle_endpoint_length_mm: float,
) -> float:
    """Symmetric SC breadth if the entire clavicle chord were mediolateral.

    This is a lower-bound/consistency helper only. Any AP or vertical
    separation increases the 3-D chord, so real geometry generally requires
    greater SC breadth or smaller AC breadth for the same endpoint length.
    """
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
    if curved_centerline_length_mm <= 0:
        return False
    return chord_length_mm(sc_xyz_mm, ac_xyz_mm) <= curved_centerline_length_mm


def evaluate_mean_outer_scaffold() -> dict:
    """Return valid mean-input bounds without collapsing 3-D to transverse."""
    biacromial = 425.15656060295987
    distance_3d = 34.0
    lower = biacromial - 2.0 * distance_3d
    return {
        "bilateral_ac_breadth_lower_bound_if_3d_distance_is_34mm": lower,
        "bilateral_ac_breadth_upper_ceiling": biacromial,
        "note": "Upper ceiling is strict: AC joints must lie medial to lateral acromia.",
    }
