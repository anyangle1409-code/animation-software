"""FEMALE F10c: toes, textures and ponytail finish on the repaired body (F10b). NEW file; input unchanged.

  * TOES: toe vertices (t5_part 8) are re-projected onto her source along their own normal (first hit from outside,
    normal agreement; 10 rounds with a light tangential relax) so the clefts between the toes follow her source more
    deeply; heel / sole / instep / proportions untouched.
  * BODY TEXTURE: after F10a/F10b the garments moved (mirrored bra, new shoulder straps), so the F09b repaint is redone
    against the NEW garments: on body faces 0.55 < z < 1.45 with no garment within 4 mm, fabric-dark texels (value <
    0.60, saturation < 0.38, dilated) are replaced by the median skin colour of the face (or its neighbourhood). Only
    faces a garment actually covers (nearest garment point along the face normal) are skipped, so the fused fabric's
    colour no longer shows as dark steps just outside the hems; her hair, brows and eyes are above z 1.45.
  * GARMENT TEXTURES: texels brighter than the garment's median fabric value + 0.08, or saturated (> 0.30) - the
    printed band logo, the light patch at the band's centre front, the strap-junction texel, the pale stair-shaped band
    baked onto the waistband - dilated twice, take the median colour; the fabric's darker tones are kept.
  * HEM CLEARANCE: body vertices under a garment (their nearest garment point lies along the garment normal, not off
    its edge) are kept >= 1.4 mm below the garment's outer surface (0.2 mm inside its inner face): no skin, and no
    fabric-coloured skin texture, shows through at the hems.
  * HANDS: dark line texels on the hands (value < 0.72 of the local median: the baked trace of the old thumb-side fold)
    take the local median skin colour.
  * PONYTAIL: (1) loose pieces: connected components under 4 % of its faces whose centre lies more than 25 mm from the
    main mass are removed; (2) folds: two Taubin passes (lambda 0.5 / mu -0.53) soften the decimation folds that render
    as dark creases; (3) texture: texels brighter than 1.6 x the median hair value (a pale baked mark) take the median hair colour, texels darker than 45 % of it are lifted half way to it; (4)
    material: roughness 0.62, specular 0.30, no coat (was glossy plastic).

usage: python3.13 finish_f10c_blender.py -- <F10b .blend> <out NEW .blend> <report .json>
"""
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
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
rig = bpy.data.objects["HGPT_FEMALE_RIG"]; rig.data.pose_position = "REST"; bpy.context.view_layer.update()
SRC = bpy.data.objects["HGPT_FEMALE_SOURCE_Mesh_0"]
src = BVHTree.FromPolygons([v.co.copy() for v in SRC.data.vertices], [tuple(p.vertices) for p in SRC.data.polygons])
body = bpy.data.objects["HGPT_Female_Body"]; me = body.data
rep = {"in": IN.name}

# ---------------- toes
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
L5 = bm.verts.layers.int["t5_part"]
toes = [v for v in bm.verts if v[L5] == 8]; P0 = {v: v.co.copy() for v in toes}; hits = 0
for _ in range(10):
    bm.normal_update()
    for v in toes:
        nb = [e.other_vert(v).co for e in v.link_edges]; d = sum(nb, Vector()) / len(nb) - v.co
        v.co += (d - v.normal * d.dot(v.normal)) * 0.1
    bm.normal_update()
    for v in toes:
        n = v.normal; h = src.ray_cast(v.co + n * 0.003, -n, 0.008)
        if h[0] is not None and h[1].dot(n) > 0.3:
            v.co = h[0]; hits += 1
mv = [(v.co - P0[v]).length * 1000 for v in toes]
rep["toes"] = {"vertices": len(toes), "moved_mm_p50_p95_max": [round(float(np.percentile(mv, q)), 2) for q in (50, 95, 100)]}
bm.to_mesh(me); me.update(); bm.free()

# ---------------- hem clearance (rest pose; garments' base surfaces = the fabric's outer face)
GBASE = []
for n in ("HGPT_Female_Bra", "HGPT_Female_Shorts"):
    o = bpy.data.objects[n]; GBASE.append(BVHTree.FromPolygons([v.co.copy() for v in o.data.vertices], [tuple(p.vertices) for p in o.data.polygons]))
pushed = 0
for v in me.vertices:
    for g in GBASE:
        h = g.find_nearest(v.co, 0.008)
        if h[0] is None:
            continue
        d = v.co - h[0]; s_ = d.dot(h[1])
        if (d - h[1] * s_).length > 0.001:          # off the garment's edge: not under it
            continue
        if s_ > -0.0014:
            v.co = v.co - h[1] * (s_ + 0.0014); pushed += 1
me.update(); rep["hem_clearance_vertices_pushed"] = pushed
# ---------------- garment weights: re-transferred from the body (nearest face, interpolated), so each garment vertex
# moves exactly like the skin under it (the F08b transfer left waistband / band vertices following other bones: the
# skin pushed through the waistband in the standing pose)
def posed_poke(names):
    rig.data.pose_position = "POSE"; bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    be = body.evaluated_get(dg); bmesh_ = be.to_mesh(); BVp = [v.co.copy() for v in bmesh_.vertices]; be.to_mesh_clear()
    out = {}
    for n in names:
        o = bpy.data.objects[n]; mods = [m for m in o.modifiers if m.type == "SOLIDIFY"]
        for m in mods:
            m.show_viewport = False
        bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); gm = oe.to_mesh()
        t = BVHTree.FromPolygons([v.co.copy() for v in gm.vertices], [tuple(p.vertices) for p in gm.polygons]); oe.to_mesh_clear()
        for m in mods:
            m.show_viewport = True
        k = 0
        for c in BVp:
            h = t.find_nearest(c, 0.01)
            if h[0] is None:
                continue
            d = c - h[0]; s_ = d.dot(h[1])
            if (d - h[1] * s_).length < 0.001 and s_ > -0.0002:
                k += 1
        out[n] = k
    rig.data.pose_position = "REST"; bpy.context.view_layer.update()
    return out


rep["posed_skin_through_garment_before"] = posed_poke(("HGPT_Female_Bra", "HGPT_Female_Shorts"))
for n in ("HGPT_Female_Bra", "HGPT_Female_Shorts"):
    o = bpy.data.objects[n]
    for g in list(o.vertex_groups):
        if g.name in rig.data.bones:
            o.vertex_groups.remove(g)
    for g in body.vertex_groups:
        if g.name in rig.data.bones and g.name not in o.vertex_groups:
            o.vertex_groups.new(name=g.name)
    dt = o.modifiers.new("WT", "DATA_TRANSFER"); dt.object = body; dt.use_vert_data = True
    dt.data_types_verts = {"VGROUP_WEIGHTS"}; dt.vert_mapping = "POLYINTERP_NEAREST"
    dt.layers_vgroup_select_src = "ALL"; dt.layers_vgroup_select_dst = "NAME"
    while o.modifiers.find("WT") > 0:
        bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_move_up(modifier="WT")
    bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier="WT")
    for v in o.data.vertices:                      # at most 4 influences, normalised
        gs = sorted([g for g in v.groups if o.vertex_groups[g.group].name in rig.data.bones and g.weight > 1e-6], key=lambda g: -g.weight)
        for g in gs[4:]:
            o.vertex_groups[g.group].remove([v.index])
        t_ = sum(g.weight for g in gs[:4])
        for g in gs[:4]:
            g.weight /= t_
rep["posed_skin_through_garment_after"] = posed_poke(("HGPT_Female_Bra", "HGPT_Female_Shorts"))
# ---------------- body texture
img = [n for n in me.materials[0].node_tree.nodes if n.type == "TEX_IMAGE"][0].image
W, H = img.size; px = np.empty(W * H * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(H, W, 4)
uv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers.active.data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
G = []
for n in ("HGPT_Female_Bra", "HGPT_Female_Shorts"):
    o = bpy.data.objects[n]; dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); m = oe.to_mesh()
    G.append(BVHTree.FromPolygons([v.co.copy() for v in m.vertices], [tuple(p.vertices) for p in m.polygons])); oe.to_mesh_clear()


def dark(c):
    mx = c.max(-1); mn = c.min(-1); return (mx < 0.60) & ((mx - mn) / np.maximum(mx, 1e-6) < 0.38)


def dilate(m):
    o = m.copy(); o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]; return o


fixed_px = 0; faces = 0; skin_global = []
for p in me.polygons:
    c = p.center
    if not (0.55 < c.z < 1.45):
        continue
    def _under(pt):
        for g in GBASE:
            h = g.find_nearest(pt, 0.008)
            if h[0] is not None:
                d = pt - h[0]; s_ = d.dot(h[1])
                if (d - h[1] * s_).length < 0.0015 and s_ < 0.002:
                    return True
        return False
    if all(_under(me.vertices[vi].co) for vi in p.vertices):     # skipped only when a garment covers the whole face
        continue
    L = [uv[li] for li in p.loop_indices]
    for A, B, C in [(L[0], L[i], L[i + 1]) for i in range(1, len(L) - 1)]:
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
# hands: dark crease-line texels
hand_px = 0
for p in me.polygons:
    c = p.center
    if not (abs(c.x) > 0.36 and c.z < 0.92):
        continue
    L = [uv[li] for li in p.loop_indices]; us = np.array(L)
    x0, x1 = int(max(us[:, 0].min() * W - 3, 0)), int(min(us[:, 0].max() * W + 4, W)); y0, y1 = int(max(us[:, 1].min() * H - 3, 0)), int(min(us[:, 1].max() * H + 4, H))
    if x1 <= x0 or y1 <= y0:
        continue
    blk = px[y0:y1, x0:x1, :3]; val = blk.max(-1); med = np.median(val)
    ln = val < 0.72 * med
    if ln.any() and ln.mean() < 0.35:
        blk[ln] = np.median(blk[~ln], 0); px[y0:y1, x0:x1, :3] = blk; hand_px += int(ln.sum())
img.pixels.foreach_set(px.ravel()); img.update(); img.pack()
rep["hand_line_texels"] = hand_px
rep["body_texture"] = {"faces_repainted": faces, "texels_repainted": fixed_px}

# ---------------- garment textures
for n in ("HGPT_Female_Bra", "HGPT_Female_Shorts"):
    o = bpy.data.objects[n]; gi = [x for x in o.data.materials[0].node_tree.nodes if x.type == "TEX_IMAGE"][0].image
    w_, h_ = gi.size; q = np.empty(w_ * h_ * 4, np.float32); gi.pixels.foreach_get(q); q = q.reshape(h_, w_, 4)
    used = q[..., :3].max(-1) > 0.02; med = np.median(q[used][:, :3], 0)
    mx = q[..., :3].max(-1); mn = q[..., :3].min(-1); sat = (mx - mn) / np.maximum(mx, 1e-6)
    bad = dilate(dilate(used & ((mx > med.max() + 0.08) | (sat > 0.30))))
    q[bad, :3] = med; gi.pixels.foreach_set(q.ravel()); gi.update(); gi.pack()
    rep[n + "_outlier_texels_set_to_fabric"] = int(bad.sum()); rep[n + "_fabric_rgb"] = [round(float(x), 3) for x in med]

# ---------------- ponytail
po = bpy.data.objects["HGPT_Female_Ponytail"]; pm = po.data
bm = bmesh.new(); bm.from_mesh(pm); bm.faces.ensure_lookup_table(); seen = set(); comps = []
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
    comps.append(comp)
comps.sort(key=len, reverse=True); main = comps[0]
mbvh = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], [tuple(v.index for v in f.verts) for f in main])
drop = []
for c in comps[1:]:
    if len(c) < 0.04 * len(bm.faces):
        ctr = sum((f.calc_center_median() for f in c), Vector()) / len(c)
        h = mbvh.find_nearest(ctr)
        if h[0] is None or h[3] > 0.025:
            drop += c
rep["ponytail_components"] = [len(c) for c in comps[:8]]; rep["ponytail_loose_faces_removed"] = len(drop)
bmesh.ops.delete(bm, geom=drop, context="FACES"); bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
bm.verts.ensure_lookup_table()
bnd = [v for v in bm.verts if v.is_boundary]
for _ in range(15):                               # ragged decimation edges (dark shards) -> smooth hair edges
    new = {}
    for v in bnd:
        nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
        if len(nb) == 2:
            new[v] = v.co.lerp((nb[0].co + nb[1].co) * 0.5, 0.5)
    for v, c in new.items():
        v.co = c
rep["ponytail_boundary_vertices_relaxed"] = len(bnd)
for f_ in (0.5, -0.53, 0.5, -0.53):
    new = {}
    for v in bm.verts:
        nb = [e.other_vert(v).co for e in v.link_edges]
        if nb and not v.is_boundary:
            new[v] = v.co + (sum(nb, Vector()) / len(nb) - v.co) * f_
    for v, c in new.items():
        v.co = c
bm.to_mesh(pm); pm.update(); bm.free()
for p in pm.polygons:
    p.use_smooth = True
mat = pm.materials[0]; nodes = mat.node_tree.nodes
pi = [x for x in nodes if x.type == "TEX_IMAGE"][0].image
w_, h_ = pi.size; q = np.empty(w_ * h_ * 4, np.float32); pi.pixels.foreach_get(q); q = q.reshape(h_, w_, 4)
val = q[..., :3].max(-1); medv = np.median(val[val > 0.02])
hi = dilate(val > 1.6 * medv); q[hi, :3] = np.median(q[val > 0.02][:, :3], 0); rep["ponytail_light_texels_set_to_hair"] = int(hi.sum())
val = q[..., :3].max(-1); lo = val < 0.45 * medv
q[lo, :3] = q[lo, :3] + (q[lo, :3] * (0.45 * medv / np.maximum(val[lo], 1e-4))[:, None] - q[lo, :3]) * 0.5
pi.pixels.foreach_set(q.ravel()); pi.update(); pi.pack(); rep["ponytail_dark_texels_lifted"] = int(lo.sum())
for b in [x for x in nodes if x.type == "BSDF_PRINCIPLED"]:
    b.inputs["Roughness"].default_value = 0.62
    for k in ("Specular IOR Level", "Specular"):
        if k in b.inputs:
            b.inputs[k].default_value = 0.30
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = 0.0
rep["ponytail_material"] = {"roughness": 0.62, "specular": 0.30, "coat": 0.0}
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = str(OUT); REP.write_text(json.dumps(rep, indent=1)); print("F10C", json.dumps(rep))
