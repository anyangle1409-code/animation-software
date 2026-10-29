"""Surface-walking skin slide, vectorised (numpy; no bpy).

The algorithm is r57's original_v1_skin_slide.slide (R24): vertices live on a fixed reference surface S as (face,
barycentric) and move along it by walking across triangle edges, the remaining displacement unfolded into the next face,
so no vertex can jump through a crease.  Each iteration every free vertex takes one step of length
min(cap, eta * cap * wfree) down the gradient of sum_faces (area / rest area - 1)^2 (gradient taken at the start of the
iteration), and a step is undone if it would turn an incident triangle more than 60 deg against the reference or crush it
below 15 % of its rest area (unless it makes an already-crushed triangle larger).

r57 walks one vertex at a time in Python (~390 us per vertex step: ~35 min for 80k vertices x 60 iterations).  Here
the free vertices are split into colour classes - no two vertices of a class share a triangle - and each class walks
and is guarded at once: within a class a vertex's guard only sees vertices that do not move in that sub-step, so the
guard is exact as in the sequential version (only the visiting order differs).

Measured on a 3 mm test grid (36 cm square, a compressed blob): the same result as r57 (energy 651 -> 5546 vs 5649 after
20 iterations, same rejections, on the surface to 0.014 mm) in 1.4 s instead of 68 s.  The energy RISES with r57's
step (1.5 mm, scale-free) on a mesh this fine; eta 0.1 or the preconditioned step (alpha) are stable but local, so the
relief spreads like diffusion (651 -> 580 in 150 iterations).  Slider carries out a given displacement field with the
same walking and guard (used by skin_slide_mvc_prototype_blender.py, method mvcwalk).
"""
import numpy as np


class Surface:
    def __init__(self, S, F):
        self.S = np.asarray(S, float); self.F = np.asarray(F)
        nf = len(self.F)
        # neighbour across the edge opposite local vertex k
        a = self.F[:, [1, 2, 0]].ravel(); b = self.F[:, [2, 0, 1]].ravel()
        key = np.minimum(a, b).astype(np.int64) * (len(self.S) + 1) + np.maximum(a, b)
        o = np.argsort(key, kind="stable"); ks = key[o]
        self.adj = np.full(nf * 3, -1)
        same = np.flatnonzero(ks[1:] == ks[:-1])
        for s0 in (same,):                                   # manifold pairs (an edge with 3+ faces keeps the first pair)
            i0, i1 = o[s0], o[s0 + 1]
            first = np.r_[True, ks[s0[1:]] != ks[s0[:-1]]] if len(s0) else np.zeros(0, bool)
            i0, i1 = i0[first], i1[first]
            self.adj[i0] = i1 // 3; self.adj[i1] = i0 // 3
        self.adj = self.adj.reshape(nf, 3)
        N = np.cross(self.S[self.F[:, 1]] - self.S[self.F[:, 0]], self.S[self.F[:, 2]] - self.S[self.F[:, 0]])
        self.N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-15)

    def bary(self, f, p):
        T = self.S[self.F[f]]
        a, b, c = T[:, 0], T[:, 1], T[:, 2]
        v0, v1, v2 = b - a, c - a, p - a
        d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1)
        d20 = (v2 * v0).sum(1); d21 = (v2 * v1).sum(1)
        den = d00 * d11 - d01 * d01
        ok = np.abs(den) >= 1e-20
        den = np.where(ok, den, 1.0)
        v = (d11 * d20 - d01 * d21) / den; w = (d00 * d21 - d01 * d20) / den
        out = np.c_[1 - v - w, v, w]
        out[~ok] = (1.0, 0.0, 0.0)
        return out

    def point(self, f, bc):
        return np.einsum("ij,ijk->ik", bc, self.S[self.F[f]])

    def walk(self, f, bc, d, hops=24):
        f = f.copy(); bc = bc.copy(); d = d.copy()
        act = np.ones(len(f), bool)
        for _ in range(hops):
            ia = np.flatnonzero(act)
            if not len(ia):
                break
            n = self.N[f[ia]]
            da = d[ia] - n * (n * d[ia]).sum(1)[:, None]
            p = self.point(f[ia], bc[ia]); q = p + da
            bq = self.bary(f[ia], q)
            inside = bq.min(1) >= -1e-9
            if inside.any():
                j = ia[inside]; c_ = np.clip(bq[inside], 0, None)
                bc[j] = c_ / np.maximum(c_.sum(1), 1e-15)[:, None]; act[j] = False
            out = ~inside
            if not out.any():
                break
            jo = ia[out]; bco, bqo = bc[jo], bq[out]
            den = bco - bqo
            cand = (bqo < 0) & (den > 1e-15)
            t = np.where(cand, bco / np.where(cand, den, 1.0), np.inf)
            k = np.argmin(t, axis=1); tk = t[np.arange(len(jo)), k]
            stop = ~np.isfinite(tk) | (tk >= 1.0)
            act[jo[stop]] = False                                 # no crossing found: stay
            go = ~stop
            jo, k, tk = jo[go], k[go], tk[go]
            if not len(jo):
                continue
            po, dao, no = p[out][go], da[out][go], n[out][go]
            pe = po + dao * tk[:, None]
            g = self.adj[f[jo], k]
            edge = g < 0                                          # mesh boundary: stop on the edge
            if edge.any():
                je = jo[edge]; bc[je] = self.bary(f[je], pe[edge]); act[je] = False
            m = ~edge
            jo, g, pe, rem, no = jo[m], g[m], pe[m], (dao * (1 - tk)[:, None])[m], no[m]
            ng = self.N[g]
            axis = np.cross(no, ng); s = np.linalg.norm(axis, axis=1)
            rot = s > 1e-12
            ax = axis[rot] / s[rot][:, None]
            ang = np.arctan2(s[rot], (no[rot] * ng[rot]).sum(1))
            r_ = rem[rot]
            rem[rot] = (r_ * np.cos(ang)[:, None] + np.cross(ax, r_) * np.sin(ang)[:, None]
                        + ax * (ax * r_).sum(1)[:, None] * (1 - np.cos(ang))[:, None])
            f[jo] = g
            c_ = np.clip(self.bary(g, pe), 0, None)
            bc[jo] = c_ / np.maximum(c_.sum(1), 1e-15)[:, None]
            d[jo] = rem
        return f, bc


def colour_classes(F, idx, nv):
    """greedy colouring of the free vertices: two vertices of one class never share a triangle"""
    nb = [[] for _ in range(nv)]
    for c in range(3):
        a, b = F[:, c], F[:, (c + 1) % 3]
        for x, y in zip(a, b):
            nb[x].append(y); nb[y].append(x)
    col = np.full(nv, -1)
    for i in idx:
        used = {col[j] for j in nb[i] if col[j] >= 0}
        c = 0
        while c in used:
            c += 1
        col[i] = c
    return [idx[col[idx] == c] for c in range(col[idx].max() + 1)] if len(idx) else []


class Slider:
    """vertices held on the reference surface as (face, barycentric); move() walks a set of vertices by given
    displacements, colour class by colour class, undoing any step that turns an incident triangle more than 60 deg
    against the reference or crushes it below 15 % of its rest area (unless it grows an already-crushed one)"""

    def __init__(self, S, F, A0):
        self.surf = Surface(S, F); F = self.surf.F; S = self.surf.S
        self.F, self.A0, nv = F, A0, len(S)
        self.host = np.full(nv, -1); self.bcs = np.zeros((nv, 3))
        for k in (2, 1, 0):                                      # first face containing each vertex
            self.host[F[:, k][::-1]] = np.arange(len(F))[::-1]
        for k in range(3):
            m = F[self.host, k] == np.arange(nv)
            self.bcs[m] = 0.0; self.bcs[m, k] = 1.0
        self.X = S.copy()
        vf_v = F.ravel(); vf_f = np.repeat(np.arange(len(F)), 3)
        o = np.argsort(vf_v, kind="stable"); self.vf_f = vf_f[o]
        self.ptr = np.searchsorted(vf_v[o], np.arange(nv + 1))
        self.rejected = 0

    def move(self, v, step):
        F, X = self.F, self.X
        f2, b2 = self.surf.walk(self.host[v], self.bcs[v], step)
        xi = self.surf.point(f2, b2)
        cnt = self.ptr[v + 1] - self.ptr[v]
        owner = np.repeat(np.arange(len(v)), cnt)
        fi = self.vf_f[np.concatenate([np.arange(self.ptr[a], self.ptr[a + 1]) for a in v])] if len(v) else np.zeros(0, int)
        P3 = X[F[fi]].copy()
        slot = F[fi] == v[owner][:, None]
        P3[slot] = xi[owner]
        nn = np.cross(P3[:, 1] - P3[:, 0], P3[:, 2] - P3[:, 0]); nl = np.linalg.norm(nn, axis=1)
        bad = (nn * self.surf.N[fi]).sum(1) <= 0.5 * nl
        a_new = nl / 2
        crushed = a_new < 0.15 * self.A0[fi]
        if crushed.any():
            Q = X[F[fi[crushed]]]
            a_old = np.linalg.norm(np.cross(Q[:, 1] - Q[:, 0], Q[:, 2] - Q[:, 0]), axis=1) / 2
            bad[np.flatnonzero(crushed)[a_new[crushed] <= a_old]] = True
        rej = np.zeros(len(v), bool); np.logical_or.at(rej, owner, bad)
        acc = ~rej
        self.host[v[acc]] = f2[acc]; self.bcs[v[acc]] = b2[acc]; X[v[acc]] = xi[acc]
        self.rejected += int(rej.sum())
        return rej

    def apply(self, disp, classes, sub=1):
        """walk every vertex of the classes by its displacement, in `sub` equal sub-steps (a rejected sub-step leaves
        the vertex where it is; the later sub-steps still try)"""
        rej = np.zeros(len(self.X), int)
        for _ in range(sub):
            for cls in classes:
                r = self.move(cls, disp[cls] / sub)
                rej[cls[r]] += 1
        return rej


def slide(S, F, A0, idx, wfree, iters=80, eta=1.0, cap=0.0015, log=None, crush_w=0.0, gq=None, decay=1.0, alpha=None):
    """Returns the slid positions X (on S).  idx: vertices allowed to move; wfree: per-vertex step weight.
    r57 steps are scale-free (every vertex moves the full step whatever its gradient), which on a ~3 mm mesh at a
    1.5 mm step jitters and RAISES the energy (measured); gq (0-100) makes the step proportional to the gradient up to
    the q-th percentile of the first iteration's free-vertex gradients (full step above it); decay shrinks the step
    each iteration.  alpha (instead): a diagonally preconditioned step -alpha * wfree * g / H, H = sum over incident
    faces of 2 (|opposite edge| / (2 rest area))^2 (the energy's curvature along the vertex's own motion), capped at
    cap - dimensionally a length that scales with the local mesh, so it neither stalls nor overshoots."""
    S = np.asarray(S, float); F = np.asarray(F); idx = np.asarray(idx)
    nv = len(S)
    surf = Surface(S, F)
    host = np.full(nv, -1); bcs = np.zeros((nv, 3))
    for k in (2, 1, 0):                                          # first face containing each vertex
        host[F[:, k][::-1]] = np.arange(len(F))[::-1]
    for k in range(3):
        m = F[host, k] == np.arange(nv)
        bcs[m] = 0.0; bcs[m, k] = 1.0
    X = S.copy()
    # vertex -> incident faces (CSR)
    vf_v = F.ravel(); vf_f = np.repeat(np.arange(len(F)), 3)
    o = np.argsort(vf_v, kind="stable"); vf_v, vf_f = vf_v[o], vf_f[o]
    ptr = np.searchsorted(vf_v, np.arange(nv + 1))
    N0 = surf.N
    classes = colour_classes(F, idx, nv)
    rejected = 0
    G0 = None
    for it in range(iters):
        e1, e2 = X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]]
        Nn = np.cross(e1, e2); A = np.linalg.norm(Nn, axis=1) / 2
        N = Nn / np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-15)
        r = A / A0
        coef = (2 * (r - 1) / A0)[:, None]
        if crush_w > 0:
            coef -= (crush_w * 2 * np.maximum(0.3 - r, 0.0) / A0)[:, None]
        g = np.zeros_like(X)
        for c in range(3):
            i, j, k = F[:, c], F[:, (c + 1) % 3], F[:, (c + 2) % 3]
            np.add.at(g, i, coef * 0.5 * np.cross(N, X[k] - X[j]))
        if alpha is not None:
            Hd = np.zeros(nv)
            for c in range(3):
                el = np.linalg.norm(X[F[:, (c + 2) % 3]] - X[F[:, (c + 1) % 3]], axis=1)
                np.add.at(Hd, F[:, c], 2 * (0.5 * el / A0) ** 2)
        if gq is not None and G0 is None:
            G0 = max(float(np.percentile(np.linalg.norm(g[idx], axis=1), gq)), 1e-12)
        for cls in classes:
            gi = -g[cls]; m = np.linalg.norm(gi, axis=1)
            mv = m >= 1e-12
            v = cls[mv]
            if not len(v):
                continue
            if alpha is not None:
                ln = np.minimum(cap, alpha * wfree[v] * m[mv] / np.maximum(Hd[v], 1e-12)) * decay ** it
            else:
                ln = np.minimum(cap, eta * cap * wfree[v]) * decay ** it
            if gq is not None:
                ln = ln * np.minimum(1.0, m[mv] / G0)
            step = gi[mv] / m[mv][:, None] * ln[:, None]
            f2, b2 = surf.walk(host[v], bcs[v], step)
            xi = surf.point(f2, b2)
            # guard: every incident face of each moving vertex, with that vertex at its new position
            cnt = ptr[v + 1] - ptr[v]
            owner = np.repeat(np.arange(len(v)), cnt)
            fi = vf_f[np.concatenate([np.arange(ptr[a], ptr[a + 1]) for a in v])] if len(v) else np.zeros(0, int)
            P3 = X[F[fi]].copy()
            slot = F[fi] == v[owner][:, None]
            P3[slot] = xi[owner]
            nn = np.cross(P3[:, 1] - P3[:, 0], P3[:, 2] - P3[:, 0]); nl = np.linalg.norm(nn, axis=1)
            bad = (nn * N0[fi]).sum(1) <= 0.5 * nl
            a_new = nl / 2
            crushed = a_new < 0.15 * A0[fi]
            if crushed.any():
                Q = X[F[fi[crushed]]]
                a_old = np.linalg.norm(np.cross(Q[:, 1] - Q[:, 0], Q[:, 2] - Q[:, 0]), axis=1) / 2
                bad[np.flatnonzero(crushed)[a_new[crushed] <= a_old]] = True
            rej = np.zeros(len(v), bool); np.logical_or.at(rej, owner, bad)
            acc = ~rej
            host[v[acc]] = f2[acc]; bcs[v[acc]] = b2[acc]; X[v[acc]] = xi[acc]
            rejected += int(rej.sum())
        if log is not None and it % 20 == 0:
            log.append((it, round(float(((r - 1) ** 2).sum()), 1), rejected))
    return X
