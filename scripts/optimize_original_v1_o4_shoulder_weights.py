"""Multi-pose shoulder/upper-torso skin-weight optimisation for the O4 CANDIDATE.

python scripts/optimize_original_v1_o4_shoulder_weights.py <dump.npz> <solution.npz> [--preset NAME]

Input is the dump written by scripts/dump_original_v1_o4_pose_skinning_blender.py
(this candidate's own rest mesh, weights and the v4 rig's per-pose skinning
matrices). Linear blend skinning is reproduced exactly in numpy (checked by the
dumper), so the weights of the shoulder zone can be optimised against every
stress pose at once:

  * hinge barriers keep every edge touching the zone inside a margin of the
    development gates (stretch <= hi, compression >= lo) in every pose;
  * a volume barrier stops any pose's whole-body volume deviation growing
    beyond its R2 value (and pushes the rhythm poses toward the 0.90-1.10 gate);
  * a small log-strain term spreads residual strain evenly;
  * graph smoothness and closeness to the source weights keep the result a
    plausible, reviewable paint job (no noise, no far-reaching edits).

Weights stay on the probability simplex over permitted bones (the vertex's
existing bones plus same-side upperarm/clavicle/scapula and spine_02/03/neck),
then are pruned to 4 influences and re-optimised on that support. Left and right
zones are solved together from their own mesh data. No external data is used.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

PRESETS = {
    # o1: first multi-pose solve from R2 weights.
    "o1": dict(zone_radius=0.24, hi=4.3, lo=0.24, w_hinge=40.0, w_strain=0.02, w_vol=4000.0,
               vol_target_cap=0.085, w_smooth=0.02, w_close=0.02, iters=1500, lr=0.01, polish_iters=600),
    # o2: o1 zone extended to all scapula-weighted upper-body vertices (midline back tear).
    "o2": dict(scap_zone=True, zone_radius=0.24, hi=4.3, lo=0.24, w_hinge=40.0, w_strain=0.02, w_vol=4000.0,
               vol_target_cap=0.085, w_smooth=0.02, w_close=0.02, iters=1500, lr=0.01, polish_iters=600),
    # o3: o2 solved with monotone projected gradient descent (Adam jittered the zone).
    "o3": dict(solver="pgd", step=1e-4, scap_zone=True, zone_radius=0.24, hi=4.3, lo=0.24, w_hinge=40.0,
               w_strain=0.02, w_vol=4000.0, vol_target_cap=0.085, w_smooth=0.02, w_close=0.02,
               iters=400, polish_iters=150),
    # o4: o3 + per-pose/region no-regression bounds vs R2, fold (dihedral) barrier
    # against new self-intersections, much stronger volume barrier.
    "o4": dict(solver="pgd", step=1e-4, scap_zone=True, zone_radius=0.24, hi=4.3, lo=0.24, w_hinge=40.0,
               no_regress=True, min_margin=0.012, max_margin=0.07,
               w_fold=20.0, fold_cos=-0.2, fold_margin=0.05,
               w_strain=0.02, w_vol=2e5, vol_slack=0.003, vol_target_cap=0.085, w_smooth=0.02, w_close=0.02,
               iters=400, polish_iters=150),
    # o5: o4 objective, stiffer no-regression hinges, solved with softmax L-BFGS.
    "o5": dict(solver="lbfgs", scap_zone=True, zone_radius=0.24, hi=4.3, lo=0.24, w_hinge=400.0,
               no_regress=True, min_margin=0.012, max_margin=0.07,
               w_fold=20.0, fold_cos=-0.2, fold_margin=0.05,
               w_strain=0.02, w_vol=2e5, vol_slack=0.003, vol_target_cap=0.085, w_smooth=0.02, w_close=0.02,
               iters=500, polish_iters=200),
    # o6: o5 + proximity barrier (deltoid cap folding into the acromion made the
    # new self-intersections), p99 guard, stiffer volume/no-regression terms.
    "o6": dict(solver="lbfgs", scap_zone=True, zone_radius=0.24, hi=4.3, lo=0.24, w_hinge=3000.0,
               no_regress=True, min_margin=0.012, max_margin=0.07,
               w_fold=20.0, fold_cos=-0.2, fold_margin=0.05,
               w_prox=2e6, prox_delta=0.010, prox_search=0.015, prox_rest_min=0.012, rounds=3,
               w_p99=5.0, p99_margin=0.03,
               w_strain=0.01, w_vol=2e6, vol_slack=0.003, vol_target_cap=0.085, w_smooth=0.02, w_close=0.02,
               iters=250, polish_iters=200),
    # o7: signed facing-sheet separation barrier (replaces vertex distance), stronger p99 guard.
    "o7": dict(solver="lbfgs", scap_zone=True, zone_radius=0.24, hi=4.3, lo=0.24, w_hinge=3000.0,
               no_regress=True, min_margin=0.012, max_margin=0.07,
               w_fold=20.0, fold_cos=-0.2, fold_margin=0.05,
               w_prox=2e6, prox_mode="signed", prox_delta=0.003, prox_search=0.015, prox_rest_min=0.010, rounds=4,
               w_p99=200.0, p99_margin=0.03,
               w_strain=0.01, w_vol=2e6, vol_slack=0.003, vol_target_cap=0.085, w_smooth=0.02, w_close=0.02,
               iters=200, polish_iters=200),
    # o8: warm start from o7; count-aware p99/p01 budgets, 10x stiffer no-regression bounds.
    "o8": dict(solver="lbfgs", scap_zone=True, zone_radius=0.24, hi=4.3, lo=0.24, w_hinge=3e4,
               no_regress=True, min_margin=0.012, max_margin=0.07,
               w_fold=20.0, fold_cos=-0.2, fold_margin=0.05,
               w_prox=2e6, prox_mode="signed", prox_delta=0.003, prox_search=0.015, prox_rest_min=0.010, rounds=4,
               w_p99=3e4, p99_mode="budget", p99_margin=0.04, p01_margin=0.015, p99_slack=6,
               w_strain=0.01, w_vol=2e6, vol_slack=0.003, vol_target_cap=0.085, w_smooth=0.02, w_close=0.02,
               iters=200, polish_iters=200),
    # o9: o8 with a 300 mm zone (front-chest edge sat on the 240 mm boundary with
    # spine-only permission) and the p99 threshold capped below the 2.0 gate.
    "o9": dict(solver="lbfgs", scap_zone=True, zone_radius=0.30, hi=4.3, lo=0.24, w_hinge=3e4,
               no_regress=True, min_margin=0.012, max_margin=0.07,
               w_fold=20.0, fold_cos=-0.2, fold_margin=0.05,
               w_prox=5e6, prox_mode="signed", prox_delta=0.003, prox_search=0.015, prox_rest_min=0.010, rounds=4,
               w_p99=3e4, p99_mode="budget", p99_margin=0.04, p99_cap=1.985, p01_margin=0.015, p99_slack=6,
               w_strain=0.01, w_vol=2e6, vol_slack=0.003, vol_target_cap=0.085, w_smooth=0.02, w_close=0.02,
               iters=200, polish_iters=200),
    # o10: r19/o8 zone; 100x fold (buckling) barrier with creases capped near 78 deg,
    # and the facing-sheet barrier extended to partly facing sheets (acromion bunching).
    "o10": dict(solver="lbfgs", scap_zone=True, zone_radius=0.24, hi=4.3, lo=0.24, w_hinge=3e4,
                no_regress=True, min_margin=0.012, max_margin=0.07,
                w_fold=2000.0, fold_cos=0.2, fold_margin=0.05,
                w_prox=5e6, prox_mode="signed", prox_delta=0.003, prox_search=0.02, prox_rest_min=0.010,
                facing_dot=0.2, rounds=4,
                w_p99=3e4, p99_mode="budget", p99_margin=0.04, p99_cap=1.985, p01_margin=0.015, p99_slack=6,
                w_strain=0.01, w_vol=2e6, vol_slack=0.003, vol_target_cap=0.085, w_smooth=0.02, w_close=0.02,
                iters=200, polish_iters=200),
}


def project_simplex(X, allowed):
    """Row-wise Euclidean projection onto {x >= 0, sum x = 1, x = 0 where not allowed}."""
    Y = np.where(allowed, X, -1e6)
    U = -np.sort(-Y, axis=1)
    css = np.cumsum(U, axis=1) - 1.0
    k = np.arange(1, X.shape[1] + 1)
    cond = U - css / k > 0
    rho = cond.shape[1] - 1 - np.argmax(cond[:, ::-1], axis=1)
    theta = css[np.arange(len(X)), rho] / (rho + 1)
    return np.where(allowed, np.maximum(Y - theta[:, None], 0.0), 0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dump")
    ap.add_argument("out")
    ap.add_argument("--preset", default="o1")
    ap.add_argument("--gradcheck", action="store_true")
    ap.add_argument("--diagnose", action="store_true")
    ap.add_argument("--init", help="warm start from an earlier solution with the same zone")
    a = ap.parse_args()
    P = PRESETS[a.preset]
    d = np.load(a.dump)
    W0, rest, E, tris, region = d["W"], d["rest"], d["edges"], d["tris"], d["region"]
    rnames = [str(x) for x in d["region_names"]]
    bones = [str(x) for x in d["bones"]]
    mats, evald, poses = d["mats"], d["evaluated"], [str(x) for x in d["poses"]]
    b = {n: i for i, n in enumerate(bones)}
    rid = {n: i for i, n in enumerate(rnames)}

    # ---- zone: both sides, shoulder/torso/arm/neck within radius of the glenohumeral joint
    # Also every upper-body vertex carrying scapula weight (the R2 probe found
    # midline back vertices shared by BOTH scapulae, torn apart in the rhythm poses).
    zone_mask = np.zeros(len(rest), bool)
    allowed_full = W0 > 1e-6
    regs = np.isin(region, [rid[n] for n in ("shoulder", "torso", "arm", "neck")])
    scap_w = W0[:, b["scapula_l"]] + W0[:, b["scapula_r"]]
    for s in "lr":
        H = d["heads"][b[f"upperarm_{s}"]]
        side = rest[:, 0] * np.sign(H[0]) > -0.005          # midline belongs to both sides
        near = np.linalg.norm(rest - H, axis=1) < P["zone_radius"]
        zs = side & regs & (near | ((scap_w > 0.01) & P.get("scap_zone", False)))
        if not P.get("scap_zone", False):
            zs &= rest[:, 0] * np.sign(H[0]) > 0.0
        zone_mask |= zs
        for n in (f"upperarm_{s}", f"clavicle_{s}", f"scapula_{s}", "spine_03", "spine_02", "neck"):
            allowed_full[zs & near, b[n]] = True
        for n in ("spine_03", "spine_02", "spine_01"):
            allowed_full[zs & ~near, b[n]] = True
    Z = np.nonzero(zone_mask)[0]
    zpos = -np.ones(len(rest), int)
    zpos[Z] = np.arange(len(Z))
    used = np.nonzero(allowed_full[Z].any(axis=0))[0]          # compact bone set
    allowed = allowed_full[Z][:, used]
    Wz = W0[Z][:, used].copy()
    Wz /= Wz.sum(axis=1, keepdims=True)
    Wz0 = Wz.copy()

    rest_h = np.c_[rest, np.ones(len(rest))]
    T = np.einsum("pbij,vj->pvbi", mats[:, used, :3, :], rest_h[Z])   # [pose, zone, bone, 3]
    # fixed contribution of bones outside `used` (always zero weight there for zone verts) -> none

    Ez = E[(zpos[E[:, 0]] >= 0) | (zpos[E[:, 1]] >= 0)]
    L0 = np.linalg.norm(rest[Ez[:, 0]] - rest[Ez[:, 1]], axis=1)
    Tz = tris[(zpos[tris] >= 0).any(axis=1)]
    vol0_all = np.einsum("ti,ti->t", rest[tris[:, 0]], np.cross(rest[tris[:, 1]], rest[tris[:, 2]])).sum() / 6
    # smoothness edges inside the zone
    Ein = E[(zpos[E[:, 0]] >= 0) & (zpos[E[:, 1]] >= 0)]
    ia, ib = zpos[Ein[:, 0]], zpos[Ein[:, 1]]

    def vol_all(Pp):
        return np.einsum("ti,ti->t", Pp[tris[:, 0]], np.cross(Pp[tris[:, 1]], Pp[tris[:, 2]])).sum() / 6

    dev_R2 = np.array([abs(abs(vol_all(evald[p])) / abs(vol0_all) - 1) for p in range(len(poses))])
    vol_target = np.minimum(dev_R2 + P.get("vol_slack", 0.0), P["vol_target_cap"])
    lhi, llo = np.log(P["hi"]), np.log(P["lo"])
    npz = len(poses)
    LHI = np.full((npz, len(Ez)), lhi)
    LLO = np.full((npz, len(Ez)), llo)
    L0all = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
    if P.get("no_regress"):
        # per pose/region: never materially worse than R2 (comparator tolerances
        # 0.02 min drop / 0.1 max rise, applied with margins), and inside the gate margin.
        ereg_all, ereg_z = region[E[:, 0]], region[Ez[:, 0]]
        for p in range(npz):
            r_all = np.linalg.norm(evald[p][E[:, 0]] - evald[p][E[:, 1]], axis=1) / L0all
            for rgn in np.unique(ereg_z):
                k = ereg_all == rgn
                kz = ereg_z == rgn
                LLO[p, kz] = np.log(max(P["lo"], r_all[k].min() - P["min_margin"]))
                LHI[p, kz] = np.log(min(P["hi"], r_all[k].max() + P["max_margin"]))
    # fold proxy: dihedral cosine between triangles sharing a mesh/diagonal edge in the zone
    edge_tris = {}
    for t, (x, y, zv) in enumerate(Tz):
        for e in ((x, y), (y, zv), (zv, x)):
            edge_tris.setdefault((min(e), max(e)), []).append(t)
    adj = np.array([v for v in edge_tris.values() if len(v) == 2])

    def tri_normals(Pp):
        A, B_, C = Pp[Tz[:, 0]], Pp[Tz[:, 1]], Pp[Tz[:, 2]]
        return np.cross(B_ - A, C - A)

    def dihedral_cos(Pp):
        n = tri_normals(Pp)
        n1, n2 = n[adj[:, 0]], n[adj[:, 1]]
        return (n1 * n2).sum(axis=1) / np.maximum(np.linalg.norm(n1, axis=1) * np.linalg.norm(n2, axis=1), 1e-18)

    P99T = np.array([np.log(min(np.percentile(np.linalg.norm(evald[p][E[:, 0]] - evald[p][E[:, 1]], axis=1) / L0all, 99)
                                 + P.get("p99_margin", 0.03), P.get("p99_cap", 99.0))) for p in range(npz)])
    # proximity: candidate vertices = zone + upper-body neighbours; pairs found per outer round
    cand = np.nonzero(zone_mask | ((rest[:, 2] > 1.15) & (np.abs(rest[:, 0]) > 0.08)))[0]
    PAIRS = [np.zeros((0, 2), int) for _ in range(npz)]
    PDELTA = [np.zeros(0) for _ in range(npz)]

    orient = np.sign(vol0_all)                       # +1 if polygon winding gives outward normals

    def vnormals(Pp):
        A, B_, C = Pp[tris[:, 0]], Pp[tris[:, 1]], Pp[tris[:, 2]]
        fn = np.cross(B_ - A, C - A) * orient
        vn = np.zeros_like(Pp)
        for k in range(3):
            np.add.at(vn, tris[:, k], fn)
        return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)

    SNB = [np.zeros((0, 3)) for _ in range(npz)]     # normal of the 'b' vertex, per directed pair

    def find_pairs_signed(Wz):
        """Directed pairs (a, b) on facing skin sheets: a must stay in front of b's tangent plane."""
        rad, dmin_rest = P.get("prox_search", 0.015), P.get("prox_rest_min", 0.010)
        for p in range(npz):
            Pp = positions(Wz, p)
            N = vnormals(Pp)
            X = Pp[cand]
            found = []
            for i0 in range(0, len(cand), 600):
                D = np.linalg.norm(X[i0:i0 + 600, None] - X[None], axis=2)
                ii, jj = np.nonzero(D < rad)
                ii += i0
                keep = ii != jj
                found.append(np.c_[cand[ii[keep]], cand[jj[keep]]])
            pr = np.concatenate(found)
            pr = pr[(zpos[pr[:, 0]] >= 0) | (zpos[pr[:, 1]] >= 0)]
            pr = pr[np.linalg.norm(rest[pr[:, 0]] - rest[pr[:, 1]], axis=1) > dmin_rest]
            pr = pr[(N[pr[:, 0]] * N[pr[:, 1]]).sum(axis=1) < P.get("facing_dot", -0.2)]   # facing sheets only
            nb = N[pr[:, 1]]
            NR2 = vnormals(evald[p])
            sR2 = ((evald[p][pr[:, 0]] - evald[p][pr[:, 1]]) * NR2[pr[:, 1]]).sum(axis=1)
            PAIRS[p], SNB[p] = pr, nb
            PDELTA[p] = np.minimum(P.get("prox_delta", 0.003), sR2 - 0.0005)

    def find_pairs(Wz):
        if P.get("prox_mode") == "signed":
            return find_pairs_signed(Wz)
        rad, dmin_rest = P.get("prox_search", 0.015), P.get("prox_rest_min", 0.012)
        for p in range(npz):
            Pp = positions(Wz, p)
            X = Pp[cand]
            found = []
            for i0 in range(0, len(cand), 600):
                D = np.linalg.norm(X[i0:i0 + 600, None] - X[None], axis=2)
                ii, jj = np.nonzero(D < rad)
                ii += i0
                keep = ii < jj
                found.append(np.c_[cand[ii[keep]], cand[jj[keep]]])
            pr = np.concatenate(found)
            pr = pr[(zpos[pr[:, 0]] >= 0) | (zpos[pr[:, 1]] >= 0)]
            pr = pr[np.linalg.norm(rest[pr[:, 0]] - rest[pr[:, 1]], axis=1) > dmin_rest]
            # merge with previous rounds' pairs
            pr = np.unique(np.concatenate([PAIRS[p], pr]), axis=0)
            dR2 = np.linalg.norm(evald[p][pr[:, 0]] - evald[p][pr[:, 1]], axis=1)
            PAIRS[p] = pr
            PDELTA[p] = np.minimum(P.get("prox_delta", 0.010), dR2 - 0.001)

    P99ACT = [np.zeros(0, int) for _ in range(npz)]
    P01ACT = [np.zeros(0, int) for _ in range(npz)]
    P01T = np.array([np.log(np.percentile(np.linalg.norm(evald[p][E[:, 0]] - evald[p][E[:, 1]], axis=1) / L0all, 1)
                             - P.get("p01_margin", 0.015)) for p in range(npz)])
    ez_mask = (zpos[E[:, 0]] >= 0) | (zpos[E[:, 1]] >= 0)      # Ez == E[ez_mask] (same order)
    nonzone_ratio = [np.linalg.norm(evald[p][E[~ez_mask, 0]] - evald[p][E[~ez_mask, 1]], axis=1) / L0all[~ez_mask]
                     for p in range(npz)]

    def refresh_p99(Wz):
        """Count-aware 99th-percentile guard: only zone edges beyond R2's budget above the
        threshold are pushed under it, choosing those closest to the threshold."""
        if P.get("p99_mode") != "budget":
            return
        k99 = int(0.01 * len(E)) - P.get("p99_slack", 6)
        for p in range(npz):
            Pp = positions(Wz, p)
            r = np.linalg.norm(Pp[Ez[:, 0]] - Pp[Ez[:, 1]], axis=1) / L0
            t = np.exp(P99T[p])
            budget = max(k99 - int((nonzone_ratio[p] > t).sum()), 0)
            above = np.nonzero(r > t * 0.985)[0]
            excess = len(above) - budget
            P99ACT[p] = above[np.argsort(r[above])[:excess]] if excess > 0 else np.zeros(0, int)
            # symmetric 1st-percentile (compression) budget
            t01 = np.exp(P01T[p])
            budget01 = max(k99 - int((nonzone_ratio[p] < t01).sum()), 0)
            below = np.nonzero(r < t01 / 0.985)[0]
            excess01 = len(below) - budget01
            P01ACT[p] = below[np.argsort(-r[below])[:excess01]] if excess01 > 0 else np.zeros(0, int)

    FOLD = np.array([np.minimum(P.get("fold_cos", -2.0), dihedral_cos(evald[p]) - P.get("fold_margin", 0.0))
                     for p in range(npz)])

    def positions(Wz, p):
        Pp = evald[p].copy()
        Pp[Z] = np.einsum("vb,vbi->vi", Wz, T[p])
        return Pp

    parts = {}

    def loss_grad(Wz):
        G = np.zeros_like(Wz)
        total = 0.0
        parts.clear()
        for p in range(len(poses)):
            Pp = positions(Wz, p)
            dv = Pp[Ez[:, 0]] - Pp[Ez[:, 1]]
            L = np.linalg.norm(dv, axis=1)
            lr = np.log(np.maximum(L, 1e-12) / L0)
            over, under = np.maximum(lr - LHI[p], 0), np.maximum(LLO[p] - lr, 0)
            h_hi, h_lo, st = P["w_hinge"] * (over ** 2).sum(), P["w_hinge"] * (under ** 2).sum(), P["w_strain"] * (lr ** 2).sum()
            total += h_hi + h_lo + st
            parts[poses[p]] = [round(float(h_hi), 2), round(float(h_lo), 2), round(float(st), 2)]
            g = P["w_hinge"] * 2 * (over - under) + P["w_strain"] * 2 * lr     # dLoss/dlr
            gP = np.zeros_like(Pp)
            coef = (g / np.maximum(L, 1e-12) ** 2)[:, None] * dv
            np.add.at(gP, Ez[:, 0], coef)
            np.add.at(gP, Ez[:, 1], -coef)
            # fold barrier: dihedral cosine may not drop below min(gate, R2 - margin)
            if P.get("w_fold", 0) > 0:
                A, B_, C = Pp[Tz[:, 0]], Pp[Tz[:, 1]], Pp[Tz[:, 2]]
                n = np.cross(B_ - A, C - A)
                n1, n2 = n[adj[:, 0]], n[adj[:, 1]]
                l1, l2 = np.maximum(np.linalg.norm(n1, axis=1), 1e-12), np.maximum(np.linalg.norm(n2, axis=1), 1e-12)
                cs = (n1 * n2).sum(axis=1) / (l1 * l2)
                fx = np.maximum(FOLD[p] - cs, 0)
                total += P["w_fold"] * (fx ** 2).sum()
                parts[poses[p]].append(round(float(P["w_fold"] * (fx ** 2).sum()), 2))
                gc = (-2 * P["w_fold"] * fx)[:, None]                      # dLoss/dcos
                gn1 = gc * (n2 / (l1 * l2)[:, None] - cs[:, None] * n1 / (l1 ** 2)[:, None])
                gn2 = gc * (n1 / (l1 * l2)[:, None] - cs[:, None] * n2 / (l2 ** 2)[:, None])
                gn = np.zeros_like(n)
                np.add.at(gn, adj[:, 0], gn1)
                np.add.at(gn, adj[:, 1], gn2)
                np.add.at(gP, Tz[:, 0], np.cross(gn, C - B_))
                np.add.at(gP, Tz[:, 1], np.cross(gn, A - C))
                np.add.at(gP, Tz[:, 2], np.cross(gn, B_ - A))
            # p99 guard: zone edges pushed under R2's 99th-percentile stretch (+margin)
            if P.get("w_p99", 0) > 0 and P.get("p99_mode") == "budget":
                act = P99ACT[p]
                o99 = np.zeros_like(lr)
                o99[act] = np.maximum(lr[act] - (P99T[p] + np.log(0.975)), 0)
                act01 = P01ACT[p]
                u01 = np.zeros_like(lr)
                u01[act01] = np.maximum((P01T[p] - np.log(0.975)) - lr[act01], 0)
                total += P["w_p99"] * ((o99 ** 2).sum() + (u01 ** 2).sum())
                gp = (P["w_p99"] * 2 * (o99 - u01) / np.maximum(L, 1e-12) ** 2)[:, None] * dv
                np.add.at(gP, Ez[:, 0], gp)
                np.add.at(gP, Ez[:, 1], -gp)
            elif P.get("w_p99", 0) > 0:
                o99 = np.maximum(lr - P99T[p], 0)
                total += P["w_p99"] * (o99 ** 2).sum()
                gp = (P["w_p99"] * 2 * o99 / np.maximum(L, 1e-12) ** 2)[:, None] * dv
                np.add.at(gP, Ez[:, 0], gp)
                np.add.at(gP, Ez[:, 1], -gp)
            # proximity barrier: far-at-rest vertices must not approach closer than delta / R2
            if P.get("w_prox", 0) > 0 and len(PAIRS[p]) and P.get("prox_mode") == "signed":
                pr, nb = PAIRS[p], SNB[p]
                sep = ((Pp[pr[:, 0]] - Pp[pr[:, 1]]) * nb).sum(axis=1)
                ex = np.maximum(PDELTA[p] - sep, 0)
                total += P["w_prox"] * (ex ** 2).sum()
                parts[poses[p]].append(round(float(P["w_prox"] * (ex ** 2).sum()), 2))
                gq = (-2 * P["w_prox"] * ex)[:, None] * nb
                np.add.at(gP, pr[:, 0], gq)
                np.add.at(gP, pr[:, 1], -gq)
            elif P.get("w_prox", 0) > 0 and len(PAIRS[p]):
                pr = PAIRS[p]
                dd = Pp[pr[:, 0]] - Pp[pr[:, 1]]
                dn = np.maximum(np.linalg.norm(dd, axis=1), 1e-9)
                ex = np.maximum(PDELTA[p] - dn, 0)
                total += P["w_prox"] * (ex ** 2).sum()
                parts[poses[p]].append(round(float(P["w_prox"] * (ex ** 2).sum()), 2))
                gq = (-2 * P["w_prox"] * ex / dn)[:, None] * dd
                np.add.at(gP, pr[:, 0], gq)
                np.add.at(gP, pr[:, 1], -gq)
            # volume barrier
            A, B_, C = Pp[Tz[:, 0]], Pp[Tz[:, 1]], Pp[Tz[:, 2]]
            vol = vol_all(Pp)
            ratio = abs(vol) / abs(vol0_all)
            dev = abs(ratio - 1)
            ex = max(dev - vol_target[p], 0.0)
            if ex > 0:
                total += P["w_vol"] * ex ** 2
                parts[poses[p]].append(round(float(P["w_vol"] * ex ** 2), 2))
                gv = P["w_vol"] * 2 * ex * np.sign(ratio - 1) * np.sign(vol) / abs(vol0_all) / 6
                np.add.at(gP, Tz[:, 0], gv * np.cross(B_, C))
                np.add.at(gP, Tz[:, 1], gv * np.cross(C, A))
                np.add.at(gP, Tz[:, 2], gv * np.cross(A, B_))
            G += np.einsum("vi,vbi->vb", gP[Z], T[p])
        dW = Wz[ia] - Wz[ib]
        total += P["w_smooth"] * (dW ** 2).sum() + P["w_close"] * ((Wz - Wz0) ** 2).sum()
        np.add.at(G, ia, 2 * P["w_smooth"] * dW)
        np.add.at(G, ib, -2 * P["w_smooth"] * dW)
        G += 2 * P["w_close"] * (Wz - Wz0)
        return total, G

    def adam(Wz, mask, iters, lr):
        # Adam with cosine step decay (lr -> lr/20); returns the best iterate seen.
        m = np.zeros_like(Wz)
        v = np.zeros_like(Wz)
        best, best_f = Wz, np.inf
        for t in range(1, iters + 1):
            f, G = loss_grad(Wz)
            if f < best_f:
                best, best_f = Wz, f
            m = 0.9 * m + 0.1 * G
            v = 0.999 * v + 0.001 * G * G
            lr_t = lr * (0.05 + 0.95 * 0.5 * (1 + np.cos(np.pi * (t - 1) / iters)))
            step = lr_t * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)
            Wz = project_simplex(Wz - step, mask)
            if t % 100 == 0 or t == 1:
                print(f"iter {t:5d} loss {f:.4f} best {best_f:.4f}", flush=True)
        return best

    def pgd(Wz, mask, iters, step):
        """Monotone projected gradient descent with backtracking (Armijo) line search."""
        f, G = loss_grad(Wz)
        for t in range(1, iters + 1):
            while True:
                Wn = project_simplex(Wz - step * G, mask)
                fn, Gn = loss_grad(Wn)
                if fn <= f - 1e-4 * (G * (Wz - Wn)).sum() or step < 1e-9:
                    break
                step *= 0.5
            if fn >= f:
                print(f"pgd converged at iter {t}", flush=True)
                break
            Wz, f, G = Wn, fn, Gn
            step *= 1.6
            if t % 25 == 0 or t == 1:
                print(f"iter {t:5d} loss {f:.4f} step {step:.2e}", flush=True)
        return Wz

    def lbfgs(Wz, mask, iters, mem=12):
        """L-BFGS over softmax logits (weights stay on the simplex of permitted bones)."""
        NEG = -1e9

        def to_w(th):
            x = np.where(mask, th, NEG)
            x = x - x.max(axis=1, keepdims=True)
            e = np.where(mask, np.exp(x), 0.0)
            return e / e.sum(axis=1, keepdims=True)

        def fg(th):
            W = to_w(th)
            f, G = loss_grad(W)
            gth = W * (G - (W * G).sum(axis=1, keepdims=True))
            return f, np.where(mask, gth, 0.0)

        th = np.where(mask, np.log(np.maximum(Wz, 1e-4)), 0.0)
        f, g = fg(th)
        S, Y = [], []
        for t in range(1, iters + 1):
            q = g.copy()
            al = []
            for s_, y_ in reversed(list(zip(S, Y))):
                rho = 1.0 / (y_ * s_).sum()
                a_ = rho * (s_ * q).sum()
                al.append((rho, a_))
                q -= a_ * y_
            if S:
                q *= (S[-1] * Y[-1]).sum() / (Y[-1] * Y[-1]).sum()
            for (s_, y_), (rho, a_) in zip(zip(S, Y), reversed(al)):
                b_ = rho * (y_ * q).sum()
                q += s_ * (a_ - b_)
            dirn = -q
            gd = (g * dirn).sum()
            if gd >= 0:
                dirn, gd, S, Y = -g, -(g * g).sum(), [], []
            step = 1.0 if S else 1.0 / max(np.abs(g).max(), 1e-12)
            while True:
                thn = th + step * dirn
                fn, gn = fg(thn)
                if fn <= f + 1e-4 * step * gd or step < 1e-12:
                    break
                step *= 0.5
            if fn >= f:
                print(f"lbfgs stalled at iter {t}", flush=True)
                break
            s_, y_ = thn - th, gn - g
            if (s_ * y_).sum() > 1e-12:
                S.append(s_); Y.append(y_)
                if len(S) > mem:
                    S.pop(0); Y.pop(0)
            th, f, g = thn, fn, gn
            if t % 25 == 0 or t == 1:
                print(f"iter {t:5d} loss {f:.4f}", flush=True)
        return to_w(th)

    if P.get("w_prox", 0) > 0:
        find_pairs(Wz0)
    refresh_p99(Wz0)
    f0, G0 = loss_grad(Wz0)
    if a.gradcheck:
        rng = np.random.default_rng(0)
        for _ in range(6):
            i, j = rng.integers(len(Z)), rng.integers(len(used))
            h = 1e-6
            Wp = Wz0.copy(); Wp[i, j] += h
            Wm = Wz0.copy(); Wm[i, j] -= h
            fd = (loss_grad(Wp)[0] - loss_grad(Wm)[0]) / (2 * h)
            print("gradcheck", i, j, f"analytic {G0[i, j]:.6g} numeric {fd:.6g}")
        return
    print("zone vertices", len(Z), "bones", len(used), "edges", len(Ez), "initial loss", round(f0, 4))
    print("terms [stretch hinge, compress hinge, strain, (volume)]", json.dumps(parts))
    if a.diagnose:
        return
    Winit = Wz0.copy()
    if a.init:
        ini = np.load(a.init)
        ub = [bones[i] for i in used]
        col = {n: ub.index(str(n)) for n in ini["bones"] if str(n) in ub}
        if len(col) != len(ini["bones"]):
            raise SystemExit("--init solution uses bones outside this zone's bone set")
        Winit = Wz0.copy()
        for k, v in enumerate(ini["vertices"]):         # map by vertex; new zone vertices keep R2 weights
            if zpos[v] >= 0:
                row = np.zeros(len(ub))
                for j, n in enumerate(ini["bones"]):
                    row[col[str(n)]] = ini["weights"][k, j]
                Winit[zpos[v]] = row
        Winit = np.where(allowed, np.maximum(Winit, 1e-4), 0.0)
        Winit /= Winit.sum(axis=1, keepdims=True)
        print("warm start from", a.init, flush=True)
    if P.get("solver") == "lbfgs" and P.get("w_prox", 0) > 0:
        Wz = Winit.copy()
        find_pairs(Wz)
        refresh_p99(Wz)
        for rnd in range(P.get("rounds", 3)):
            Wz = lbfgs(Wz, allowed, P["iters"])
            find_pairs(Wz)
            refresh_p99(Wz)
            print("round", rnd, "p99 active", [len(x) for x in P99ACT], "p01 active", [len(x) for x in P01ACT], flush=True)
            print("round", rnd, "pairs", [len(x) for x in PAIRS], flush=True)
    elif P.get("solver") == "lbfgs":
        Wz = lbfgs(Wz0.copy(), allowed, P["iters"])
    elif P.get("solver") == "pgd":
        Wz = pgd(Wz0.copy(), allowed, P["iters"], P["step"])
    else:
        Wz = adam(Wz0.copy(), allowed, P["iters"], P["lr"])
    # prune to 4 influences, polish on that support
    order = np.argsort(-Wz, axis=1)
    sup = np.zeros_like(allowed)
    sup[np.arange(len(Wz))[:, None], order[:, :4]] = True
    sup &= allowed
    Wz = project_simplex(np.where(sup, Wz, 0.0), sup)
    if P.get("solver") == "lbfgs":
        Wz = lbfgs(Wz, sup, P["polish_iters"])
        Wz = np.where(Wz < 1e-4, 0.0, Wz)
        Wz /= Wz.sum(axis=1, keepdims=True)
    elif P.get("solver") == "pgd":
        Wz = pgd(Wz, sup, P["polish_iters"], P["step"])
    else:
        Wz = adam(Wz, sup, P["polish_iters"], P["lr"] * 0.5)
    f1, _ = loss_grad(Wz)
    print("final terms", json.dumps(parts))

    # predicted metrics (same definitions as the pose test) for R2 and the solution
    def metrics(Wz):
        out = {}
        for p, name in enumerate(poses):
            Pp = positions(Wz, p)
            r = np.linalg.norm(Pp[E[:, 0]] - Pp[E[:, 1]], axis=1) / np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
            reg = region[E[:, 0]]
            m = {"volume_ratio": round(abs(vol_all(Pp)) / abs(vol0_all), 4)}
            for rn in ("shoulder", "torso", "arm", "neck"):
                k = reg == rid[rn]
                m[rn] = [round(float(r[k].min()), 3), round(float(r[k].max()), 3)]
            out[name] = m
        return out

    before, after = metrics(Wz0), metrics(Wz)
    for name in poses:
        print(f"{name:20s}", "R2", json.dumps(before[name]), "\n" + " " * 20, "NEW", json.dumps(after[name]))
    np.savez_compressed(a.out, vertices=Z, bones=np.array([bones[i] for i in used]), weights=Wz)
    rec = {"generated_utc": datetime.now(timezone.utc).isoformat(), "preset": a.preset, "parameters": P,
           "source_dump": str(d["source"]), "zone_vertices": int(len(Z)), "bones": [bones[i] for i in used],
           "loss_before": f0, "loss_after": f1, "predicted_before": before, "predicted_after": after,
           "inputs": "this candidate's own ORIGINAL v1 mesh/weights and the v4 rig only"}
    Path(a.out).with_suffix(".json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print("SOLUTION", a.out, "loss", round(f0, 3), "->", round(f1, 3))


if __name__ == "__main__":
    main()
