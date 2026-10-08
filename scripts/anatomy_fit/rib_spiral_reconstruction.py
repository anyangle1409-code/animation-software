"""Source-locked Holcombe 2016 in-plane rib reconstruction primitives.

Only the distal logarithmic-spiral segment is accepted here. Equations 2.2-2.7
are unambiguous in the indexed thesis text and can be reproduced exactly.

The proximal equations are documented in
ORIGINAL_V1_WORK/anatomy/rib_inplane_derivation_holcombe2016_v1.json,
but final proximal branch selection is intentionally NOT implemented until the
second feasibility/branch constraint in Eq. 2.18 is recovered unambiguously.
"""

from __future__ import annotations

import math


def distal_unscaled(theta: float, Bd: float) -> tuple[float, float]:
    """Holcombe thesis Eq. 2.2."""
    e = math.exp(Bd * theta)
    return -e * math.cos(theta), e * math.sin(theta)


def distal_theta_peak(Bd: float) -> float:
    """Holcombe thesis Eq. 2.3; local-y maximum of the distal spiral."""
    return 2.0 * math.atan(math.sqrt(Bd * Bd + 1.0) + Bd)


def _first_root_after(func, start: float, stop: float, *, steps: int = 20000) -> float:
    """Find first non-trivial sign-changing root after start, then bisect."""
    eps = 1e-7
    a = start + eps
    fa = func(a)
    span = stop - a
    prev = a
    for i in range(1, steps + 1):
        b = a + span * i / steps
        fb = func(b)
        if not (math.isfinite(fa) and math.isfinite(fb)):
            raise ValueError("non-finite root function while reconstructing rib")
        if fa == 0.0:
            return prev
        if fa * fb < 0.0 or fb == 0.0:
            lo, hi = prev, b
            flo, fhi = fa, fb
            for _ in range(80):
                mid = 0.5 * (lo + hi)
                fm = func(mid)
                if flo * fm <= 0.0:
                    hi, fhi = mid, fm
                else:
                    lo, flo = mid, fm
            return 0.5 * (lo + hi)
        prev, fa = b, fb
    raise ValueError("no non-trivial distal endpoint root found")


def distal_theta_end(Xpk: float, Ypk: float, Bd: float) -> tuple[float, float]:
    """Holcombe thesis Eqs. 2.4-2.5."""
    if not (0.0 < Xpk < 1.0 and Ypk > 0.0):
        raise ValueError("expected normalized peak with 0<Xpk<1 and Ypk>0")
    theta_pk = distal_theta_peak(Bd)
    xpk_u, ypk_u = distal_unscaled(theta_pk, Bd)
    slope = -Ypk / (1.0 - Xpk)

    def collinear(theta: float) -> float:
        x, y = distal_unscaled(theta, Bd)
        return (y - ypk_u) - slope * (x - xpk_u)

    # Parameter bounds allow strong exponential growth/decay; four full turns
    # safely bracket the first non-trivial solution for all committed A1 means.
    theta_end = _first_root_after(collinear, theta_pk, theta_pk + 4.0 * math.pi)
    return theta_pk, theta_end


def distal_transform(Xpk: float, Ypk: float, Bd: float) -> dict:
    """Return source/target transform values from thesis Eqs. 2.6-2.7."""
    theta_pk, theta_end = distal_theta_end(Xpk, Ypk, Bd)
    xpk_u, ypk_u = distal_unscaled(theta_pk, Bd)
    xend_u, yend_u = distal_unscaled(theta_end, Bd)
    source_distance = math.hypot(xend_u - xpk_u, yend_u - ypk_u)
    target_distance = math.hypot(1.0 - Xpk, Ypk)
    if source_distance <= 0.0:
        raise ValueError("degenerate distal source span")
    return {
        "theta_pk": theta_pk,
        "theta_end": theta_end,
        "xpk_u": xpk_u,
        "ypk_u": ypk_u,
        "scale": target_distance / source_distance,
    }


def distal_point(theta: float, Xpk: float, Ypk: float, Bd: float) -> tuple[float, float]:
    """Transform one distal spiral point to normalized rib coordinates."""
    t = distal_transform(Xpk, Ypk, Bd)
    x, y = distal_unscaled(theta, Bd)
    return (
        (x - t["xpk_u"]) * t["scale"] + Xpk,
        (y - t["ypk_u"]) * t["scale"] + Ypk,
    )


def distal_curve(Xpk: float, Ypk: float, Bd: float, *, samples: int = 101) -> list[list[float]]:
    """Sample the exact normalized distal segment from peak [Xpk,Ypk] to [1,0]."""
    if samples < 2:
        raise ValueError("samples must be >= 2")
    t = distal_transform(Xpk, Ypk, Bd)
    out = []
    for i in range(samples):
        u = i / (samples - 1)
        theta = t["theta_pk"] + u * (t["theta_end"] - t["theta_pk"])
        x, y = distal_unscaled(theta, Bd)
        out.append([
            (x - t["xpk_u"]) * t["scale"] + Xpk,
            (y - t["ypk_u"]) * t["scale"] + Ypk,
        ])
    return out


def physical_distal_curve(Sx_mm: float, Xpk: float, Ypk: float, Bd: float, *, samples: int = 101) -> list[list[float]]:
    """Scale normalized coordinates by end-to-end rib span Sx (mm)."""
    if Sx_mm <= 0.0:
        raise ValueError("Sx_mm must be positive")
    return [[Sx_mm * x, Sx_mm * y] for x, y in distal_curve(Xpk, Ypk, Bd, samples=samples)]
