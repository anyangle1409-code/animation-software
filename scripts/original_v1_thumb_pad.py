"""First-party local thumb-pad clearance geometry (Phase 3C). numpy only; shared by the declaration tool and the
Blender apply script so the declared mask and the applied edit cannot drift apart.

Input is the read-only survey written by scripts/survey_original_v1_thumb_pad_clearance_blender.py: for the frozen
curl_handle / pullup_bar poses the handle frame (centre, axis, radius) expressed in the REST coordinates of the hand and
every vertex's pre-close signed distance to the handle (negative = inside). Because all hand-chain bones carry one
rigid transform before closing, that rest-space description is exact.

Edit rule (local, smooth, minimal): every thumb-region vertex that is inside the handle by p metres needs to move out
by p + margin along its own radial direction away from the handle axis (so the distance-from-axis grows by exactly
that amount). The required displacement is spread to neighbouring thumb vertices with a cosine^2 falloff of radius L
(support envelope  A(v) = max_u a_u * K(|x_v - x_u| / L) ), so the surface stays smooth and the field is Lipschitz.
Mask = thumb-region vertices within L of an inside vertex. Nothing but vertex positions of those vertices changes.
"""
from __future__ import annotations

import numpy as np

SCHEMA = 1


def kernel(t):
    """cosine^2 falloff: 1 at 0, 0 at t >= 1."""
    t = np.clip(t, 0.0, 1.0)
    return np.cos(0.5 * np.pi * t) ** 2


def side_frame(survey, side):
    """Union over the two frozen poses of this side's handle frame (identical within numerical noise) and distances."""
    frames = [survey["poses"][p][side] for p in ("curl_handle", "pullup_bar")]
    c = np.array(frames[0]["handle_centre_rest"])
    a = np.array(frames[0]["handle_axis_rest"])
    R = float(frames[0]["handle_radius_m"])
    for f in frames[1:]:
        if np.abs(np.array(f["handle_centre_rest"]) - c).max() > 1e-4 or np.abs(np.array(f["handle_axis_rest"]) - a).max() > 1e-4:
            raise ValueError("curl_handle and pullup_bar handle frames differ in rest space; survey is inconsistent")
    return c, a / np.linalg.norm(a), R


def inside_vertices(survey, side, thumb_ids):
    """Thumb-region vertices of this side that are inside the handle in either frozen pose (id -> penetration m)."""
    thumb = set(int(i) for i in thumb_ids)
    pen = {}
    for pose in ("curl_handle", "pullup_bar"):
        for k, v in survey["poses"][pose][side]["distance_to_handle_mm_thumb_region"].items():
            i = int(k)
            if i in thumb and v < 0:
                pen[i] = max(pen.get(i, 0.0), -v / 1000.0)
    return pen


def plan(survey, rest, thumb_ids, side_of, margin_m, falloff_m):
    """Return (mask_ids, displacement dict id -> vector, report) for both sides.

    rest      : (n,3) rest positions;  thumb_ids: iterable of thumb-region vertex ids (both sides)
    side_of   : function vertex id -> 'l' | 'r'
    """
    thumb_ids = sorted(int(i) for i in thumb_ids)
    mask, disp, report = set(), {}, {}
    for side in "lr":
        ids_side = [i for i in thumb_ids if side_of(i) == side]
        c, a, R = side_frame(survey, side)
        pen = inside_vertices(survey, side, ids_side)
        if not pen:
            continue
        core = np.array(sorted(pen))
        need = np.array([pen[i] + margin_m for i in core])
        X = rest[ids_side]
        # radial direction away from the handle axis for every candidate vertex
        v = X - c
        rad = v - np.outer(v @ a, a)
        r = np.linalg.norm(rad, axis=1)
        u = rad / np.maximum(r, 1e-12)[:, None]
        # envelope of required displacement: A(v) = max_u need_u * K(|x_v - x_u| / L)
        d = np.linalg.norm(X[:, None, :] - rest[core][None, :, :], axis=2)
        A = (need[None, :] * kernel(d / falloff_m)).max(axis=1)
        sel = A > 1e-9
        for j in np.nonzero(sel)[0]:
            i = ids_side[j]
            mask.add(i)
            disp[i] = (A[j] * u[j])
        report[side] = {"inside_vertices": int(len(core)), "max_penetration_mm": float(max(pen.values()) * 1000),
                        "mask_vertices": int(sel.sum()), "max_displacement_mm": float(A.max() * 1000),
                        "handle_radius_mm": R * 1000.0}
    return sorted(mask), disp, report


def clearance_after(survey, rest, disp, side_of):
    """Rest-space distance from the handle axis minus radius, for every displaced vertex that was inside, after the edit."""
    out = {}
    for side in "lr":
        c, a, R = side_frame(survey, side)
        for i, dv in disp.items():
            if side_of(i) != side:
                continue
            x = rest[i] + dv
            v = x - c
            out[i] = float(np.linalg.norm(v - (v @ a) * a) - R)
    return out
