"""Spread the trunk-to-arm weight change evenly over the first cap rings of the axilla - writes a NEW file.

Measured on 06h (right side, trunk-facing half of the cap, below the shoulder joint): at 135 deg the rungs between cap
rings 0-1 / 1-2 / 2-3 stretch x7.6 / x10.5 / x6.0, while rings 5 and up stretch x2 or less. Ring 0 is the torso's socket
rim (trunk-weighted), by ring 2 the skin is almost fully arm-weighted, so the whole raise is taken by one or two rows of
the vault - the sharp crease on the inner arm. Real axillary skin stretches progressively across the hollow.

Here the bone weights of the trunk-facing cap vertices in rings 1..K-1 are relaxed (harmonic / Laplace, all edges, ITERS
Jacobi steps) between FIXED boundaries: ring 0 (the torso rim - and so the whole chest wall below it - keeps its
weights, nothing is taken from the ribcage, so the batwing chest lift cannot return), ring K and every lateral
(deltoid-side) vertex. The result is an even weight gradient in ring index across rings 0..K. At most 4 influences.

Result 06h -> rig 06i (K=5): rung stretch at 135 deg x7.6 / 10.5 / 6.0 / 4.9 / 3.2 -> x4.3 / 6.2 / 5.2 / 5.9 / 6.1
(rings 0-1 .. 4-5); new sharp edges in the armpit zone 5/4/5/7/8 -> 0/1/1/1/4 (45-170 deg); back-fold stretch p95 at
135 deg 4.99 -> 4.27, scapula zone 5.02 -> 3.45; deltoid volume unchanged; trunk 180-300 mm band at 105 deg 13 mm
(unchanged - no batwing); the inner-arm crease spike (sagittal slice 30 mm medial of the joint) is gone at 90-170 deg.

usage: python3.13 axillary_ring_relax_blender.py -- <bound .blend> <out NEW .blend> <report .json> [K]
"""
import json
import sys
from collections import deque
from pathlib import Path

import bpy
import bmesh  # noqa: E402
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2]); K = int(a[3]) if len(a) > 3 else 5
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
ITERS = 200
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
rig = bpy.data.objects["MESHY_RIG"]; body = bpy.data.objects["MESHY_BODY"]; me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
LR, LC = bm.verts.layers.int["t3_row"], bm.verts.layers.int["t3_col"]; L4, L5 = bm.verts.layers.int["t4_part"], bm.verts.layers.int["t5_part"]
shell = [(v[LR] > 0 or v[LC] > 0) for v in bm.verts]
cap = [(not shell[v.index]) and v[L4] == 0 and v[L5] == 0 and v.co.z > 0.95 for v in bm.verts]
NV = len(me.vertices); nbr = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
GN = {g.index: g.name for g in body.vertex_groups}; names = sorted(GN.values()); col = {n: k for k, n in enumerate(names)}
Wm = np.zeros((NV, len(names)))
for v in me.vertices:
    for g in v.groups:
        Wm[v.index, col[GN[g.group]]] = g.weight
Wm /= np.maximum(Wm.sum(1, keepdims=True), 1e-9)
rep = {"method": __doc__.split("usage")[0].strip(), "params": {"K": K, "iters": ITERS}, "sides": {}}
for sd, sg in (("r", 1), ("l", -1)):
    gh = rig.matrix_world @ rig.data.bones[f"upperarm_{sd}"].head_local
    rim = [v for v in bm.verts if shell[v.index] and v.co.x * sg > 0.1 and any(cap[e.other_vert(v).index] for e in v.link_edges)]
    ring = {v.index: 0 for v in rim}; q = deque(rim)
    while q:
        v = q.popleft()
        for e in v.link_edges:
            w = e.other_vert(v)
            if cap[w.index] and w.index not in ring and w.co.x * sg > 0.05:
                ring[w.index] = ring[v.index] + 1; q.append(w)
    free = np.array([i for i, k in ring.items() if 1 <= k < K and (gh.x - me.vertices[i].co.x) * sg > -0.01 and me.vertices[i].co.z < gh.z - 0.03])
    ua = col[f"upperarm_{sd}"]; before = Wm[free, ua].copy()
    for _ in range(ITERS):
        Wn = Wm.copy()
        for i in free:
            Wn[i] = Wm[nbr[i]].mean(0)
        Wm = Wn
    for i in free:                                         # keep the 4 largest influences
        r = Wm[i].copy(); keep = np.argsort(-r)[:4]; m = np.zeros_like(r); m[keep] = r[keep]; Wm[i] = m / m.sum()
    rk = np.array([ring[i] for i in free])
    rep["sides"][sd] = {"relaxed_vertices": int(len(free)),
                        "upperarm_weight_by_ring_before": {int(k): round(float(before[rk == k].mean()), 3) for k in range(1, K)},
                        "upperarm_weight_by_ring_after": {int(k): round(float(Wm[free[rk == k], ua].mean()), 3) for k in range(1, K)},
                        "ring0_mean": round(float(Wm[[i for i, k in ring.items() if k == 0], ua].mean()), 3),
                        "ringK_mean": round(float(Wm[[i for i, k in ring.items() if k == K], ua].mean()), 3)}
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
for k, n in enumerate(names):
    idx = np.where(Wm[:, k] > 1e-5)[0]
    if len(idx):
        vg = body.vertex_groups.new(name=n)
        for i in idx:
            vg.add([int(i)], float(Wm[i, k]), "REPLACE")
body["AXILLARY_RING_RELAX"] = json.dumps({k: v for k, v in rep.items() if k != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = OUT.name; REP.write_text(json.dumps(rep, indent=1)); print("RELAX", json.dumps(rep["sides"]))
