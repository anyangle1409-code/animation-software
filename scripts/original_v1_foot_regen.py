"""Regenerate the ORIGINAL_v1 foot skin from the O2 body generator with re-proportioned foot constants (pure numpy).

The O2 generator (scripts/original_v1_o2_body.py) authors the foot from constants (FOOT_FAN heel/ankle fan about the
dorsal ankle crease, FOOT_SECTIONS forefoot sections, TOE_SPLIT_F, TOE_TIPS_F). With unchanged constants it reproduces
the a003 foot vertices exactly (max 2.3e-7 m over the 3,210 foot vertices, same vertex order), so a foot regenerated
with new constants can replace the a003 foot vertex-for-vertex (same topology, groups and weights).

Parameters (all in the generator's internal frame: f = forward = -Y, metres):
  sections_f   four FOOT_SECTIONS f stations (dimensions unchanged)
  toe_split_f  TOE_SPLIT_F
  tips_f       five TOE_TIPS_F
  heel_gain    (kept at 0 by the C3 builder) extra straight-back (180 deg) fan radius on the fan rings with theta < 90: factor
               1 + (0.25 + heel_gain) sin(2 theta); the oblique 135/225 deg entries keep the generator's factor, so the
               heel lengthens without widening
"""
from __future__ import annotations

import math
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import original_v1_o2_body as g  # noqa: E402

ORIGINAL = {'FOOT_SECTIONS': list(g.FOOT_SECTIONS), 'TOE_SPLIT_F': g.TOE_SPLIT_F, 'TOE_TIPS_F': list(g.TOE_TIPS_F)}
_BUILD_LEG = g.build_leg


def _build_leg_with_heel(heel_gain):
    def build_leg(B, bones, side, loop):
        lateral = np.array([float(side), 0.0, 0.0])
        rings = []
        for z, (lx, f), (rf, rl, rb, rm), deltas in g.LEG_LEVELS:
            if 0.55 < z < 0.78:
                rf, rl, rb = rf * 1.05, rl * 1.05, rb * 1.04
            elif 0.20 < z < 0.46:
                rl, rb, rm = rl * 1.04, rb * 1.05, rm * 1.04
            extra = {}
            if z > 0.70:
                k = (z - 0.70) / 0.10
                extra = {40: 0.5 * (rf + rl) * (1.02 - 0.16 * k), 60: 0.5 * (rf + rl) * (1.02 - 0.15 * k)}
            base = g.limb_prof(rf, rl, rb, rm, extra)
            for ang, d in (deltas or {}).items():
                extra[ang] = base(math.radians(ang)) + d
            rings.append((g.sidep(side, (lx, f, z)), g.FWD, lateral, g.limb_prof(rf, rl, rb, rm, extra)))
        last = B.loft(loop, rings, region="leg")
        px, pf, pz = g.FOOT_PIVOT
        fan = []
        for theta, vc, half_len, half_w, shift in g.FOOT_FAN:
            t = math.radians(theta)
            e1 = np.array([0.0, math.cos(t), math.sin(t)])
            centre = g.sidep(side, (px + shift, pf, pz)) - e1 * vc
            heel = 1.0 + 0.25 * math.sin(t * 2) if theta < 90 else 1.0
            back = heel + (heel_gain * math.sin(t * 2) if theta < 90 else 0.0)
            prof = g.periodic_profile({0: half_len * 0.55, 45: half_len * 0.75, 90: half_w, 135: half_len * heel * 0.95,
                                       180: half_len * back, 225: half_len * heel * 0.95, 270: half_w * 0.97,
                                       315: half_len * 0.75})
            fan.append((centre, e1, lateral, prof))
        last = B.loft(last, fan, blend=2, region="foot")
        secs = []
        for f, (lx, zc), top, bottom, lat_r, med_r, deltas in g.FOOT_SECTIONS:
            spec = {0: top, 45: 0.5 * (top + lat_r) * 1.05, 90: lat_r,
                    135: 0.5 * (bottom + lat_r) * 1.08, 180: bottom,
                    225: 0.5 * (bottom + med_r) * 1.08, 270: med_r,
                    315: 0.5 * (top + med_r) * 1.05}
            for ang, d in (deltas or {}).items():
                spec[ang] = spec.get(ang, g.periodic_profile(spec)(math.radians(ang))) + d
            secs.append((g.sidep(side, (lx, f, zc)), g.UP, lateral, g.periodic_profile(spec)))
        last = B.loft(last, secs, blend=2, region="foot")
        g.build_toes(B, side, last)
    return build_leg


@contextmanager
def patched(sections_f=None, toe_split_f=None, tips_f=None, heel_gain=0.0):
    try:
        if sections_f is not None:
            g.FOOT_SECTIONS = [(f,) + tuple(s[1:]) for f, s in zip(sections_f, ORIGINAL['FOOT_SECTIONS'])]
        if toe_split_f is not None:
            g.TOE_SPLIT_F = toe_split_f
        if tips_f is not None:
            g.TOE_TIPS_F = list(tips_f)
        g.build_leg = _build_leg_with_heel(heel_gain)
        yield
    finally:
        g.FOOT_SECTIONS = list(ORIGINAL['FOOT_SECTIONS']); g.TOE_SPLIT_F = ORIGINAL['TOE_SPLIT_F']
        g.TOE_TIPS_F = list(ORIGINAL['TOE_TIPS_F']); g.build_leg = _BUILD_LEG


def build_vertices(**params):
    """Blender-frame vertices (N, 3) of the whole generated body with the given foot parameters."""
    with patched(**params):
        return np.asarray(g.build()['vertices'], float)


def foot_metrics(V, y_ajc):
    zmin = V[:, 2].min()
    F = V[(V[:, 0] > 0.02) & (V[:, 2] < zmin + 0.16)]
    return {'heel_y': float(F[:, 1].max()), 'tip_y': float(F[:, 1].min()), 'length': float(F[:, 1].max() - F[:, 1].min()),
            'heel_behind_ajc': float(F[:, 1].max() - y_ajc), 'breadth': float(F[:, 0].max() - F[:, 0].min())}


def solve_tip(tip_y_target, sections_f, toe_split_f, tips_f_mapped, y_ajc, heel_gain=0.0, iters=22):
    """Bisection on a uniform toe-length factor so that the most anterior toe skin lands at tip_y_target (the heel is
    lengthened separately: growing the generator's heel fan radially also drives the heel below the floor, and the
    generator then re-grounds the whole lower leg). Returns params, V, metrics, factor."""
    lo, hi = 0.7, 1.3
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        tips = [toe_split_f + (t - toe_split_f) * mid for t in tips_f_mapped]
        m = foot_metrics(build_vertices(sections_f=sections_f, toe_split_f=toe_split_f, tips_f=tips, heel_gain=heel_gain), y_ajc)
        lo, hi = (mid, hi) if m['tip_y'] > tip_y_target else (lo, mid)
    k = 0.5 * (lo + hi)
    params = {'sections_f': list(sections_f), 'toe_split_f': toe_split_f,
              'tips_f': [toe_split_f + (t - toe_split_f) * k for t in tips_f_mapped], 'heel_gain': heel_gain}
    V = build_vertices(**params)
    return params, V, foot_metrics(V, y_ajc), k
