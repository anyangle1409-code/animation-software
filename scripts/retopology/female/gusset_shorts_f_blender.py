"""FEMALE F12b: a crotch gusset for the F12a shorts. NEW file; input unchanged.

Validation of F12a (midline rays from the skin) found the rebuilt shorts did not reach under the crotch: the leg
openings had been raised to her SOURCE's midline underside, where the source's fused fabric sits ~0.79, while the
body's crotch underside is at z 0.73-0.78, so between y -0.06 and +0.06 the skin was bare and the front and back
panels ended in two hems with one opening round both legs. Re-cutting the shorts from body faces down to the body's
crotch line was tried four ways and failed: the body's crotch underside is only ~2 cm wide between the inguinal
creases, so the face coverage either hung down the inner thighs, narrowed to a string when the hems were relaxed, or
folded when the hems were snapped to a curve.

Here the clean F12a shorts are kept and closed underneath by a gusset, as a real pair of shorts is made:
  * the front and back crotch hems (|x| < W) are the gusset's ends; the back hem is resampled to the front's count;
  * the grid between them is laid by rays from inside the pelvis: for each column a centre (x, 0, ZC) and a fan of
    directions in the sagittal plane from the front-hem direction to the back-hem direction; the exit point on the
    skin + GAP along its normal;
  * the grid (and the old front / back hem rows, now inside the garment) is relaxed, each vertex keeping its x (tapered to (1 - TAPER)
    under the crotch) so the panel spans the thigh roots, as a membrane with a collision constraint (a Laplacian step, then anything within GAP_MIN of
    the skin pushed out along the skin normal) with the two end rows fixed; the side edges (the new parts of the leg
    openings) are smoothed along themselves. A membrane spans the inguinal creases instead of following them;
  * the last grid row is joined to the existing back hem vertices; fabric UV;
  * the whole garment's weights are rebuilt from the skin (F12a's rebuild had broken them - see WEIGHTS below).
Then the whole shorts keeps >= GAP_MIN over the skin, the gusset >= GAP_GUSSET (it is where skin and fabric meet in
the standing pose's thigh rotation).

usage: python3.13 gusset_shorts_f_blender.py -- <in .blend> <out NEW .blend> <report .json>
"""
import json
import math
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
W, ROWS, ZC, GAP, GAP_MIN, GAP_GUSSET, MEM_IT = 0.036, 14, 0.80, 0.0030, 0.0018, 0.0030, 120
TAPER = 0.45                                         # gusset half-width under the crotch = (1 - TAPER) x the hem width
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
rig = bpy.data.objects["HGPT_FEMALE_RIG"]; rig.data.pose_position = "REST"; bpy.context.view_layer.update()
body = bpy.data.objects["HGPT_Female_Body"]; me = body.data
P = np.array([v.co[:] for v in me.vertices])
bt = BVHTree.FromPolygons([Vector(p) for p in P], [tuple(p.vertices) for p in me.polygons])
so = bpy.data.objects["HGPT_Female_Shorts"]; g = bmesh.new(); g.from_mesh(so.data); g.verts.ensure_lookup_table()
rep = {"in": IN.name, "faces_before": len(g.faces)}
hem = [v for v in g.verts if v.is_boundary and abs(v.co.x) < W and v.co.z < 0.86]
F = sorted([v for v in hem if v.co.y < 0], key=lambda v: v.co.x); B = sorted([v for v in hem if v.co.y > 0], key=lambda v: v.co.x)
K = len(F); rep.update({"front_hem_vertices": K, "back_hem_vertices": len(B)})


def resample(vs, n):
    pts = np.array([v.co[:] for v in vs]); s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    t = np.linspace(0, s[-1], n); return np.column_stack([np.interp(t, s, pts[:, k]) for k in range(3)])


Fp = np.array([v.co[:] for v in F]); Bp = resample(B, K)
grid = [list(F)]
for r in range(1, ROWS):
    u = r / ROWS; row = []
    for j in range(K):
        x = (1 - u) * Fp[j, 0] + u * Bp[j, 0]; c = Vector((x, 0, ZC))
        af = math.atan2(Fp[j, 1], -(Fp[j, 2] - ZC)); ab = math.atan2(Bp[j, 1], -(Bp[j, 2] - ZC)); th = (1 - u) * af + u * ab
        d = Vector((0, math.sin(th), -math.cos(th))); h = bt.ray_cast(c, d, 0.3)
        p = (h[0] + h[1] * GAP) if h[0] is not None else c + d * 0.07
        row.append(g.verts.new(p))
    grid.append(row)
for r in range(ROWS - 1):
    for j in range(K - 1):
        g.faces.new((grid[r][j], grid[r][j + 1], grid[r + 1][j + 1], grid[r + 1][j]))
# zipper: last grid row (K) to the back hem (len(B)), both ordered by x
L, Rr = grid[-1], B; i = k = 0
while i < len(L) - 1 or k < len(Rr) - 1:
    adv_l = k >= len(Rr) - 1 or (i < len(L) - 1 and (L[i + 1].co.x + L[i].co.x) / 2 <= (Rr[k + 1].co.x + Rr[k].co.x) / 2)
    if adv_l:
        g.faces.new((L[i], L[i + 1], Rr[k])); i += 1
    else:
        g.faces.new((L[i], Rr[k + 1], Rr[k])); k += 1
new_verts = [v for row in grid[1:] for v in row]; nvs = set(new_verts); rep["gusset_vertices"] = len(new_verts)
interior = [v for row in grid[1:] for v in row[1:-1]] + F[1:-1] + B[1:-1]; edges = [row[0] for row in grid[1:]] + [row[-1] for row in grid[1:]]
side_nb = {}
for c in (0, K - 1):
    col = [grid[r][c] for r in range(ROWS)] + [B[0] if c == 0 else B[-1]]
    for r in range(1, ROWS):
        side_nb[col[r]] = (col[r - 1], col[r + 1])


def push(p, gap=GAP_MIN):
    hb = bt.find_nearest(p); s_ = (p - hb[0]).dot(hb[1])
    return hb[0] + hb[1] * gap if s_ < gap else p


# each vertex keeps its lateral position (x) while relaxing: a free membrane slid its side edges into the inguinal
# creases and pinched the gusset to ~1 cm (seen in a trial); with x held the panel spans from thigh to thigh
# held x tapers from the hem width at both ends to (1 - TAPER) of it under the crotch: at full width the side edges
# hung below the crotch into the gap between the thighs (a floating flap, seen in a trial)
rowu = {v: r / ROWS for r, row in enumerate(grid) for v in row}
X0 = {v: v.co.x * (1 - TAPER * math.sin(math.pi * rowu.get(v, 0.0))) for v in interior + list(side_nb)}
for it in range(MEM_IT):
    upd = {}
    for v in interior:
        nb = [e.other_vert(v).co for e in v.link_edges]; upd[v] = v.co.lerp(sum(nb, Vector()) / len(nb), 0.5)
    for v, (p0, p1) in side_nb.items():
        upd[v] = v.co.lerp((p0.co + p1.co) * 0.5, 0.5)
    for v, c in upd.items():
        c.x = X0[v]; v.co = push(c, GAP_GUSSET if v in nvs else GAP_MIN)
# UV, normals (weights: after the mesh is written, below)
uvl = g.loops.layers.uv.active; u0 = so.data.uv_layers.active.data[0].uv.copy()
for f in g.faces:
    for lo in f.loops:
        if lo.vert in set(new_verts) or any(x in set(new_verts) for x in f.verts):
            lo[uvl].uv = u0
bmesh.ops.recalc_face_normals(g, faces=g.faces[:])
if sum((f.normal.dot(bt.find_nearest(f.calc_center_median())[1]) > 0) for f in g.faces[:300]) < 150:
    bmesh.ops.reverse_faces(g, faces=g.faces[:])
for v in g.verts:
    v.co = push(v.co, GAP_GUSSET if v in nvs else GAP_MIN)
for f in g.faces:
    f.smooth = True
g.verts.index_update(); new_idx = [v.index for v in new_verts]
dlay = g.verts.layers.deform.active                  # drop every old deform entry (stale indices included)
if dlay is not None:
    g.verts.layers.deform.remove(dlay)
g.to_mesh(so.data); so.data.update()
# WEIGHTS for the whole garment. F12a's rebuild assigned a new mesh datablock to the shorts; vertex-group NAMES live on
# the mesh, so the new mesh kept only 3 names and most weights pointed at groups that did not exist (the shorts
# barely followed the thighs: 30-67 mm off the skin at 45-90 deg hip flexion; invisible at rest). Every shorts
# vertex now takes the skin's weights at its nearest skin point (inverse-distance blend of that face's corners),
# top 4 influences, normalised - the same rule as the skin (rig contract).
for vg in list(so.vertex_groups):
    so.vertex_groups.remove(vg)
bones = set(rig.data.bones.keys()); bgn = {x.index: x.name for x in body.vertex_groups}
VG = {nm: so.vertex_groups.new(name=nm) for nm in sorted(set(bgn.values()) & bones)}
W_ = [{bgn[gg.group]: gg.weight for gg in v.groups if bgn.get(gg.group) in bones} for v in me.vertices]
for v in so.data.vertices:
    hb = bt.find_nearest(v.co); fv = me.polygons[hb[2]].vertices
    iw = np.array([1.0 / max((Vector(P[k]) - hb[0]).length, 1e-5) for k in fv]); iw /= iw.sum(); acc = {}
    for k, w in zip(fv, iw):
        for nm, x in W_[k].items():
            acc[nm] = acc.get(nm, 0.0) + w * x
    top = sorted(acc.items(), key=lambda t: -t[1])[:4]; tot = sum(x for _, x in top)
    for nm, x in top:
        if x > 1e-4:
            VG[nm].add([v.index], x / tot, "REPLACE")
rep["weights"] = {"groups": len(VG), "rule": "nearest skin point, top 4, normalised"}
bm2 = bmesh.new(); bm2.from_mesh(so.data)
rep.update({"faces_after": len(bm2.faces), "non_manifold_edges": sum(1 for e in bm2.edges if not e.is_manifold and not e.is_boundary),
            "boundary_loops_vertices": sum(1 for v in bm2.verts if v.is_boundary)}); bm2.free()
d = np.array([bt.find_nearest(v.co)[3] for v in so.data.vertices]) * 1000
rep["off_skin_mm"] = {"p50": round(float(np.percentile(d, 50)), 2), "p95": round(float(np.percentile(d, 95)), 2), "max": round(float(d.max()), 2)}
dg = np.array([bt.find_nearest(so.data.vertices[i].co)[3] for i in new_idx]) * 1000
rep["gusset_off_skin_mm"] = {"p50": round(float(np.percentile(dg, 50)), 2), "max": round(float(dg.max()), 2)}
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = str(OUT); REP.write_text(json.dumps(rep, indent=1)); print("GUSSET", json.dumps(rep))
