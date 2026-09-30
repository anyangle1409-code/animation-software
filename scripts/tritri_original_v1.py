"""Vectorised triangle-triangle intersection helpers (numpy only) for the O4 weight optimiser.

Two triangles intersect when any edge of one crosses the other (Moller-Trumbore
segment test; coplanar contact is ignored). Triangles sharing a vertex are
never paired, matching the pose test's exclusion of adjacent faces.
"""
from __future__ import annotations

import numpy as np


def seg_tri_hit(p0, p1, v0, v1, v2, eps=1e-12):
    e1, e2, d = v1 - v0, v2 - v0, p1 - p0
    h = np.cross(d, e2)
    a = (e1 * h).sum(-1)
    ok = np.abs(a) > eps
    f = np.where(ok, 1.0 / np.where(ok, a, 1.0), 0.0)
    s = p0 - v0
    u = f * (s * h).sum(-1)
    q = np.cross(s, e1)
    v = f * (d * q).sum(-1)
    t = f * (e2 * q).sum(-1)
    return ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t >= 0) & (t <= 1)


def tri_pairs_intersecting(P, tris, cand_tris, radius=0.03, chunk=400):
    """Return intersecting (i, j) index pairs (i < j) among cand_tris for vertex positions P."""
    T = tris[cand_tris]
    C = P[T].mean(axis=1)
    out = []
    for i0 in range(0, len(T), chunk):
        D = np.linalg.norm(C[i0:i0 + chunk, None] - C[None], axis=2)
        ii, jj = np.nonzero(D < radius)
        ii += i0
        keep = ii < jj
        ii, jj = ii[keep], jj[keep]
        share = (T[ii][:, :, None] == T[jj][:, None, :]).any(axis=(1, 2))
        ii, jj = ii[~share], jj[~share]
        if not len(ii):
            continue
        A, B = P[T[ii]], P[T[jj]]
        hit = np.zeros(len(ii), bool)
        for k in range(3):
            a0, a1 = A[:, k], A[:, (k + 1) % 3]
            hit |= seg_tri_hit(a0, a1, B[:, 0], B[:, 1], B[:, 2])
            b0, b1 = B[:, k], B[:, (k + 1) % 3]
            hit |= seg_tri_hit(b0, b1, A[:, 0], A[:, 1], A[:, 2])
        out.append(np.c_[cand_tris[ii[hit]], cand_tris[jj[hit]]])
    return np.concatenate(out) if out else np.zeros((0, 2), int)
