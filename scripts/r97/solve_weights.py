"""r97 shoulder-girdle weight solve (offline, numpy/scipy).

Harmonic (cotangent-Laplacian) interpolation on the body SURFACE between anatomical anchors, solved for the left side and
mirrored to the right. Weights diffuse along the skin only, so they cannot jump across the gap between the hanging arm and the
ribs, and the result is smooth (no staircase from 4-influence truncation).

usage: solve_weights.py rest.npz mirror_idx.npy params.json out.npz
"""
import json
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl
from scipy.sparse.csgraph import connected_components

rest, mirror_path, params_path, out = sys.argv[1:5]
d = np.load(rest)
co, tris, W0 = d["co"], d["tris"], d["W"].astype(np.float64)
names = [str(x) for x in d["names"]]
bn = [str(x) for x in d["bn"]]
bone = {b: (d["bh"][i], d["bt"][i]) for i, b in enumerate(bn)}
ix = {n: i for i, n in enumerate(names)}
mirror = np.load(mirror_path)
P = json.load(open(params_path))
n = len(co)


def cotan_laplacian(V, T):
    I, J, Wt = [], [], []
    for k in range(3):
        i, j, o = T[:, k], T[:, (k + 1) % 3], T[:, (k + 2) % 3]
        u, v = V[i] - V[o], V[j] - V[o]
        cot = np.einsum("ij,ij->i", u, v) / np.maximum(np.linalg.norm(np.cross(u, v), axis=1), 1e-12)
        cot = np.clip(cot, -P.get("cot_clip", 5.0), P.get("cot_clip", 5.0))
        I += [i, j]; J += [j, i]; Wt += [0.5 * cot, 0.5 * cot]
    I, J, Wt = np.concatenate(I), np.concatenate(J), np.concatenate(Wt)
    Wt = np.maximum(Wt, P.get("min_edge_weight", 1e-4))       # keep the operator an M-matrix (max principle -> weights stay in [0,1])
    A = sp.coo_matrix((Wt, (I, J)), shape=(len(V), len(V))).tocsr()
    return sp.diags(np.asarray(A.sum(1)).ravel()) - A


def seg_dist(p, a, b):
    ab = b - a
    t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(p - (a + np.outer(t, ab)), axis=1), t


L = cotan_laplacian(co, tris)

# ---------------------------------------------------------------- left-side classification
x, y, z = co[:, 0], co[:, 1], co[:, 2]
left = x < -1e-6
dom = W0.argmax(1)
dom_name = np.array(names)[dom]
C = bone["upperarm_l"][0]                                 # glenohumeral centre
arm_axis = (bone["upperarm_l"][1] - C) / np.linalg.norm(bone["upperarm_l"][1] - C)

# arm tube: connected component of the left side below the axilla that contains the elbow
below = left & (z < P["axilla_cut_z"])
adj = sp.coo_matrix((np.ones(len(tris) * 3), (np.r_[tris[:, 0], tris[:, 1], tris[:, 2]], np.r_[tris[:, 1], tris[:, 2], tris[:, 0]])), shape=(n, n)).tocsr()
sub = np.nonzero(below)[0]
ncomp, lab = connected_components(adj[sub][:, sub], directed=False)
elbow = bone["forearm_l"][0]
elbow_v = sub[np.argmin(np.linalg.norm(co[sub] - elbow, axis=1))]
arm_tube = np.zeros(n, bool); arm_tube[sub[lab == lab[np.searchsorted(sub, elbow_v)]]] = True

PERMIT = {"spine_02", "spine_03", "clavicle_l", "scapula_l", "upperarm_l"}
pidx = np.array([ix[b] for b in PERMIT])
neckish = np.isin(dom_name, ["neck", "head"])
if P.get("protect_neck_boundary"):
    neckish |= (W0[:, ix["neck"]] + W0[:, ix["head"]]) > P.get("neck_boundary_threshold", 0.15)      # protected neck boundary keeps r95 weights exactly
domain = left & (z > P["torso_floor_z"]) & ~neckish & ~(arm_tube & (z < P["arm_fixed_z"]))
domain &= ~np.isin(dom_name, ["forearm_l", "forearm_tw0_l", "forearm_tw1_l", "hand_l"])
# vertices whose r95 weight involves only non-permitted bones (e.g. neck/pelvis blends) stay fixed
domain &= W0[:, pidx].sum(1) > 1e-6
if "neck_band_free" in P:
    # protected neck-boundary vertices: the declared-bone share is re-solved (free in the harmonic solve) instead of frozen at
    # r95's uneven girdle weights; neck/head weights are restored exactly afterwards by preserve_nonpermitted
    NB = P["neck_band_free"]
    domain |= left & neckish & ~np.isin(dom_name, ["neck", "head"]) & (z > NB["z_min"]) & (z < NB["z_max"]) & (W0[:, pidx].sum(1) > 1e-6)

fixed_vals = {}                                          # vertex -> weight row (full)


def setw(mask, comp):
    row = np.zeros(len(names))
    for b, v in comp.items():
        row[ix[b]] = v
    for i in np.nonzero(mask)[0]:
        fixed_vals[int(i)] = row


# anchors (inside the domain); later anchors override earlier ones
nrm_back = y  # +y is posterior
spine_split = lambda zz: np.clip((zz - P["spine23_z0"]) / (P["spine23_z1"] - P["spine23_z0"]), 0, 1)

# trunk beyond the glenohumeral junction -> spine only (split spine_02/spine_03 by height); the transition is confined to
# the junction around the joint, so the rib-cage wall stretches with the folds but never rotates with the arm
dC = np.linalg.norm(co - C, axis=1)
t_arm = (co - C) @ arm_axis
rib = domain & ~arm_tube & ((z < P["rib_anchor_z"]) | (dC > P.get("junction_radius", 9.0)))
for i in np.nonzero(rib)[0]:
    t = spine_split(z[i]); fixed_vals[int(i)] = None
    row = np.zeros(len(names)); row[ix["spine_03"]] = t; row[ix["spine_02"]] = 1 - t; fixed_vals[int(i)] = row
# medial chest (sternal half of the pec) and medial back (paraspinal) -> spine_03
med = domain & ~arm_tube & (x > P["medial_x"]) & (z < P["clavicle_z_cap"])
for i in np.nonzero(med)[0]:
    t = spine_split(z[i]); row = np.zeros(len(names)); row[ix["spine_03"]] = t; row[ix["spine_02"]] = 1 - t; fixed_vals[int(i)] = row
# skin over the scapular body -> partial scapula (skin slides over the bone)
sa, sb = bone["scapula_l"]
sc_c = np.array(P["scapula_centre"])
r = np.linalg.norm((co - sc_c) * np.array([1.0, 0.0, 1.0]), axis=1)
scap = domain & ~arm_tube & (y > P["back_y"]) & (r < P["scapula_radius"]) & (x > P.get("scapula_x_lateral_limit", -9.0))
for i in np.nonzero(scap)[0]:
    f = P["scapula_share"] * (1 - (r[i] / P["scapula_radius"]) ** 2) ** 2
    if f <= 0.02:
        continue
    row = np.zeros(len(names)); row[ix["scapula_l"]] = f; row[ix["spine_03"]] = 1 - f; fixed_vals[int(i)] = row
# clavicle ridge
ca, cb = bone["clavicle_l"]
dcl, tcl = seg_dist(co, ca, cb)
clav = domain & (dcl < P["clavicle_radius"]) & (tcl > P["clavicle_t0"]) & (y < P["clavicle_front_y"])
for i in np.nonzero(clav)[0]:
    f = P["clavicle_share"] * min(1.0, (tcl[i] - P["clavicle_t0"]) / 0.25)
    row = np.zeros(len(names)); row[ix["clavicle_l"]] = f; row[ix["spine_03"]] = 1 - f; fixed_vals[int(i)] = row
# upper trapezius slope (neck base -> acromion, top and back of the shoulder): trunk girdle mix, no arm share
if "trapezius" in P:
    T_ = P["trapezius"]
    dCt = np.linalg.norm(co - C, axis=1)
    trap = domain & (z > T_["z_min"]) & (x > T_["x_lateral"]) & (y > T_["y_min"]) & (dCt > T_["min_dist_from_joint"])
    for i in np.nonzero(trap)[0]:
        f = 1.0
        if "x_medial_ramp" in T_:                       # girdle share ramps in from the spinal midline
            a0, a1 = T_["x_medial_ramp"]
            tt = np.clip((x[i] - a0) / (a1 - a0), 0, 1); f = tt * tt * (3 - 2 * tt)
        row = np.zeros(len(names)); row[ix["spine_03"]] = 1 - f * (1 - T_["spine"]); row[ix["clavicle_l"]] = f * T_["clavicle"]; row[ix["scapula_l"]] = f * T_["scapula"]
        fixed_vals[int(i)] = row
# spinal midline at the neck base: follows the spine only (no girdle share crossing the midline)
if "midline_spine" in P:
    M_ = P["midline_spine"]
    # includes protected neck-boundary vertices: their neck/head share is restored exactly by preserve_nonpermitted, only the
    # declared-bone part becomes spine_03 (r95 put up to ~0.5 clavicle+scapula on midline neck-base vertices)
    mid = left & (x > -M_["x"]) & (z > M_["z_min"]) & (z < M_["z_max"]) & (W0[:, pidx].sum(1) > 1e-6)
    domain = domain | mid
    setw(mid, {"spine_03": 1.0})
# acromion / top of the shoulder cap
acr = np.array(P["acromion"])
dac = np.linalg.norm(co - acr, axis=1)
acrm = domain & (dac < P["acromion_radius"])
for i in np.nonzero(acrm)[0]:
    row = np.zeros(len(names)); row[ix["scapula_l"]] = P["acromion_scapula"]; row[ix["clavicle_l"]] = P["acromion_clavicle"]
    row[ix["upperarm_l"]] = 1 - P["acromion_scapula"] - P["acromion_clavicle"]; fixed_vals[int(i)] = row
# humerus beyond the junction: the arm moves rigidly with the humerus (deltoid body, biceps, triceps)
if "arm_t0" in P:
    armfix = domain & (t_arm > P["arm_t0"]) & (dC < 0.25) & (co[:, 0] < C[0] + P.get("arm_medial_margin", 0.03))
    if P.get("armfix_lateral_only"):
        armfix &= arm_tube & ((co[:, 0] < C[0] - P.get("armfix_lateral_x", 0.0)) | (t_arm > P.get("arm_t_all", 0.15)))
    elif P.get("armfix_tube_only"):
        armfix &= arm_tube
    else:
        armfix &= (arm_tube | (np.linalg.norm(np.cross(co - C, arm_axis), axis=1) < P.get("arm_radius", 0.065)))
    for i in np.nonzero(armfix)[0]:
        row = np.zeros(len(names)); row[ix["upperarm_l"]] = 1.0; fixed_vals[int(i)] = row
# arm tube below the deltoid insertion stays as r95 (boundary, outside the domain)

free = np.array(sorted(set(np.nonzero(domain)[0]) - set(k for k, v in fixed_vals.items() if v is not None)))
fixed_dom = np.array(sorted(k for k, v in fixed_vals.items() if v is not None))
boundary = np.nonzero(~domain)[0]                          # all non-domain vertices keep r95 weights
Wb = W0.copy()
for k in fixed_dom:
    Wb[k] = fixed_vals[k]
known = np.r_[fixed_dom, boundary].astype(int)
Lff = L[free][:, free].tocsc()
Lfk = L[free][:, known]
rhs = -(Lfk @ Wb[known])
if "soft" in P:
    # screened harmonic: soft pulls toward pure humerus on the arm surface and pure spine on the distant trunk, rising smoothly
    # with distance from the joint -> rigid arm / still ribs without the tearing of hard anchors near the junction
    S = P["soft"]
    def ss(e0, e1, v):
        t = np.clip((v - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
    t_arm = (co - C) @ arm_axis
    dC = np.linalg.norm(co - C, axis=1)
    lateral = co[:, 0] < C[0] - S.get("lateral_x", 0.01)
    arm_like = arm_tube | (lateral & (t_arm > -0.03))
    lam_arm = S["arm_lambda"] * ss(S["arm_t0"], S["arm_t1"], t_arm) * arm_like
    lam_trk = S["trunk_lambda"] * ss(S["trunk_r0"], S["trunk_r1"], dC) * (~arm_like)
    lam = (lam_arm + lam_trk)[free]
    target = np.zeros((len(free), len(names)))
    fa = arm_like[free]
    target[fa, ix["upperarm_l"]] = 1.0
    tz = np.clip((z[free] - P["spine23_z0"]) / (P["spine23_z1"] - P["spine23_z0"]), 0, 1)
    target[~fa, ix["spine_03"]] = tz[~fa]; target[~fa, ix["spine_02"]] = 1 - tz[~fa]
    Lff = (Lff + sp.diags(lam)).tocsc()
    rhs = rhs + lam[:, None] * target
lu = spl.splu(Lff)
Wf = lu.solve(rhs)
Wn = Wb.copy(); Wn[free] = Wf
Wn = np.clip(Wn, 0, None)

if P.get("geodesic_u"):
    # Arm share from surface distance: u = dT / (dT + dA) along the skin, between the trunk-rigid anchors (T) and the humerus-
    # rigid arm (A). Spreads the trunk->arm change evenly along the real skin path (armpit unfolds row by row) and cannot jump
    # across the gap between the hanging arm and the ribs. Trunk-side bone proportions come from the harmonic solve.
    from scipy.sparse.csgraph import dijkstra
    G = P["geodesic_u"]
    e = np.r_[tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]
    ln = np.linalg.norm(co[e[:, 0]] - co[e[:, 1]], axis=1)
    keep = left[e[:, 0]] & left[e[:, 1]]
    Gm = sp.coo_matrix((ln[keep], (e[keep, 0], e[keep, 1])), shape=(n, n)).tocsr(); Gm = Gm.maximum(Gm.T)
    t_arm = (co - C) @ arm_axis
    dC = np.linalg.norm(co - C, axis=1)
    A = left & arm_tube & (t_arm > G["arm_t"])
    T = left & ~arm_tube & ((dC > G["trunk_r"]) | (z < G["trunk_z"]))
    dA = dijkstra(Gm, indices=np.nonzero(A)[0], min_only=True)
    dT = dijkstra(Gm, indices=np.nonzero(T)[0], min_only=True)
    rows = np.nonzero(domain)[0]
    u = np.clip(dT[rows] / np.maximum(dT[rows] + dA[rows], 1e-9), 0, 1)
    u = u ** G.get("gamma", 1.0)
    ua_ = ix["upperarm_l"]
    tw = Wn[rows].copy(); tw[:, ua_] = 0
    for k, i in enumerate(rows):
        s_ = tw[k].sum()
        if s_ < 1e-6:                                   # no trunk proportions here: give the trunk share to the spine
            tw[k] = 0; t = spine_split(z[i]); tw[k, ix["spine_03"]] = t; tw[k, ix["spine_02"]] = 1 - t; s_ = 1.0
        tw[k] /= s_
    Wn[rows] = tw * (1 - u)[:, None]
    Wn[rows, ua_] = u

def smoothstep(e0, e1, v):
    t = np.clip((v - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)

def move_to_spine(rows, removed):
    t = spine_split(z[rows])
    Wn[rows, ix["spine_03"]] += removed * t
    Wn[rows, ix["spine_02"]] += removed * (1 - t)

if "shape" in P:
    S = P["shape"]
    dC = np.linalg.norm(co - C, axis=1)
    t_arm = (co - C) @ arm_axis
    dom_rows = np.nonzero(domain)[0]
    medial = co[dom_rows, 0] > C[0] - S["medial_offset"]          # trunk side of the joint
    # 1. arm share fades out on the trunk with distance from the joint
    f = smoothstep(S["trunk_r_out"], S["trunk_r_in"], dC[dom_rows])
    rows = dom_rows[medial & ~arm_tube[dom_rows]]
    fr = f[medial & ~arm_tube[dom_rows]]
    ua_ = ix["upperarm_l"]
    removed = Wn[rows, ua_] * (1 - fr)
    Wn[rows, ua_] *= fr
    move_to_spine(rows, removed)
    # 2. scapula share fades out on the front and side of the chest
    rows = dom_rows[~arm_tube[dom_rows] & (co[dom_rows, 1] < S["back_y"])]
    g = smoothstep(S["scap_r_out"], S["scap_r_in"], dC[rows])
    sc_ = ix["scapula_l"]
    removed = Wn[rows, sc_] * (1 - g)
    Wn[rows, sc_] *= g
    move_to_spine(rows, removed)
    # 3. the humerus carries the arm surface rigidly beyond the junction (lateral/arm side only)
    rows = dom_rows[arm_tube[dom_rows] | (co[dom_rows, 0] < C[0] - S["lateral_offset"])]
    sv = smoothstep(S["arm_t0"], S["arm_t1"], t_arm[rows])
    u0 = Wn[rows, ua_].copy()
    u1 = u0 + (1 - u0) * sv
    others = np.ones(len(names), bool); others[ua_] = False
    sc_f = np.where(u0 < 1 - 1e-9, (1 - u1) / np.maximum(1 - u0, 1e-9), 0.0)
    Wn[np.ix_(rows, np.nonzero(others)[0])] *= sc_f[:, None]
    Wn[rows, ua_] = u1

# prune to 4 influences, renormalise (runtime limit)
def prune4(Wm, rows):
    for i in rows:
        w = Wm[i]
        prot = np.zeros(len(w), bool); prot[PROTECT_COLS] = True
        prot &= w > 0
        if np.count_nonzero(w > 1e-6) > 4:
            free_c = np.nonzero(~prot & (w > 1e-6))[0]
            k = max(0, 4 - int(prot.sum()))
            keep = free_c[np.argsort(w[free_c])[-k:]] if k else np.array([], int)
            m = np.zeros_like(w); m[keep] = w[keep]; m[prot] = w[prot]; w = m
        small = (w < P.get("min_weight", 0.01)) & ~prot
        w[small] = 0
        # renormalise only the declared share so protected weights stay exact
        ps = w[~prot].sum(); target = 1 - w[prot].sum()
        if ps > 0:
            w[~prot] *= target / ps
            Wm[i] = w
            continue
        s = w.sum(); Wm[i] = w / s if s > 0 else W0[i]
    return Wm

# arm tube below the solve region: keep only arm-chain influences (r95 carried stray scapula/clavicle/spine traces)
ARM_CHAIN = [ix[b] for b in names if b in ("upperarm_l", "forearm_l", "forearm_tw0_l", "forearm_tw1_l", "hand_l")]
clean = arm_tube & ~domain & (z > P.get("arm_clean_z0", 1.15))
for i in np.nonzero(clean)[0]:
    # stray girdle/trunk traces move to the humerus; forearm/hand weights stay exactly as they were
    removed = Wn[i].sum() - Wn[i, ARM_CHAIN].sum()
    if Wn[i, ARM_CHAIN].sum() > 0.5 and removed > 0:
        w = np.zeros(len(names)); w[ARM_CHAIN] = Wn[i, ARM_CHAIN]; w[ix["upperarm_l"]] += removed
        Wn[i] = w
edited = np.nonzero(domain | clean)[0]
if P.get("gh_helper"):
    # rotation-aware split: the harmonic arm share u is re-expressed across trunk -> half-rotation helper -> humerus, so no
    # vertex blends across the full glenohumeral angle (chord collapse); partition of unity is preserved exactly
    names += ["glenohumeral_half_l", "glenohumeral_half_r"]
    ix["glenohumeral_half_l"], ix["glenohumeral_half_r"] = len(names) - 2, len(names) - 1
    Wn = np.c_[Wn, np.zeros((n, 2))]; W0 = np.c_[W0, np.zeros((n, 2))]
    ua, hh = ix["upperarm_l"], ix["glenohumeral_half_l"]
    rows = np.nonzero(domain)[0]
    u = Wn[rows, ua].copy()
    if "u_remap" in P:                                  # monotone contrast of the arm share: pure trunk / pure humerus ends
        b0, b2 = P["u_remap"]
        u_new = np.clip((u - b0) / (b2 - b0), 0, 1)
        # rescale trunk proportions to the new trunk share
        tr = np.ones(len(names), bool); tr[[ua, hh]] = False
        tsum = Wn[np.ix_(rows, np.nonzero(tr)[0])].sum(1)
        f = np.where(tsum > 1e-9, (1 - u_new) / np.maximum(tsum, 1e-9), 0.0)
        Wn[np.ix_(rows, np.nonzero(tr)[0])] *= f[:, None]
        empty = (tsum <= 1e-9) & (u_new < 1)
        for k in np.nonzero(empty)[0]:
            i = rows[k]; t = spine_split(z[i]); Wn[i, ix["spine_03"]] = (1 - u_new[k]) * t; Wn[i, ix["spine_02"]] = (1 - u_new[k]) * (1 - t)
        u = u_new; Wn[rows, ua] = u
    other = np.ones(len(names), bool); other[[ua, hh]] = False
    lo = u <= 0.5
    scale = np.where(lo, (1 - 2 * u) / np.maximum(1 - u, 1e-9), 0.0)
    Wn[np.ix_(rows, np.nonzero(other)[0])] *= scale[:, None]
    Wn[rows, hh] = np.where(lo, 2 * u, 2 * (1 - u))
    Wn[rows, ua] = np.where(lo, 0.0, 2 * u - 1)
PROTECT_COLS = np.array([], int)
Wn = prune4(Wn, edited)
# mirror left -> right for the edited set
right_rows = mirror[edited]
perm = np.arange(len(names))
ix = {nm: i for i, nm in enumerate(names)}
for i, nm in enumerate(names):
    if nm.endswith("_l") and nm[:-2] + "_r" in ix:
        perm[i] = ix[nm[:-2] + "_r"]; perm[ix[nm[:-2] + "_r"]] = i
Wn[right_rows] = Wn[edited][:, perm]
changed = np.r_[edited, right_rows]
if P.get("preserve_nonpermitted"):
    # bones outside the declared set keep their r95 weight exactly, on each side; the solved shoulder-girdle distribution
    # (declared bones + helpers) fills the remaining share; then prune to 4 influences without touching protected weights
    W0x = np.c_[W0, np.zeros((n, Wn.shape[1] - W0.shape[1]))]
    decl = {"spine_02", "spine_03", "clavicle_l", "clavicle_r", "scapula_l", "scapula_r", "upperarm_l", "upperarm_r"}
    perm_mask = np.array([(nm in decl) or nm.startswith("glenohumeral_half") for nm in names])
    rows = np.unique(changed)
    q = W0x[np.ix_(rows, np.nonzero(~perm_mask)[0])].sum(1)
    sol = Wn[np.ix_(rows, np.nonzero(perm_mask)[0])]
    sol = sol / np.maximum(sol.sum(1), 1e-9)[:, None] * (1 - q)[:, None]
    Wn[np.ix_(rows, np.nonzero(perm_mask)[0])] = sol
    Wn[np.ix_(rows, np.nonzero(~perm_mask)[0])] = W0x[np.ix_(rows, np.nonzero(~perm_mask)[0])]
    PROTECT_COLS = np.nonzero(~perm_mask)[0]
    Wn = prune4(Wn, rows)
delta = np.abs(Wn - W0).max(1)
print(json.dumps({"domain_left": int(domain.sum()), "free": int(len(free)), "fixed_in_domain": int(len(fixed_dom)),
                  "arm_tube": int(arm_tube.sum()), "changed_vertices": int((delta > 1e-4).sum()),
                  "max_influences": int((Wn > 0).sum(1).max()), "weight_sum_err": float(np.abs(Wn.sum(1) - 1).max())}))
np.savez(out, W=Wn, names=np.array(names), changed=changed, domain=domain, arm_tube=arm_tube)
