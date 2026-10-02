"""First-party solve of the generic shoulder/axilla corrective (numpy only; touches no Blend).

python scripts/optimize_original_v1_shoulder_corrective.py <arc dump.npz> <out solution.npz> [--theta0 40] [--theta1 150] [--declare-mask mask.json]
       [--hi 3.2] [--lo 0.30] [--w-trunk 3e6] [--w-smooth 20] [--w-mag 2] [--iters 300] [--init prev.npz]

Design: docs/ORIGINAL_V1_SHOULDER_CORRECTIVE_DESIGN.md. The posed position of a vertex with the corrective is

    P_v(pose) = P0_v(pose) + A_v(pose) . ( lam_L a(theta_L) D^L_v + lam_R a(theta_R) D^R_v ),   A_v = sum_b W_vb R_b(pose)   (3x3 blend of the bone rotations)

because skinning is linear in the rest position. D^L lives on the left-owned mask (x <= 0, midline included), D^R(v) = S * D^L(m(v)) with S = (-1,1,1) and m the exact
mirror map: symmetric by construction. a(theta) is the C1 smoothstep between theta0 and theta1. Minimised over D^L: edge stretch/compression hinges (against the TRUE rest length),
the trunk-anchoring form prior for lateral-torso skin (tent flaps), graph smoothness of the net field, a small magnitude term. Training set = the dump's entries (15 stress poses plus
continuous-arc samples of the shoulder poses). The exact LBS model comes from the candidate itself; inputs are this candidate's own mesh/weights/rig only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


def smoothstep(theta, t0, t1):
    t = np.clip((np.asarray(theta, dtype=float) - t0) / (t1 - t0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def dsmoothstep(theta, t0, t1):
    t = np.clip((np.asarray(theta, dtype=float) - t0) / (t1 - t0), 0.0, 1.0)
    return 6.0 * t * (1.0 - t) / (t1 - t0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dump")
    ap.add_argument("out")
    ap.add_argument("--theta0", type=float, default=40.0)
    ap.add_argument("--theta1", type=float, default=150.0)
    ap.add_argument("--declare-mask")
    ap.add_argument("--radius", type=float, default=0.30)
    ap.add_argument("--hi", type=float, default=3.2)
    ap.add_argument("--lo", type=float, default=0.30)
    ap.add_argument("--abs-lo", action="store_true", help="compression bound is the absolute --lo for every mask edge (default: never worse than min(lo, current))")
    ap.add_argument("--w-hinge", type=float, default=2e4)
    ap.add_argument("--w-trunk", type=float, default=3e6)
    ap.add_argument("--trunk-a0", type=float, default=0.05)
    ap.add_argument("--trunk-a1", type=float, default=0.20)
    ap.add_argument("--trunk-rb", type=float, default=0.18)
    ap.add_argument("--w-fold", type=float, default=0.0, help="dihedral fold barrier (cos below min(0.2, current-0.05) is penalised)")
    ap.add_argument("--w-smooth", type=float, default=20.0)
    ap.add_argument("--w-mag", type=float, default=2.0)
    ap.add_argument("--iters", type=int, default=300)
    ap.add_argument("--init")
    a = ap.parse_args()

    d = np.load(a.dump)
    W, rest, E, region = d["W"], d["rest"], d["edges"], d["region"]
    rn = [str(x) for x in d["region_names"]]
    bones = [str(x) for x in d["bones"]]
    mats, evald, poses, theta = d["mats"], d["evaluated"], [str(x) for x in d["poses"]], d["theta"]
    b = {n: i for i, n in enumerate(bones)}
    nV, nP = len(rest), len(poses)

    # ---------------------------------------------------------------- mask (left-owned) and exact mirror map
    key = {tuple(np.round(rest[i], 5)): i for i in range(nV)}
    mir = np.array([key.get(tuple(np.round(rest[i] * [-1, 1, 1], 5)), -1) for i in range(nV)])
    if (mir < 0).any():
        raise SystemExit("mesh is not exactly mirror symmetric")
    regs = np.isin(region, [rn.index(n) for n in ("torso", "shoulder", "arm")])
    Hl = d["heads"][b["upperarm_l"]]
    left_gh = np.linalg.norm(rest - Hl, axis=1)
    Lset = np.nonzero((rest[:, 0] <= 1e-8) & regs & ((left_gh < a.radius) | (W[:, b["scapula_l"]] > 0.01)))[0]
    Rset = mir[Lset[rest[Lset, 0] < -1e-8]]                       # right-owned mirror twins of the strictly-left vertices
    mask_all = np.unique(np.concatenate([Lset, Rset]))
    mid = Lset[np.abs(rest[Lset, 0]) <= 1e-8]
    if a.declare_mask:
        rec = {"declared_utc": datetime.now(timezone.utc).isoformat(), "declared_before_edit": True, "source_dump": str(d["source"]),
               "rule": "left-owned: x <= 0 (midline included), regions torso/shoulder/arm, within radius of the left glenohumeral joint OR scapula_l weight > 0.01; right side = exact mirror",
               "radius_m": a.radius, "left_owned_vertex_ids": [int(i) for i in Lset], "mirror_of_strict_left_vertex_ids": [int(i) for i in Rset],
               "midline_vertex_ids": [int(i) for i in mid], "vertex_count_total": int(len(mask_all)),
               "ids_sha256": hashlib.sha256(np.asarray(Lset, dtype="<i8").tobytes()).hexdigest(),
               "allowed_change": "rest-space displacement vectors (shape key data) of these vertices only; no weights/topology/rest geometry/bones/other vertices",
               "theta0_deg": a.theta0, "theta1_deg": a.theta1}
        Path(a.declare_mask).write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
        print("CORRECTIVE MASK DECLARED", a.declare_mask, "left-owned", len(Lset), "total", len(mask_all), "midline", len(mid))
        return

    nL = len(Lset)
    posL = {int(v): k for k, v in enumerate(Lset)}
    # full-field index helpers: DLfull = D on Lset; DRfull(v) = S * D[mirror(v)] on Rset' = mirror of strictly-left vertices AND midline (both keys act on midline)
    Rkeys = Lset                                                       # every left-owned vertex v has a mirror twin m(v) that receives S*D[v]
    Rtarget = mir[Lset]                                                # vertex receiving the right key's displacement from D[k]
    S = np.array([-1.0, 1.0, 1.0])
    in_mask = np.zeros(nV, bool)
    in_mask[mask_all] = True
    Z = mask_all
    zpos = {int(v): k for k, v in enumerate(Z)}
    Lz = np.array([zpos[int(v)] for v in Lset])
    Rz = np.array([zpos[int(v)] for v in Rtarget])

    A = np.einsum("vb,pbij->pvij", W[Z], mats[:, :, :3, :3])           # [pose, zone vertex, 3, 3]
    P0 = evald.copy()
    lam = d["lam"] if "lam" in d.files else np.ones_like(theta)
    al = smoothstep(theta[:, 0], a.theta0, a.theta1) * lam[:, 0]
    ar = smoothstep(theta[:, 1], a.theta0, a.theta1) * lam[:, 1]
    # trunk-driven reference positions (trunk bones only, weights renormalised)
    trunk = [b[n] for n in ("root", "pelvis", "spine_01", "spine_02", "spine_03", "neck", "head") if n in b]
    Wt = np.zeros_like(W)
    Wt[:, trunk] = W[:, trunk]
    Wt = Wt / np.maximum(Wt.sum(axis=1, keepdims=True), 1e-9)
    rest_h = np.c_[rest, np.ones(nV)]
    PTR = np.stack([np.einsum("vb,vbi->vi", Wt[Z], np.einsum("bij,vj->vbi", mats[p][:, :3, :], rest_h[Z])) for p in range(nP)])
    Hr = d["heads"][b["upperarm_r"]]
    rj = np.minimum(np.linalg.norm(rest[Z] - Hl, axis=1), np.linalg.norm(rest[Z] - Hr, axis=1))
    ALLOW = a.trunk_a0 + a.trunk_a1 * np.exp(-(rj / a.trunk_rb) ** 2)
    TORSO = region[Z] == rn.index("torso")
    # edges touching the mask
    Em = E[in_mask[E[:, 0]] | in_mask[E[:, 1]]]
    L0 = np.linalg.norm(rest[Em[:, 0]] - rest[Em[:, 1]], axis=1)
    cur = np.stack([np.log(np.maximum(np.linalg.norm(P0[p][Em[:, 0]] - P0[p][Em[:, 1]], axis=1), 1e-12) / L0) for p in range(nP)])
    LHI = np.maximum(np.log(a.hi), 0.0) * np.ones_like(cur)
    LLO = (np.log(a.lo) * np.ones_like(cur)) if a.abs_lo else np.minimum(np.log(a.lo), cur)                                # never required to be better than the current compression, never allowed to get worse than min(lo, current)
    # smoothness edges (inside the mask, on the net field)
    Es = E[in_mask[E[:, 0]] & in_mask[E[:, 1]]]
    Esz0, Esz1 = np.array([zpos[int(v)] for v in Es[:, 0]]), np.array([zpos[int(v)] for v in Es[:, 1]])
    # fold barrier: triangles touching the mask and the adjacent pairs among them (new buckling/self-intersection proxy)
    tris = d["tris"]
    Tz = tris[in_mask[tris].any(axis=1)]
    edge_tris = {}
    for t, (x_, y_, z_) in enumerate(Tz):
        for e in ((x_, y_), (y_, z_), (z_, x_)):
            edge_tris.setdefault((min(e), max(e)), []).append(t)
    adj = np.array([v for v in edge_tris.values() if len(v) == 2])

    def dihedral(Pp):
        A_, B_, C_ = Pp[Tz[:, 0]], Pp[Tz[:, 1]], Pp[Tz[:, 2]]
        n = np.cross(B_ - A_, C_ - A_)
        n1, n2 = n[adj[:, 0]], n[adj[:, 1]]
        return n, n1, n2, (n1 * n2).sum(axis=1) / np.maximum(np.linalg.norm(n1, axis=1) * np.linalg.norm(n2, axis=1), 1e-18)

    FOLD = np.stack([np.minimum(0.2, dihedral(P0[p])[3] - 0.05) for p in range(nP)]) if a.w_fold > 0 else None
    zidx = -np.ones(nV, int)
    zidx[Z] = np.arange(len(Z))

    def net_fields(Dv):
        DL = np.zeros((len(Z), 3))
        DR = np.zeros((len(Z), 3))
        np.add.at(DL, Lz, Dv)
        np.add.at(DR, Rz, Dv * S)
        return DL, DR

    def loss_grad(x):
        Dv = x.reshape(nL, 3)
        DL, DR = net_fields(Dv)
        gDL = np.zeros_like(DL)
        gDR = np.zeros_like(DR)
        total = 0.0
        for p in range(nP):
            if al[p] <= 0 and ar[p] <= 0:
                continue
            Deff = al[p] * DL + ar[p] * DR
            dP = np.einsum("vij,vj->vi", A[p], Deff)
            Pp = P0[p].copy()
            Pp[Z] += dP
            dv = Pp[Em[:, 0]] - Pp[Em[:, 1]]
            Ln = np.maximum(np.linalg.norm(dv, axis=1), 1e-12)
            lr = np.log(Ln / L0)
            over, under = np.maximum(lr - LHI[p], 0.0), np.maximum(LLO[p] - lr, 0.0)
            total += a.w_hinge * ((over ** 2).sum() + (under ** 2).sum())
            g = a.w_hinge * 2.0 * (over - under)
            gP = np.zeros_like(Pp)
            coef = (g / Ln ** 2)[:, None] * dv
            np.add.at(gP, Em[:, 0], coef)
            np.add.at(gP, Em[:, 1], -coef)
            # trunk anchoring for torso skin
            dtr = Pp[Z] - PTR[p]
            dn = np.maximum(np.linalg.norm(dtr, axis=1), 1e-12)
            exc = np.where(TORSO, np.maximum(dn - ALLOW, 0.0), 0.0)
            total += a.w_trunk * (exc ** 2).sum()
            gP[Z] += (2.0 * a.w_trunk * exc / dn)[:, None] * dtr
            if a.w_fold > 0:
                n, n1, n2, cs = dihedral(Pp)
                fx = np.maximum(FOLD[p] - cs, 0.0)
                if (fx > 0).any():
                    total += a.w_fold * (fx ** 2).sum()
                    l1, l2 = np.maximum(np.linalg.norm(n1, axis=1), 1e-12), np.maximum(np.linalg.norm(n2, axis=1), 1e-12)
                    gc = (-2.0 * a.w_fold * fx)[:, None]
                    gn1 = gc * (n2 / (l1 * l2)[:, None] - cs[:, None] * n1 / (l1 ** 2)[:, None])
                    gn2 = gc * (n1 / (l1 * l2)[:, None] - cs[:, None] * n2 / (l2 ** 2)[:, None])
                    gn = np.zeros_like(n)
                    np.add.at(gn, adj[:, 0], gn1)
                    np.add.at(gn, adj[:, 1], gn2)
                    A_, B_, C_ = Pp[Tz[:, 0]], Pp[Tz[:, 1]], Pp[Tz[:, 2]]
                    np.add.at(gP, Tz[:, 0], np.cross(gn, C_ - B_))
                    np.add.at(gP, Tz[:, 1], np.cross(gn, A_ - C_))
                    np.add.at(gP, Tz[:, 2], np.cross(gn, B_ - A_))
            gDeff = np.einsum("vji,vj->vi", A[p], gP[Z])                 # A^T gP
            gDL += al[p] * gDeff
            gDR += ar[p] * gDeff
        # net field smoothness (symmetric pose: both keys fully active)
        T = DL + DR
        dT = T[Esz0] - T[Esz1]
        total += a.w_smooth * (dT ** 2).sum() + a.w_mag * (T ** 2).sum()
        gT = np.zeros_like(T)
        np.add.at(gT, Esz0, 2 * a.w_smooth * dT)
        np.add.at(gT, Esz1, -2 * a.w_smooth * dT)
        gT += 2 * a.w_mag * T
        gDL += gT
        gDR += gT
        gD = np.zeros_like(Dv)
        np.add.at(gD, np.arange(nL), gDL[Lz])
        np.add.at(gD, np.arange(nL), gDR[Rz] * S)
        return total, gD.ravel()

    x = np.zeros(nL * 3)
    if a.init:
        s0 = np.load(a.init)
        mp = {int(v): k for k, v in enumerate(s0["vertices"])}
        for k, v in enumerate(Lset):
            if int(v) in mp:
                x[3 * k:3 * k + 3] = s0["delta"][mp[int(v)]]
    f, g = loss_grad(x)
    print(f"mask left-owned {nL} total {len(Z)} edges {len(Em)} poses {nP} (active {int(((al > 0) | (ar > 0)).sum())}) initial loss {f:.1f}")
    # L-BFGS with Armijo backtracking
    m, S_, Y_ = 12, [], []
    for it in range(1, a.iters + 1):
        q = g.copy()
        al_ = []
        for s, y in zip(reversed(S_), reversed(Y_)):
            rho = 1.0 / max(float(y @ s), 1e-18)
            ai = rho * float(s @ q)
            al_.append((ai, rho, s, y))
            q -= ai * y
        gamma = (float(S_[-1] @ Y_[-1]) / max(float(Y_[-1] @ Y_[-1]), 1e-18)) if S_ else 1e-6 / max(np.linalg.norm(g), 1e-12) * 1.0
        r = gamma * q
        for ai, rho, s, y in reversed(al_):
            bi = rho * float(y @ r)
            r += s * (ai - bi)
        dirn = -r
        if float(g @ dirn) >= 0:
            dirn = -g
            S_, Y_ = [], []
        step, ok = 1.0, False
        for _ in range(30):
            xn = x + step * dirn
            fn, gn = loss_grad(xn)
            if fn <= f + 1e-4 * step * float(g @ dirn):
                ok = True
                break
            step *= 0.5
        if not ok:
            print("line search failed at iteration", it)
            break
        s, y = xn - x, gn - g
        if float(y @ s) > 1e-18:
            S_.append(s)
            Y_.append(y)
            if len(S_) > m:
                S_.pop(0)
                Y_.pop(0)
        x, f, g = xn, fn, gn
        if it % 25 == 0 or it == 1:
            print(f"iter {it:4d} loss {f:.3f} |g| {np.linalg.norm(g):.3e} max|D| {np.abs(x).max():.4f}")
    Dv = x.reshape(nL, 3)
    DL, DR = net_fields(Dv)
    # report: per entry the metrics before/after on the mask-touching edges and torso drift
    rows = []
    for p in range(nP):
        if al[p] <= 0 and ar[p] <= 0:
            continue
        Deff = al[p] * DL + ar[p] * DR
        Pp = P0[p].copy()
        Pp[Z] += np.einsum("vij,vj->vi", A[p], Deff)
        r1 = np.linalg.norm(Pp[Em[:, 0]] - Pp[Em[:, 1]], axis=1) / L0
        r0 = np.exp(cur[p])
        drift = np.linalg.norm(Pp[Z] - PTR[p], axis=1)[TORSO]
        drift0 = np.linalg.norm(P0[p][Z] - PTR[p], axis=1)[TORSO]
        rows.append((poses[p], float(theta[p, 0]), float(al[p]), float(r0.max()), float(r1.max()), float(r0.min()), float(r1.min()), float(drift0.max()), float(drift.max())))
    print("entry                     theta  act  edgeMax before->after   edgeMin before->after   torsoDrift before->after")
    for r in rows:
        if "@" in r[0] and not r[0].endswith(("@0.500", "@0.750", "@0.875")):
            continue
        print(f"{r[0]:26s}{r[1]:6.1f} {r[2]:5.2f}   {r[3]:6.2f} -> {r[4]:6.2f}        {r[5]:6.3f} -> {r[6]:6.3f}        {r[7]:6.3f} -> {r[8]:6.3f}")
    np.savez_compressed(a.out, vertices=Lset, delta=Dv, theta0=a.theta0, theta1=a.theta1, source=str(d["source"]),
                        source_sha256=str(d["source_sha256"]), params=json.dumps(vars(a)))
    print("SOLUTION", a.out, "loss", f"{f:.3f}", "max |D| %.4f m" % np.abs(Dv).max())


if __name__ == "__main__":
    main()
