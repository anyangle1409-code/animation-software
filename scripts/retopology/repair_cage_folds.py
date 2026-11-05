"""Repair cage folds the source does not have (topology / layout defects) - writes a NEW checkpoint.

For every interior edge, compare the cage's fold angle (between its two quads) with the SOURCE's fold angle at the same
place (source normals nearest the two quad centres). An edge whose cage fold exceeds the source fold by more than
EXCESS_DEG is a layout defect (quads folded into a fin where the real surface is smooth), not anatomy. Those edges'
vertices plus a one-ring margin are re-laid: moved towards their neighbours' average (unfold), then projected back
onto the source along the vertex normal (not to the nearest point, which inside a fold can be the opposite wall);
repeat while the count falls and keep the best state. Optional region filter (4th argument). Real creases (where the source itself folds)
are left alone, so this is not a cosmetic smoothing pass. Reports the defect edges by region before and after.

usage: python3.13 repair_cage_folds.py -- <in .blend> <out NEW .blend> <report .json> [regions comma list]
"""
import json
import sys
from collections import Counter
from pathlib import Path

import bpy
import bmesh  # noqa: E402
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
EXCESS_DEG = 50.0; PROJ_MAX = 0.008; STEP = 0.6; MAX_ROUNDS = 30
REGIONS = set(a[3].split(",")) if len(a) > 3 else None   # restrict the repair to these regions
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
SRC = bpy.data.objects["HGPT_SOURCE_PROXY_Mesh_0"]; body = bpy.data.objects["HGPT_Male_Task3_Body"]
sb = BVHTree.FromPolygons([v.co.copy() for v in SRC.data.vertices], [tuple(p.vertices) for p in SRC.data.polygons])
bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
L4 = bm.verts.layers.int["t4_part"]; L5 = bm.verts.layers.int["t5_part"]
orig = [v.co.copy() for v in bm.verts]


def region(p, v):
    if v[L4] >= 10: return "fingers_thumb"
    if v[L4]: return "palm"
    if v[L5] == 8: return "toes"
    if v[L5] in (6, 7): return "ankle_foot"
    if v[L5]: return "hips_legs"
    if p.z > 1.55: return "head_neck"
    if abs(p.x) > 0.13 and p.z > 1.2: return "shoulder_armpit"
    return "torso_arms"


def defects():
    bm.normal_update(); out = []
    for e in bm.edges:
        if len(e.link_faces) != 2:
            continue
        if REGIONS and region(e.verts[0].co, e.verts[0]) not in REGIONS:
            continue
        f0, f1 = e.link_faces; cage = np.degrees(f0.normal.angle(f1.normal, 0.0))
        if cage < EXCESS_DEG:
            continue
        n0 = sb.find_nearest(f0.calc_center_median())[1]; n1 = sb.find_nearest(f1.calc_center_median())[1]
        if n0 is None or n1 is None:
            continue
        srcd = np.degrees(n0.angle(n1, 0.0))
        if cage - srcd > EXCESS_DEG:
            out.append(e)
    return out


d = defects(); before = Counter(region(e.verts[0].co, e.verts[0]) for e in d); hist = [len(d)]
best_state = (len(d), [x.co.copy() for x in bm.verts])
for rnd in range(MAX_ROUNDS):
    if not d:
        break
    vs = {v for e in d for v in e.verts}; vs |= {e.other_vert(v) for v in list(vs) for e in v.link_edges}
    new = {}
    for v in vs:                                     # 1) unfold: move towards the neighbours (no snapping yet)
        if not v.is_boundary:
            nb = [e.other_vert(v).co for e in v.link_edges]; new[v] = v.co.lerp(sum(nb, Vector()) / len(nb), STEP)
    for v, p in new.items():
        v.co = p
    bm.normal_update()
    for v in new:                                    # 2) back onto the source ALONG the vertex normal (the nearest point
        if v[L4] >= 10:                              #    inside a fold can lie on the opposite wall and rebuild the fin)
            continue
        best = None
        for sgn in (1, -1):
            h = sb.ray_cast(v.co, v.normal * sgn, PROJ_MAX)
            if h[0] is not None and (best is None or (h[0] - v.co).length < (best - v.co).length):
                best = h[0]
        if best is not None:
            v.co = best
    d = defects(); hist.append(len(d))
    if len(d) < best_state[0]:
        best_state = (len(d), [x.co.copy() for x in bm.verts])
    if rnd >= 5 and hist[-1] >= hist[-5]:
        break
for v, p in zip(bm.verts, best_state[1]):
    v.co = p
d = defects()
after = Counter(region(e.verts[0].co, e.verts[0]) for e in d)
moved = [(v.co - orig[v.index]).length for v in bm.verts]
# the repair must not create self-intersections
tris = bm.calc_loop_triangles(); T = [tuple(l.vert.index for l in t) for t in tris]
bvh = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], T, all_triangles=True)
inter = sum(1 for i, j in bvh.overlap(bvh) if not set(T[i]) & set(T[j]))
bm.to_mesh(body.data); body.data.update()
rep = {"method": __doc__.split("usage")[0].strip(), "in": IN.name, "excess_deg": EXCESS_DEG,
       "defect_edges_before": hist[0], "by_region_before": dict(before), "defect_edges_after": len(d), "by_region_after": dict(after),
       "history": hist, "vertices_moved_over_0p5mm": sum(m > 0.0005 for m in moved), "max_move_mm": round(1000 * max(moved), 2),
       "self_intersections_after": inter}
body["FOLD_REPAIR"] = json.dumps({k: v for k, v in rep.items() if k != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = OUT.name; REP.write_text(json.dumps(rep, indent=1)); print("REPAIR", json.dumps({k: v for k, v in rep.items() if k != "method"}))
