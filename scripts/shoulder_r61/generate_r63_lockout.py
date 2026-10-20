"""R63 unsaved press candidate: posed-space lockout sculpt for 146-166 deg (Claude, 20 Oct 2026).

Owner, on R60/R61 at 156 deg: from ~148 deg to the top the arm stops flowing into the body and a dip appears under the
arm; R61 (holding the REST-space fill to lockout) pushed skin into the arm (contacts 7 -> 165).  Owner: "go ahead with the
lockout sculpt" (20 Oct).

Work's R52 data gives, for every recorded press pose s, the posed skin as an exact affine function of the 72 one-degree S7
controls:  posed_s = base_s + mat_s @ blend(dense, decode(weight_s))  (verified natively to 0.01 mm by the gates).  So the
lockout shape is designed IN THE POSED POSE and solved back:

  1. start from the R62b candidate (R60 smoothing + 15 mm upper-trapezius bunching);
  2. for each press sample with elevation >= --from, compute the posed skin; per side, seen from behind (u = outward, z = up),
     fit a straight line to the outer edge of the raised upper arm and push the side of the torso below the armpit out to
     it (gain, fading over --depth below the armpit and with distance in from the torso outline, Gaussian --sigma), the
     R29 LAT_WEB construction that matched the owner's reference; ramp in with elevation from --from to --full;
  3. smooth that push over the mesh;
  4. per affected vertex, least-squares solve the controls 146..166 so the posed skin at those samples reaches the target,
     with a temporal second-difference penalty (continuity with 144/145 kept) and a weak tie to the start values.

Controls <= 145 (incl. the approved marked pose) are untouched.  95/110 stay zero; 166 is released (owner, 20 Oct).
Nothing is saved to a .blend.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

K0, K1 = 51, 71                      # controls 146 .. 166 by default (index = deg - 95); K0 follows --from


def ht_of(t):
    k = np.clip(t, 0, 1)
    return 70.0 + 96.0 * k * k * (3 - 2 * k)


def smoothstep(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def neighbour_mean(faces, nv):
    """sparse row-normalised vertex adjacency: (Avg @ X)[i] = mean of X over i's one-ring"""
    from scipy.sparse import coo_matrix, diags
    e = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    e = np.unique(np.sort(e, axis=1), axis=0)
    r = np.concatenate([e[:, 0], e[:, 1]]); c = np.concatenate([e[:, 1], e[:, 0]])
    A = coo_matrix((np.ones(len(r)), (r, c)), shape=(nv, nv)).tocsr()
    deg = np.asarray(A.sum(1)).ravel()
    return diags(1.0 / np.maximum(deg, 1)) @ A


def upper_hull(z, u):
    """R64b: outward (max-u) convex envelope of outline points (z, u), as a function of z"""
    o = np.argsort(z); pts = []
    for p in zip(z[o], u[o]):
        while len(pts) >= 2 and (pts[-1][0] - pts[-2][0]) * (p[1] - pts[-2][1]) - (pts[-1][1] - pts[-2][1]) * (p[0] - pts[-2][0]) >= 0:
            pts.pop()
        pts.append(p)
    h = np.array(pts)
    return lambda q: np.interp(q, h[:, 0], h[:, 1])


def lat_fill(P, armw, wholearm, gain, depth, sigma, maxpush, torso_max=0.3, top=0.02, hull=False, bulge=0.0, bulge_span=0.15):
    D = np.zeros_like(P)
    info = {}
    for k, side in enumerate("lr"):
        sg = -1.0 if side == "l" else 1.0
        u = sg * P[:, 0]; z = P[:, 2]
        arm = armw[k] >= 0.5
        if arm.sum() < 50:
            continue
        za0, za1 = np.percentile(z[arm], [5, 95])
        zz, uu = [], []
        for z0 in np.arange(za0 + 0.03, za1 - 0.03, 0.01):
            m = arm & (z >= z0) & (z < z0 + 0.01)
            if m.sum() > 2:
                zz.append(z0 + 0.005); uu.append(u[m].max())
        if len(zz) < 4:
            continue
        b, a = np.polyfit(zz, uu, 1)
        torso = (wholearm[k] < torso_max) & (u > 0.03)   # R63e: torso_max 0.7 lets the shared arm/torso corner skin move
        if hull:
            # R64b (owner, 20 Oct: the arm-to-back outline steps in under the arm at lockout; references show one smooth
            # convex line): the wanted outline is the outward convex envelope, seen from behind, of the whole skin outline
            # from --depth below the armpit to the arm's top, so arm edge and back join in one curve with no notch.
            outl = u > 0.03
            hz, hu = [], []
            for z0 in np.arange(za0 - depth, za1, 0.01):
                m = outl & (z >= z0) & (z < z0 + 0.01)
                if m.sum() > 2:
                    hz.append(z0 + 0.005); hu.append(u[m].max())
            env = upper_hull(np.array(hz), np.array(hu))
        pushes = []
        for z0 in np.arange(za0 - depth, za0 + top, 0.01):   # R63e: top 0.06 fills up into the corner under the arm
            m = np.flatnonzero(torso & (z >= z0) & (z < z0 + 0.01))
            if len(m) < 3:
                continue
            edge = u[m].max(); want = env(z0 + 0.005) if hull else a + b * (z0 + 0.005)
            if hull and bulge > 0 and za0 - bulge_span <= z0 + 0.005 <= za0:
                # R65 (owner photos, 20 Oct): the upper back is widest just under the arms (lat + teres major), so the
                # outline below the armpit bulges out by up to --lat-bulge before narrowing to the waist
                want += bulge * np.sin(np.pi * (za0 - z0 - 0.005) / bulge_span)
            fade = smoothstep((z0 - (za0 - depth)) / (0.4 * depth))
            d = min(max(want - edge, 0.0) * gain * fade, maxpush)
            if d <= 0:
                continue
            f = np.exp(-((edge - u[m]) / sigma) ** 2)
            D[m, 0] = sg * np.maximum(sg * D[m, 0], d * f)
            pushes.append(d)
        info[side] = {"arm_edge_deg_from_vertical": round(float(np.degrees(np.arctan(abs(b)))), 1),
                      "armpit_z": round(float(za0), 3), "max_push_mm": round(float(max(pushes, default=0) * 1000), 1)}
    return D, info


def vertex_normals(P, faces):
    n = np.cross(P[faces[:, 1]] - P[faces[:, 0]], P[faces[:, 2]] - P[faces[:, 0]])
    vn = np.zeros_like(P)
    for j in range(3):
        np.add.at(vn, faces[:, j], n)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)


def fold_region(rest, centre, radius):
    """R64: rest-space weight (1 at the posterior-armpit centre, 0 at radius) for both sides (centre given for the left, x<0)"""
    w = np.zeros(len(rest))
    for sg in (-1.0, 1.0):
        c = np.array([sg * abs(centre[0]), centre[1], centre[2]])
        w = np.maximum(w, smoothstep(1.0 - np.linalg.norm(rest - c, axis=1) / radius))
    return w


def root_region(rest, armw, Avg, passes=20):
    """R65: rest-space weight for the lower/back half of the arm-root blend ring (upper-arm weight ~0.5), both sides"""
    w = np.zeros(len(rest))
    for k, sg in enumerate((-1.0, 1.0)):
        a_ = armw[k]
        ring = (a_ > 0.15) & (a_ < 0.85)
        if ring.sum() < 10:
            continue
        zc = np.median(rest[ring, 2])
        r = np.clip(1.0 - np.abs(2.0 * a_ - 1.0), 0, 1)
        low = smoothstep((zc + 0.02 - rest[:, 2]) / 0.04)          # under-arm half of the ring
        back = smoothstep((rest[:, 1] + 0.02) / 0.06)              # posterior (+y is the back)
        w = np.maximum(w, r * low * back * (sg * rest[:, 0] > 0))
    for _ in range(passes):
        w = 0.5 * w + 0.5 * (Avg @ w)
    return w / max(w.max(), 1e-12)


def fold_fill(Q, faces, Avg, w, iters, step, maxpush):
    """R64 posterior axillary fold (owner, 20 Oct: the arm-to-back join at lockout dips in and crumples; anatomy references
    show one smooth convex band of latissimus + teres major from the arm's underside into the back, no notch).
    Outward-only Laplacian: each pass moves a region vertex by the tangential part of (neighbour mean - vertex) - which
    evens out the crumpled facets - plus the normal part ONLY where it points outward, i.e. where the vertex sits in a dent.
    Bumps are never pushed in, dents are filled, so the patch converges to a taut convex skin bridging arm and back."""
    Q0 = Q.copy(); Q = Q.copy()
    for _ in range(iters):
        n = vertex_normals(Q, faces)
        L = Avg @ Q - Q
        ln = np.einsum("ij,ij->i", L, n)
        Q = Q + (step * w)[:, None] * (L - np.minimum(ln, 0.0)[:, None] * n)
    D = Q - Q0
    Dn = np.linalg.norm(D, axis=1)
    return D * np.minimum(1.0, maxpush / np.maximum(Dn, 1e-12))[:, None]


def main():
    ap = argparse.ArgumentParser()
    for a in ("--r57src", "--response", "--start", "--out"):
        ap.add_argument(a, required=True)
    ap.add_argument("--arm", default=str(Path(__file__).resolve().parent / "r63_arm_weights.npz"))
    ap.add_argument("--gain", type=float, default=0.6)
    ap.add_argument("--depth", type=float, default=0.25)
    ap.add_argument("--sigma", type=float, default=0.05)
    ap.add_argument("--maxpush", type=float, default=0.04)
    ap.add_argument("--from", dest="hfrom", type=float, default=146.0)
    ap.add_argument("--full", type=float, default=152.0)
    ap.add_argument("--smooth", type=int, default=30)
    ap.add_argument("--lam", type=float, default=0.3)
    ap.add_argument("--tie", type=float, default=0.02)
    ap.add_argument("--arm-margin", type=float, default=0.008, help="R63b: keep pushed torso skin this far (m) from the arm")
    ap.add_argument("--torso-max", type=float, default=0.3, help="R63e: skin with whole-arm weight below this may be pushed")
    ap.add_argument("--top", type=float, default=0.02, help="R63e: fill up to this far (m) above the armpit")
    ap.add_argument("--include-bench", action="store_true", help="R63f: also solve against the benchmark press samples 41..81")
    ap.add_argument("--guard-bench", action="store_true", help="R63g: benchmark press samples only guard against arm contact")
    ap.add_argument("--guard-weight", type=float, default=4.0)
    ap.add_argument("--guard-iters", type=int, default=6)
    ap.add_argument("--lat-bulge", type=float, default=0.0, help="R65: outline bulge (m) just under the armpit (hull mode)")
    ap.add_argument("--lat-bulge-span", type=float, default=0.15)
    ap.add_argument("--root-mm", type=float, default=0.0, help="R65: inflate the posterior arm root by this much (mm) along the posed normal")
    ap.add_argument("--step-limit", type=float, default=0.0, help="R64j: smooth solved control curves until adjacent steps <= this (m)")
    ap.add_argument("--hull", action="store_true", help="R64b: fill the rear outline to its outward convex envelope")
    ap.add_argument("--fold", action="store_true", help="R64: sculpt the posterior axillary fold (outward-only relax)")
    ap.add_argument("--fold-centre", default="0.17,0.07,1.40", help="R64: rest-space centre of the posterior armpit (m)")
    ap.add_argument("--fold-radius", type=float, default=0.10)
    ap.add_argument("--fold-iters", type=int, default=80)
    ap.add_argument("--fold-step", type=float, default=0.5)
    ap.add_argument("--fold-max", type=float, default=0.025)
    a = ap.parse_args()
    global K0
    # R63c: the first solved control follows --from; never at or below 136 deg (the marked pose uses controls 135/136)
    K0 = max(int(np.ceil(a.hfrom)) - 95, 42)
    sys.path[:0] = [str(Path(a.r57src) / "scripts")]
    from original_review_r52_temporal import decode, oscillation

    z = np.load(a.response)
    rest, faces = z["rest"], z["faces"]
    nv = len(rest)
    d0 = np.load(a.start)["dense_delta"].astype(float)
    arm = np.load(a.arm)
    ci = arm["check_ids"].astype(int)
    dpos = float(np.abs(arm["check_rest"] - rest[ci]).max() * 1000)
    assert dpos < 1.0, f"arm weight file does not match the source rest mesh ({dpos:.3f} mm)"
    armw = arm["upperarm_weight"].astype(float); whole = arm["whole_arm_weight"].astype(float)
    Avg = neighbour_mean(faces, nv)
    root_w = root_region(rest, armw, Avg) if a.root_mm > 0 else None
    fold_w = fold_region(rest, [float(c) for c in a.fold_centre.split(",")], a.fold_radius) if a.fold else None

    samples = [s for s in range(41) if ht_of(s / 40) >= a.hfrom - 1.0]
    sample_ht = {s: ht_of(s / 40) for s in samples}
    guard_samples = set()
    if a.include_bench or a.guard_bench:
        # R63f: the gates also pose the benchmark shoulder-press path (samples 41..81); R63e's corner fill touched the arm
        # there (18 new arm/torso contacts at samples 77-81).  Include every benchmark sample that uses the solved controls,
        # with its elevation read from Work's decoded control weights, so the fill is solved against both paths.
        for s in range(41, 82):
            lo_, hi_, t_ = decode(z["weight"][s][None])
            e = float(np.median(95.0 + lo_[0] + t_[0]))
            if e >= a.hfrom - 1.0:
                samples.append(s); sample_ht[s] = e
                if a.guard_bench:
                    guard_samples.add(s)
    targets, maps, report_s = {}, {}, []
    for s in samples:
        lo, hi, t = decode(z["weight"][s][None])
        lo, hi, t = lo[0].astype(int), hi[0].astype(int), t[0]
        maps[s] = (lo, hi, t)
        v = np.arange(nv)
        inc = (1 - t)[:, None] * d0[lo, v] + t[:, None] * d0[hi, v]
        P = z["base"][s] + np.einsum("nij,nj->ni", z["mat"][s], inc)
        D, info = lat_fill(P, armw, whole, a.gain, a.depth, a.sigma, a.maxpush, a.torso_max, a.top, a.hull, a.lat_bulge, a.lat_bulge_span)
        if a.arm_margin > 0 and np.abs(D).sum() > 0:
            # R63b: never push torso skin into the arm - cap each vertex's push (and its 30-pass smoothing spread) at its
            # posed distance to the nearest upper-arm skin minus --arm-margin (R63 without this: contacts 7 -> 215)
            from scipy.spatial import cKDTree
            armpts = np.flatnonzero(np.maximum(armw[0], armw[1]) >= max(0.3, a.torso_max))
            dist, _ = cKDTree(P[armpts]).query(P, k=1)
            room = np.maximum(dist - a.arm_margin, 0.0)
            room[armpts] = 0.0
            Dn = np.linalg.norm(D, axis=1)
            scale = np.where(Dn > room, room / np.maximum(Dn, 1e-12), 1.0)
            D *= scale[:, None]
            info["arm_cap_vertices"] = int((scale < 1).sum())
        ramp = smoothstep((sample_ht[s] - a.hfrom) / (a.full - a.hfrom))
        D *= ramp
        if np.abs(D).sum() > 0:
            for _ in range(a.smooth):
                D = 0.5 * D + 0.5 * (Avg @ D)
            if a.arm_margin > 0:
                Dn = np.linalg.norm(D, axis=1)          # smoothing must not spread the push back into the arm
                D *= np.where(Dn > room, room / np.maximum(Dn, 1e-12), 1.0)[:, None]
        fold_mm = 0.0
        if fold_w is not None and ramp > 0 and s not in guard_samples:
            # R64: no arm-distance cap here - that cap (distance to the arm skin) is ~0 right at the arm/back join and is
            # what kept R63g's notch; the outward-only relax only smooths/fills, and the benchmark guard still runs below.
            Df = fold_fill(P + D, faces, Avg, fold_w, a.fold_iters, a.fold_step, a.fold_max) * ramp
            D = D + Df
            fold_mm = float(np.linalg.norm(Df, axis=1).max() * 1000)
        root_max = 0.0
        if root_w is not None and ramp > 0 and s not in guard_samples:
            # R65 (owner photos): the arm stays thick into the body; the posterior deltoid, the arm's underside and the
            # top of the lat merge into one rounded mass - inflate the back/under half of the arm-root ring
            Dr = vertex_normals(P + D, faces) * (a.root_mm / 1000.0 * ramp * root_w)[:, None]
            D = D + Dr
            root_max = float(np.linalg.norm(Dr, axis=1).max() * 1000)
        targets[s] = (P, D)
        report_s.append({"sample": s, "ht_deg": round(float(sample_ht[s]), 2), "ramp": round(float(ramp), 3), "sides": info,
                         "max_fold_push_mm": round(fold_mm, 2), "max_root_push_mm": round(root_max, 2),
                         "max_target_push_mm": round(float(np.linalg.norm(D, axis=1).max() * 1000), 2)})
        print("R63_TARGET", json.dumps(report_s[-1]), flush=True)

    Dmax = np.max([np.linalg.norm(targets[s][1], axis=1) for s in samples], axis=0)
    affected = np.flatnonzero(Dmax > 0.2e-3)
    K = np.arange(K0, K1 + 1); nk = len(K); kidx = {k: i for i, k in enumerate(K)}
    # temporal second differences over controls 144..166 (144/145 fixed from the start candidate)
    span = np.arange(K0 - 2, K1 + 1)
    out = d0.copy()
    nA = len(affected)
    # Batched normal equations, one 3nk x 3nk system per affected vertex (unknowns control-major, xyz-minor).
    # Data term: sum_s |M_sv (blend_sv(x) + fixed_sv) - want_sv|^2 ; smoothness: lam |2nd diff over 144..166|^2 ;
    # tie: tie |x - start|^2.
    H = np.zeros((nA, 3 * nk, 3 * nk)); g = np.zeros((nA, 3 * nk))

    def accumulate(s, target_pos, weight):
        """add weight * |posed_s(x) - target_pos|^2 for every affected vertex (weight may be per-vertex, 0 = skip)"""
        lo, hi, t = maps[s]
        wv = np.broadcast_to(np.asarray(weight, float), (nA,))
        Mv = z["mat"][s][affected]                                   # (nA,3,3)
        want = target_pos - z["base"][s][affected]
        coef = np.zeros((nA, nk)); fixed = np.zeros((nA, 3))
        for kk, w in ((lo[affected], 1 - t[affected]), (hi[affected], t[affected])):
            inK = (kk >= K0) & (kk <= K1)
            coef[np.flatnonzero(inK), kk[inK] - K0] += w[inK]
            out_ = np.flatnonzero(~inK)
            fixed[out_] += w[out_, None] * d0[kk[out_], affected[out_]]
        rhs = want - np.einsum("nij,nj->ni", Mv, fixed)               # (nA,3)
        MtM = np.einsum("nki,nkj->nij", Mv, Mv) * wv[:, None, None]; Mtr = np.einsum("nki,nk->ni", Mv, rhs) * wv[:, None]
        for p in range(nk):
            cp = coef[:, p]
            if not cp.any():
                continue
            g[:, 3 * p:3 * p + 3] += cp[:, None] * Mtr
            for q in range(nk):
                cq = coef[:, q]
                if cq.any():
                    H[:, 3 * p:3 * p + 3, 3 * q:3 * q + 3] += (cp * cq)[:, None, None] * MtM

    def posed_now(s, dense):
        lo, hi, t = maps[s]
        inc = (1 - t)[affected, None] * dense[lo[affected], affected] + t[affected, None] * dense[hi[affected], affected]
        return z["base"][s][affected] + np.einsum("nij,nj->ni", z["mat"][s][affected], inc)

    for s in samples:
        if s in guard_samples:
            continue                                                  # R63g: guard-only samples do not drive the shape
        P, D = targets[s]
        accumulate(s, P[affected] + D[affected], 1.0)
    # smoothness (span 144..166; 144/145 fixed from the start candidate)
    for j0 in range(1, len(span) - 1):
        ks = span[j0 - 1:j0 + 2]; cc = np.array([1.0, -2.0, 1.0])
        crow = np.zeros(nk); cfix = np.zeros((nA, 3))
        for kk, c in zip(ks, cc):
            if K0 <= kk <= K1:
                crow[kk - K0] += c
            else:
                cfix += c * d0[kk, affected]
        Ck = np.kron(crow[None], np.eye(3))                          # (3, 3nk)
        H += a.lam * (Ck.T @ Ck)[None]
        g += -a.lam * np.einsum("ik,ni->nk", Ck, cfix)
    H += a.tie * np.eye(3 * nk)[None]
    g += a.tie * d0[K][:, affected].transpose(1, 0, 2).reshape(nA, -1)
    x = np.linalg.solve(H, g[..., None])[..., 0]
    out[K[:, None], affected[None, :]] = x.reshape(nA, nk, 3).transpose(1, 0, 2)
    guard_log = []
    if guard_samples:
        # R63g (owner chose option 1, 20 Oct): the benchmark-press samples only GUARD against arm contact.  After each
        # solve, any affected vertex that a guard pose brings within --arm-margin of the upper-arm skin (and closer than
        # the start candidate) is pinned back to its start-candidate position in that pose (weight --guard-weight); repeat
        # until no new offenders.  The guard never adds fill, so it cannot pull the shape the way R63f's equal weighting did.
        from scipy.spatial import cKDTree
        armpts = np.flatnonzero(np.maximum(armw[0], armw[1]) >= max(0.3, a.torso_max))
        pinned = {s: np.zeros(nA, bool) for s in guard_samples}
        for it in range(a.guard_iters):
            new = 0
            for s in guard_samples:
                lo, hi, t = maps[s]; v_all = np.arange(nv)
                P0 = z["base"][s] + np.einsum("nij,nj->ni", z["mat"][s], (1 - t)[:, None] * d0[lo, v_all] + t[:, None] * d0[hi, v_all])
                tree = cKDTree(P0[armpts])
                Pn = posed_now(s, out)
                dn, _ = tree.query(Pn, k=1); d_0, _ = tree.query(P0[affected], k=1)
                bad = (dn < a.arm_margin) & (dn < d_0 - 1e-4) & ~pinned[s]
                if bad.any():
                    pinned[s] |= bad; new += int(bad.sum())
                    accumulate(s, P0[affected], np.where(bad, a.guard_weight, 0.0))
            guard_log.append(new)
            if not new:
                break
            x = np.linalg.solve(H, g[..., None])[..., 0]
            out[K[:, None], affected[None, :]] = x.reshape(nA, nk, 3).transpose(1, 0, 2)
    # posed fit error at the samples
    fit_err = []
    for s in [q for q in samples if q not in guard_samples]:
        lo, hi, t = maps[s]; P, D = targets[s]
        inc = (1 - t)[affected, None] * out[lo[affected], affected] + t[affected, None] * out[hi[affected], affected]
        Pn = z["base"][s][affected] + np.einsum("nij,nj->ni", z["mat"][s][affected], inc)
        fit_err.append(float(np.linalg.norm(Pn - (P[affected] + D[affected]), axis=1).max()))
    step_log = {}
    if a.step_limit > 0:
        # R64j: the gate limits the change between adjacent one-degree controls (3 mm).  Where a vertex's solved curve
        # over controls K0-1..166 steps more than --step-limit, relax only that vertex's curve in time ([1,2,1]/4 on the
        # free controls; K0-1 stays fixed, 166 is pulled half-way to 165) until it is under the limit.
        def worst(o):
            st = np.linalg.norm(np.diff(o[K0 - 1:K1 + 1], axis=0), axis=2)    # (nk, nv)
            return st
        st = worst(out); k_, v_ = np.unravel_index(np.argmax(st), st.shape)
        step_log["before_mm"] = round(float(st.max() * 1000), 3)
        step_log["before_at"] = {"controls": [int(95 + K0 - 1 + k_), int(95 + K0 + k_)], "rest": np.round(rest[v_], 3).tolist()}
        it = 0
        while it < 2000:
            bad = np.flatnonzero(worst(out).max(axis=0) > a.step_limit)
            if not len(bad):
                break
            c = out[K0 - 1:K1 + 1][:, bad].copy()
            c[1:-1] = 0.25 * c[:-2] + 0.5 * c[1:-1] + 0.25 * c[2:]
            c[-1] = 0.5 * c[-1] + 0.5 * c[-2]
            out[K0:K1 + 1, bad] = c[1:]
            it += 1
        step_log.update({"iterations": it, "after_mm": round(float(worst(out).max() * 1000), 3)})
        print("R64_STEP", json.dumps(step_log), flush=True)
    norms = np.linalg.norm(out, axis=2)
    capped = int((norms > 0.045).any(axis=0).sum())
    over = norms > 0.045
    out[over] *= (0.045 / norms[over])[:, None]
    assert not np.any(out[[0, 15]]), "protected 95/110 control changed"
    assert np.array_equal(out[:K0], d0[:K0]), "controls below the solved range (incl. the marked pose) must be untouched"
    from original_review_r52_temporal import SOURCE
    np.savez_compressed(a.out, dense_delta=out, delta=out[SOURCE])
    metrics = {"status": "R63_IN_MEMORY_STUDY_NOT_ACCEPTED", "model_saved": False, "owner_approved": False,
               "scope_change": f"owner-approved lockout sculpt (20 Oct): controls {95 + K0}..166 re-solved in posed space; 166 released",
               "params": {k: getattr(a, k) for k in ("gain", "depth", "sigma", "maxpush", "hfrom", "full", "smooth", "lam", "tie", "arm_margin", "torso_max", "top", "include_bench", "guard_bench", "guard_weight", "guard_iters", "step_limit", "lat_bulge", "lat_bulge_span", "root_mm", "hull", "fold", "fold_centre", "fold_radius", "fold_iters", "fold_step", "fold_max")},
               "samples": report_s, "affected_vertices": int(len(affected)), "vertices_capped_at_45mm": capped,
               "posed_fit_max_error_mm": round(max(fit_err, default=0) * 1000, 3), "posed_fit_error_by_sample_mm": [round(e * 1000, 2) for e in fit_err],
               "max_change_from_start_mm": round(float(np.linalg.norm(out - d0, axis=2).max() * 1000), 2),
               "max_adjacent_control_mm": oscillation(out)["maximum_adjacent_mm"],
               "arm_file_match_mm": round(dpos, 4), "step_limit": step_log, "guard_new_pins_per_iteration": guard_log}
    Path(a.out + ".json").write_text(json.dumps(metrics, indent=2) + "\n")
    print("R63_GENERATOR", json.dumps({k: v for k, v in metrics.items() if k != "samples"}))


if __name__ == "__main__":
    main()
