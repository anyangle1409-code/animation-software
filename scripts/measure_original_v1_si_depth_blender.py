"""Read-only: depth and rest-geometry of the self-intersecting face pairs of a posed candidate (never saves the .blend).

blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
  --python scripts/measure_original_v1_si_depth_blender.py -- <out.json> <pose[,pose...]>

For each intersecting polygon pair (pose-test definition) it records: the minimum REST distance between the two polygons' vertices (are they the
same surface folded through itself or different sheets?), the minimum POSED vertex-to-other-polygon-plane distance (penetration depth proxy, signed
along the other polygon's outward normal) and the vertex ids, so a collision-resolution mask and its separation target can be derived from data.
"""
import json
import sys
import tempfile
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index("--") + 1:]
out, poses = Path(args[0]), args[1].split(",")
ps = Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py")
src = ps.read_text(encoding="utf-8")
saved = sys.argv
sys.argv = ["blender", "--", tempfile.mkdtemp(), ""]
ns = {"__name__": "pose_defs", "__file__": ps.name}
exec(compile(src[:src.index("# ---------------------------------------------------------------- metrics")], "defs", "exec"), ns)
sys.argv = saved
rig, body, POSES, reset, upd = ns["rig"], ns["body"], ns["POSES"], ns["reset"], ns["upd"]
mask = body.modifiers.get("HGPT_DRESSED_MASK")
if mask is not None:
    mask.show_viewport = False
me = body.data
rest = np.array([v.co[:] for v in me.vertices])
polys = [tuple(p.vertices) for p in me.polygons]
psets = [set(p) for p in polys]
res = {}
for name in poses:
    reset()
    rig.location = (0, 0, 0)
    ns["HANDLE"].clear()
    POSES[name]()
    upd()
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    V = np.array([(ev.matrix_world @ v.co)[:] for v in ev.data.vertices])
    tree = BVHTree.FromPolygons([Vector(p) for p in V], polys)
    pairs = sorted({tuple(sorted((a, b))) for a, b in tree.overlap(tree) if a != b and not (psets[a] & psets[b])})
    rows = []
    for a, b in pairs:
        va, vb = list(polys[a]), list(polys[b])
        rest_d = min(float(np.linalg.norm(rest[i] - rest[j])) for i in va for j in vb)
        pos_d = min(float(np.linalg.norm(V[i] - V[j])) for i in va for j in vb)

        def depth(vs, pl):
            p = V[list(pl)]
            n = np.cross(p[1] - p[0], p[2] - p[0])
            n = n / max(np.linalg.norm(n), 1e-12)
            return float(min(((V[i] - p.mean(axis=0)) @ n) for i in vs))        # most negative = deepest on the inside of the other polygon
        rows.append({"a": a, "b": b, "rest_min_vertex_distance": round(rest_d, 4), "posed_min_vertex_distance": round(pos_d, 5),
                     "depth_a_in_b": round(depth(va, polys[b]), 5), "depth_b_in_a": round(depth(vb, polys[a]), 5), "va": va, "vb": vb})
    rd = np.array([r["rest_min_vertex_distance"] for r in rows]) if rows else np.zeros(1)
    dp = np.array([min(r["depth_a_in_b"], r["depth_b_in_a"]) for r in rows]) if rows else np.zeros(1)
    res[name] = {"pairs": len(rows), "rest_distance_percentiles": [round(float(np.percentile(rd, q)), 4) for q in (0, 25, 50, 75, 100)],
                 "depth_percentiles_m": [round(float(np.percentile(dp, q)), 5) for q in (0, 25, 50, 75, 100)],
                 "pairs_with_rest_distance_gt_0p03": int((rd > 0.03).sum()), "rows": rows}
    print("SIDEPTH", name, len(rows), "rest dist pct", res[name]["rest_distance_percentiles"], "depth pct (m)", res[name]["depth_percentiles_m"], ">3cm at rest:", res[name]["pairs_with_rest_distance_gt_0p03"])
reset()
out.write_text(json.dumps(res) + "\n", encoding="utf-8")
