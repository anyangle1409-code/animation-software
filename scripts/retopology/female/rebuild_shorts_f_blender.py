"""FEMALE F12a: shorts rebuilt with a continuous crotch panel and clean leg openings. NEW file; input unchanged.

The F07a-F11a shorts were cut from the body cage by albedo; at the crotch they ended in two flaps meeting at a slit,
a pointed tab hanging at the front centre and a thin spike underneath (the protrusion seen in the clothed views).
The body there was clean; the garment was the cause. Rebuilt here (same object, materials, Solidify, armature):
  * COVERAGE on the body: faces below the waistband line (the existing shorts' top hem, by angle round the pelvis)
    and above the leg openings. Each leg opening is a plane z = a + b|x| + c y fitted to the existing hem where it is
    clean (|x| > 0.06), raised linearly towards the midline to just under HER crotch line (her source's midline
    underside, front to back) - so the crotch panel runs continuously under the crotch, and the inner-thigh contact
    skin below it stays skin, as in her source. Largest connected piece, hands excluded.
  * SHAPE: each vertex on her source's (fabric) surface - first hit from outside along the skin normal, normals
    agreeing - lifted LIFT; at least GAP_MIN over the skin; hems relaxed along themselves and re-projected; a light
    Taubin pass inside. Her source shorts' look and the hip / thigh proportions are kept.
  * WEIGHTS copied from the skin vertex each garment vertex was made from (the fabric moves exactly with the skin);
    UVs on the fabric colour (uniform fabric).

KNOWN DEFECTS (found in F12 validation; kept as run so F12a stays reproducible - corrected downstream by
gusset_shorts_f_blender.py, which makes F12d):
  * the leg openings were raised to the SOURCE's crotch line, which sits above the body's crotch underside, so these
    shorts have no crotch panel (bare skin from y -0.06 to +0.06);
  * WEIGHTS: `so.data = newme` swaps the mesh datablock, and vertex-group names live on the mesh, so the new shorts
    kept only 3 group names and most weights point at groups that do not exist - invisible at rest, but the shorts
    lift 30-67 mm off the skin at 45-90 deg hip flexion.

usage: python3.13 rebuild_shorts_f_blender.py -- <in .blend> <out NEW .blend> <report .json>
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
LIFT, GAP_MIN, HEM_IT = 0.0006, 0.0018, 60
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
rig = bpy.data.objects["HGPT_FEMALE_RIG"]; rig.data.pose_position = "REST"; bpy.context.view_layer.update()
body = bpy.data.objects["HGPT_Female_Body"]; me = body.data
P = np.array([v.co[:] for v in me.vertices]); FACES = [list(p.vertices) for p in me.polygons]
t4 = np.array([d.value for d in me.attributes["t4_part"].data])
SRC = bpy.data.objects["HGPT_FEMALE_SOURCE_Mesh_0"]; SV = np.array([v.co[:] for v in SRC.data.vertices])
src = BVHTree.FromPolygons([Vector(p) for p in SV], [tuple(p.vertices) for p in SRC.data.polygons])
bodyb = BVHTree.FromPolygons([Vector(p) for p in P], FACES)
so = bpy.data.objects["HGPT_Female_Shorts"]; old = so.data
OV = np.array([v.co[:] for v in old.vertices])
g0 = bmesh.new(); g0.from_mesh(old); g0.verts.ensure_lookup_table()
OB = np.array([v.co[:] for v in g0.verts if v.is_boundary]); g0.free()
rep = {"in": IN.name, "old_faces": len(old.polygons)}

# waistband line: the old top hem, z by angle round the pelvis axis
cy = float(np.median(P[(P[:, 2] > 0.85) & (P[:, 2] < 0.95), 1]))
top = OB[OB[:, 2] > 0.86]; ang = np.arctan2(top[:, 1] - cy, top[:, 0])
bins = np.linspace(-math.pi, math.pi, 73); ztop = np.full(72, np.nan)
for k in range(72):
    m = (ang >= bins[k]) & (ang < bins[k + 1])
    if m.any():
        ztop[k] = np.median(top[m, 2])
ok = ~np.isnan(ztop); cen = (bins[:-1] + bins[1:]) / 2
z_top = lambda x, y: float(np.interp(math.atan2(y - cy, x), np.concatenate([cen[ok] - 2 * math.pi, cen[ok], cen[ok] + 2 * math.pi]), np.tile(ztop[ok], 3)))
# her crotch line (source midline underside)
mid = SV[(np.abs(SV[:, 0]) < 0.008) & (SV[:, 2] > 0.6) & (SV[:, 2] < 0.9) & (np.abs(SV[:, 1]) < 0.1)]
yb = np.linspace(-0.1, 0.1, 41); zl = np.full(41, np.nan)
for k, y_ in enumerate(yb):
    q = mid[np.abs(mid[:, 1] - y_) < 0.004]
    if len(q):
        zl[k] = q[:, 2].min()
okl = ~np.isnan(zl); z_cr = lambda y: float(np.interp(y, yb[okl], zl[okl]))
# leg-opening planes from the clean part of the old leg hems
legs = OB[(OB[:, 2] < 0.86) & (np.abs(OB[:, 0]) > 0.06)]
coef = {}
for sg in (1, -1):
    q = legs[np.sign(legs[:, 0]) == sg]
    A = np.column_stack([np.ones(len(q)), np.abs(q[:, 0]), q[:, 1]]); coef[sg] = np.linalg.lstsq(A, q[:, 2], rcond=None)[0]
rep["leg_plane_z_a_b_c"] = {("left" if s > 0 else "right"): [round(float(c), 4) for c in coef[s]] for s in coef}


def z_open(x, y):
    c = coef[1 if x >= 0 else -1]; zp = c[0] + c[1] * max(abs(x), 0.06) + c[2] * y
    if abs(x) >= 0.06:
        return zp
    zc = z_cr(y) - 0.003; t = np.clip((0.06 - abs(x)) / 0.04, 0, 1)
    return zp + (zc - zp) * t


sel = []
for k, f in enumerate(FACES):
    c = P[f].mean(0)
    if t4[f[0]] >= 1 or abs(c[0]) > 0.3 or not (0.6 < c[2] < 1.02):
        continue
    if c[2] < z_top(c[0], c[1]) and c[2] > z_open(c[0], c[1]):
        sel.append(k)
# largest connected piece
fs = set(sel); vf = {}
for k in sel:
    for v in FACES[k]:
        vf.setdefault(v, []).append(k)
seen = set(); best = []
for k0 in sel:
    if k0 in seen:
        continue
    comp = [k0]; seen.add(k0); i = 0
    while i < len(comp):
        for v in FACES[comp[i]]:
            for k in vf[v]:
                if k not in seen:
                    seen.add(k); comp.append(k)
        i += 1
    if len(comp) > len(best):
        best = comp
rep["coverage_faces"] = len(best)
# new mesh
Nb = np.zeros_like(P)
for f in FACES:
    n = np.cross(P[f[1]] - P[f[0]], P[f[2]] - P[f[0]]); Nb[f] += n
Nb /= np.maximum(np.linalg.norm(Nb, axis=1, keepdims=True), 1e-12)


def place(p, n):
    o = Vector(p + n * 0.02); h = src.ray_cast(o, Vector(-n), 0.04)
    q = np.array(h[0][:]) + np.array(h[1][:]) * LIFT if (h[0] is not None and h[1].dot(Vector(n)) > 0.3) else p + n * 0.002
    hb = bodyb.find_nearest(Vector(q)); s_ = np.dot(q - np.array(hb[0][:]), np.array(hb[1][:]))
    if s_ < GAP_MIN:
        q = np.array(hb[0][:]) + np.array(hb[1][:]) * GAP_MIN
    return q


g = bmesh.new(); vmap = {}; src_list = []
for k in best:
    for vi in FACES[k]:
        if vi not in vmap:
            nv = g.verts.new(Vector(place(P[vi], Nb[vi]))); vmap[vi] = nv; src_list.append(vi)
for k in best:
    g.faces.new([vmap[v] for v in FACES[k]])
g.verts.ensure_lookup_table(); g.normal_update()
bnd = [v for v in g.verts if v.is_boundary]; bset = set(bnd)
ring = {e.other_vert(v) for v in bnd for e in v.link_edges} - bset


def reproj(p):
    hb = bodyb.find_nearest(p); n = Vector(hb[1]); q = place(np.array(hb[0][:]), np.array(n[:])); return Vector(q)


for _ in range(HEM_IT):
    upd = {}
    for v in bnd:
        nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
        if len(nb) == 2:
            upd[v] = reproj(v.co.lerp((nb[0].co + nb[1].co) * 0.5, 0.5))
    for v in ring:
        nb = [e.other_vert(v).co for e in v.link_edges]
        upd[v] = reproj(v.co.lerp(sum(nb, Vector()) / len(nb), 0.3))
    for v, c in upd.items():
        v.co = c
for _ in range(6):
    for f_ in (0.5, -0.53):
        new = {v: v.co + (sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges) - v.co) * f_ for v in g.verts if not v.is_boundary}
        for v, c in new.items():
            v.co = c
for v in g.verts:                                    # final clearance
    hb = bodyb.find_nearest(v.co); s_ = (v.co - hb[0]).dot(hb[1])
    if s_ < GAP_MIN:
        v.co = hb[0] + hb[1] * GAP_MIN
bmesh.ops.recalc_face_normals(g, faces=g.faces[:])
if sum((f.normal.dot(bodyb.find_nearest(f.calc_center_median())[1]) > 0) for f in g.faces[:300]) < 150:
    bmesh.ops.reverse_faces(g, faces=g.faces[:])
# UV (uniform fabric) and weights
g.verts.index_update(); g.verts.ensure_lookup_table()
uvl = g.loops.layers.uv.new("UVMap"); u0 = old.uv_layers.active.data[0].uv.copy()
for f in g.faces:
    for lo in f.loops:
        lo[uvl].uv = u0
dl = g.verts.layers.deform.verify()
bgn = {x.index: x.name for x in body.vertex_groups}; sgi = {x.name: x.index for x in so.vertex_groups}
for nm in set(bgn.values()):
    if nm not in sgi and nm in rig.data.bones:
        sgi[nm] = so.vertex_groups.new(name=nm).index
g.verts.ensure_lookup_table()
for v in g.verts:
    for gg in me.vertices[src_list[v.index]].groups:
        nm = bgn.get(gg.group)
        if nm in sgi and nm in rig.data.bones:
            v[dl][sgi[nm]] = gg.weight
newme = bpy.data.meshes.new("HGPT_Female_Shorts_F12a"); g.to_mesh(newme); g.free()
for m in old.materials:
    newme.materials.append(m)
so.data = newme
for p in newme.polygons:
    p.use_smooth = True
d = np.array([bodyb.find_nearest(v.co)[3] for v in newme.vertices]) * 1000
rep.update({"new_vertices": len(newme.vertices), "new_faces": len(newme.polygons),
            "off_skin_mm": {"p50": round(float(np.percentile(d, 50)), 2), "p95": round(float(np.percentile(d, 95)), 2), "max": round(float(d.max()), 2)}})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = str(OUT); REP.write_text(json.dumps(rep, indent=1)); print("F12A", json.dumps(rep))
