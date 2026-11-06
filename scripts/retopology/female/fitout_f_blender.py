"""FEMALE fit-out of the densified body: toes and hands onto her surface. NEW file; the input is not changed.

* Toe cap (t5_part 8): each vertex is projected, along her foot axis (heel -> toe tip), onto the closed toe envelope
  (convex hull of her forefoot, which bridges the gaps between her separate toes) from IN FRONT of the toes (rays cast
  backwards: the first hit is the front of the envelope), then snapped to her real toe surface where that lies within
  3 mm. Toes are not separated in the geometry (documented; colour / shading carry them).
* Hands and feet (t4_part > 0, t5_part >= 6): a vertex INSIDE her source volume (ray parity on her full, closed source)
  moves to the nearest point of her surface (the thumb roots / thenar region the builders left under the skin);
  then RELAX passes of a light umbrella relax with re-projection onto the surface (same region, toe cap included).
Run the female untangle afterwards.

usage: python3.13 fitout_f_blender.py -- <densified .blend> <out NEW .blend> <report .json>
"""
import json
import sys
from pathlib import Path

import bpy
import bmesh  # noqa: E402
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from scipy.spatial import ConvexHull

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
RELAX = 4
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
SRC = bpy.data.objects["HGPT_FEMALE_SOURCE_Mesh_0"]; TGT = bpy.data.objects["HGPT_FEMALE_SOURCE_BODY_TARGET"]; body = bpy.data.objects["HGPT_Female_Body"]
SV = np.array([v.co[:] for v in SRC.data.vertices])
full = BVHTree.FromPolygons([Vector(p) for p in SV], [tuple(p.vertices) for p in SRC.data.polygons])
tgt = BVHTree.FromPolygons([v.co.copy() for v in TGT.data.vertices], [tuple(p.vertices) for p in TGT.data.polygons])
LEGS = json.loads(body["TASK5_LEGS"])
bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
L4 = bm.verts.layers.int["t4_part"]; L5 = bm.verts.layers.int["t5_part"]


def inside(p):
    d = Vector((0.31, 0.53, 0.79)).normalized(); cnt = 0; t = 0.0
    while True:
        h = full.ray_cast(p + d * (t + 1e-5), d)
        if h[0] is None:
            return cnt % 2 == 1
        cnt += 1; t = (h[0] - p).length


rep = {"in": IN.name}
# ---- toes
toe_moved = 0
for side, sg in (("right", 1.0), ("left", -1.0)):
    Lg = LEGS[side]; heel = np.array(Lg["heel"]); tip = np.array(Lg["toe_tip"])
    tdir = tip - heel; tdir[2] = 0; tdir /= np.linalg.norm(tdir)
    cap = [v for v in bm.verts if v[L5] == 8 and v.co.x * sg > 0]
    if not cap:
        continue
    yb = max(float((np.array(v.co[:]) - heel) @ tdir) for v in cap)
    base = min(float((np.array(v.co[:]) - heel) @ tdir) for v in cap)
    P = SV[(SV[:, 2] < 0.07) & (SV[:, 0] * sg > 0.05) & (((SV - heel) @ tdir) > base - 0.005) & (np.abs(SV[:, 0] - tip[0]) < 0.09)]
    hull = ConvexHull(P); hb = BVHTree.FromPolygons([Vector(q) for q in P], [tuple(s) for s in hull.simplices])
    T = Vector(tdir)
    for v in cap:
        o = v.co + T * 0.15; h = hb.ray_cast(o, -T, 0.3)
        if h[0] is None:
            continue
        q = h[0]; n = tgt.find_nearest(q)
        v.co = n[0] if (n[0] is not None and n[3] < 0.003) else q; toe_moved += 1
rep["toe_cap_vertices_projected"] = toe_moved
# ---- hands and feet: out of the source volume
region = [v for v in bm.verts if v[L4] > 0 or v[L5] >= 6]
fixed_in = 0
for v in region:
    if inside(v.co):
        n = tgt.find_nearest(v.co)
        if n[0] is not None:
            v.co = n[0]; fixed_in += 1
rep["hand_foot_vertices_inside_moved_out"] = fixed_in
for _ in range(RELAX):
    upd = {}
    for v in region:
        nb = [e.other_vert(v).co for e in v.link_edges]; avg = sum(nb, Vector()) / len(nb)
        p = v.co.lerp(avg, 0.3); n = tgt.find_nearest(p)
        upd[v] = n[0] if (n[0] is not None and n[3] < 0.003) else p
    for v, p in upd.items():
        v.co = p
still_in = sum(1 for v in region if inside(v.co))
rep["hand_foot_vertices_still_inside_after_relax"] = still_in
bm.to_mesh(body.data); body.data.update()
body["FITOUT"] = json.dumps(rep)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = str(OUT); REP.write_text(json.dumps(rep, indent=1)); print("FITOUT", json.dumps(rep))
