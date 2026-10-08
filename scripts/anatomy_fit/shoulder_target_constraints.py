"""Constraint helpers for the skeleton-first shoulder-girdle target.

This module deliberately does not select a production coordinate. It keeps
measurement definitions separate and exposes only geometry that is valid
before the scapular local frame is frozen.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Iterable, Tuple


@dataclass(frozen=True)
class Band:
    mean: float
    low: float
    high: float


def bilateral_ac_breadth(biacromial_mm: float, lateral_acromion_to_ac_mm: float) -> float:
    """Return bilateral AC-centre breadth from outer acromial breadth.

    Assumes left/right symmetric medial offsets for the canonical target.
    Both inputs are straight transverse landmark distances in millimetres.
    """
    value = biacromial_mm - 2.0 * lateral_acromion_to_ac_mm
    if value <= 0.0:
        raise ValueError("AC breadth must remain positive")
    return value


def ac_breadth_cross_product_range(
    biacromial_band: Tuple[float, float],
    ac_offset_band: Tuple[float, float],
) -> Tuple[float, float]:
    """Conservative min/max AC breadth over independent input bands."""
    b_lo, b_hi = biacromial_band
    o_lo, o_hi = ac_offset_band
    if not (0 < b_lo <= b_hi and 0 <= o_lo <= o_hi):
        raise ValueError("invalid bands")
    lo = bilateral_ac_breadth(b_lo, o_hi)
    hi = bilateral_ac_breadth(b_hi, o_lo)
    return lo, hi


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


def evaluate_mean_scaffold() -> dict:
    """Return the registered mean-input consistency values for audit/debug."""
    biacromial = 425.15656060295987
    offset = 34.0
    endpoint = 154.8
    ac = bilateral_ac_breadth(biacromial, offset)
    return {
        "bilateral_ac_breadth_mm": ac,
        "half_ac_coordinate_mm": ac / 2.0,
        "lateral_only_bilateral_sc_breadth_mm":
            minimum_bilateral_sc_breadth_for_lateral_only_chord(ac, endpoint),
    }
