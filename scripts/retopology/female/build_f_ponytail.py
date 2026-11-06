"""FEMALE ponytail: a separate quad mesh fitted to her source ponytail (NEW file; the body is not changed).

* Hair surface: the source faces left out of her projection target (the hanging ponytail) whose centre lies more than
  8 mm behind her back / head surface, plus the tie on her crown (z > 1.625 m, y > 0.015 m, as in the shell builder).
* Mesh: her hair surface itself (those faces only, merged), reduced by collapse decimation to ~TARGET_FACES and
  converted to mostly quads (a first version that marched a 16-vertex tube through the 191k-face strand clump ended
  up inside the hair). This keeps her strand shapes exactly; the layout is a decimated one, not designed loops
  (acceptable for a separate hair object that follows the head bone; documented).

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
TV_all = np.array([v.co[:] for v in TGT.data.vertices])
# back reference: HER RETOPOLOGISED BODY (it has no ponytail), not the projection target (which kept a few 2 mm slabs
# of hair where the shell builder's section labelling missed them)
TV = np.array([v.co[:] for v in bpy.data.objects["HGPT_Female_Body"].data.vertices])


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
    if not (0.9 < c[2] < 1.65 and abs(c[0]) < 0.12):
        continue
    if c[1] > BY[round(min(max(c[2], 0.90), 1.69), 2)] + 0.008:
        hair_f.append(f)
hv = sorted({i for f in hair_f for i in f}); HP = SV[hv]
hbvh = BVHTree.FromPolygons([Vector(p) for p in SV], hair_f)
scalp = BVHTree.FromPolygons([Vector(p) for p in TV_all], [tuple(p.vertices) for p in TGT.data.polygons])

TARGET_FACES = 8000
used = sorted({i for f in hair_f for i in f}); vm = {k: n for n, k in enumerate(used)}
me = bpy.data.meshes.new("HGPT_Female_Ponytail"); me.from_pydata([tuple(SV[k]) for k in used], [], [[vm[i] for i in f] for f in hair_f]); me.update()
ob = bpy.data.objects.new("HGPT_Female_Ponytail", me); bpy.data.objects["HGPT_Female_Body"].users_collection[0].objects.link(ob)
import bmesh  # noqa: E402
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(me); bm.free()
dec = ob.modifiers.new("Decimate", "DECIMATE"); dec.decimate_type = "COLLAPSE"; dec.ratio = min(1.0, TARGET_FACES / max(len(me.polygons), 1))
with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
    bpy.ops.object.modifier_apply(modifier=dec.name)
    pass
bm = bmesh.new(); bm.from_mesh(me)
# keep the parts that reach her crown (z > 1.5) or are narrow hanging hair (mean |x| < 5 cm, > 3 cm tall): drops
# fabric strips (bra-band lips standing off her back, wide and thin)
seen = set(); drop = []
for v0 in bm.verts:
    if v0 in seen:
        continue
    comp = []; st = [v0]; seen.add(v0)
    while st:
        v = st.pop(); comp.append(v)
        for e in v.link_edges:
            w = e.other_vert(v)
            if w not in seen:
                seen.add(w); st.append(w)
    zs_ = [v.co.z for v in comp]; mx_ = float(np.mean([abs(v.co.x) for v in comp]))
    if not (max(zs_) > 1.5 or (mx_ < 0.05 and max(zs_) - min(zs_) > 0.03)):
        drop += comp
bmesh.ops.delete(bm, geom=drop, context="VERTS")
bmesh.ops.join_triangles(bm, faces=bm.faces[:], angle_face_threshold=0.70, angle_shape_threshold=0.70)
bm.to_mesh(me); bm.free()
me.polygons.foreach_set("use_smooth", [True] * len(me.polygons)); me.update()
bm = bmesh.new(); bm.from_mesh(me)
dev = [hbvh.find_nearest(v.co)[3] for v in bm.verts]
Z = np.array([v.co.z for v in bm.verts])
rep = {"in": IN.name, "hair_source_faces": len(hair_f), "vertices": len(bm.verts), "faces": len(bm.faces),
       "quads": sum(len(f.verts) == 4 for f in bm.faces), "triangles": sum(len(f.verts) == 3 for f in bm.faces),
       "z_range": [round(float(Z.min()), 3), round(float(Z.max()), 3)], "boundary_edges": sum(e.is_boundary for e in bm.edges),
       "distance_to_hair_mm_p50_p95": [round(float(np.percentile(dev, q)) * 1000, 2) for q in (50, 95)]}
ob["PONYTAIL"] = json.dumps(rep)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = str(OUT); REP.write_text(json.dumps(rep, indent=1)); print("PONYTAIL", json.dumps(rep))
