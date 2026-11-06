"""FEMALE clothing separation: the fused sports bra and shorts become separate removable meshes; the body under them
gets a conservative anatomical surface. NEW file; the input is not changed.

Inputs: the densified body (F06) and the per-vertex source colour (sample_source_colour_blender.py at the body
vertices: Meshy Pro albedo, Image_0).

1. Garment vertices: dark, unsaturated fabric (value < V_MAX, saturation < S_MAX) within the trunk (0.55 < z < 1.40,
   not hands / feet / head). Garment faces: at least 3 of 4 garment vertices; enclosed non-garment islands smaller
   than HOLE_FACES are filled and garment islands smaller than ISLAND_FACES are dropped (texture noise). Components
   above / below z 1.02 are the bra / shorts.
2. Garments: the garment faces are copied out as HGPT_Female_Bra / HGPT_Female_Shorts at the CURRENT surface (their
   appearance is the source's: the body cage was fitted to the fabric), with a Solidify of GARMENT_T inward.
3. Body under the garments (conservative; no anatomy is invented beyond what the source shows):
   a. EVIDENCE: Meshy fused the garments as a layer over a skin surface that partly continues under the fabric. Where a
      ray from a garment vertex inward along -normal meets, within REACH, a surface of her FULL source that faces
      outward (the hidden skin), the body vertex takes that point (cleavage: REACH_GORE, the centre panel spans it).
   b. ELSEWHERE: the vertex is inset by the median depth measured in (a) (fabric thickness + ease), clamped to
      MIN_INSET..MAX_INSET (1.5-3 mm: sports-bra / shorts fabric + ease; conservative, documented).
   c. A few Taubin smoothing passes inside the garment region (hem ridges, band lips and strap edges are fabric, not
      anatomy), tapered over the first ring outside it; then every body vertex is kept at least CLEAR behind the
      garment surface.
   No nipples, genital or other unsupported detail are modelled (neutral form). Under the sports bra the breasts keep
   the bra's supported shape minus the fabric (the source shows no unsupported shape) - documented as an assumption.
Reports: per-region counts of evidence-based vs assumed (inset) vertices, inset depths, clearance.

usage: python3.13 separate_clothing_f_blender.py -- <densified .blend> <colour .npz> <out NEW .blend> <report .json>
"""
import json
import sys
from collections import deque
from pathlib import Path

import bpy
import bmesh  # noqa: E402
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, COL, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2]), Path(a[3])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
V_MAX, S_MAX = 0.45, 0.30          # her albedo is bimodal: fabric value 0.2-0.3, sat < 0.2; skin 0.75-0.85, sat 0.3-0.5
HOLE_FACES, ISLAND_FACES = 400, 150
GARMENT_T = 0.0012; REACH = 0.004; REACH_GORE = 0.045; MIN_INSET = 0.0015; MAX_INSET = 0.003; CLEAR = 0.0012
# (a first run with REACH 10 mm found 'hidden skin' 6.7-9.4 mm deep at only 149 vertices: band lips / garment
# thickness, not skin; an 8 mm inset would have taken ~5 cm off her bust and hip girths)
TAUBIN = (6, 0.5, -0.53)

bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
SRC = bpy.data.objects["HGPT_FEMALE_SOURCE_Mesh_0"]; body = bpy.data.objects["HGPT_Female_Body"]
full = BVHTree.FromPolygons([v.co.copy() for v in SRC.data.vertices], [tuple(p.vertices) for p in SRC.data.polygons])
RGB = np.load(COL)["RGB"]
bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table(); bm.normal_update()
assert len(RGB) == len(bm.verts), "colour samples must match the body vertices"
mx, mn = RGB.max(1), RGB.min(1); sat = (mx - mn) / np.maximum(mx, 1e-6)
L4 = bm.verts.layers.int.get("t4_part"); L5 = bm.verts.layers.int.get("t5_part")


def trunk(v):
    if (L4 and v[L4] > 0) or (L5 and v[L5] >= 6):
        return False
    return 0.55 < v.co.z < 1.40 and abs(v.co.x) < 0.25


gv = np.array([trunk(v) and mx[v.index] < V_MAX and sat[v.index] < S_MAX for v in bm.verts])
gf = np.array([sum(gv[v.index] for v in f.verts) >= 3 for f in bm.faces])


def components(mask):
    seen = np.zeros(len(bm.faces), bool); out = []
    for f0 in range(len(bm.faces)):
        if seen[f0] or mask[f0] != True:  # noqa: E712
            continue
        comp = []; q = deque([f0]); seen[f0] = True
        while q:
            f = bm.faces[q.popleft()]; comp.append(f.index)
            for e in f.edges:
                for g in e.link_faces:
                    if not seen[g.index] and mask[g.index]:
                        seen[g.index] = True; q.append(g.index)
        out.append(comp)
    return out


filled = 0
for comp in components(~gf):                     # enclosed small non-garment islands -> garment
    cs = set(comp)
    if len(comp) < HOLE_FACES and all(gf[g.index] for i in comp for e in bm.faces[i].edges for g in e.link_faces if g.index not in cs):
        gf[comp] = True; filled += len(comp)
dropped = 0
for comp in components(gf):
    if len(comp) < ISLAND_FACES:
        gf[comp] = False; dropped += len(comp)
comps = components(gf)
bra = [i for c in comps if np.mean([bm.faces[i].calc_center_median().z for i in c]) > 1.02 for i in c]
shorts = [i for c in comps if np.mean([bm.faces[i].calc_center_median().z for i in c]) <= 1.02 for i in c]

# ---- garments (current surface = the source fabric)
garments = {}
for name, fl in (("HGPT_Female_Bra", bra), ("HGPT_Female_Shorts", shorts)):
    vids = sorted({v.index for i in fl for v in bm.faces[i].verts}); vmap = {k: n for n, k in enumerate(vids)}
    me = bpy.data.meshes.new(name)
    me.from_pydata([bm.verts[k].co.copy() for k in vids], [], [[vmap[v.index] for v in bm.faces[i].verts] for i in fl])
    me.update(); ob = bpy.data.objects.new(name, me); body.users_collection[0].objects.link(ob)
    sd = ob.modifiers.new("Fabric_Thickness", "SOLIDIFY"); sd.thickness = GARMENT_T; sd.offset = -1.0; sd.use_even_offset = True
    ob["GARMENT"] = json.dumps({"faces": len(fl), "source": "faces of the fitted body cage classified as fabric by her albedo"})
    garments[name] = {"faces": len(fl), "vertices": len(vids)}
gvert = {v.index for i in bra + shorts for v in bm.faces[i].verts}

# ---- body under the garments
orig = {i: bm.verts[i].co.copy() for i in gvert}
ev, inset_needed, depth = {}, [], []
for i in gvert:
    v = bm.verts[i]; n = v.normal.copy(); p = v.co.copy()
    gore = abs(p.x) < 0.04 and n.y < -0.6 and 1.12 < p.z < 1.30
    reach = REACH_GORE if gore else REACH
    t = 0.0003; hit = None
    while t < reach:
        h = full.ray_cast(p - n * t, -n, reach - t)
        if h[0] is None:
            break
        if h[1].dot(n) > 0.5 and (h[0] - p).length > 0.0008:     # an outward-facing surface below: hidden skin
            hit = h[0]; break
        t = (h[0] - p).length + 0.0003
    if hit is not None:
        ev[i] = hit; depth.append((hit - p).length)
    else:
        inset_needed.append(i)
d_med = float(np.median(depth)) if depth else 0.003
inset = float(np.clip(d_med, MIN_INSET, MAX_INSET))
for i, q in ev.items():
    bm.verts[i].co = q
for i in inset_needed:
    v = bm.verts[i]; v.co = v.co - v.normal * inset
# Taubin smoothing in the garment region, tapered over one ring outside
ring1 = {e.other_vert(bm.verts[i]).index for i in gvert for e in bm.verts[i].link_edges} - gvert
wt = {i: 1.0 for i in gvert}; wt.update({i: 0.4 for i in ring1})
for it in range(TAUBIN[0]):
    for lam in (TAUBIN[1], TAUBIN[2]):
        upd = {}
        for i, w in wt.items():
            v = bm.verts[i]
            if v.is_boundary:
                continue
            nb = [e.other_vert(v).co for e in v.link_edges]; avg = sum(nb, Vector()) / len(nb)
            upd[i] = v.co + (avg - v.co) * lam * w
        for i, p in upd.items():
            bm.verts[i].co = p
# clearance behind the garment surface
gb = {}
for name, fl in (("HGPT_Female_Bra", bra), ("HGPT_Female_Shorts", shorts)):
    for i in fl:
        for v in bm.faces[i].verts:
            gb[v.index] = orig.get(v.index)
pushed = 0; clear = []
bm.normal_update()
gsurf = BVHTree.FromPolygons([orig[i] if i in orig else bm.verts[i].co.copy() for i in range(len(bm.verts))],
                             [[v.index for v in bm.faces[i].verts] for i in bra + shorts])
for i in gvert | ring1:
    v = bm.verts[i]; h = gsurf.find_nearest(v.co)
    if h[0] is None:
        continue
    d = (h[0] - v.co).dot(h[1])                      # >0: behind the garment surface
    if d < CLEAR + GARMENT_T:
        v.co = v.co - h[1] * (CLEAR + GARMENT_T - d); pushed += 1
    clear.append(max(d, CLEAR + GARMENT_T))
bm.to_mesh(body.data); body.data.update()
tris = bm.calc_loop_triangles(); T = [tuple(l.vert.index for l in t) for t in tris]
sb = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], T, all_triangles=True)
inter = sum(1 for i, j in sb.overlap(sb) if not set(T[i]) & set(T[j]))
rep = {"in": IN.name, "thresholds": {"value_max": V_MAX, "saturation_max": S_MAX}, "holes_filled_faces": filled,
       "islands_dropped_faces": dropped, "garments": garments,
       "under_garment_vertices": len(gvert), "evidence_hidden_skin_vertices": len(ev), "assumed_inset_vertices": len(inset_needed),
       "hidden_skin_depth_mm_p10_p50_p90": [round(float(np.percentile(depth, q)) * 1000, 2) for q in (10, 50, 90)] if depth else None,
       "inset_used_mm": round(inset * 1000, 2), "clearance_pushed_vertices": pushed, "body_intersecting_pairs": inter}
body["CLOTHING_SEPARATION"] = json.dumps(rep)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = str(OUT); REP.write_text(json.dumps(rep, indent=1)); print("CLOTHING", json.dumps(rep))
