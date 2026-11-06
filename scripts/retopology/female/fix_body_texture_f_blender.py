"""FEMALE body texture clean-up: fabric colour baked onto UNCOVERED skin is repainted with skin. NEW file.

Garment texels that baked skin (hem bands) are set to the garment's median fabric colour. Two bake artefacts on the body albedo: (1) where her arm lies within millimetres of the bra (rest pose), bake rays from
the arm reached the fabric; (2) at the crotch the source's shorts inseam lip lies on body faces the removable shorts
do not cover. Here, for body faces with 0.55 < z < 1.40 (her hair, brows and eyes are legitimately dark and are not
touched) that are NOT covered by a garment (no garment surface within 5 mm), the texels of the face's UV triangles
whose colour is fabric-dark (value < 0.45, saturation < 0.30, as the clothing classifier) are replaced with the median
skin colour of the face's own skin texels, or of its neighbourhood when the whole face is dark.

usage: python3.13 fix_body_texture_f_blender.py -- <textured .blend> <out NEW .blend> <report .json>
"""
import json
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
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
rig = bpy.data.objects.get("HGPT_FEMALE_RIG")
if rig:
    rig.data.pose_position = "REST"; bpy.context.view_layer.update()
body = bpy.data.objects["HGPT_Female_Body"]; me = body.data
img = [n for n in me.materials[0].node_tree.nodes if n.type == "TEX_IMAGE"][0].image
W, H = img.size; px = np.empty(W * H * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(H, W, 4)
uv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers.active.data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
G = []
for n in ("HGPT_Female_Bra", "HGPT_Female_Shorts"):
    o = bpy.data.objects[n]; dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); m = oe.to_mesh()
    G.append(BVHTree.FromPolygons([o.matrix_world @ v.co for v in m.vertices], [tuple(p.vertices) for p in m.polygons])); oe.to_mesh_clear()


def dark(c):                                  # fabric and fabric/skin blends at the patch borders
    mx = c.max(-1); mn = c.min(-1); return (mx < 0.60) & ((mx - mn) / np.maximum(mx, 1e-6) < 0.38)


def dilate(m):
    o = m.copy(); o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]; return o


fixed_px = 0; faces = 0; skin_global = []
for p in me.polygons:
    c = body.matrix_world @ p.center
    if not (0.55 < c.z < 1.40):
        continue
    if any(g.find_nearest(c, 0.005)[0] is not None for g in G):
        continue
    # beside a garment (within 15 mm along the surface, e.g. the band just above the shorts' waistband): the fabric
    # colour there continues her source hem line and is kept; only faces that LOOK AT a garment across a gap (her
    # arm beside the bra: the garment lies along the face normal) are repainted
    nrm = (body.matrix_world.to_3x3() @ p.normal).normalized(); beside = False
    for g in G:
        h = g.find_nearest(c, 0.015)
        if h[0] is not None and nrm.dot((h[0] - c).normalized()) < 0.5:
            beside = True
    if beside and c.z > 0.80:                    # below 0.80 m: the shorts' inseam lip on her inner thighs is repainted
        continue
    L = [uv[li] for li in p.loop_indices]
    tris = [(L[0], L[i], L[i + 1]) for i in range(1, len(L) - 1)]
    for A, B, C in tris:
        xs = np.array([A[0], B[0], C[0]]) * W; ys = np.array([A[1], B[1], C[1]]) * H
        x0, x1 = int(max(xs.min() - 1, 0)), int(min(xs.max() + 2, W)); y0, y1 = int(max(ys.min() - 1, 0)), int(min(ys.max() + 2, H))
        if x1 <= x0 or y1 <= y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(d) < 1e-9:
            continue
        l1 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
        l2 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d
        inside = (l1 >= -0.05) & (l2 >= -0.05) & (1 - l1 - l2 >= -0.05)
        blk = px[y0:y1, x0:x1, :3]; dk = dilate(dark(blk)) & inside
        if not dk.any():
            ok = inside & ~dark(blk)
            if ok.any() and len(skin_global) < 20000:
                skin_global.append(np.median(blk[ok], 0))
            continue
        ok = inside & ~dk
        col = np.median(blk[ok], 0) if ok.sum() >= 5 else (np.median(np.array(skin_global[-200:]), 0) if skin_global else np.array([0.75, 0.55, 0.45]))
        blk[dk] = col; px[y0:y1, x0:x1, :3] = blk; fixed_px += int(dk.sum()); faces += 1
img.pixels.foreach_set(px.ravel()); img.update(); img.pack()
rep = {"in": IN.name, "faces_repainted": faces, "texels_repainted": fixed_px}
# ponytail: loose fragments of the decimated hair (< 1.5 % of its faces: shards near the ears) are removed
import bmesh  # noqa: E402
po_ = bpy.data.objects.get("HGPT_Female_Ponytail")
if po_ is not None:
    bm = bmesh.new(); bm.from_mesh(po_.data); seen = set(); drop = []; nf = len(bm.faces)
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
        if len(comp) < 0.015 * nf:
            drop += comp
    bmesh.ops.delete(bm, geom=drop, context="FACES"); bm.to_mesh(po_.data); bm.free(); po_.data.update()
    rep["ponytail_fragment_faces_removed"] = len(drop)
# ponytail: texels the bake left black (rays that missed her hair) take the median hair colour
po = bpy.data.objects.get("HGPT_Female_Ponytail")
if po is not None:
    pi = [x for x in po.data.materials[0].node_tree.nodes if x.type == "TEX_IMAGE"][0].image
    w_, h_ = pi.size; q = np.empty(w_ * h_ * 4, np.float32); pi.pixels.foreach_get(q); q = q.reshape(h_, w_, 4)
    mx = q[..., :3].max(-1); ok = mx > 0.06; hair = np.median(q[ok][:, :3], 0); bad = ~ok
    q[bad, :3] = hair; pi.pixels.foreach_set(q.ravel()); pi.update(); pi.pack(); rep["ponytail_black_texels_filled"] = int(bad.sum())
# garments: one uniform fabric; texels that baked skin (hems straightened past the source fabric edge) take the
# garment's median fabric colour
for n in ("HGPT_Female_Bra", "HGPT_Female_Shorts"):
    o = bpy.data.objects[n]; gi = [x for x in o.data.materials[0].node_tree.nodes if x.type == "TEX_IMAGE"][0].image
    w_, h_ = gi.size; q = np.empty(w_ * h_ * 4, np.float32); gi.pixels.foreach_get(q); q = q.reshape(h_, w_, 4)
    mx = q[..., :3].max(-1); mn = q[..., :3].min(-1); sat = (mx - mn) / np.maximum(mx, 1e-6)
    fab = (mx < 0.45) & (sat < 0.30) & (mx > 0.02); fabcol = np.median(q[fab][:, :3], 0)
    bad = dilate(~fab & (mx > 0.02))
    q[bad, :3] = fabcol; gi.pixels.foreach_set(q.ravel()); gi.update(); gi.pack()
    rep[n + "_texels_set_to_fabric"] = int(bad.sum())
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = str(OUT); REP.write_text(json.dumps(rep, indent=1)); print("TEXFIX", json.dumps(rep))
