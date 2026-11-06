"""FEMALE garments: straighten the bra / shorts hems and lift the garments off the skin. NEW file; input unchanged.

The garments were cut from the body cage by face (her albedo per vertex), so their hems follow quad edges (a
5 mm staircase). Here, on the bound file (vertex counts unchanged, so the transferred weights stay valid):
  * each garment boundary loop is relaxed along itself (HEM_IT passes, factor 0.5) and re-projected onto her source
    surface (nearest point), so the hem becomes a smooth line through the staircase;
  * the first two interior rows relax with it (factor 0.3, re-projected) so no garment face folds;
  * the whole garment is lifted LIFT along its vertex normals (no coincident garment / skin surfaces).

usage: python3.13 garment_hems_f_blender.py -- <bound .blend> <out NEW .blend> <report .json>
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
HEM_IT, LIFT = 25, 0.0006
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
TGT = bpy.data.objects["HGPT_FEMALE_SOURCE_BODY_TARGET"]
tgt = BVHTree.FromPolygons([v.co.copy() for v in TGT.data.vertices], [tuple(p.vertices) for p in TGT.data.polygons])
rep = {"in": IN.name}
for name in ("HGPT_Female_Bra", "HGPT_Female_Shorts"):
    ob = bpy.data.objects[name]; me = ob.data
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    bnd = [v for v in bm.verts if v.is_boundary]; bset = set(bnd)
    ring1 = {e.other_vert(v) for v in bnd for e in v.link_edges} - bset
    ring2 = {e.other_vert(v) for v in ring1 for e in v.link_edges} - bset - ring1
    start = [v.co.copy() for v in bm.verts]
    for _ in range(HEM_IT):
        upd = {}
        for v in bnd:
            nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
            if len(nb) != 2:
                continue
            p = v.co.lerp((nb[0].co + nb[1].co) * 0.5, 0.5); h = tgt.find_nearest(p)[0]
            upd[v] = h if h is not None else p
        for v in ring1 | ring2:
            nb = [e.other_vert(v).co for e in v.link_edges]
            p = v.co.lerp(sum(nb, Vector()) / len(nb), 0.3); h = tgt.find_nearest(p)[0]
            upd[v] = h if h is not None else p
        for v, p in upd.items():
            v.co = p
    bm.normal_update()
    for v in bm.verts:
        v.co = v.co + v.normal * LIFT
    mv = [(v.co - start[v.index]).length for v in bm.verts]
    bm.to_mesh(me); me.update()
    rep[name] = {"boundary_vertices": len(bnd), "moved_mm_p50_p95_max": [round(float(np.percentile(mv, q)) * 1000, 2) for q in (50, 95, 100)]}
    bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = str(OUT); REP.write_text(json.dumps(rep, indent=1)); print("HEMS", json.dumps(rep))
