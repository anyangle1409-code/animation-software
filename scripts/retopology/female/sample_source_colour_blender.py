"""Sample HER source base colour (Image_0, the Meshy Pro albedo) at the nearest source point of given positions.

Reads an .npz with P (n x 3 positions) and writes an .npz with RGB (n x 3, 0..1, sRGB as stored), the source face
index and the distance. Used to classify the fused sports bra / shorts (dark grey fabric) against skin, and (later)
to check texture transfer. The source .blend is opened read-only and never saved.

usage: python3.13 sample_source_colour_blender.py -- <original source .blend> <in .npz> <out .npz>
"""
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0], load_ui=False)
ob = [o for o in bpy.data.objects if o.type == "MESH"][0]; me = ob.data
V = [ob.matrix_world @ v.co for v in me.vertices]
polys = [tuple(p.vertices) for p in me.polygons]
bvh = BVHTree.FromPolygons(V, polys)
im = bpy.data.images["Image_0"]; W, H = im.size
px = np.empty(W * H * 4, np.float32); im.pixels.foreach_get(px); px = px.reshape(H, W, 4)
uv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers["UVMap"].data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
ls = np.array([p.loop_start for p in me.polygons]); lt = np.array([p.loop_total for p in me.polygons])
P = np.load(a[1])["P"]; out = np.zeros((len(P), 3), np.float32); fid = np.zeros(len(P), np.int32); dist = np.zeros(len(P), np.float32)
for i, p in enumerate(P):
    q, n, f, d = bvh.find_nearest(Vector(p))
    fid[i] = f; dist[i] = d
    vs = polys[f]; A, B, C = (np.array(V[k][:]) for k in vs[:3])
    # barycentric in the first triangle of the face (Meshy faces are triangles)
    v0, v1, v2 = B - A, C - A, np.array(q[:]) - A
    d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
    den = d00 * d11 - d01 * d01 or 1e-12
    w1 = (d11 * d20 - d01 * d21) / den; w2 = (d00 * d21 - d01 * d20) / den; w0 = 1 - w1 - w2
    t = uv[ls[f]] * w0 + uv[ls[f] + 1] * w1 + uv[ls[f] + 2] * w2
    x = int(np.clip(t[0] % 1.0 * W, 0, W - 1)); y = int(np.clip(t[1] % 1.0 * H, 0, H - 1))
    out[i] = px[max(y - 1, 0):y + 2, max(x - 1, 0):x + 2, :3].reshape(-1, 3).mean(0)
np.savez(a[2], RGB=out, F=fid, D=dist)
print("SAMPLED", len(P), "mean", out.mean(0).round(3).tolist())
