"""Surface-walking skin slide for ORIGINAL_v1 review candidates (numpy; no bpy).  R24 (Claude, 15 Oct 2026).

Owner, choosing to keep researching an automatic fix for the press-lockout shoulder: "2".  At lockout the deltoid region
holds more skin than the shape can take, while the armpit and side of the chest are short of skin.  Real skin slides from
one to the other.  Here vertices live on a fixed reference surface S as (face, barycentric).  Each step moves them along
S by walking across triangle edges, with the remaining displacement unfolded into the next face.  So no vertex can jump
through a crease: snapping to the nearest surface point did, giving 2,360 self-intersecting pairs.  A step is undone if it
would turn an incident triangle over (normal against the reference) or crush it below 15 % of its rest area.
Energy: sum over faces of (area / rest area - 1)^2.
"""
import math
import numpy as np


class Walker:
    def __init__(self, S, F):
        self.S = S; self.F = F
        e2f = {}
        for fi, f in enumerate(F):
            for k in range(3):
                e2f.setdefault(frozenset((f[k], f[(k + 1) % 3])), []).append(fi)
        self.adj = np.full((len(F), 3), -1)            # neighbour across the edge opposite local vertex k
        for fi, f in enumerate(F):
            for k in range(3):
                e = frozenset((f[(k + 1) % 3], f[(k + 2) % 3]))
                for g in e2f[e]:
                    if g != fi:
                        self.adj[fi, k] = g
        N = np.cross(S[F[:, 1]] - S[F[:, 0]], S[F[:, 2]] - S[F[:, 0]])
        self.N = N / np.maximum(np.linalg.norm(N, axis=1)[:, None], 1e-15)

    def bary(self, f, p):
        a, b, c = self.S[self.F[f]]
        v0, v1, v2 = b - a, c - a, p - a
        d00, d01, d11 = v0 @ v0, v0 @ v1, v1 @ v1
        d20, d21 = v2 @ v0, v2 @ v1
        den = d00 * d11 - d01 * d01
        if abs(den) < 1e-20:
            return np.array([1.0, 0.0, 0.0])
        v = (d11 * d20 - d01 * d21) / den
        w = (d00 * d21 - d01 * d20) / den
        return np.array([1 - v - w, v, w])

    def point(self, f, bc):
        return bc @ self.S[self.F[f]]

    def walk(self, f, bc, d, hops=24):
        for _ in range(hops):
            n = self.N[f]
            d = d - n * (n @ d)
            p = self.point(f, bc)
            q = p + d
            bq = self.bary(f, q)
            if bq.min() >= -1e-9:
                return f, np.clip(bq, 0, None) / max(np.clip(bq, 0, None).sum(), 1e-15)
            t, k = 1.0, -1
            for i in range(3):
                if bq[i] < 0 and bc[i] - bq[i] > 1e-15:
                    ti = bc[i] / (bc[i] - bq[i])
                    if ti < t:
                        t, k = ti, i
            if k < 0:
                return f, bc
            pe = p + d * t
            g = self.adj[f, k]
            if g < 0:                                    # mesh boundary: stop on the edge
                return f, self.bary(f, pe)
            # unfold the remaining displacement into g's plane (rotation about the shared edge)
            rem = d * (1 - t)
            ng = self.N[g]
            axis = np.cross(n, ng)
            s = np.linalg.norm(axis)
            if s > 1e-12:
                axis /= s
                ang = math.atan2(s, float(n @ ng))
                rem = (rem * math.cos(ang) + np.cross(axis, rem) * math.sin(ang)
                       + axis * (axis @ rem) * (1 - math.cos(ang)))
            f = g
            bc = self.bary(f, pe)
            bc = np.clip(bc, 0, None); bc /= max(bc.sum(), 1e-15)
            d = rem
        return f, bc


def slide(S, F, A0, idx, wfree, iters=80, eta=1.0, cap=0.0015, log=None):
    """Returns the slid positions X (on S).  idx: vertices allowed to move; wfree: per-vertex step weight."""
    Wk = Walker(S, F)
    nv = len(S)
    host = np.full(nv, -1)
    bcs = np.zeros((nv, 3))
    for fi, f in enumerate(F):
        for k in range(3):
            if host[f[k]] < 0:
                host[f[k]] = fi
                b = np.zeros(3); b[k] = 1.0
                bcs[f[k]] = b
    X = S.copy()
    vf = [[] for _ in range(nv)]
    for fi, f in enumerate(F):
        for k in range(3):
            vf[f[k]].append(fi)
    N0 = np.cross(S[F[:, 1]] - S[F[:, 0]], S[F[:, 2]] - S[F[:, 0]])
    N0 /= np.maximum(np.linalg.norm(N0, axis=1)[:, None], 1e-15)
    rejected = [0]

    def ok(i, xi):
        """No incident triangle may turn over (normal vs the reference surface) or drop below 15 % of its rest area."""
        for fi in vf[i]:
            f = F[fi]
            pts = [xi if v == i else X[v] for v in f]
            n = np.cross(pts[1] - pts[0], pts[2] - pts[0])
            a = np.linalg.norm(n) / 2
            if a < 0.15 * A0[fi] or (n @ N0[fi]) <= 0.5 * np.linalg.norm(n):
                return False
        return True
    for it in range(iters):
        A = np.linalg.norm(np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]]), axis=1) / 2
        r = A / A0
        N = np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]])
        N /= np.maximum(np.linalg.norm(N, axis=1)[:, None], 1e-15)
        g = np.zeros_like(X)
        coef = (2 * (r - 1) / A0)[:, None]
        for c in range(3):
            i, j, k = F[:, c], F[:, (c + 1) % 3], F[:, (c + 2) % 3]
            np.add.at(g, i, coef * 0.5 * np.cross(N, X[k] - X[j]))
        # per-vertex normalised step: move each vertex a little along -grad (scale-free), capped
        moved = 0
        for i in idx:
            gi = -g[i]
            m = np.linalg.norm(gi)
            if m < 1e-12:
                continue
            step = gi / m * min(cap, eta * cap * wfree[i])
            f2, b2 = Wk.walk(host[i], bcs[i], step)
            xi = Wk.point(f2, b2)
            if not ok(i, xi):
                rejected[0] += 1
                continue
            host[i], bcs[i] = f2, b2
            X[i] = xi
            moved += 1
        if log is not None and it % 20 == 0:
            log.append((it, round(float(((r - 1) ** 2).sum()), 1), rejected[0]))
    return X
