"""Declare the small local edit zone around the axilla/anterior-shoulder 'knot' BEFORE any solve (numpy only).

python scripts/declare_original_v1_pit_knot_zone.py <arc_or_pose_dump.npz> <knot_diagnostic.json> <out declaration.json> [--rings 2] [--poses a,b,c]

Rule (documented, deterministic): the vertices that the read-only diagnostic (diagnose_original_v1_pit_knot_blender.py) flagged near the LEFT pit in the
listed poses (crease / collapsed face / roughness) in the shoulder, torso, arm and neck regions, dilated by <rings> mesh rings restricted to the same
regions; the right zone is the exact mirror (x -> -x). Allowed change (later): the deform-bone weights of exactly these vertices (clavicle, scapula,
upper arm, spine_03, spine_02, neck, same side) - no vertex position, topology, other weights, bones or mesh data. Written with its SHA-256 so the solve
can refuse any other set.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("dump")
ap.add_argument("knot")
ap.add_argument("out")
ap.add_argument("--rings", type=int, default=2)
ap.add_argument("--poses", default="press_top,press_top_rhythm,pullup_hang,pullup_hang_rhythm")
a = ap.parse_args()
d = np.load(a.dump)
rest, E, region = d["rest"], d["edges"], d["region"]
rn = [str(x) for x in d["region_names"]]
ok = np.isin(region, [rn.index(n) for n in ("shoulder", "torso", "arm", "neck")])
kn = json.loads(Path(a.knot).read_text(encoding="utf-8"))
seed = set()
for p in a.poses.split(","):
    for b in kn[p]["bad"]:
        if rest[b["v"], 0] <= 1e-8:
            seed.add(int(b["v"]))
cur = np.zeros(len(rest), bool)
cur[list(seed)] = True
cur &= ok
for _ in range(a.rings):
    nxt = cur.copy()
    nxt[E[cur[E[:, 0]], 1]] = True
    nxt[E[cur[E[:, 1]], 0]] = True
    cur = nxt & ok
cur &= rest[:, 0] <= 1e-8                       # left-owned (midline included)
left = np.nonzero(cur)[0]
key = {tuple(np.round(rest[i], 5)): i for i in range(len(rest))}
mir = np.array([key[tuple(np.round(rest[i] * [-1, 1, 1], 5))] for i in range(len(rest))])
right = mir[left[rest[left, 0] < -1e-8]]
zone = np.unique(np.concatenate([left, right]))
rec = {"declared_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(), "declared_before_edit": True,
       "rule": f"left pit-knot vertices flagged in poses {a.poses} (shoulder/torso/arm/neck) dilated by {a.rings} rings in the same regions; right = exact mirror",
       "source_dump": str(d["source"]), "diagnostic": Path(a.knot).name, "diagnostic_sha256": hashlib.sha256(Path(a.knot).read_bytes()).hexdigest(),
       "seed_vertices": len(seed), "rings": a.rings, "left_vertex_ids": [int(v) for v in left], "zone_vertex_ids": [int(v) for v in zone],
       "zone_vertex_count": int(len(zone)), "zone_ids_sha256": hashlib.sha256(np.asarray(zone, dtype="<i8").tobytes()).hexdigest(),
       "allowed_change": "deform-bone weights of exactly these vertices (clavicle, scapula, upperarm, spine_03, spine_02, neck of the same side); nothing else",
       "centroid_left_m": [round(float(c), 4) for c in rest[left].mean(axis=0)], "extent_left_m": [round(float(c), 4) for c in (rest[left].max(axis=0) - rest[left].min(axis=0))]}
Path(a.out).write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
print("KNOT ZONE DECLARED", a.out, "seed", len(seed), "left", len(left), "total", len(zone), "centroid", rec["centroid_left_m"], "extent", rec["extent_left_m"])
