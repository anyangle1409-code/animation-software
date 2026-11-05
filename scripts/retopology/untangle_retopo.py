"""Remove self-intersections of the closed retopology body (rest pose) - local, on-surface, topology unchanged.

Loop: find non-adjacent intersecting triangle pairs; take their vertices plus a one-ring margin; move each to the
average of its edge neighbours (umbrella), then back onto the source surface (nearest point), unless the nearest
point is more than SNAP_MAX from the smoothed point (fused fingers / toes, where the nearest surface can belong to the
neighbouring digit) - those stay at the smoothed point. Repeat while the count falls. Vertices of the hand tagged as
fingers / thumb (t4_part >= 10) are smoothed without snapping. Reports the count by region before and after.

usage: python3.13 untangle_retopo.py -- <in .blend> <out NEW .blend> <report .json>
"""
import json
import sys
from collections import Counter
from pathlib import Path

import bpy
import bmesh  # noqa: E402
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
SRC = bpy.data.objects["HGPT_SOURCE_PROXY_Mesh_0"]; body = bpy.data.objects["HGPT_Male_Task3_Body"]
src_bvh = BVHTree.FromPolygons([v.co.copy() for v in SRC.data.vertices], [tuple(p.vertices) for p in SRC.data.polygons])
SNAP_MAX = 0.003; MAX_ROUNDS = 40; STEP = 0.6
bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
L4 = bm.verts.layers.int["t4_part"]; L5 = bm.verts.layers.int["t5_part"]


def region(v):
    p = v.co
    if v[L4] >= 10: return "fingers_thumb"
    if v[L4] == 1: return "palm"
    if v[L5] == 8: return "toes"
    if v[L5] in (6, 7): return "ankle_heel_foot"
    if v[L5] in (1, 2, 3, 4, 5): return "hips_legs"
    return "head_neck" if p.z > 1.55 else "torso_arms"


def hits():
    tris = bm.calc_loop_triangles(); T = [tuple(l.vert.index for l in t) for t in tris]
    bvh = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], T, all_triangles=True); out = []
    for i, j in bvh.overlap(bvh):
        if not set(T[i]) & set(T[j]):
            out.append((T[i], T[j]))
    return out


h = hits(); before = Counter(region(bm.verts[t[0][0]]) for t in h); hist = [len(h)]
best = (len(h), [v.co.copy() for v in bm.verts])
for rnd in range(MAX_ROUNDS):
    if not h:
        break
    vs = {i for t in h for tri in t for i in tri}
    vs |= {e.other_vert(bm.verts[i]).index for i in list(vs) for e in bm.verts[i].link_edges}
    new = {}
    for i in vs:
        v = bm.verts[i]
        if v.is_boundary:
            continue
        nb = [e.other_vert(v).co for e in v.link_edges]; avg = sum(nb, Vector()) / len(nb)
        p = v.co.lerp(avg, STEP)
        if v[L4] < 10:
            q = src_bvh.find_nearest(p)[0]
            if q is not None and (q - p).length < SNAP_MAX:
                p = q
        new[i] = p
    for i, p in new.items():
        bm.verts[i].co = p
    h = hits(); hist.append(len(h))
    if len(h) < best[0]:
        best = (len(h), [v.co.copy() for v in bm.verts])
    if rnd >= 6 and hist[-1] >= hist[-6]:
        break
for v, p in zip(bm.verts, best[1]):
    v.co = p
h = hits(); after = Counter(region(bm.verts[t[0][0]]) for t in h)
# how far the clean-up moved the surface (vs the input)
src_in = bpy.data.objects["HGPT_Male_Task3_Body"].data
moved = [(bm.verts[i].co - src_in.vertices[i].co).length for i in range(len(bm.verts))]
bm.to_mesh(body.data); body.data.update()
rep = {"method": __doc__.split("usage")[0].strip(), "in": IN.name, "intersecting_pairs_before": hist[0], "by_region_before": dict(before),
       "intersecting_pairs_after": len(h), "by_region_after": dict(after), "rounds": len(hist) - 1, "history": hist,
       "vertices_moved_over_0p5mm": sum(m > 0.0005 for m in moved), "max_move_mm": round(1000 * max(moved), 2)}
body["UNTANGLE"] = json.dumps({k: v for k, v in rep.items() if k != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = str(OUT); REP.write_text(json.dumps(rep, indent=1)); print("UNTANGLE", json.dumps({k: v for k, v in rep.items() if k != "method"}))
