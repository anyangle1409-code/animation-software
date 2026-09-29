"""Read-only self-intersection audit of the ORIGINAL v1 body surface.

blender --background --factory-startup <blend> --python scripts/audit_original_v1_o2_self_intersection_blender.py [-- <report.json>]

Counts pairs of faces that intersect each other without sharing a vertex
(BVH overlap test), and reports where they are. Rest-pose self-intersection is
a topology defect (interpenetrating toes, fingers, folds). Never saves.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = Path(args[0]) if args else ROOT / "reports" / "original_v1_o2_self_intersection.json"

body = next(o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("HGPT_ORIGINAL_V1"))
mw = body.matrix_world
V = [mw @ v.co for v in body.data.vertices]
polys = [tuple(p.vertices) for p in body.data.polygons]
sets = [set(p) for p in polys]
tree = BVHTree.FromPolygons(V, polys)
pairs = [(a, b) for a, b in tree.overlap(tree) if a < b and not (sets[a] & sets[b])]


def zone(p: Vector) -> str:
    if p.z < 0.14:
        return "foot"
    if abs(p.x) > 0.17 and p.z < 0.95:
        return "hand"
    if abs(p.x) > 0.17:
        return "arm"
    if p.z < 0.88:
        return "leg"
    if p.z > 1.58:
        return "head_neck"
    return "torso"


zones = {}
samples = []
for a, _b in pairs:
    c = sum((V[i] for i in polys[a]), Vector()) / len(polys[a])
    z = zone(c)
    zones[z] = zones.get(z, 0) + 1
    if len(samples) < 12:
        samples.append([round(c.x, 4), round(c.y, 4), round(c.z, 4)])
report = {"blend": bpy.data.filepath, "pass": not pairs, "intersecting_face_pairs": len(pairs),
          "by_zone": zones, "sample_centroids": samples}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("SELF-INTERSECTION", json.dumps({k: report[k] for k in ("pass", "intersecting_face_pairs", "by_zone", "sample_centroids")}))
