"""Declare (before any edit) a weight-smoothing zone that is a declared zone dilated by mesh rings (numpy only; touches no Blend).

python scripts/declare_original_v1_dilated_weight_zone.py <dump.npz> <source declaration.json> <out declaration.json> <target_rev> [--rings 2] [--note TEXT]

The new zone = the source declaration's mirror-closed vertex set dilated by <rings> mesh rings, restricted to the shoulder/torso/arm/neck regions, left side
(x <= 0) plus the exact mirror. Output keys follow the weight-smoothing declaration format (left_owned_vertex_ids, mirror_of_strict_left_vertex_ids, ids hash).
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("dump")
ap.add_argument("source")
ap.add_argument("out")
ap.add_argument("target")
ap.add_argument("--rings", type=int, default=2)
ap.add_argument("--note", default="")
ap.add_argument("--regions", default="shoulder,torso,arm,neck", help="comma list of regions the zone may contain (the source zone is also restricted to them)")
a = ap.parse_args()
d = np.load(a.dump)
rest, E, region = d["rest"], d["edges"], d["region"]
rn = [str(x) for x in d["region_names"]]
ok = np.isin(region, [rn.index(n) for n in a.regions.split(",")])
nV = len(rest)
src = json.loads(Path(a.source).read_text(encoding="utf-8"))
key = {tuple(np.round(rest[i], 5)): i for i in range(nV)}
mir = np.array([key[tuple(np.round(rest[i] * [-1, 1, 1], 5))] for i in range(nV)])
zone = np.zeros(nV, bool)
zone[src["left_owned_vertex_ids"]] = True
zone &= ok
for _ in range(a.rings):
    nxt = zone.copy()
    nxt[E[zone[E[:, 0]], 1]] = True
    nxt[E[zone[E[:, 1]], 0]] = True
    zone = nxt & ok
left = np.nonzero(zone & (rest[:, 0] <= 1e-8))[0]
right = mir[left[rest[left, 0] < -1e-8]]
rec = {"schema_version": 1, "declared_utc": datetime.now(timezone.utc).isoformat(), "declared_before_edit": True, "target_revision": a.target,
       "zone_origin": str(a.source).replace("\\", "/"), "zone_origin_sha256": hashlib.sha256(Path(a.source).read_bytes()).hexdigest(),
       "zone_rule": f"source zone dilated by {a.rings} mesh rings inside the regions {a.regions}; left-owned x <= 0; right = exact mirror", "rings": a.rings,
       "left_owned_vertex_ids": [int(v) for v in left], "mirror_of_strict_left_vertex_ids": sorted(int(v) for v in right), "vertex_count_total": int(len(left) + len(right)),
       "ids_sha256": hashlib.sha256(np.asarray(left, dtype="<i8").tobytes()).hexdigest(),
       "rest_bbox_min_m": [round(float(x), 5) for x in rest[left].min(axis=0)], "rest_bbox_max_m": [round(float(x), 5) for x in rest[left].max(axis=0)],
       "note": a.note,
       "allowed_change": "deform-bone weights of exactly these mirror-closed vertices by deterministic diffusion smoothing (scripts/smooth_original_v1_weights_zone.py); then a re-fitted shoulder corrective (separate declaration); no bone, bind, topology, pose-definition, threshold, baseline or other-vertex change",
       "production_approved": False}
Path(a.out).write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
print("DILATED ZONE DECLARED", a.out, "left", len(left), "total", rec["vertex_count_total"], "bbox", rec["rest_bbox_min_m"], rec["rest_bbox_max_m"])
