import json, hashlib, datetime, os
import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
REPO = r"C:\Users\Mark\Documents\animation-software\repo"
d = np.load(SP + r"\r93_scap_dump.npz", allow_pickle=True)
rest, reg, W, E, tris, mats = d["rest"], d["region"], d["W"], d["edges"], d["tris"], d["mats"].astype(np.float64)
rn = [str(x) for x in d["region_names"]]; bones = [str(b) for b in d["bones"]]; poses = [str(p) for p in d["poses"]]
sha = str(d["source_sha256"])
key = {tuple(np.round(rest[i], 5)): i for i in range(len(rest))}
mir = np.array([key[tuple(np.round(rest[i] * [-1, 1, 1], 5))] for i in range(len(rest))])
wz = json.load(open(REPO + r"\ORIGINAL_V1_WORK\candidates\repair_preparation\r94_wing_scapula_weight_declared\wing_zone_declared_before_edit.json"))
zone_left = np.array(wz["left_owned_vertex_ids"])
inz = np.zeros(len(rest), bool); inz[zone_left] = True
nb = [[] for _ in range(len(rest))]
for a, b in E:
    nb[a].append(b); nb[b].append(a)
allowed = np.isin(reg, [rn.index("torso"), rn.index("shoulder")]) & (rest[:, 0] <= 1e-8) & (rest[:, 1] > -0.03)
mask = inz.copy()
frontier = set(np.nonzero(mask)[0])
for ring in range(3):
    nxt = set()
    for v in frontier:
        for u in nb[v]:
            if allowed[u] and not mask[u]:
                mask[u] = True; nxt.add(u)
    frontier = nxt
Lset = np.nonzero(mask)[0]
Rset = np.array(sorted(int(mir[v]) for v in Lset if rest[v, 0] < -1e-8))
mid = Lset[np.abs(rest[Lset, 0]) <= 1e-8]


def vn(P):
    n = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]]); v = np.zeros_like(P)
    for k in range(3): np.add.at(v, tris[:, k], n)
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-18)


vrest = vn(rest)
TRUNK = ("pelvis", "spine_01", "spine_02", "spine_03", "neck", "head")
tcols = [bones.index(b) for b in TRUNK]
R1 = np.c_[rest, np.ones(len(rest))]
sl, c3 = bones.index("scapula_l"), bones.index("spine_03")
table = []
for i, p in enumerate(poses):
    Rrel = mats[i][c3][:3, :3].T @ mats[i][sl][:3, :3]
    u = float(np.degrees(np.arccos(np.clip((np.trace(Rrel) - 1) / 2, -1, 1))))
    Wt = W[:, tcols]; s = Wt.sum(axis=1, keepdims=True); Wn = Wt / np.maximum(s, 1e-9)
    M = np.einsum("vb,bij->vij", Wn, mats[i][tcols]); Ptr = np.einsum("vij,vj->vi", M, R1)[:, :3]
    n = np.einsum("vij,vj->vi", M[:, :3, :3], vrest); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-18)
    off = ((d["evaluated"][i] - Ptr) * n).sum(axis=1)[zone_left]
    table.append({"entry": p, "theta_deg": round(float(d["theta"][i][0]), 1), "scapular_rotation_u_deg": round(u, 1), "lobe_zone_outward_offset_cm": {"max": round(100 * float(off.max()), 2), "p95": round(100 * float(np.percentile(off, 95)), 2), "median": round(100 * float(np.median(off)), 2)}})
rec = {"schema_version": 1, "declared_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "declared_before_edit": True,
       "target_revision": "r95", "fallback": "r93 (SHA %s), immutable" % sha, "source_candidate_sha256": sha,
       "rule": "left-owned (x <= 0) vertices of the declared lobe zone (torso-region, scapula_l weight > 0.10, y > 0, 1.20 < z < 1.42, x < -0.09; repair_preparation/r94_wing_scapula_weight_declared/wing_zone_declared_before_edit.json) dilated by 3 mesh rings inside the torso/shoulder regions with y > -0.03 (continuity taper); right side = exact mirror",
       "left_owned_vertex_ids": [int(v) for v in Lset], "mirror_of_strict_left_vertex_ids": [int(v) for v in Rset], "midline_vertex_ids": [int(v) for v in mid],
       "vertex_count_total": int(len(Lset) + len(Rset)), "ids_sha256": hashlib.sha256(np.asarray(Lset, dtype="<i8").tobytes()).hexdigest(),
       "lobe_zone_left_vertex_count": int(len(zone_left)),
       "rest_bbox_min_m": [round(float(x), 4) for x in rest[Lset].min(0)], "rest_bbox_max_m": [round(float(x), 4) for x in rest[Lset].max(0)],
       "affected_anatomical_surfaces": "lateral and posterior upper torso skin below and beside the scapula (latissimus / lateral ribcage / infrascapular region) in the torso label; the shoulder-label skin directly over the scapula is inside the taper ring only, not in the limited zone",
       "underlying_thorax_reference": "trunk-rigid surface: every vertex skinned with only the trunk bones (pelvis, spine_01-03, neck, head), weights renormalised; outward offset = (P_posed - P_trunk_rigid) . n, with n the rest vertex normal transported by the same trunk-only blended rotation",
       "measured_before_the_edit_r93": table,
       "driver_equation": "u(side) = angle in degrees of R_rel = R_spine_03^T R_scapula_side, R = 3x3 rotation of the bone skinning matrix (posed matrix times inverse rest matrix) in the armature frame; a(side) = t^2 (3 - 2 t), t = clamp((u - u0) / (u1 - u0), 0, 1); key value = a",
       "zero_activation_region": "u <= u0 = 15 deg (lobe offset <= about 3.4 cm in the measured poses: arm-down, squat, push-up, row, early arcs, pullup_top at 16 deg stays at a(16 deg) = 0.001)",
       "transition_region": "15 deg < u < 75 deg, C1 smoothstep",
       "maximum_activation": "1.0 at u >= 75 deg (press_top 74.9, hangs 68-85, rhythm poses 85-94)",
       "why_this_driver": "u is the scapular upward rotation itself; across the 50 measured entries the lobe offset correlates 0.99 with u (0.93 with humerothoracic elevation) and is exactly zero where u is zero (squat, push-up, row). It is a joint-mechanics quantity, with no pose name or constant tied to a test pose",
       "geometric_displacement_limit": "outward offset of the lobe-zone vertices from the trunk-rigid surface <= 0.045 m in every pose where the key is active (hinge 1e7); no vertex may be drawn through the thorax because the limit is one-sided and the dent/volume/edge guards of the existing solves are kept (hold-region guards, area/fold/Laplacian barriers, smoothness); the taper ring and the existing key terms give continuity at the mask boundary",
       "mechanism": "third mirrored shape-key pair HGPT_SHOULDER_SCAP_L/R added on top of r93 (the abduction and flexion keys, weights and bones are untouched); solved with the existing barrier solver --driver scapular --u0 15 --u1 75 --lobe-limit 0.045 --w-lobe 1e7 and all r93 solve arguments",
       "hypothesis": "the lobe is the scapula-bound skin following the accepted scapular rotation; a smooth rest-space displacement driven by that same rotation can draw the lateral/back skin back toward the thorax to a natural 4.5 cm without touching the shoulder-label skin over the scapula, the chest, the clavicle or the upper arm, and without a pit because the limit is one-sided",
       "stop_conditions": ["a development gate fails", "meaningful press/pull-up regression versus r93 or a new strict P3B1 regression (pullup_top torso must not deteriorate materially from 0.670)", "chest/axilla dent, clavicle web, shoulder collapse, abnormal flattening or a visible discontinuity at the taper boundary in the renders", "new self-intersections above P3B1 (press_top 95, rhythm 54, pullup_hang 4, hang_rhythm 0, squat 108, push-up 158) or above r93's values by a material margin", "loss of the squat, volume-floor, flexion, wrist-patch or r92/r93 chest and clavicle gains", "the lobe only moves elsewhere (renders) or numerical improvement without a visible anatomical improvement", "non-deterministic re-solve"],
       "production_approved": False}
out = REPO + r"\ORIGINAL_V1_WORK\candidates\repair_preparation\r95_scapular_lobe_corrective_declared"
os.makedirs(out, exist_ok=True)
json.dump(rec, open(out + r"\scapular_lobe_mask_declared_before_solve.json", "w", newline="\n"), indent=2)
open(out + r"\scapular_lobe_mask_declared_before_solve.json", "a").write("\n")
lz = {"left_owned_vertex_ids": [int(v) for v in zone_left], "mirror_of_strict_left_vertex_ids": sorted(int(mir[v]) for v in zone_left if rest[v, 0] < -1e-8)}
json.dump(lz, open(out + r"\lobe_limit_zone_declared_before_solve.json", "w", newline="\n"), indent=2)
print("mask", rec["vertex_count_total"], "left", len(Lset), "lobe zone left", len(zone_left))
for t in table:
    if t["entry"] in ("neutral", "press_bottom", "press_top@0.500", "press_top@0.750", "press_top", "press_top_rhythm", "pullup_top", "pullup_hang", "pullup_hang_rhythm"):
        print(t["entry"], t["theta_deg"], t["scapular_rotation_u_deg"], t["lobe_zone_outward_offset_cm"])
