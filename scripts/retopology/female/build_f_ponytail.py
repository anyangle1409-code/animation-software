"""FEMALE ponytail: a separate quad mesh fitted to her source ponytail (NEW file; the body is not changed).

* Hair surface: the source faces left out of her projection target (the hanging ponytail) whose centre lies more than
  8 mm behind her back / head surface, plus the tie on her crown (z > 1.625 m, y > 0.015 m, as in the shell builder).
* Centre line: marched through the hair point cloud from the lowest hair point (the tip) upwards: at each step the
  hair points in a slab perpendicular to the current direction, within 7 cm of the last centre, give the next centre;
  the direction is updated from the last centres; it stops at the tie on the crown.
* Rings: N_RING vertices perpendicular to the centre line (frames carried by parallel transport); each vertex is the
  OUTERMOST hair-surface hit of a radial ray from the centre (strand grooves are left to the texture). The tip is
  closed by a quad cap; the top ring sinks 4 mm into the scalp under the tie.
* Light relax along the rings (no shrinking: re-projected radially).

usage: python3.13 build_f_ponytail.py -- <in .blend (with HGPT_Female_Body)> <out NEW .blend> <report .json>
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
N_RING, STEP = 16, 0.012
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
SRC = bpy.data.objects["HGPT_FEMALE_SOURCE_Mesh_0"]; TGT = bpy.data.objects["HGPT_FEMALE_SOURCE_BODY_TARGET"]
SV = np.array([v.co[:] for v in SRC.data.vertices]); SF = [tuple(p.vertices) for p in SRC.data.polygons]
kept = {tuple(sorted(p.vertices)) for p in TGT.data.polygons}
TV = np.array([v.co[:] for v in TGT.data.vertices])


def back_y(z):
    s = TV[(np.abs(TV[:, 2] - z) < 0.004) & (np.abs(TV[:, 0]) < 0.05)]
    s = s[s[:, 2] < 1.625] if z < 1.625 else s
    return float(s[:, 1].max()) if len(s) else 0.0


BY = {round(z, 2): back_y(z) for z in np.arange(0.90, 1.70, 0.01)}
hair_f = []
for f in SF:
    c = SV[list(f)].mean(0)
    if c[2] > 1.625 and c[1] > 0.015 and abs(c[0]) < 0.07:
        hair_f.append(f); continue                                   # the tie / ponytail root on the crown
    if tuple(sorted(f)) in kept or not (0.9 < c[2] < 1.65 and abs(c[0]) < 0.12):
        continue
    if c[1] > BY[round(min(max(c[2], 0.90), 1.69), 2)] + 0.008:
        hair_f.append(f)
hv = sorted({i for f in hair_f for i in f}); HP = SV[hv]
hbvh = BVHTree.FromPolygons([Vector(p) for p in SV], hair_f)
scalp = BVHTree.FromPolygons([Vector(p) for p in TV], [tuple(p.vertices) for p in TGT.data.polygons])

# ---- centre line, tip -> crown
start = HP[np.argmin(HP[:, 2])]
d = np.array([0.0, 0.0, 1.0]); C = [HP[np.linalg.norm(HP - start, axis=1) < 0.03].mean(0)]
for it in range(200):
    o = C[-1] + d * STEP
    rel = HP - o; sl = HP[(np.abs(rel @ d) < 0.004) & (np.linalg.norm(rel - np.outer(rel @ d, d), axis=1) < 0.07)]
    if len(sl) < 12:
        break
    c = sl.mean(0); C.append(c)
    if len(C) >= 3:
        nd = C[-1] - C[-3]; d = nd / np.linalg.norm(nd)
    if c[2] > 1.60 and c[1] < 0.03:                                  # reached the tie on the crown
        break
C = np.array(C)
# ---- rings (parallel transport)
T = [(C[min(i + 1, len(C) - 1)] - C[max(i - 1, 0)]) for i in range(len(C))]; T = [t / np.linalg.norm(t) for t in T]
e1 = np.cross(T[0], [1.0, 0, 0]); e1 /= np.linalg.norm(e1)
rings = []; radii = []
for i, c in enumerate(C):
    if i:
        e1 = e1 - T[i] * (e1 @ T[i]); e1 /= np.linalg.norm(e1)
    e2 = np.cross(T[i], e1); rg = []; rr = []
    for k in range(N_RING):
        ang = 2 * math.pi * k / N_RING; dv = Vector(e1 * math.cos(ang) + e2 * math.sin(ang))
        o = Vector(c); far = None; t = 0.0
        while True:                                                  # outermost hit along the ray (within 8 cm)
            h = hbvh.ray_cast(o + dv * (t + 0.0003), dv, 0.08 - t)
            if h[0] is None:
                break
            t = (h[0] - o).length; far = h[0]
        if far is None:
            far = o + dv * (radii[-1][k] if radii else 0.01)
        rg.append(np.array(far[:])); rr.append((far - o).length)
    rings.append(rg); radii.append(rr)
# relax radii along each ring and between rings (strand grooves / missing hits), keep centres
R = np.array(radii)
for _ in range(3):
    R = 0.5 * R + 0.25 * (np.roll(R, 1, 1) + np.roll(R, -1, 1))
for i in range(len(C)):
    dirs = [(np.array(rings[i][k]) - C[i]) / max(np.linalg.norm(np.array(rings[i][k]) - C[i]), 1e-9) for k in range(N_RING)]
    rings[i] = [C[i] + dirs[k] * R[i, k] for k in range(N_RING)]
# top ring sinks into the scalp under the tie
top = np.array(rings[-1]); sunk = []
for p in top:
    h = scalp.find_nearest(Vector(p))[0]; n = (Vector(p) - h).normalized() if h else Vector((0, 0, 1))
    sunk.append(np.array((h - n * 0.004)[:]) if h else p)
rings.append(sunk)
# ---- mesh
verts = [p for rg in rings for p in rg]; faces = []
for i in range(len(rings) - 1):
    for k in range(N_RING):
        faces.append([i * N_RING + k, i * N_RING + (k + 1) % N_RING, (i + 1) * N_RING + (k + 1) % N_RING, (i + 1) * N_RING + k])
# tip cap: a 4 x 4 quad grid whose 16 perimeter vertices are the first ring (Coons patch, pushed 4 mm towards the tip)
G = 4; per = [(0, j) for j in range(G)] + [(i, G) for i in range(G)] + [(G, j) for j in range(G, 0, -1)] + [(i, 0) for i in range(G, 0, -1)]
gid = {per[k]: k for k in range(N_RING)}; P0 = {per[k]: np.array(rings[0][k]) for k in range(N_RING)}
for i in range(1, G):
    for j in range(1, G):
        u, w = j / G, i / G
        pt = ((1 - w) * P0[0, j] + w * P0[G, j] + (1 - u) * P0[i, 0] + u * P0[i, G]
              - ((1 - u) * (1 - w) * P0[0, 0] + u * (1 - w) * P0[0, G] + (1 - u) * w * P0[G, 0] + u * w * P0[G, G]))
        bulge = 1.0 - (abs(u - 0.5) + abs(w - 0.5))
        gid[i, j] = len(verts); verts.append(pt - T[0] * 0.004 * bulge)
for i in range(G):
    for j in range(G):
        faces.append([gid[i, j], gid[i, j + 1], gid[i + 1, j + 1], gid[i + 1, j]])
me = bpy.data.meshes.new("HGPT_Female_Ponytail"); me.from_pydata([tuple(p) for p in verts], [], faces); me.validate(); me.update()
ob = bpy.data.objects.new("HGPT_Female_Ponytail", me); bpy.data.objects["HGPT_Female_Body"].users_collection[0].objects.link(ob)
me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
import bmesh  # noqa: E402
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); me.update()
nonmanifold = sum(1 for e in bm.edges if len(e.link_faces) not in (1, 2))
dev = [hbvh.find_nearest(Vector(p))[3] for rg in rings[:-1] for p in rg]
rep = {"in": IN.name, "hair_source_faces": len(hair_f), "centre_line_stations": len(C), "length_m": round(float(np.linalg.norm(np.diff(C, axis=0), axis=1).sum()), 3),
       "tip_z": round(float(C[0][2]), 3), "root": [round(float(x), 3) for x in C[-1]], "vertices": len(me.vertices), "faces": len(me.polygons),
       "non_quads": sum(len(p.vertices) != 4 for p in me.polygons), "boundary_edges": sum(1 for e in bm.edges if e.is_boundary), "nonmanifold_edges": nonmanifold,
       "distance_to_hair_mm_p50_p95": [round(float(np.percentile(dev, q)) * 1000, 2) for q in (50, 95)]}
ob["PONYTAIL"] = json.dumps(rep)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = str(OUT); REP.write_text(json.dumps(rep, indent=1)); print("PONYTAIL", json.dumps(rep))
