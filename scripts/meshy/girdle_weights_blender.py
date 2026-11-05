"""Anatomical shoulder-girdle weights (scapula, clavicle) on the bound retopology - writes a NEW file.

Bone-heat gives the scapula and clavicle bones weight over large parts of the back and neck, so a real scapulohumeral
rhythm (scapular upward rotation, clavicle elevation / retraction) drags the whole upper back into a hump. Here the two
girdle bones get geometric, anatomically placed influence regions on the REST mesh (per side, relative to the joints):
  scapula   posterior surface over the scapula: an ellipse centred SCAP_C (x from the midline, z below the shoulder
            joint) with semi-axes SCAP_AX, full weight inside, fading to zero over FADE outside; only surfaces facing
            backwards (rest normal y > 0.2) and not the arm itself.
  clavicle  a band around the clavicle line (sternoclavicular -> acromioclavicular joint) of radius CLAV_R, fading
            over FADE; top and front of the shoulder (trapezius edge, supraclavicular hollow).
For each vertex the girdle weight g is placed first; the remaining (1 - g) is shared by the vertex's other bones in
their existing proportions (upper-arm weights are kept: g never takes weight from the upper arm). The previous
scapula / clavicle weights outside these regions are removed (given back to the vertex's other bones). At most 4
influences, normalised.

usage: python3.13 girdle_weights_blender.py -- <bound .blend> <out NEW .blend> <report .json>
"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
SCAP_C = (0.115, -0.075)       # scapula centre: |x| from the midline, z relative to the shoulder joint (m)
SCAP_AX = (0.055, 0.095)       # semi-axes (x, z)
CLAV_R = 0.035
FADE = 0.04
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
rig = bpy.data.objects["MESHY_RIG"]; body = bpy.data.objects["MESHY_BODY"]; me = body.data
V = np.array([v.co[:] for v in me.vertices]); NV = len(V)
NRM = np.array([v.normal[:] for v in me.vertices])
GN = {g.index: g.name for g in body.vertex_groups}
W = [dict() for _ in range(NV)]
for v in me.vertices:
    for g in v.groups:
        W[v.index][GN[g.group]] = g.weight
B = lambda n, end: np.array(rig.matrix_world @ (rig.data.bones[n].head_local if end == "h" else rig.data.bones[n].tail_local))
rep = {"method": __doc__.split("usage")[0].strip(), "params": {"scap_c": SCAP_C, "scap_ax": SCAP_AX, "clav_r": CLAV_R, "fade": FADE}, "sides": {}}


def smooth01(t):
    t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)


for sd, sg in (("r", 1), ("l", -1)):
    gh = B(f"upperarm_{sd}", "h"); sc_ = B(f"clavicle_{sd}", "h"); ac = B(f"clavicle_{sd}", "t")
    side = V[:, 0] * sg > 0.01
    # scapula: elliptical distance on the back
    ex = (np.abs(V[:, 0]) - SCAP_C[0]) / SCAP_AX[0]; ez = (V[:, 2] - (gh[2] + SCAP_C[1])) / SCAP_AX[1]
    r = np.sqrt(ex * ex + ez * ez); edge = (r - 1.0) * min(SCAP_AX) / FADE          # >0 outside, in fade units
    g_s = 1.0 - smooth01(edge); g_s[r <= 1.0] = 1.0
    back = smooth01((NRM[:, 1] - 0.0) / 0.4)                                        # facing backwards
    g_s = g_s * back * side
    # clavicle band
    u = (ac - sc_); L = np.linalg.norm(u); u /= L; t = np.clip((V - sc_) @ u, 0, L)
    dist = np.linalg.norm(V - (sc_ + np.outer(t, u)), axis=1)
    g_c = (1.0 - smooth01((dist - CLAV_R) / FADE)) * side * (V[:, 2] > sc_[2] - 0.06)
    g_c[dist <= CLAV_R] = 1.0 * side[dist <= CLAV_R]
    ns, nc, nu = f"scapula_{sd}", f"clavicle_{sd}", f"upperarm_{sd}"; changed = 0
    for i in np.where(side)[0]:
        w = dict(W[i]); arm = w.get(nu, 0.0)
        w.pop(ns, None); w.pop(nc, None)
        free = max(0.0, 1.0 - arm)                          # the girdle never takes weight from the upper arm
        gs = min(float(g_s[i]), 1.0) * free * 0.85; gc = min(float(g_c[i]), 1.0) * free * 0.85 * (1 - min(float(g_s[i]), 1.0))
        rest_bones = {n: x for n, x in w.items() if n != nu}; rs = sum(rest_bones.values())
        share = max(0.0, 1.0 - arm - gs - gc)
        new = {nu: arm} if arm > 0 else {}
        if rs > 1e-9:
            for n, x in rest_bones.items():
                new[n] = x / rs * share
        elif share > 1e-6:
            new["spine_03"] = share
        if gs > 1e-4:
            new[ns] = gs
        if gc > 1e-4:
            new[nc] = gc
        top = sorted(((n, x) for n, x in new.items() if x > 1e-5), key=lambda kv: -kv[1])[:4]; s = sum(x for _, x in top)
        new = {n: x / s for n, x in top}
        if any(abs(new.get(n, 0) - W[i].get(n, 0)) > 1e-3 for n in set(new) | set(W[i])):
            changed += 1
        W[i] = new
    rep["sides"][sd] = {"scapula_full_weight_vertices": int(((g_s >= 0.99) & side).sum()), "scapula_region_vertices": int(((g_s > 0.01) & side).sum()),
                        "clavicle_region_vertices": int(((g_c > 0.01) & side).sum()), "vertices_changed": changed}
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
groups = {}
for i in range(NV):
    for n, x in W[i].items():
        if n not in groups:
            groups[n] = body.vertex_groups.new(name=n)
        groups[n].add([i], x, "REPLACE")
body["PHASE3_GIRDLE_WEIGHTS"] = json.dumps({k: v for k, v in rep.items() if k != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = OUT.name; REP.write_text(json.dumps(rep, indent=1)); print("GIRDLE", json.dumps({k: v for k, v in rep.items() if k != "method"}))
