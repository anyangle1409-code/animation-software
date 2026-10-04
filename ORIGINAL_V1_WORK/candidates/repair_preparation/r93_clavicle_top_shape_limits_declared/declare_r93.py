import json, hashlib, datetime, os
import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
REPO = r"C:\Users\Mark\Documents\animation-software\repo"
d = np.load(SP + r"\r92_base_dump.npz", allow_pickle=True)
rest, reg, W = d["rest"], d["region"], d["W"]
rn = [str(x) for x in d["region_names"]]; bones = [str(b) for b in d["bones"]]
_key = {tuple(np.round(rest[i], 5)): i for i in range(len(rest))}
mir = np.array([_key[tuple(np.round(rest[i] * [-1, 1, 1], 5))] for i in range(len(rest))])
S = (rest[:, 0] <= 1e-8) & (reg == rn.index("shoulder")) & (rest[:, 2] > 1.44) & (W[:, bones.index("clavicle_l")] > 0.35)
left = np.nonzero(S)[0]
right = np.nonzero(S & (rest[:, 0] < -1e-8))[0]
right = np.array(sorted(int(mir[v]) for v in right))
rec = {"schema_version": 1, "declared_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "declared_before_edit": True,
       "target_revision": "r93 (probes)", "fallback": "r92 (SHA 1cfe04744c6c432daee2fb76a1d6bebf30962f496bdef0b05dc61294df52a108), immutable",
       "zone_rule": "left-owned (x <= 0) vertices of the shoulder region with rest z > 1.44 m and clavicle_l weight > 0.35, plus the exact mirror (clavicle-top / trapezius-neck-base skin)",
       "left_owned_vertex_ids": [int(v) for v in left], "mirror_of_strict_left_vertex_ids": [int(v) for v in right], "vertex_count_total": int(len(left) + len(right)),
       "ids_sha256": hashlib.sha256(np.asarray(left, dtype="<i8").tobytes()).hexdigest(),
       "rest_bbox_min_m": [round(float(x), 4) for x in rest[left].min(0)], "rest_bbox_max_m": [round(float(x), 4) for x in rest[left].max(0)],
       "measured_in_r92_press_top_before_the_edit": {
           "front_knob": "28-33 clavicle-weighted vertices (clavicle 0.57-0.75) move 2.0-2.6 cm tangentially and 0.4-1.7 cm outward relative to the uncorrected pose; local bump height 0.65 cm (uncorrected 0.39 cm); the knob is visible in the render, absent in the weights-only render",
           "rear_web": "posterior neck-base triangles (rest centre about (-0.08, +0.087, 1.57)) reach 3.16x and 3.10x their rest area in press_top (uncorrected 0.32x and 0.85x); 3 triangles above 2x in press_top, 4 in press_top_rhythm, 3 in pullup_hang; zone-touching edge ratio max 2.01 (uncorrected 1.68)",
           "other": "outward bulge at the zone is 1.7-2.1 cm at 104-146 degrees of elevation and 0.3 cm at 62 degrees; tangential slide mean 0.6 cm"},
       "constraints": {"area_cap": "triangles touching the zone: posed corrected area <= C x REST area (probe A1 C = 1.6)",
                       "slide_limit": "zone vertices: tangential displacement relative to the uncorrected pose <= s (probe A2 s = 0.015 m)",
                       "bulge_limit": "zone vertices: outward displacement along the uncorrected normal <= b (probe A2 b = 0.010 m)"},
       "mechanism": "the existing abduction corrective (same driver, mask, weights, flexion keys and every r92 solve argument including the 0.025 m dent limit) is re-solved with these geometric hinge terms (weight 1e6); no pose or exercise name, active only where the key is active",
       "hypothesis": "the front knob and rear web are the corrective's way of separating the clavicle-driven and upper-arm-driven skin sheets; bounding how far a vertex may slide or bulge and how far a triangle may grow beyond its rest area keeps the separation but removes the lumps; the self-intersection count may rise toward the weights-only value (P3B1: press_top 95, rhythm 54, hang 4) - the probes measure whether it stays below P3B1",
       "stop_condition": "reject if any development gate fails, shoulder self-intersections exceed P3B1 (press_top 95, press_top_rhythm 54, pullup_hang 4, pullup_hang_rhythm 0, squat 108), the r92 chest-pit improvement is lost, a new strict P3B1 regression appears, or the renders show the knob/web replaced by another large-scale artefact (flattened shoulder, collapse, new crease); r92 is then retained",
       "production_approved": False}
out = REPO + r"\ORIGINAL_V1_WORK\candidates\repair_preparation\r93_clavicle_top_shape_limits_declared"
os.makedirs(out, exist_ok=True)
open(out + r"\clavicle_top_zone_declared_before_solve.json", "w", newline="\n").write(json.dumps(rec, indent=2) + "\n")
print("declared", rec["vertex_count_total"], "left", len(left))
