import json, hashlib, datetime, os
import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
REPO = r"C:\Users\Mark\Documents\animation-software\repo"
d = np.load(SP + r"\r92_base_dump.npz", allow_pickle=True)
rest, reg, W, E = d["rest"], d["region"], d["W"], d["edges"]
rn = [str(x) for x in d["region_names"]]; bones = [str(b) for b in d["bones"]]
scl = bones.index("scapula_l")
key = {tuple(np.round(rest[i], 5)): i for i in range(len(rest))}
mir = np.array([key[tuple(np.round(rest[i] * [-1, 1, 1], 5))] for i in range(len(rest))])
torso = reg == rn.index("torso")
zone = (rest[:, 0] <= 1e-8) & torso & (W[:, scl] > 0.10) & (rest[:, 1] > 0.0) & (rest[:, 2] > 1.20) & (rest[:, 2] < 1.42) & (rest[:, 0] < -0.09)
# ring depth: mesh rings from the zone boundary (0 = outside the zone, 1 = zone vertex with a non-zone neighbour, ...)
nb = [[] for _ in range(len(rest))]
for a, b in E:
    nb[a].append(b); nb[b].append(a)
depth = np.zeros(len(rest), int)
frontier = [v for v in np.nonzero(zone)[0] if any(not zone[u] for u in nb[v])]
for v in frontier: depth[v] = 1
cur = set(frontier)
k = 1
inzone = zone.copy()
done = set(frontier)
while cur:
    nxt = set()
    for v in cur:
        for u in nb[v]:
            if zone[u] and u not in done:
                depth[u] = k + 1; done.add(u); nxt.add(u)
    cur = nxt; k += 1
left = np.nonzero(zone)[0]
right = np.array(sorted(int(mir[v]) for v in left if rest[v, 0] < -1e-8))
pre_off = None
rec = {"schema_version": 1, "declared_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "declared_before_edit": True,
       "target": "Step B: lateral/back wing flaps (r93 fallback r92 = immutable; r93 sha 6dfcd85a65e77fd832c9eb91cbe7eda04c81dc635201d260d6cbcf0eee508984)",
       "zone_rule": "left-owned (x <= 0) torso-region vertices with scapula_l weight > 0.10, rest y > 0 (posterior), 1.20 < z < 1.42, x < -0.09; right = exact mirror. Shoulder-region (legitimate scapular) skin is excluded",
       "left_owned_vertex_ids": [int(v) for v in left], "mirror_of_strict_left_vertex_ids": [int(v) for v in right], "vertex_count_total": int(len(left) + len(right)),
       "ring_depth_left": {str(int(v)): int(depth[v]) for v in left},
       "ids_sha256": hashlib.sha256(np.asarray(left, dtype="<i8").tobytes()).hexdigest(),
       "rest_bbox_min_m": [round(float(x), 4) for x in rest[left].min(0)], "rest_bbox_max_m": [round(float(x), 4) for x in rest[left].max(0)],
       "measured_before_the_edit": {"r93_press_top": "117 vertices of the zone-like set are 2-8 cm outside the thorax (mean 4.4 cm, max 8.0 cm; weights-only mean 4.8, max 9.7); scapula weight mean 0.55, max 1.0 (some vertices fully scapula-weighted); offset correlates with scapula weight (r = 0.60, 3.5 cm per unit weight); offset grows with elevation: 82 deg max 3.8 cm, 104 deg 6.1, 125 deg 6.8, 166 deg 8.0; pull-up top 3.4, squat 1.4, push-up 1.6, row 2.5",
                                   "corrective contribution": "reduces the maximum from 9.7 to 8.0 cm, mean 4.8 to 4.4 cm"},
       "proposed_local_weight_change": "W'_scapula(v) = W_scapula(v) * (1 - beta * f(v)), f(v) = min(1, (ring_depth(v) - 1) / 2) (boundary vertices of the zone unchanged, full beta from ring depth 3); the freed weight is given to spine_02 and spine_03 in proportion to their current weights (spine_02 if both are zero), top-4 renormalised, mirror-symmetric. Probes: beta in {0.3, 0.5, 0.7}",
       "anatomical_rationale": "the lateral/back torso skin below and beside the scapula is attached to the ribcage and latissimus, not to the scapula; the scapula's lateral border lifts away from the ribs during elevation but the covering skin should slide with the thorax over it. Skin directly over the scapula (the 280 shoulder-region vertices) keeps its scapular weight",
       "hypothesis": "lowering the scapula share on this torso skin reduces the outward wing displacement roughly in proportion (about 3.5 cm per unit weight) without a pit (the freed weight goes to the trunk, so the vertices move toward the thorax surface, not through it), and without touching the shoulder-region skin; the edge ratios across the zone boundary may stretch (the scapula-driven shoulder skin and the trunk-driven torso skin move apart), which the corrective re-solve must absorb",
       "stop_condition": "reject if the wing is replaced by a pit/flattening/tent at the zone edge (renders), a development gate fails, the shoulder self-intersections exceed P3B1, squat/volume/push-up/flexion gains are lost, pull-up or press metrics deteriorate beyond P3B1 tolerance, or the weights-only screening shows region maximum edge ratios beyond the gates at the zone boundary; r93 is then retained",
       "production_approved": False}
out = REPO + r"\ORIGINAL_V1_WORK\candidates\repair_preparation\r94_wing_scapula_weight_declared"
os.makedirs(out, exist_ok=True)
open(out + r"\wing_zone_declared_before_edit.json", "w", newline="\n").write(json.dumps(rec, indent=2) + "\n")
print("declared", rec["vertex_count_total"], "left", len(left), "ring depths", np.bincount(depth[left]).tolist())
