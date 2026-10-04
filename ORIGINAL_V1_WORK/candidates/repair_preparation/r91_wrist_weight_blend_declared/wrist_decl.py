import json, hashlib, datetime, os
import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
REPO = r"C:\Users\Mark\Documents\animation-software\repo"
a, b = np.load(SP + r"\pl_r47.npz"), np.load(SP + r"\pl_r90.npz")
rest, bones = a["rest"], [str(x) for x in a["bones"]]
c = np.array([-0.2323, 0.0432, 0.9219])
R = 0.03
near = np.minimum(np.linalg.norm(rest - c, axis=1), np.linalg.norm(rest - c * [-1, 1, 1], axis=1))
zone = near < R
left = np.nonzero(zone & (rest[:, 0] <= 1e-8))[0]
right = np.nonzero(zone & (rest[:, 0] > 1e-8))[0]
changed = np.abs(a["W"] - b["W"]).max(axis=1) > 1e-6
B = json.load(open(SP + r"\pl_r90.json"))
extra = [p for p in B["pairs"] if tuple(p["polys"]) in {(9400, 9474), (9404, 9477), (9408, 9480), (15563, 15633), (15567, 15638), (15571, 15643)}]
rec = {"schema_version": 1, "declared_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "declared_before_edit": True,
       "target": "push-up self-intersections 164 (r90) vs P3B1 158; the six extra pairs", "fallback": "r90 (SHA 5c408a6d28f23e75ebf024cc9def753c9556f6cf3b7b99b82c9092dee20f4c8f), immutable",
       "extra_pairs_r90_minus_r47": [{"polys": p["polys"], "verts": p["verts"], "regions": p["regions"], "dominant_bones": p["dominant_bones"], "posed_mid_m": p["posed_mid"], "rest_distance_m": p["rest_distance_m"]} for p in extra],
       "pushup_hand_min": {"P3B1/r47": 0.119, "r90": 0.240, "development_gate_region_min": 0.15, "note": "the hand-minimum edges (r47 4704/34691 at 0.119; r90 16742/31622 at 0.240) sit 1.5-2.6 cm from the pair-vertex centroid"},
       "region": "left-owned vertices whose rest position is within %.3f m of the pair-vertex rest centroid %s (mirror-folded), plus the exact mirror" % (R, c.tolist()),
       "radius_m": R, "centre_m": c.tolist(), "left_owned_vertex_ids": [int(v) for v in left], "mirror_of_strict_left_vertex_ids": [int(v) for v in right], "vertex_count_total": int(zone.sum()),
       "left_vertices_with_changed_weights_r47_to_r90": int((zone & changed & (rest[:, 0] <= 1e-8)).sum()),
       "ids_sha256": hashlib.sha256(np.asarray(left, dtype="<i8").tobytes()).hexdigest(),
       "hypothesis": "The six pairs and the hand-minimum improvement come from the same wrist-band weight patch (r47 -> r48). Blending the r90 weights of the declared patch back toward r47's weights by lambda removes some or all six pairs; it either keeps the hand minimum >= 0.15 (then the experiment succeeds) or the hand minimum falls back toward 0.119 (the trade-off is demonstrated and the experiment stops). Screen lambda in {0.25, 0.5, 0.75, 1.0}: numpy hand minimum first, then the metrics-only 15-pose test for pair count and every gate.",
       "allowed_change": "deform-bone weights of exactly the declared vertices (mirror-symmetric), blended between the r90 and r47 weights, top-4 renormalised; no bone, topology, pose definition, shoulder geometry, corrective, threshold or baseline change",
       "stop_condition": "if removing the six pairs reintroduces the hand-minimum failure (or any equivalent regression) at every blend strength, the experiment stops, evidence is preserved and r90 is retained",
       "production_approved": False}
out = REPO + r"\ORIGINAL_V1_WORK\candidates\repair_preparation\r91_wrist_weight_blend_declared"
os.makedirs(out, exist_ok=True)
open(out + r"\wrist_patch_declared_before_edit.json", "w", newline="\n").write(json.dumps(rec, indent=2) + "\n")
print("declared", int(zone.sum()), "left", len(left), "changed-weight left", rec["left_vertices_with_changed_weights_r47_to_r90"])
