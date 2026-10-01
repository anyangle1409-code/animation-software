"""First-party local midline relief groove (Phase 3E). numpy only; shared by the declaration tool and the Blender apply script
so the declared mask and the applied edit cannot drift apart.

Why: in deep hip flexion (lunge) the groin/gluteal midline vertices are stretched 6-7x because the two halves of the cleft
start at ZERO rest separation (no rest length to unfold). Weights alone cannot fix it without breaking squat volume and
percentile tolerances. A shallow V relief along the midline gives the cleft real rest length, which lowers the stretch ratio
of the same posed distance. The rule is geometric and generic (it is keyed to midline vertices that the dump shows are
over-stretched under hip flexion, not to an exercise name).

Rule: displacement of vertex v = -h * N(v) * T(v) * P(v)
  N : area-weighted outward vertex normal of the rest mesh (dump)
  T : cos^2 taper of the distance to the nearest declared core vertex (radius L)
  P : cos^2 profile of |x| (half width w)         (so only the midline strip moves; x = 0 is deepest)
Only vertex positions of the vertices with T*P > 0 and 0.5 < z < 1.2 change.
"""
from __future__ import annotations

import numpy as np


def normals(rest, tris):
    a, b, c = rest[tris[:, 0]], rest[tris[:, 1]], rest[tris[:, 2]]
    fn = np.cross(b - a, c - a)
    vol = np.einsum("ti,ti->t", a, np.cross(b, c)).sum() / 6.0
    fn = fn * np.sign(vol)
    vn = np.zeros_like(rest)
    for k in range(3):
        np.add.at(vn, tris[:, k], fn)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)


def cos2(t):
    return np.cos(0.5 * np.pi * np.clip(t, 0.0, 1.0)) ** 2


def plan(rest, tris, core_ids, depth_m, half_width_m, taper_m):
    """Return (mask_ids, displacement dict id -> vector, report)."""
    core = np.array(sorted(int(i) for i in core_ids))
    d = np.linalg.norm(rest[:, None, :] - rest[core][None, :, :], axis=2).min(axis=1)
    z = rest[:, 2]
    amp = cos2(d / taper_m) * cos2(np.abs(rest[:, 0]) / half_width_m) * ((z > 0.5) & (z < 1.2))
    vn = normals(rest, tris)
    ids = np.nonzero(amp > 1e-9)[0]
    disp = {int(i): -depth_m * amp[i] * vn[i] for i in ids}
    rep = {"core_vertices": int(len(core)), "mask_vertices": int(len(ids)), "max_displacement_mm": float(depth_m * amp.max() * 1000)}
    return [int(i) for i in ids], disp, rep
