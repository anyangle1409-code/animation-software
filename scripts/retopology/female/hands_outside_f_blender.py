"""FEMALE hands / feet: bring cage vertices that lie INSIDE her surface out onto it (thumb roots / thenar region, where
the hand builder's palm rings chord across). NEW file; the input is not changed.

Blender Shrinkwrap, nearest surface point, wrap mode OUTSIDE_SURFACE (a vertex inside the target - judged by the normal
of its nearest surface point - moves onto the surface; vertices outside stay), target = her projection target, applied
to the hand vertices (t4_part > 0) and one ring of the wrist, and the feet (t5_part >= 6). Then a light re-projected
relax on the moved vertices. Run the female untangle afterwards.

usage: python3.13 hands_outside_f_blender.py -- <in .blend> <out NEW .blend> <report .json>
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
TGT = bpy.data.objects["HGPT_FEMALE_SOURCE_BODY_TARGET"]; body = bpy.data.objects["HGPT_Female_Body"]; me = body.data
n = len(me.vertices)
P4 = np.zeros(n, int); me.attributes["t4_part"].data.foreach_get("value", P4)
P5 = np.zeros(n, int); me.attributes["t5_part"].data.foreach_get("value", P5)
sel = set(np.where((P4 > 0) | (P5 >= 6))[0].tolist())
ring = {e.vertices[1] if e.vertices[0] in sel else e.vertices[0] for e in me.edges if (e.vertices[0] in sel) != (e.vertices[1] in sel)}
sel |= ring
before = np.array([v.co[:] for v in me.vertices])
g = body.vertex_groups.new(name="FIT_OUT"); g.add(sorted(sel), 1.0, "REPLACE")
sw = body.modifiers.new("FitOut", "SHRINKWRAP"); sw.target = TGT; sw.wrap_method = "NEAREST_SURFACEPOINT"
sw.wrap_mode = "OUTSIDE_SURFACE"; sw.vertex_group = "FIT_OUT"
with bpy.context.temp_override(object=body, active_object=body):
    bpy.ops.object.modifier_apply(modifier=sw.name)
after = np.array([v.co[:] for v in me.vertices]); d = np.linalg.norm(after - before, axis=1)
moved = np.where(d > 0.0003)[0]
# light relax of the moved vertices, re-projected (nearest surface within 3 mm)
tgt = BVHTree.FromPolygons([v.co.copy() for v in TGT.data.vertices], [tuple(p.vertices) for p in TGT.data.polygons])
adj = {i: [] for i in moved}
ms = set(moved.tolist())
for e in me.edges:
    a0, a1 = e.vertices
    if a0 in ms:
        adj[a0].append(a1)
    if a1 in ms:
        adj[a1].append(a0)
for _ in range(3):
    upd = {}
    for i in moved:
        avg = sum((me.vertices[j].co for j in adj[i]), Vector()) / max(len(adj[i]), 1)
        p = me.vertices[i].co.lerp(avg, 0.3); h = tgt.find_nearest(p)
        upd[i] = h[0] if (h[0] is not None and h[3] < 0.003) else p
    for i, p in upd.items():
        me.vertices[i].co = p
body.vertex_groups.remove(body.vertex_groups["FIT_OUT"]); me.update()
rep = {"in": IN.name, "region_vertices": len(sel), "moved_out": int(len(moved)),
       "move_mm_p50_p95_max": [round(float(np.percentile(d[moved], q)) * 1000, 2) for q in (50, 95, 100)] if len(moved) else None}
body["HANDS_OUTSIDE"] = json.dumps(rep)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = str(OUT); REP.write_text(json.dumps(rep, indent=1)); print("OUTSIDE", json.dumps(rep))
