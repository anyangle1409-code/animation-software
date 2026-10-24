"""Candidate (new blend): untangle small folded flaps that make the rest mesh intersect itself.

After the rest-contact pass, the evaluated rest pose of R121 I7 still had 168 self-intersecting triangle pairs, all in a
4 mm patch at the back of the LEFT armpit (shoulder_cap_l skin overlapping itself and the chest wall) - the remains of an
R120 stitch pleat that R121's unfold left on that side.  Here: the vertices of every self-intersecting pair (the rest
pose with the r57 drives applied, as the trajectory test evaluates it) and RINGS rings round them are smoothed by plain
Laplacian steps on the basis (and every shape key moves with it), repeated until no pair remains.

usage: python3.13 local_flap_fix_candidate_blender.py -- <in.blend> <r57src> <out.blend>
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
SRC, ROOT, OUT = Path(args[0]), Path(args[1]), Path(args[2])
RINGS, STEPS, ROUNDS = 4, 40, 8
if OUT.exists():
    raise ValueError("output must be new")
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts/anatomy_fit"), str(Path(__file__).resolve().parent)]
bpy.ops.wm.open_mainfile(filepath=str(SRC))
import build_original_movement_benchmarks_blender as bench  # noqa: E402
import original_v1_review_candidate_drives as drives  # noqa: E402
import r121_drives  # noqa: E402

body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
me = body.data; n = len(me.vertices)
TRI = np.array([(p.vertices[0], p.vertices[k], p.vertices[k + 1]) for p in me.polygons for k in range(1, len(p.vertices) - 1)])
E = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
A = csr_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n))
Dinv = 1.0 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)
V = np.empty(n * 3); me.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
bench._reset(rig)


def rest_pairs():
    bench._reset(rig); bpy.context.view_layer.update(); drives.drive(rig, body); r121_drives.drive(rig, body)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); m = ev.to_mesh()
    P = np.empty(n * 3); m.vertices.foreach_get("co", P); ev.to_mesh_clear(); P = P.reshape(-1, 3)
    bvh = BVHTree.FromPolygons([Vector(p) for p in P], TRI.tolist(), all_triangles=True)
    pr = np.array(bvh.overlap(bvh), dtype=np.int64).reshape(-1, 2)
    if not len(pr):
        return pr
    pr = pr[pr[:, 0] < pr[:, 1]]
    share = (TRI[pr[:, 0]][:, :, None] == TRI[pr[:, 1]][:, None, :]).any(axis=(1, 2))
    return pr[~share]


hist = []; D = np.zeros_like(V)
for rnd in range(ROUNDS):
    pr = rest_pairs(); hist.append(int(len(pr)))
    if not len(pr):
        break
    m = np.zeros(n); m[TRI[pr].ravel()] = 1.0
    for _ in range(RINGS):
        m = np.maximum(m, ((A @ m) * Dinv > 0).astype(float))
    Q = V + D
    for _ in range(STEPS):
        Q = Q + 0.6 * m[:, None] * ((A @ Q) * Dinv[:, None] - Q)
    dD = Q - (V + D); D = Q - V
    me.vertices.foreach_set("co", (V + D).ravel())
    if me.shape_keys:
        for kb in me.shape_keys.key_blocks:
            if kb.name == me.shape_keys.reference_key.name:
                kb.data.foreach_set("co", (V + D).ravel())
            else:
                c = np.empty(n * 3); kb.data.foreach_get("co", c); kb.data.foreach_set("co", (c.reshape(-1, 3) + dD).ravel())
    me.update()
hist.append(int(len(rest_pairs())))
rep = {"rest_pairs_per_round": hist, "max_move_mm": round(float(np.linalg.norm(D, axis=1).max() * 1000), 2),
       "moved_vertices_gt_0.1mm": int((np.linalg.norm(D, axis=1) > 1e-4).sum())}
body["hgpt_r121_flap_fix"] = json.dumps(rep)
bench._reset(rig)
for kb in me.shape_keys.key_blocks[1:]:
    kb.value = 0.0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), copy=True)
print("FLAP", json.dumps(rep), flush=True)
