"""Read-only O2 rig-fit audit: are v4 joint centres inside the body, and how deep?

blender --background --factory-startup <blend> --python scripts/audit_original_v1_o2_rig_fit_blender.py [-- <report.json>]

For every bone, samples the head, seven interior points and the (non-terminal)
tail, and reports whether each lies inside the closed body surface and its
distance to that surface.
Writes reports/original_v1_o2_rig_fit.json. Never modifies or saves the Blend.
Numeric only: placement inside the *intended anatomical landmark* still needs
visual review.
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
out = Path(args[0]) if args else ROOT / "reports" / "original_v1_o2_rig_fit.json"

body = bpy.data.objects["HGPT_ORIGINAL_V1_CLEAN_SCAFFOLD"]
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
mw = body.matrix_world
bvh = BVHTree.FromPolygons([mw @ v.co for v in body.data.vertices],
                           [tuple(p.vertices) for p in body.data.polygons])


def inside(p: Vector) -> bool:
    """Ray-parity test against the closed manifold surface."""
    hits, origin = 0, p.copy()
    direction = Vector((1.0, 0.00013, 0.00007)).normalized()
    for _ in range(64):
        loc, _n, _i, _d = bvh.ray_cast(origin, direction)
        if loc is None:
            break
        hits += 1
        origin = loc + direction * 1e-6
    return hits % 2 == 1


# Terminal tails expected at/near the skin are reported but not gated.
SURFACE_TAILS = {"head", "toe_l", "toe_r"} | {
    f"{f}_03_{s}" for f in ("index", "middle", "ring", "pinky", "thumb") for s in "lr"}

rows, failures = [], []
for bone in rig.data.bones:
    if bone.name == "root":
        continue
    points = [("head", bone.head_local)]
    points += [(f"t{k}", bone.head_local.lerp(bone.tail_local, k / 8)) for k in range(1, 8)]
    points += [("tail", bone.tail_local)]
    for label, local in points:
        p = rig.matrix_world @ local
        _loc, _n, _i, dist = bvh.find_nearest(p)
        ok = inside(p)
        gated = not (label == "tail" and bone.name in SURFACE_TAILS)
        rows.append({"bone": bone.name, "point": label, "inside": ok,
                     "surface_distance_m": round(dist, 5), "gated": gated})
        if gated and not ok:
            failures.append(f"{bone.name}.{label}")

shallow = sorted((r for r in rows if r["gated"] and r["inside"]),
                 key=lambda r: r["surface_distance_m"])[:8]
report = {
    "blend": bpy.data.filepath,
    "pass": not failures,
    "joint_failures": failures,
    "shallowest_inside": shallow,
    "scope": "Numeric joint containment only; anatomical landmark placement needs visual review.",
    "joints": rows,
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: report[k] for k in ("pass", "joint_failures", "shallowest_inside")}, indent=2))
