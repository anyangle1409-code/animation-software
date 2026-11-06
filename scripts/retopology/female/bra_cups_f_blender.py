"""FEMALE F12b: sports-bra cups that read as two forms. NEW file; input unchanged.

Sections at the bust (z 1.20) showed: the body (F11a) already has two breast forms with a ~30 mm sternal valley, but
the bra followed her source's fused fabric, which is a near-flat shelf across both breasts (the source's bra
compressed them into one mass, with a hidden cleavage pocket behind it); the bra dipped only ~13 mm at the centre,
so the clothed chest read as one continuous mass. Here the bra's front (y < 0, 1.08 < z < 1.30, |x| < XW) is eased
onto the body's valley: each vertex's gap over the skin (along the skin normal at its nearest point) becomes
lerp(GAP_GORE, its gap, S(|x|)), S a smoothstep from the midline to XW (only ever inward); a light Taubin pass, and
>= GAP_MIN over the skin everywhere. The cups keep their support (the outer cups are unchanged); the centre gore
lies on the sternum as an encapsulating sports bra does, without compressing the breasts into a shelf. Skin texels
just outside the garment hems that differ strongly from the local skin colour (the old fused fabric edge) are cleaned.

usage: python3.13 bra_cups_f_blender.py -- <in .blend> <out NEW .blend> <report .json>
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
XW, GAP_GORE, GAP_MIN = 0.08, 0.0035, 0.0018
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
rig = bpy.data.objects["HGPT_FEMALE_RIG"]; rig.data.pose_position = "REST"; bpy.context.view_layer.update()
body = bpy.data.objects["HGPT_Female_Body"]; me = body.data
bt = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
bra = bpy.data.objects["HGPT_Female_Bra"]; g = bmesh.new(); g.from_mesh(bra.data); g.verts.ensure_lookup_table()
rep = {"in": IN.name}; moved = []; zone = []
for v in g.verts:
    p = v.co
    if not (p.y < 0 and 1.08 < p.z < 1.30 and abs(p.x) < XW):
        continue
    h = bt.find_nearest(p); g0 = (p - h[0]).dot(h[1])
    s = min(abs(p.x) / XW, 1.0); s = s * s * (3 - 2 * s)
    gt = GAP_GORE + (g0 - GAP_GORE) * s
    if gt < g0:
        q = h[0] + h[1] * gt; moved.append((q - p).length); v.co = q
    zone.append(v)
zs = set(zone)
for _ in range(10):
    for f_ in (0.5, -0.53):
        new = {}
        for v in zone:
            if v.is_boundary:
                continue
            nb = [e.other_vert(v).co for e in v.link_edges]
            new[v] = v.co + (sum(nb, Vector()) / len(nb) - v.co) * f_
        for v, c in new.items():
            v.co = c
pushed = 0
for v in g.verts:
    h = bt.find_nearest(v.co); s_ = (v.co - h[0]).dot(h[1])
    if s_ < GAP_MIN:
        v.co = h[0] + h[1] * GAP_MIN; pushed += 1
g.to_mesh(bra.data); bra.data.update(); g.free()
rep.update({"zone_vertices": len(zone), "eased": len(moved), "moved_mm_max": round(max(moved) * 1000, 1) if moved else 0,
            "pushed_to_gap_min": pushed})
d = np.array([bt.find_nearest(v.co)[3] for v in bra.data.vertices]) * 1000
rep["bra_off_skin_mm"] = {"p50": round(float(np.percentile(d, 50)), 2), "p95": round(float(np.percentile(d, 95)), 2), "max": round(float(d.max()), 2)}
# skin texture just outside the hems: the old fused fabric edge left blotches (light / dark texels) on the skin within a
# few mm below the band and beside the leg openings; texels of body faces within 12 mm outside a garment hem that
# differ from the face neighbourhood's median skin colour by > 0.15 take that median
from scipy.spatial import cKDTree  # noqa: E402
HEM = []
for n in ("HGPT_Female_Bra", "HGPT_Female_Shorts"):
    gm = bmesh.new(); gm.from_mesh(bpy.data.objects[n].data); HEM += [((e.verts[0].co + e.verts[1].co) / 2)[:] for e in gm.edges if e.is_boundary]; gm.free()
hk = cKDTree(np.array(HEM))
GB = [BVHTree.FromPolygons([v.co.copy() for v in bpy.data.objects[n].data.vertices], [tuple(p.vertices) for p in bpy.data.objects[n].data.polygons]) for n in ("HGPT_Female_Bra", "HGPT_Female_Shorts")]
img = [n for n in me.materials[0].node_tree.nodes if n.type == "TEX_IMAGE"][0].image
W, H = img.size; px = np.empty(W * H * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(H, W, 4)
uv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers.active.data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
fixed = 0
for p in me.polygons:
    c = p.center
    if hk.query(c[:])[0] > 0.012 or c.z < 0.6 or c.z > 1.4:
        continue
    under = False
    for gb in GB:
        h = gb.find_nearest(c, 0.008)
        if h[0] is not None:
            d = c - h[0]; s_ = d.dot(h[1])
            if (d - h[1] * s_).length < 0.0015 and s_ < 0.002:
                under = True
    if under:
        continue
    us = uv[list(p.loop_indices)]
    x0, x1 = int(max(us[:, 0].min() * W - 4, 0)), int(min(us[:, 0].max() * W + 5, W)); y0, y1 = int(max(us[:, 1].min() * H - 4, 0)), int(min(us[:, 1].max() * H + 5, H))
    if x1 <= x0 or y1 <= y0:
        continue
    blk = px[y0:y1, x0:x1, :3]; med = np.median(blk.reshape(-1, 3), 0); bad = np.linalg.norm(blk - med, axis=-1) > 0.15
    if bad.any() and bad.mean() < 0.5:
        blk[bad] = med; px[y0:y1, x0:x1, :3] = blk; fixed += int(bad.sum())
img.pixels.foreach_set(px.ravel()); img.update(); img.pack(); rep["hem_skin_texels_cleaned"] = fixed
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = str(OUT); REP.write_text(json.dumps(rep, indent=1)); print("F12B", json.dumps(rep))
