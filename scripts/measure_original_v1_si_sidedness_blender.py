"""Read-only: which sheet pokes out through which, for the shoulder-top self-intersections of a posed candidate (never saves the .blend).

blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
  --python scripts/measure_original_v1_si_sidedness_blender.py -- <out.json> <pose[,pose...]>

For every intersecting polygon pair whose two polygons are driven mainly by the clavicle (C) and the upper arm (U) of the same side it reports the
signed distances (along the OUTWARD normal of the other polygon; positive = outside the other sheet) of the U polygon's vertices relative to the C
polygon's plane and of the C polygon's vertices relative to the U polygon's plane (mean, min, max), and the outward-normal alignment cos(nC, nU).
The summary counts how often the U sheet lies mostly outside / mostly inside the C sheet, which decides the physically correct direction of a
collision resolution (the sheet that pokes out has to move back inside).
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
polys = [tuple(p.vertices) for p in me.polygons]
psets = [set(p) for p in polys]
gname = {vg.index: vg.name for vg in body.vertex_groups}
W = {}
for v in me.vertices:
    W[v.index] = {gname[g.group]: g.weight for g in v.groups}


def dom(poly):
    acc = {}
    for v in poly:
        for k, w in W[v].items():
            acc[k] = acc.get(k, 0.0) + w
    return max(acc, key=acc.get) if acc else "none"


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

    def normal(pl):
        p = V[list(pl)]
        n = np.cross(p[1] - p[0], p[2] - p[0])
        return n / max(np.linalg.norm(n), 1e-12), p.mean(axis=0)

    rows = []
    for a, b in pairs:
        da, db = dom(polys[a]), dom(polys[b])
        if da.startswith("clavicle") and db.startswith("upperarm"):
            c, u = a, b
        elif db.startswith("clavicle") and da.startswith("upperarm"):
            c, u = b, a
        else:
            continue
        nc, cc = normal(polys[c])
        nu, cu = normal(polys[u])
        du = np.array([(V[i] - cc) @ nc for i in polys[u]])          # U vertices relative to C plane (+ = outside C)
        dc = np.array([(V[i] - cu) @ nu for i in polys[c]])          # C vertices relative to U plane (+ = outside U)
        rows.append({"c": c, "u": u, "U_vs_C_mean": float(du.mean()), "U_vs_C_min": float(du.min()), "U_vs_C_max": float(du.max()),
                     "C_vs_U_mean": float(dc.mean()), "C_vs_U_min": float(dc.min()), "C_vs_U_max": float(dc.max()), "cos_nC_nU": float(nc @ nu)})
    arr = lambda k: np.array([r[k] for r in rows]) if rows else np.zeros(1)
    res[name] = {"pairs_clavicle_vs_upperarm": len(rows),
                 "U_mostly_outside_C": int((arr("U_vs_C_mean") > 0).sum()), "U_mostly_inside_C": int((arr("U_vs_C_mean") < 0).sum()),
                 "C_mostly_outside_U": int((arr("C_vs_U_mean") > 0).sum()), "C_mostly_inside_U": int((arr("C_vs_U_mean") < 0).sum()),
                 "median_U_vs_C_mean": round(float(np.median(arr("U_vs_C_mean"))), 4), "median_C_vs_U_mean": round(float(np.median(arr("C_vs_U_mean"))), 4),
                 "median_cos_normals": round(float(np.median(arr("cos_nC_nU"))), 3), "normals_aligned_cos_gt_0": int((arr("cos_nC_nU") > 0).sum()), "rows": rows}
    r = res[name]
    print("SIDEDNESS", name, r["pairs_clavicle_vs_upperarm"], "U outside/inside C:", r["U_mostly_outside_C"], r["U_mostly_inside_C"], "| C outside/inside U:", r["C_mostly_outside_U"], r["C_mostly_inside_U"],
          "| median U-vs-C", r["median_U_vs_C_mean"], "median C-vs-U", r["median_C_vs_U_mean"], "| median cos(nC,nU)", r["median_cos_normals"])
reset()
out.write_text(json.dumps(res) + "\n", encoding="utf-8")
