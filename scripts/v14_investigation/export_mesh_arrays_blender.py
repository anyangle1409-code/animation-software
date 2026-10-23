"""Read-only: export a body .blend's mesh as arrays (vertex positions, faces as a flat index list + sizes, vertex-group
weights) for cross-run comparison without moving .blend files around.

usage: python3.13 export_mesh_arrays_blender.py -- <body.blend> <out.npz>
"""
import sys
from pathlib import Path

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, out = Path(args[0]), Path(args[1])
bpy.ops.wm.open_mainfile(filepath=str(src))
ob = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; me = ob.data
n = len(me.vertices)
P = np.empty(n * 3); me.vertices.foreach_get("co", P)
sizes = np.array([len(p.vertices) for p in me.polygons], np.int32)
flat = np.empty(int(sizes.sum()), np.int32); me.polygons.foreach_get("vertices", flat)
W = np.zeros((n, len(ob.vertex_groups)), np.float32)
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
out.parent.mkdir(parents=True, exist_ok=True)
np.savez_compressed(out, positions=P.reshape(-1, 3), face_sizes=sizes, face_verts=flat, weights=W,
                    groups=np.array([g.name for g in ob.vertex_groups]))
print("EXPORTED", out, n, len(sizes), flush=True)
