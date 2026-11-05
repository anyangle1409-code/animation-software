"""Phase 3: shoulder weight shaping on the bound retopology (MESHY_RIG / MESHY_BODY) - writes a NEW file.

Bone-heat weights change abruptly between the trunk bones and the upper arm around the shoulder, which concentrates
the stretch of a raised arm in a narrow band (front armpit crease, chest-side / armpit over-stretch). Here the weights
of the shoulder bone set (clavicle, scapula, upper arm, spine_02, spine_03 of that side) are smoothed over the mesh
graph (umbrella average, ITER passes) for vertices within RADIUS of the shoulder joint, with a falloff so the
smoothing fades out at the region's edge. Vertices far down the arm (beyond ARM_KEEP from the joint along the upper
arm) keep their weights, so the elbow and below are untouched. Other bones' weights are not changed; each vertex's
total stays the same; at most 4 influences, normalised.

usage: python3.13 shoulder_weight_shaping_blender.py -- <bound .blend> <out NEW .blend> <report .json> [iterations] [radius m]
"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2])
ITER = int(a[3]) if len(a) > 3 else 30
RADIUS = float(a[4]) if len(a) > 4 else 0.20
ARM_KEEP = 0.16
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
rig = bpy.data.objects["MESHY_RIG"]; body = bpy.data.objects["MESHY_BODY"]; me = body.data
V = np.array([v.co[:] for v in me.vertices]); NV = len(V)
E = np.array([e.vertices[:] for e in me.edges])
nbr = [[] for _ in range(NV)]
for i, j in E:
    nbr[i].append(j); nbr[j].append(i)
G = {g.name: g.index for g in body.vertex_groups}; GN = {i: n for n, i in G.items()}
W = [dict() for _ in range(NV)]
for v in me.vertices:
    for g in v.groups:
        W[v.index][GN[g.group]] = g.weight
rep = {"method": __doc__.split("usage")[0].strip(), "iterations": ITER, "radius_m": RADIUS, "sides": {}}
for sd in ("r", "l"):
    sg = 1 if sd == "r" else -1
    gh = np.array(rig.matrix_world @ rig.data.bones[f"upperarm_{sd}"].head_local)
    el = np.array(rig.matrix_world @ rig.data.bones[f"upperarm_{sd}"].tail_local); ua = (el - gh) / np.linalg.norm(el - gh)
    SET = [f"clavicle_{sd}", f"scapula_{sd}", f"upperarm_{sd}", "spine_02", "spine_03"]
    d = np.linalg.norm(V - gh, axis=1); along = (V - gh) @ ua
    reg = (d < RADIUS) & (V[:, 0] * sg > -0.02) & (along < ARM_KEEP)
    idx = np.where(reg)[0]; fall = np.clip((RADIUS - d[idx]) / (0.35 * RADIUS), 0, 1)   # 1 inside, fades to 0 at the rim
    # current set weights as a matrix; the total of the set per vertex is preserved
    M = np.array([[W[i].get(n, 0.0) for n in SET] for i in range(NV)])
    tot = M.sum(1)
    for _ in range(ITER):
        A = np.array([M[nbr[i]].mean(0) if nbr[i] else M[i] for i in idx])
        s = A.sum(1, keepdims=True); A = np.where(s > 1e-9, A / np.maximum(s, 1e-9) * tot[idx, None], M[idx])
        M[idx] = M[idx] * (1 - fall[:, None]) + A * fall[:, None]
    changed = 0
    for k, i in enumerate(idx):
        new = dict(W[i])
        for c, n in enumerate(SET):
            if M[i, c] > 1e-5:
                new[n] = float(M[i, c])
            else:
                new.pop(n, None)
        top = sorted(new.items(), key=lambda kv: -kv[1])[:4]; s = sum(v for _, v in top)
        new = {n: v / s for n, v in top}
        if any(abs(new.get(n, 0) - W[i].get(n, 0)) > 1e-3 for n in set(new) | set(W[i])):
            changed += 1
        W[i] = new
    rep["sides"][sd] = {"region_vertices": int(len(idx)), "vertices_changed": changed}
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
groups = {}
for i in range(NV):
    for n, val in W[i].items():
        if n not in groups:
            groups[n] = body.vertex_groups.new(name=n)
        groups[n].add([i], val, "REPLACE")
body["PHASE3_SHOULDER_WEIGHTS"] = json.dumps({k: v for k, v in rep.items() if k != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = OUT.name; REP.write_text(json.dumps(rep, indent=1)); print("SHAPE", json.dumps({k: v for k, v in rep.items() if k != "method"}))
