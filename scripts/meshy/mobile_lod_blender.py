"""Mobile-performance check for the bound Meshy mesh: decimate to target triangle budgets (weights carried by the
Decimate modifier), measure the surface deviation from the full mesh (both directions, mm), the bone influences per
vertex, and export a skinned GLB per level to read its size.  Review only.
usage: python3.13 mobile_lod_blender.py -- <meshy_bound.blend> <out dir> [budgets comma list]"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(a[0]), Path(a[1]); OUT.mkdir(parents=True, exist_ok=True)
BUD = [int(x) for x in (a[2] if len(a) > 2 else "60000,40000,25000").split(",")]
bpy.ops.wm.open_mainfile(filepath=str(SRC))
body = bpy.data.objects["MESHY_BODY"]; rig = bpy.data.objects["MESHY_RIG"]
V0 = np.array([v.co[:] for v in body.data.vertices]); T0 = [tuple(p.vertices) for p in body.data.polygons]
bvh0 = BVHTree.FromPolygons([tuple(p) for p in V0], T0)
n0 = len(T0); infl = np.array([sum(1 for g in v.groups if g.weight > 1e-3) for v in body.data.vertices])
rep = {"full": {"triangles": n0, "vertices": len(V0), "influences_max": int(infl.max()), "influences_over_4": int((infl > 4).sum())}}
for b in BUD:
    ob = body.copy(); ob.data = body.data.copy(); ob.name = f"LOD_{b}"; bpy.context.scene.collection.objects.link(ob)
    m = ob.modifiers.new("DEC", "DECIMATE"); m.ratio = b / n0; m.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = ob
    for mm in list(ob.modifiers):
        if mm.type == "DECIMATE":
            bpy.ops.object.modifier_apply(modifier=mm.name)
    V = np.array([v.co[:] for v in ob.data.vertices]); T = [tuple(p.vertices) for p in ob.data.polygons]
    bvh = BVHTree.FromPolygons([tuple(p) for p in V], T)
    d1 = np.array([(bvh.find_nearest(p)[0] - p).length for p in map(lambda q: __import__("mathutils").Vector(q), V0[::7])])
    d2 = np.array([(bvh0.find_nearest(p)[0] - p).length for p in map(lambda q: __import__("mathutils").Vector(q), V[::3])])
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True); rig.select_set(True)
    fp = OUT / f"meshy_lod_{b}.glb"
    bpy.ops.export_scene.gltf(filepath=str(fp), use_selection=True, export_format="GLB", export_skins=True, export_animations=False,
                              export_morph=False, export_normals=True, export_texcoords=False)
    rep[str(b)] = {"triangles": len(T), "vertices": len(V), "deviation_mm_p95": round(float(np.percentile(np.r_[d1, d2], 95)) * 1000, 2),
                   "deviation_mm_max": round(float(np.r_[d1, d2].max()) * 1000, 2), "glb_bytes": fp.stat().st_size}
    print("LOD", b, json.dumps(rep[str(b)]), flush=True)
    bpy.data.objects.remove(ob, do_unlink=True)
(OUT / "lod_report.json").write_text(json.dumps(rep, indent=1)); print("LOD done", json.dumps(rep["full"]))
