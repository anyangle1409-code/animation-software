"""FEMALE source-to-mesh comparison (read-only): proportions and surface deviation of the new model vs her source.

Models (rest pose, the source's A-pose): SOURCE (her Meshy Pro surface), NEW CLOTHED (body skin + bra + shorts:
the outer surface, comparable to the source, which has the garments fused) and NEW BODY (the body under the
removable garments).
  * girths: tape-measure perimeters (convex hull) of horizontal sections at her baseline levels - bust 1.196, under-
    bust 1.12, waist 1.045, hips 0.82 (trunk sections with the arms excluded), thigh 0.70, calf 0.30 (right leg),
    upper arm (right, at z 1.15 perpendicular to the vertical: arm section beyond the torso);
  * height, shoulder breadth over the deltoids (2-6 cm below the shoulder top), hip width;
  * deviation: distance of the new clothed surface's vertices from the source surface (nearest point), by region,
    and the reverse (source vertices to the new surface) for coverage.

usage: python3.13 compare_f_source_blender.py -- <final .blend> <out .json>
"""
import json
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from scipy.spatial import ConvexHull

a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0], load_ui=False)
rig = bpy.data.objects.get("HGPT_FEMALE_RIG")
if rig:
    rig.data.pose_position = "REST"; bpy.context.view_layer.update()


def world_mesh(names):
    dg = bpy.context.evaluated_depsgraph_get(); V = []; F = []
    for n in names:
        o = bpy.data.objects.get(n)
        if o is None:
            continue
        oe = o.evaluated_get(dg); m = oe.to_mesh(); off = len(V)
        V += [o.matrix_world @ v.co for v in m.vertices]; F += [[i + off for i in p.vertices] for p in m.polygons]
        oe.to_mesh_clear()
    return np.array([v[:] for v in V]), F


MODELS = {"source": world_mesh(["HGPT_FEMALE_SOURCE_BODY_TARGET"]),
          "new_clothed": world_mesh(["HGPT_Female_Body", "HGPT_Female_Bra", "HGPT_Female_Shorts", "HGPT_Female_Ponytail"]),
          "new_body": world_mesh(["HGPT_Female_Body"])}
src_used = sorted({i for f in MODELS["source"][1] for i in f})


def pts(model):
    V, F = MODELS[model]
    return V[src_used] if model == "source" else V


EDGES = {}


def section_pts(model, z):
    """points where the model's edges cross the plane z (exact section, independent of mesh density)"""
    V, F = MODELS[model]
    if model not in EDGES:
        E = set()
        for f in F:
            for i in range(len(f)):
                a_, b_ = f[i], f[(i + 1) % len(f)]; E.add((min(a_, b_), max(a_, b_)))
        EDGES[model] = np.array(sorted(E))
    E = EDGES[model]; za, zb = V[E[:, 0], 2], V[E[:, 1], 2]; m = (za - z) * (zb - z) < 0
    t = (z - za[m]) / (zb[m] - za[m]); return V[E[m, 0]] + (V[E[m, 1]] - V[E[m, 0]]) * t[:, None]


def hull_perim(P2):
    if len(P2) < 8:
        return None
    h = ConvexHull(P2); q = P2[h.vertices]; return float(np.linalg.norm(q - np.roll(q, 1, 0), axis=1).sum())


def trunk_girth(model, z, xmax):
    P = section_pts(model, z); s = P[(np.abs(P[:, 0]) < xmax) & (P[:, 1] < 0.12)]
    return hull_perim(s[:, :2])


out = {"models": list(MODELS)}
for m in MODELS:
    P = pts(m); r = {}
    r["height_m"] = round(float(P[:, 2].max() - P[:, 2].min()), 4)
    for name, z, xm in (("bust", 1.196, 0.148), ("underbust", 1.12, 0.16), ("waist", 1.045, 0.20), ("hips", 0.82, 0.21)):
        g = trunk_girth(m, z, xm); r[f"{name}_cm"] = round(g * 100, 1) if g else None
    s = section_pts(m, 0.70); s = s[(s[:, 0] > 0.01) & (s[:, 0] < 0.25)]; g = hull_perim(s[:, :2]); r["thigh_cm"] = round(g * 100, 1) if g else None
    s = section_pts(m, 0.30); s = s[(s[:, 0] > 0.05) & (s[:, 0] < 0.30)]; g = hull_perim(s[:, :2]); r["calf_cm"] = round(g * 100, 1) if g else None
    s = section_pts(m, 1.15); s = s[(s[:, 0] > 0.17) & (s[:, 0] < 0.35)]; g = hull_perim(s[:, :2]); r["upper_arm_cm"] = round(g * 100, 1) if g else None
    top = P[:, 2].max()
    sh = P[(P[:, 2] > 1.26) & (P[:, 2] < 1.30) & (np.abs(P[:, 0]) < 0.30)]; r["shoulder_breadth_deltoids_cm"] = round(float(np.ptp(sh[:, 0])) * 100, 1)
    hp = P[(np.abs(P[:, 2] - 0.82) < 0.01) & (np.abs(P[:, 0]) < 0.25)]; r["hip_width_cm"] = round(float(np.ptp(hp[:, 0])) * 100, 1)
    out[m] = r
src = out["source"]
out["new_clothed_vs_source_pct"] = {k: round(100 * (out["new_clothed"][k] - src[k]) / src[k], 2) for k in src if isinstance(src[k], float) and src[k] and isinstance(out["new_clothed"].get(k), float)}
# deviation
V, F = MODELS["source"]
Vf, Ff = world_mesh(["HGPT_FEMALE_SOURCE_Mesh_0"]); sb = BVHTree.FromPolygons([Vector(p) for p in Vf], Ff)   # full source (hair included)
Vn, Fn = MODELS["new_clothed"]; nb = BVHTree.FromPolygons([Vector(p) for p in Vn], Fn)
# visible outer surface only: body skin hidden under a garment (within 5 mm behind it) is excluded
Vg, Fg = world_mesh(["HGPT_Female_Bra", "HGPT_Female_Shorts"]); gb = BVHTree.FromPolygons([Vector(p) for p in Vg], Fg)
nbody = len(MODELS["new_body"][0])
vis = np.array([not (i < nbody and gb.find_nearest(Vector(Vn[i]), 0.005)[0] is not None) for i in range(len(Vn))])
Vn = Vn[vis]
d = np.array([sb.find_nearest(Vector(p))[3] for p in Vn])


def region(p):
    if p[2] > 1.40 and p[1] > 0.06: return "head_back_hair"
    if p[2] > 1.40: return "head_neck"
    if abs(p[0]) > 0.33 and p[2] < 0.90: return "hands"
    if p[2] < 0.10: return "feet"
    return "trunk_limbs"


regs = np.array([region(p) for p in Vn]); dev = {}
for rg in sorted(set(regs)):
    x = d[regs == rg] * 1000; dev[rg] = {"n": int(len(x)), "p50_mm": round(float(np.percentile(x, 50)), 2), "p95_mm": round(float(np.percentile(x, 95)), 2),
                                         "p99_mm": round(float(np.percentile(x, 99)), 2), "max_mm": round(float(x.max()), 2)}
out["deviation_new_to_source"] = dev
S_ = V[src_used][::3]; dr = np.array([nb.find_nearest(Vector(p))[3] for p in S_]) * 1000
out["coverage_source_to_new_mm"] = {"p50": round(float(np.percentile(dr, 50)), 2), "p95": round(float(np.percentile(dr, 95)), 2), "p99": round(float(np.percentile(dr, 99)), 2)}
json.dump(out, open(a[1], "w"), indent=1); print("COMPARE", json.dumps(out))
