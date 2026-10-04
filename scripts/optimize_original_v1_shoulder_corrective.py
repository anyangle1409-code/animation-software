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
    ap.add_argument("--driver", choices=("abduction", "flexion"), default="abduction", help="abduction: activation = smoothstep(theta) * lam (default, r69-r83); flexion: smoothstep(theta) * (1 - lam), a separate key pair for forward-flexed arms")
    ap.add_argument("--theta0", type=float, default=40.0)
    ap.add_argument("--theta1", type=float, default=150.0)
    ap.add_argument("--declare-mask")
    ap.add_argument("--mask-file", help="restrict solve to left_owned_vertex_ids from an existing pre-edit declaration")
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
    ap.add_argument("--w-area", type=float, default=0.0, help="signed face-area/orientation barrier for mask triangles; disabled by default")
    ap.add_argument("--area-min", type=float, default=0.20, help="minimum signed projected double-area ratio versus the uncorrected pose")
    ap.add_argument("--w-prox", type=float, default=0.0, help="no-new-contact barrier between non-neighbouring mask vertices (sheets must not close below min(base distance, --prox-d))")
    ap.add_argument("--prox-d", type=float, default=0.012)
    ap.add_argument("--w-area-rest", type=float, default=0.0, help="rest-relative face-area floor: triangles touching the mask whose posed/rest area ratio is below --area-floor are penalised (collapse / sliver). (Before the merge with the signed-area barrier this option was called --w-area.)")
    ap.add_argument("--area-floor", type=float, default=0.2)
    ap.add_argument("--w-lap", type=float, default=0.0, help="surface roughness barrier: |v - mean(neighbours)| / mean edge length of a mask vertex may exceed its rest value by at most --lap-tol")
    ap.add_argument("--lap-tol", type=float, default=0.35)
    ap.add_argument("--fold-floor", type=float, default=None, help="absolute dihedral-cosine floor for adjacent triangle pairs that are smooth at rest (cos>0.5); default keeps the old 'never worse than now' rule")
    ap.add_argument("--rounds", type=int, default=1)
    ap.add_argument("--p99-tail", type=float, default=1.95, help="edges currently below this ratio may not rise above it (keeps the 99th percentile); edges above keep the --hi bound")
    ap.add_argument("--w-smooth", type=float, default=20.0)
    ap.add_argument("--w-mag", type=float, default=2.0)
    ap.add_argument("--iters", type=int, default=300)
    ap.add_argument("--init")
    ap.add_argument("--json-out", help="optional machine-readable before/after solve report")
    ap.add_argument("--w-pen", type=float, default=0.0, help="anti-penetration barrier: a moving vertex must stay on the same side of every nearby non-adjacent skin triangle as it is at rest (separation >= --pen-delta)")
    ap.add_argument("--pen-delta", type=float, default=0.002)
    ap.add_argument("--pen-radius", type=float, default=0.05, help="only vertex/triangle pairs closer than this (posed) are constrained")
    ap.add_argument("--pen-rest-min", type=float, default=0.03, help="vertex/triangle pairs closer than this at rest are neighbours on the same surface and are skipped")
    ap.add_argument("--hold-region-max", type=float, default=None, help="regional-maximum guard: mask edges may not stretch above (that region's current whole-mesh maximum edge ratio in that pose) plus this margin")
    ap.add_argument("--w-vol", type=float, default=0.0, help="weight of a mesh-volume floor: in every pose where the key is active, total mesh volume may not fall below --vol-floor x rest volume")
    ap.add_argument("--vol-floor", type=float, default=0.95)
    ap.add_argument("--region-floor", default=None, help="comma list region:ratio (e.g. arm:0.765,torso:0.684): absolute minimum edge ratio for mask edges of that region in EVERY pose (no pose names), enforced with the --w-hold hinge; needs --w-hold")
    ap.add_argument("--hold-scope", choices=("region", "local"), default="region", help="region: bounds from whole-mesh region min/max (comparator metric); local: bounds from the mask edges of each pose (axilla trial selection metric)")
    ap.add_argument("--w-hold", type=float, default=None, help="separate hinge weight for the regional guards (default: merge them into the ordinary bounds with --w-hinge)")
    ap.add_argument("--hold-region-min", type=float, default=None, help="regional-minimum guard: mask edges may not shorten below (that region's current whole-mesh minimum edge ratio in that pose) minus this margin")
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
    if a.declare_mask and a.mask_file:
        raise SystemExit("--declare-mask and --mask-file are mutually exclusive")
    if a.mask_file:
        decl = json.loads(Path(a.mask_file).read_text(encoding="utf-8"))
        source_sha = str(d["source_sha256"].item()) if np.asarray(d["source_sha256"]).shape == () else str(d["source_sha256"])
        if decl.get("source_candidate_sha256") != source_sha:
            raise SystemExit("local mask declaration was created from a different source candidate")
        ids = decl.get("left_owned_vertex_ids")
        if not isinstance(ids, list) or not ids or ids != sorted(set(int(v) for v in ids)):
            raise SystemExit("local mask left_owned_vertex_ids must be non-empty, sorted and unique")
        Lset = np.asarray(ids, dtype=int)
        if (Lset < 0).any() or (Lset >= nV).any() or (rest[Lset, 0] > 1e-8).any():
            raise SystemExit("local mask contains invalid or non-left-owned vertices")
        expected_right = sorted(int(mir[v]) for v in Lset if rest[v, 0] < -1e-8)
        declared_right = sorted(int(v) for v in decl.get("mirror_of_strict_left_vertex_ids", []))
        if declared_right != expected_right:
            raise SystemExit("local mask mirror set disagrees with source mesh")
    else:
        Lset = np.nonzero((rest[:, 0] <= 1e-8) & regs & ((left_gh < a.radius) | (W[:, b["scapula_l"]] > 0.01)))[0]
    Rset = mir[Lset[rest[Lset, 0] < -1e-8]]
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
    _g = (lambda x: x) if a.driver == "abduction" else (lambda x: 1.0 - x)
    al = smoothstep(theta[:, 0], a.theta0, a.theta1) * _g(lam[:, 0])
    ar = smoothstep(theta[:, 1], a.theta0, a.theta1) * _g(lam[:, 1])
    # trunk-driven reference positions (trunk bones only, weights renormalised)
    trunk = [b[n] for n in ("root", "pelvis", "spine_01", "spine_02", "spine_03", "neck", "head") if n in b]
    Wt = np.zeros_like(W)
    Wt[:, trunk] = W[:, trunk]
    Wt = Wt / np.maximum(Wt.sum(axis=1, keepdims=True), 1e-9)
    rest_h = np.c_[rest, np.ones(nV)]
    # Same-pose uncorrected LBS surface. P0 may already include corrective shape keys.
    # The area barrier uses this surface so it can reopen an existing corrective-induced sliver.
    PUNC = np.stack([np.einsum("vb,vbi->vi", W, np.einsum("bij,vj->vbi", mats[p][:, :3, :], rest_h)) for p in range(nP)])
    PTR = np.stack([np.einsum("vb,vbi->vi", Wt[Z], np.einsum("bij,vj->vbi", mats[p][:, :3, :], rest_h[Z])) for p in range(nP)])
    Hr = d["heads"][b["upperarm_r"]]
    rj = np.minimum(np.linalg.norm(rest[Z] - Hl, axis=1), np.linalg.norm(rest[Z] - Hr, axis=1))
    ALLOW = a.trunk_a0 + a.trunk_a1 * np.exp(-(rj / a.trunk_rb) ** 2)
    TORSO = region[Z] == rn.index("torso")
    # edges touching the mask
    Em = E[in_mask[E[:, 0]] | in_mask[E[:, 1]]]
    L0 = np.linalg.norm(rest[Em[:, 0]] - rest[Em[:, 1]], axis=1)
    cur = np.stack([np.log(np.maximum(np.linalg.norm(P0[p][Em[:, 0]] - P0[p][Em[:, 1]], axis=1), 1e-12) / L0) for p in range(nP)])
    LHI = np.where(cur < np.log(a.p99_tail), np.log(a.p99_tail), np.log(a.hi))     # no NEW tail edges; existing tail edges may stay under --hi
    LLO = (np.log(a.lo) * np.ones_like(cur)) if a.abs_lo else np.minimum(np.log(a.lo), cur)                                # never required to be better than the current compression, never allowed to get worse than min(lo, current)
    LLO_H = LHI_H = None
    if a.hold_region_min is not None or a.hold_region_max is not None:
        # Regional guards that mirror the comparator tolerances (region_min_ratio_drop / region_max_ratio_rise): for every pose and region, no mask edge may
        # shorten below that region's CURRENT whole-mesh minimum edge ratio minus --hold-region-min, nor stretch above its CURRENT maximum plus --hold-region-max.
        # Edge region = region shared by both endpoints. Without --w-hold they are merged into the ordinary hinge bounds (earlier behaviour, weight --w-hinge);
        # with --w-hold they get their own, much stronger hinge.
        EA, EB = E[:, 0], E[:, 1]
        L0_all = np.linalg.norm(rest[EA] - rest[EB], axis=1)
        reg_e = np.where(region[EA] == region[EB], region[EA], -1)
        reg_m = reg_e[in_mask[E[:, 0]] | in_mask[E[:, 1]]]
        LLO_H = np.full(cur.shape, -1e9)
        LHI_H = np.full(cur.shape, 1e9)
        for p in range(nP):
            if a.hold_scope == 'local':
                # bounds taken over the MASK edges of this pose (this is how the axilla trial selection measures edge_min_drop / edge_max_rise)
                if a.hold_region_min is not None:
                    LLO_H[p, :] = np.log(max(float(np.exp(cur[p].min())) - a.hold_region_min, 1e-3))
                if a.hold_region_max is not None:
                    LHI_H[p, :] = np.log(float(np.exp(cur[p].max())) + a.hold_region_max)
                continue
            r_all = np.linalg.norm(P0[p][EA] - P0[p][EB], axis=1) / np.maximum(L0_all, 1e-12)
            for rg in np.unique(reg_m[reg_m >= 0]):
                sel = reg_m == rg
                if a.hold_region_min is not None:
                    LLO_H[p, sel] = np.log(max(float(r_all[reg_e == rg].min()) - a.hold_region_min, 1e-3))
                if a.hold_region_max is not None:
                    LHI_H[p, sel] = np.log(float(r_all[reg_e == rg].max()) + a.hold_region_max)
        if a.w_hold is None:
            LLO = np.maximum(LLO, LLO_H)
            LHI = np.minimum(LHI, LHI_H)
            LLO_H = LHI_H = None
    if a.region_floor:
        if a.w_hold is None:
            raise SystemExit('--region-floor needs --w-hold')
        EA, EB = E[:, 0], E[:, 1]
        reg_e2 = np.where(region[EA] == region[EB], region[EA], -1)
        reg_m2 = reg_e2[in_mask[EA] | in_mask[EB]]
        if LLO_H is None:
            LLO_H = np.full(cur.shape, -1e9)
            LHI_H = np.full(cur.shape, 1e9)
        for item in a.region_floor.split(','):
            rname, fl = item.split(':')
            sel2 = reg_m2 == rn.index(rname)
            LLO_H[:, sel2] = np.maximum(LLO_H[:, sel2], np.log(float(fl)))
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
    # rest geometry of the same triangles/pairs: face areas, and which adjacent pairs are smooth at rest
    _n0 = np.cross(rest[Tz[:, 1]] - rest[Tz[:, 0]], rest[Tz[:, 2]] - rest[Tz[:, 0]])
    AREA0 = np.maximum(0.5 * np.linalg.norm(_n0, axis=1), 1e-12)
    _u0 = _n0 / np.maximum(np.linalg.norm(_n0, axis=1), 1e-18)[:, None]
    SMOOTH_REST = (_u0[adj[:, 0]] * _u0[adj[:, 1]]).sum(axis=1) > 0.5
    # roughness barrier set-up: directed neighbour pairs (v in the mask, u any neighbour)
    _dv = np.concatenate([E[in_mask[E[:, 0]], 0], E[in_mask[E[:, 1]], 1]])
    _du = np.concatenate([E[in_mask[E[:, 0]], 1], E[in_mask[E[:, 1]], 0]])
    LV = np.array([zpos[int(v)] for v in _dv])                        # zone index of v for each directed pair
    LDEG = np.maximum(np.bincount(LV, minlength=len(Z)).astype(float), 1.0)
    LEL = np.maximum(np.bincount(LV, weights=np.linalg.norm(rest[_dv] - rest[_du], axis=1), minlength=len(Z)) / LDEG, 1e-9)

    def lap_vec(Pp_):
        sn = np.zeros((len(Z), 3))
        np.add.at(sn, LV, Pp_[_du])
        return Pp_[Z] - sn / LDEG[:, None]
    LAP0 = np.linalg.norm(lap_vec(rest), axis=1) / LEL
    if a.w_fold > 0 and a.fold_floor is not None:
        FOLD = np.where(SMOOTH_REST[None, :], a.fold_floor, FOLD)
    # Signed projected face-area/orientation target against the SAME-POSE UNCORRECTED LBS surface.
    # This is intentionally not P0: P0 may already contain the r55 sliver. A negative ratio
    # means reversal relative to uncorrected LBS; a small positive ratio means collapse.
    AREA_N0 = AREA_DEN = None
    if a.w_area > 0:
        area_n0, area_den = [], []
        for p in range(nP):
            A0_, B0_, C0_ = PUNC[p][Tz[:, 0]], PUNC[p][Tz[:, 1]], PUNC[p][Tz[:, 2]]
            n0 = np.cross(B0_ - A0_, C0_ - A0_)
            area_n0.append(n0)
            area_den.append(np.maximum((n0 * n0).sum(axis=1), 1e-18))
        AREA_N0 = np.stack(area_n0)
        AREA_DEN = np.stack(area_den)

    # no-new-contact barrier: pairs of mask vertices far apart on the rest surface (>= 3 cm) that are close in a pose
    rZ = rest[Z]
    far_rest = None

    def find_pairs(Pc, base):
        """Pairs (i, j) (zone indices, i < j) within 2.5 x prox-d now or in the base pose; dmin = min(base distance, prox-d)."""
        out = []
        for lo in range(0, len(Z), 600):
            blk = slice(lo, min(lo + 600, len(Z)))
            dnow = np.linalg.norm(Pc[blk, None, :] - Pc[None, :, :], axis=2)
            dbase = np.linalg.norm(base[blk, None, :] - base[None, :, :], axis=2)
            drest = np.linalg.norm(rZ[blk, None, :] - rZ[None, :, :], axis=2)
            ii, jj = np.nonzero(((dnow < 2.5 * a.prox_d) | (dbase < 2.5 * a.prox_d)) & (drest > 0.03))
            ii = ii + lo
            keep = ii < jj
            out.append(np.stack([ii[keep], jj[keep]], axis=1))
        pr = np.concatenate(out) if out else np.zeros((0, 2), int)
        db = np.linalg.norm(base[pr[:, 0]] - base[pr[:, 1]], axis=1)
        return pr, np.minimum(db, a.prox_d) * 0.95

    # anti-penetration barrier set-up: triangles that touch the mask, their REST centroids/normals (side reference) and per-pose constrained (vertex, triangle) pairs
    TP = d["tris"][in_mask[d["tris"]].any(axis=1)]
    _r0, _r1, _r2 = rest[TP[:, 0]], rest[TP[:, 1]], rest[TP[:, 2]]
    CT0 = (_r0 + _r1 + _r2) / 3.0
    _n = np.cross(_r1 - _r0, _r2 - _r0)
    NT0 = _n / np.maximum(np.linalg.norm(_n, axis=1, keepdims=True), 1e-18)
    PEN = [None] * nP

    def find_pen(Pfull):
        """(vertex id, triangle row, side sign at rest, fixed current normal) for posed vertex/triangle pairs within --pen-radius that are far apart at rest."""
        c = (Pfull[TP[:, 0]] + Pfull[TP[:, 1]] + Pfull[TP[:, 2]]) / 3.0
        nn = np.cross(Pfull[TP[:, 1]] - Pfull[TP[:, 0]], Pfull[TP[:, 2]] - Pfull[TP[:, 0]])
        nn = nn / np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-18)
        vs, ts = [], []
        for lo in range(0, len(Z), 300):
            vb = Z[lo:lo + 300]
            near = np.linalg.norm(Pfull[vb][:, None, :] - c[None, :, :], axis=2) < a.pen_radius
            far = np.linalg.norm(rest[vb][:, None, :] - CT0[None, :, :], axis=2) > a.pen_rest_min
            member = (TP[None, :, :] == vb[:, None, None]).any(axis=2)
            ii, jj = np.nonzero(near & far & ~member)
            vs.append(vb[ii])
            ts.append(jj)
        v_ = np.concatenate(vs) if vs else np.zeros(0, int)
        t_ = np.concatenate(ts) if ts else np.zeros(0, int)
        sg = np.sign(((rest[v_] - CT0[t_]) * NT0[t_]).sum(axis=1))
        sg[sg == 0] = 1.0
        return v_, t_, sg, nn[t_]

    PAIRS = [np.zeros((0, 2), int) for _ in range(nP)]
    PDMIN = [np.zeros(0) for _ in range(nP)]
    zidx = -np.ones(nV, int)
    zidx[Z] = np.arange(len(Z))

    def net_fields(Dv):
        DL = np.zeros((len(Z), 3))
        DR = np.zeros((len(Z), 3))
        np.add.at(DL, Lz, Dv)
        np.add.at(DR, Rz, Dv * S)
        return DL, DR

    tris_all = d['tris']
    VREST = float(np.einsum('ij,ij->i', rest[tris_all[:, 0]], np.cross(rest[tris_all[:, 1]], rest[tris_all[:, 2]])).sum() / 6.0)

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
            if LLO_H is not None:
                oh, uh = np.maximum(lr - LHI_H[p], 0.0), np.maximum(LLO_H[p] - lr, 0.0)
                total += a.w_hold * ((oh ** 2).sum() + (uh ** 2).sum())
                g = g + a.w_hold * 2.0 * (oh - uh)
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
            if a.w_area_rest > 0:
                _A, _B, _C = Pp[Tz[:, 0]], Pp[Tz[:, 1]], Pp[Tz[:, 2]]
                _n = np.cross(_B - _A, _C - _A)
                _ln = np.maximum(np.linalg.norm(_n, axis=1), 1e-12)
                _ex = np.maximum(a.area_floor - 0.5 * _ln / AREA0, 0.0)
                if (_ex > 0).any():
                    total += a.w_area_rest * (_ex ** 2).sum()
                    _gn = (-2.0 * a.w_area_rest * _ex / AREA0 * 0.5 / _ln)[:, None] * _n          # d penalty / d n
                    np.add.at(gP, Tz[:, 0], np.cross(_gn, _C - _B))
                    np.add.at(gP, Tz[:, 1], np.cross(_gn, _A - _C))
                    np.add.at(gP, Tz[:, 2], np.cross(_gn, _B - _A))
            if a.w_vol > 0:
                _a, _b, _c = Pp[tris_all[:, 0]], Pp[tris_all[:, 1]], Pp[tris_all[:, 2]]
                _V = np.einsum('ij,ij->i', _a, np.cross(_b, _c)).sum() / 6.0
                _exv = max(a.vol_floor * VREST - _V, 0.0) / VREST
                if _exv > 0:
                    total += a.w_vol * _exv ** 2
                    _s = -2.0 * a.w_vol * _exv / VREST / 6.0
                    np.add.at(gP, tris_all[:, 0], _s * np.cross(_b, _c))
                    np.add.at(gP, tris_all[:, 1], _s * np.cross(_c, _a))
                    np.add.at(gP, tris_all[:, 2], _s * np.cross(_a, _b))
            if a.w_lap > 0:
                _l = lap_vec(Pp)
                _ln2 = np.maximum(np.linalg.norm(_l, axis=1), 1e-12)
                _ex2 = np.maximum(_ln2 / LEL - LAP0 - a.lap_tol, 0.0)
                if (_ex2 > 0).any():
                    total += a.w_lap * (_ex2 ** 2).sum()
                    _gl = (2.0 * a.w_lap * _ex2 / LEL / _ln2)[:, None] * _l
                    gP[Z] += _gl
                    np.add.at(gP, _du, -(_gl / LDEG[:, None])[LV])
            if a.w_area > 0:
                A_, B_, C_ = Pp[Tz[:, 0]], Pp[Tz[:, 1]], Pp[Tz[:, 2]]
                n = np.cross(B_ - A_, C_ - A_)
                signed_area_ratio = (n * AREA_N0[p]).sum(axis=1) / AREA_DEN[p]
                ax = np.maximum(a.area_min - signed_area_ratio, 0.0)
                if (ax > 0).any():
                    total += a.w_area * (ax ** 2).sum()
                    gn = ((-2.0 * a.w_area * ax) / AREA_DEN[p])[:, None] * AREA_N0[p]
                    np.add.at(gP, Tz[:, 0], np.cross(gn, C_ - B_))
                    np.add.at(gP, Tz[:, 1], np.cross(gn, A_ - C_))
                    np.add.at(gP, Tz[:, 2], np.cross(gn, B_ - A_))
            if a.w_pen > 0 and PEN[p] is not None and len(PEN[p][0]):
                pv, pt, psg, pn = PEN[p]
                cT = (Pp[TP[pt, 0]] + Pp[TP[pt, 1]] + Pp[TP[pt, 2]]) / 3.0
                s_ = psg * ((Pp[pv] - cT) * pn).sum(axis=1)
                ex_p = np.maximum(a.pen_delta - s_, 0.0)
                if (ex_p > 0).any():
                    total += a.w_pen * (ex_p ** 2).sum()
                    gs = (-2.0 * a.w_pen * ex_p * psg)[:, None] * pn
                    np.add.at(gP, pv, gs)
                    for k_ in range(3):
                        np.add.at(gP, TP[pt, k_], -gs / 3.0)
            if a.w_prox > 0 and len(PAIRS[p]):
                pr, dmin = PAIRS[p], PDMIN[p]
                pi_, pj_ = Z[pr[:, 0]], Z[pr[:, 1]]
                dd = Pp[pi_] - Pp[pj_]
                dn_ = np.maximum(np.linalg.norm(dd, axis=1), 1e-9)
                ex_ = np.maximum(dmin - dn_, 0.0)
                total += a.w_prox * (ex_ ** 2).sum()
                gq = (-2.0 * a.w_prox * ex_ / dn_)[:, None] * dd
                np.add.at(gP, pi_, gq)
                np.add.at(gP, pj_, -gq)
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
        source_sha = str(d["source_sha256"].item()) if np.asarray(d["source_sha256"]).shape == () else str(d["source_sha256"])
        init_sha = str(s0["source_sha256"].item()) if "source_sha256" in s0 and np.asarray(s0["source_sha256"]).shape == () else str(s0["source_sha256"]) if "source_sha256" in s0 else ""
        if init_sha != source_sha:
            raise SystemExit("--init solution was solved against a different source candidate; refusing double-application")
        mp = {int(v): k for k, v in enumerate(s0["vertices"])}
        for k, v in enumerate(Lset):
            if int(v) in mp:
                x[3 * k:3 * k + 3] = s0["delta"][mp[int(v)]]
    def refresh_pairs(xv):
        if a.w_prox <= 0:
            return
        Dv_ = xv.reshape(nL, 3)
        DL_, DR_ = net_fields(Dv_)
        tot = 0
        for p in range(nP):
            if al[p] <= 0 and ar[p] <= 0:
                continue
            Pc = P0[p][Z] + np.einsum("vij,vj->vi", A[p], al[p] * DL_ + ar[p] * DR_)
            PAIRS[p], PDMIN[p] = find_pairs(Pc, P0[p][Z])
            tot += len(PAIRS[p])
        print("contact pairs refreshed:", tot, flush=True)

    def refresh_pen(xv):
        if a.w_pen <= 0:
            return
        DL_, DR_ = net_fields(xv.reshape(nL, 3))
        tot = viol = 0
        for p in range(nP):
            if al[p] <= 0 and ar[p] <= 0:
                continue
            Pc = P0[p].copy()
            Pc[Z] += np.einsum("vij,vj->vi", A[p], al[p] * DL_ + ar[p] * DR_)
            PEN[p] = find_pen(Pc)
            pv, pt, psg, pn = PEN[p]
            cT = (Pc[TP[pt, 0]] + Pc[TP[pt, 1]] + Pc[TP[pt, 2]]) / 3.0
            tot += len(pv)
            viol += int((psg * ((Pc[pv] - cT) * pn).sum(axis=1) < 0).sum())
        print("penetration pairs refreshed:", tot, "currently on the wrong side:", viol, flush=True)

    refresh_pairs(x)
    refresh_pen(x)
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
        if a.rounds > 1 and it % max(a.iters // a.rounds, 1) == 0 and it < a.iters:
            refresh_pairs(x)
            refresh_pen(x)
            f, g = loss_grad(x)
            S_, Y_ = [], []
        if it % 25 == 0 or it == 1:
            print(f"iter {it:4d} loss {f:.3f} |g| {np.linalg.norm(g):.3e} max|D| {np.abs(x).max():.4f}")
    Dv = x.reshape(nL, 3)
    DL, DR = net_fields(Dv)
    # report: per entry metrics before/after, including local signed face area vs uncorrected LBS
    rows = []
    report_rows = []
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
        row = (poses[p], float(theta[p, 0]), float(al[p]), float(r0.max()), float(r1.max()), float(r0.min()), float(r1.min()), float(drift0.max()), float(drift.max()))
        rows.append(row)
        rr = {"entry": poses[p], "theta_l_deg": float(theta[p, 0]), "activation_l": float(al[p]),
              "edge_max_before": float(r0.max()), "edge_max_after": float(r1.max()),
              "edge_min_before": float(r0.min()), "edge_min_after": float(r1.min()),
              "torso_drift_max_before_m": float(drift0.max()), "torso_drift_max_after_m": float(drift.max())}
        if AREA_N0 is not None:
            def signed_area_ratio(P):
                Aa, Bb, Cc = P[Tz[:, 0]], P[Tz[:, 1]], P[Tz[:, 2]]
                nn = np.cross(Bb - Aa, Cc - Aa)
                return (nn * AREA_N0[p]).sum(axis=1) / AREA_DEN[p]
            sb, sa = signed_area_ratio(P0[p]), signed_area_ratio(Pp)
            rr.update({"signed_area_min_before": float(sb.min()), "signed_area_min_after": float(sa.min()),
                       "faces_below_area_min_before": int((sb < a.area_min).sum()), "faces_below_area_min_after": int((sa < a.area_min).sum()),
                       "flipped_faces_before": int((sb < 0.0).sum()), "flipped_faces_after": int((sa < 0.0).sum())})
        report_rows.append(rr)
    print("entry                     theta  act  edgeMax before->after   edgeMin before->after   torsoDrift before->after")
    for r in rows:
        if "@" in r[0] and not r[0].endswith(("@0.500", "@0.750", "@0.875")):
            continue
        print(f"{r[0]:26s}{r[1]:6.1f} {r[2]:5.2f}   {r[3]:6.2f} -> {r[4]:6.2f}        {r[5]:6.3f} -> {r[6]:6.3f}        {r[7]:6.3f} -> {r[8]:6.3f}")
    if a.json_out:
        source_sha = str(d["source_sha256"].item()) if np.asarray(d["source_sha256"]).shape == () else str(d["source_sha256"])
        report = {"schema_version": 1, "source_candidate": str(d["source"].item()) if np.asarray(d["source"]).shape == () else str(d["source"]),
                  "source_candidate_sha256": source_sha, "mask_file": a.mask_file, "solution": a.out,
                  "final_loss": float(f), "max_abs_delta_m": float(np.abs(Dv).max()), "area_reference": "same_pose_uncorrected_lbs",
                  "parameters": vars(a), "entries": report_rows}
        Path(a.json_out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    np.savez_compressed(a.out, vertices=Lset, delta=Dv, theta0=a.theta0, theta1=a.theta1, source=str(d["source"]),
                        source_sha256=str(d["source_sha256"]), params=json.dumps(vars(a)))
    print("SOLUTION", a.out, "loss", f"{f:.3f}", "max |D| %.4f m" % np.abs(Dv).max())


if __name__ == "__main__":
    main()
