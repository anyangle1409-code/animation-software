"""FEMALE F10a: bra mesh repair - complete right front strap, no flap into the armpit. NEW file; input unchanged.

F07a cut the bra from the body cage by albedo; on her right side the thin front strap was missed (17 faces above
z 1.28 against 47 on the left: the strap stopped at a spike below the shoulder, the rest of it was only painted on the
skin) and on her left side the side panel ran 2 cm into the armpit (a flap). The left half is the complete one, so:
  * the bra is cut at the mid-sagittal plane (x = 0), the right half removed and the left half mirrored (seam welded
    within 0.5 mm); vertex weights of the mirrored half are swapped _l <-> _r;
  * faces whose centre lies more than XMAX from the midline at armpit level (the flap) are removed;
  * every vertex is then projected onto HER source surface (nearest point) and lifted LIFT along the source normal, so
    the mirrored half follows her own (asymmetric) body, not the left side's shape;
  * the hems are relaxed along themselves and re-projected (as garment_hems_f_blender.py), small loose pieces dropped.
The fabric texture is uniform (F09b set every garment texel to the median fabric colour), so the mirrored UVs are
valid.

usage: python3.13 fix_bra_f_blender.py -- <in .blend> <out NEW .blend> <report .json>
"""
import heapq
import json
import sys
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
XMAX, LIFT, HEM_IT = 0.147, 0.0006, 20
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
rig = bpy.data.objects["HGPT_FEMALE_RIG"]; rig.data.pose_position = "REST"; bpy.context.view_layer.update()
SRC = bpy.data.objects["HGPT_FEMALE_SOURCE_Mesh_0"]
src = BVHTree.FromPolygons([v.co.copy() for v in SRC.data.vertices], [tuple(p.vertices) for p in SRC.data.polygons])
ob = bpy.data.objects["HGPT_Female_Bra"]; me = ob.data
names = [g.name for g in ob.vertex_groups]; gi = {n: i for i, n in enumerate(names)}


def twin(n):
    return n[:-2] + "_r" if n.endswith("_l") else (n[:-2] + "_l" if n.endswith("_r") else n)


rep = {"in": IN.name, "faces_before": len(me.polygons)}
bm = bmesh.new(); bm.from_mesh(me)
geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_inner=True, dist=1e-5)
n_half = len(bm.faces)
res = bmesh.ops.mirror(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], axis="X", merge_dist=0.0005)
dl = bm.verts.layers.deform.active
for v in [e for e in res["geom"] if isinstance(e, bmesh.types.BMVert)]:
    d = dict(v[dl]); v[dl].clear()
    for k, w in d.items():
        v[dl][gi.get(twin(names[k]), k)] = w
seam = [v for v in bm.verts if abs(v.co.x) < 1e-4]
bmesh.ops.remove_doubles(bm, verts=seam, dist=0.001)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
out_ = sum((f.normal.dot(src.find_nearest(f.calc_center_median())[1]) > 0) for f in bm.faces[:400])
if out_ < 200:                                      # normals must point away from her body (Solidify offset -1)
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
rep["seam_vertices_welded"] = len(seam)
# over-the-shoulder strap segments: F07a missed them (thin), so between each front strap's top and the back Y arm on
# the same side they exist only as fused fabric on her skin (raised edge lips over the trapezius). Each is rebuilt as
# a strip: the shortest path over HER body surface between the two strap ends (extended 8 mm into each, under-lapping
# the existing strap), resampled every 5 mm, smoothed, 3 vertices across STRAP_W, projected onto her source and lifted
# STRAP_LIFT (0.3 mm proud of the strap it overlaps). Weights are copied from the nearest body vertex.
STRAP_W, STRAP_LIFT = 0.013, 0.0009
body = bpy.data.objects["HGPT_Female_Body"]; bme = body.data
BP = np.array([v.co[:] for v in bme.vertices]); bnb = [[] for _ in BP]
for e in bme.edges:
    bnb[e.vertices[0]].append(e.vertices[1]); bnb[e.vertices[1]].append(e.vertices[0])
bgn = {g.index: g.name for g in body.vertex_groups}
uvl = bm.loops.layers.uv.active; uv0 = next(iter(bm.faces)).loops[0][uvl].uv.copy()
BV = np.array([v.co[:] for v in bm.verts])


def shortest(i0, i1):
    dist = {i0: 0.0}; prev = {}; pq = [(0.0, i0)]
    while pq:
        d0, i = heapq.heappop(pq)
        if i == i1:
            break
        if d0 > dist[i]:
            continue
        for j in bnb[i]:
            nd = d0 + float(np.linalg.norm(BP[i] - BP[j]))
            if nd < dist.get(j, 1e9):
                dist[j] = nd; prev[j] = i; heapq.heappush(pq, (nd, j))
    path = [i1]
    while path[-1] != i0:
        path.append(prev[path[-1]])
    return BP[path[::-1]]


added = 0; STRAPV = set()
for sgn in (1, -1):
    fr = BV[(BV[:, 1] < 0) & (sgn * BV[:, 0] > 0)]; A = fr[np.argsort(-fr[:, 2])[:4]].mean(0)
    bk = BV[(BV[:, 1] > 0) & (sgn * BV[:, 0] > 0)]; B = bk[np.argsort(-bk[:, 2])[:4]].mean(0)
    i0 = int(np.argmin(np.linalg.norm(BP - A, axis=1))); i1 = int(np.argmin(np.linalg.norm(BP - B, axis=1)))
    pts = shortest(i0, i1)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); t = np.concatenate([[0], np.cumsum(seg)])
    ext = 0.008; L = t[-1]; ts = np.arange(-ext, L + ext + 1e-9, 0.005)
    d0 = (pts[1] - pts[0]) / max(seg[0], 1e-9); d1 = (pts[-1] - pts[-2]) / max(seg[-1], 1e-9)
    Q = np.array([pts[0] + d0 * x if x < 0 else (pts[-1] + d1 * (x - L) if x > L else
                  np.array([np.interp(x, t, pts[:, k]) for k in range(3)])) for x in ts])
    for _ in range(6):
        Q[1:-1] = Q[1:-1] * 0.5 + (Q[:-2] + Q[2:]) * 0.25
        Q = np.array([src.find_nearest(Vector(q))[0][:] for q in Q])
    rows = []
    for k in range(len(Q)):
        tg = Q[min(k + 1, len(Q) - 1)] - Q[max(k - 1, 0)]; tg /= np.linalg.norm(tg)
        n = np.array(src.find_nearest(Vector(Q[k]))[1][:]); side = np.cross(n, tg); side /= np.linalg.norm(side)
        row = []
        for off in (-0.5, 0.0, 0.5):
            h = src.find_nearest(Vector(Q[k] + side * off * STRAP_W))
            v = bm.verts.new(h[0] + h[1] * STRAP_LIFT)
            bi = int(np.argmin(np.linalg.norm(BP - np.array(v.co[:]), axis=1)))
            for g in bme.vertices[bi].groups:
                nm = bgn.get(g.group)
                if nm in gi:
                    v[dl][gi[nm]] = g.weight
            row.append(v); STRAPV.add(v)
        rows.append(row)
    for k in range(len(rows) - 1):
        for c in range(2):
            f = bm.faces.new([rows[k][c], rows[k][c + 1], rows[k + 1][c + 1], rows[k + 1][c]])
            for lo in f.loops:
                lo[uvl].uv = uv0
            added += 1
    rep[f"strap_{'left' if sgn > 0 else 'right'}"] = {"from": [round(x, 3) for x in A], "to": [round(x, 3) for x in B],
                                                      "length_mm": round(float(L) * 1000, 1)}
rep["shoulder_strap_faces_added"] = added
# the flap into the armpit
flap = [f for f in bm.faces if abs(f.calc_center_median().x) > XMAX and 1.15 < f.calc_center_median().z < 1.25]
bmesh.ops.delete(bm, geom=flap, context="FACES"); rep["flap_faces_removed"] = len(flap)
# loose pieces
bm.faces.ensure_lookup_table(); seen = set(); drop = []
for f0 in bm.faces:
    if f0 in seen:
        continue
    comp = []; st = [f0]; seen.add(f0)
    while st:
        f = st.pop(); comp.append(f)
        for e in f.edges:
            for g in e.link_faces:
                if g not in seen:
                    seen.add(g); st.append(g)
    if len(comp) < 30:
        drop += comp
bmesh.ops.delete(bm, geom=drop, context="FACES"); rep["loose_faces_removed"] = len(drop)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")


bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
if sum((f.normal.dot(src.find_nearest(f.calc_center_median())[1]) > 0) for f in bm.faces[:400]) < 200:
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:])


def to_src(p):
    h = src.find_nearest(p)
    return (h[0] + h[1] * LIFT) if h[0] is not None else p


for v in bm.verts:
    if v not in STRAPV:
        v.co = to_src(v.co)
bnd = [v for v in bm.verts if v.is_boundary and v not in STRAPV]; bset = set(bnd)
ring = {e.other_vert(v) for v in bnd for e in v.link_edges} - bset - STRAPV
for _ in range(HEM_IT):
    upd = {}
    for v in bnd:
        nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
        if len(nb) == 2:
            upd[v] = to_src(v.co.lerp((nb[0].co + nb[1].co) * 0.5, 0.5))
    for v in ring:
        nb = [e.other_vert(v).co for e in v.link_edges]
        upd[v] = to_src(v.co.lerp(sum(nb, Vector()) / len(nb), 0.3))
    for v, p in upd.items():
        v.co = p
bm.to_mesh(me); me.update()
C = np.array([p.center[:] for p in me.polygons])
rep.update({"faces_after": len(me.polygons), "half_faces": n_half,
            "strap_faces_front_above_1_28": {"left": int(((C[:, 0] > 0) & (C[:, 1] < 0) & (C[:, 2] > 1.28)).sum()),
                                             "right": int(((C[:, 0] < 0) & (C[:, 1] < 0) & (C[:, 2] > 1.28)).sum())},
            "boundary_vertices": len(bnd)})
bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = str(OUT); REP.write_text(json.dumps(rep, indent=1)); print("BRAFIX", json.dumps(rep))
