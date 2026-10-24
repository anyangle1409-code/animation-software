"""Candidate (new blend): resolve the rest pose's arm-to-body interpenetration as skin contact.

At the rig's rest pose (arms hanging with no carriage) the rebuilt body self-intersects (1929 triangle pairs:
inner arm into the chest wall 608, forearm into the hip 420, hands into the thighs 731; movement_trajectory_test_blender.py).
A body cannot hold that pose without the surfaces meeting, so here they are made to meet: repeatedly, triangles of the arm
(upper arm / forearm / hand weights > 0.5) that intersect triangles of the rest of the body push their vertices laterally
and the body's vertices medially by STEP, the push is spread over a few rings so the surfaces stay smooth, until no such
pair remains.  The basis and every shape key move together.  The input is not modified.

usage: python3.13 rest_contact_candidate_blender.py -- <in.blend> <out.blend>
"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from scipy.sparse import csr_matrix

args = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(args[0]), Path(args[1])
STEP, MAXIT = 0.0004, 120
if OUT.exists():
    raise ValueError("output must be new")
bpy.ops.wm.open_mainfile(filepath=str(SRC))
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; me = body.data
n = len(me.vertices)
V = np.empty(n * 3); me.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
GN = [g.name for g in body.vertex_groups]
armw = np.zeros(n)
ARMK = ("upperarm", "forearm", "hand", "thumb", "index", "middle", "ring", "pinky", "metacarpal")
for v in me.vertices:
    for g in v.groups:
        if any(k in GN[g.group] for k in ARMK):
            armw[v.index] += g.weight
ARM = armw > 0.5
TRI = np.array([(p.vertices[0], p.vertices[k], p.vertices[k + 1]) for p in me.polygons for k in range(1, len(p.vertices) - 1)])
TARM = ARM[TRI[:, 0]]
E = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
A = csr_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n))
Dinv = 1.0 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)
lat = np.sign(V[:, 0])[:, None] * np.array([1.0, 0.0, 0.0])


def pairs(P):
    bvh = BVHTree.FromPolygons([Vector(p) for p in P], TRI.tolist(), all_triangles=True)
    pr = np.array(bvh.overlap(bvh), dtype=np.int64).reshape(-1, 2)
    if not len(pr):
        return pr
    pr = pr[TARM[pr[:, 0]] != TARM[pr[:, 1]]]                       # arm against body only
    share = (TRI[pr[:, 0]][:, :, None] == TRI[pr[:, 1]][:, None, :]).any(axis=(1, 2))
    return pr[~share]


P = V.copy(); hist = []
for it in range(MAXIT):
    pr = pairs(P); hist.append(int(len(pr)))
    if not len(pr):
        break
    hit = np.zeros(n, bool); hit[TRI[pr].ravel()] = True
    d = np.where(ARM[:, None], lat, -lat) * (STEP * hit)[:, None]
    w = hit.astype(float)
    for _ in range(3):                                             # spread so the contact face stays smooth
        d = np.where(w[:, None] > 0, d, (A @ d) * Dinv[:, None])
        w = np.maximum(w, ((A @ w) * Dinv > 0).astype(float))
    P += d
D = P - V
for _ in range(6):                                                 # final smoothing of the whole displacement field
    D = 0.5 * D + 0.5 * (A @ D) * Dinv[:, None]
final = int(len(pairs(V + D)))
me.vertices.foreach_set("co", (V + D).ravel())
if me.shape_keys:
    for kb in me.shape_keys.key_blocks:
        c = np.empty(n * 3); kb.data.foreach_get("co", c); kb.data.foreach_set("co", (c.reshape(-1, 3) + D).ravel())
me.update()
rep = {"pairs_per_iteration": hist[:5] + ["..."] + hist[-3:], "iterations": len(hist), "pairs_after_smoothing": final,
       "max_move_mm": round(float(np.linalg.norm(D, axis=1).max() * 1000), 2),
       "moved_vertices_gt_0.1mm": int((np.linalg.norm(D, axis=1) > 1e-4).sum())}
body["hgpt_r121_rest_contact"] = json.dumps(rep)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), copy=True)
print("REST_CONTACT", json.dumps(rep), flush=True)
