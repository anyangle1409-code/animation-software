"""Local fold relief: skin that folds THROUGH ITSELF under skinning is unfolded, as a corrective - writes a NEW file.

Found on the densified body (07a): at 45-135 deg of arm elevation a ~1 cm patch in front of the right clavicle
(clavicle 0.74 / upper arm 0.20 weights) folds through itself - intersecting faces 1-3 edges apart, normals
anti-parallel. Plain subdivision without any source snapping shows the same fold, so it is a linear-skinning crumple
that the coarse 06j faces only bent sharply; the finer faces make it cross. That is not a contact between body parts
(those are handled by the contact correctives), and it is not a shape to keep.

Method: at each key elevation (both arms, anatomical elbow - shoulder_pose_lib hinge=True - press-like girdle), the
intersecting triangle pairs within FOLD_HOPS edges of each other are found; their vertices plus RINGS rings around them
are relaxed in posed space (umbrella Laplacian, the outer ring fixed) until no local fold is left (at most ITERS passes).
Nothing else moves. The posed displacement is inverse-skinned per vertex into FOLD_<deg> and driven by the arm
elevation (ROTATION_DIFF(upper arm, arm_ref), both sides averaged per side key): tents between the key elevations,
zero at and below E_ON and above the last key.

usage: python3.13 build_fold_relief_blender.py -- <bound .blend> <out NEW .blend> <report .json>
"""
import json
import math
import sys
from collections import deque
from pathlib import Path

import bpy
import numpy as np
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
sys.path.insert(0, str(Path(__file__).resolve().parent))
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
from shoulder_pose_lib import arm_pose, rest_capture, rest_restore  # noqa: E402
E_ON, KEYS, FOLD_HOPS, RINGS, ITERS = 20.0, ((55.0, 40, 70, 8), (105.0, 30, 115, 15), (170.0, 15, 175, 25)), 4, 2, 60
rig = bpy.data.objects["MESHY_RIG"]; body = bpy.data.objects["MESHY_BODY"]; me = body.data; pb = rig.pose.bones
NV = len(me.vertices); nbr = [[] for _ in range(NV)]
for e in me.edges:
    i, j = e.vertices; nbr[i].append(j); nbr[j].append(i)
GN = {g.index: g.name for g in body.vertex_groups}; WT = [dict() for _ in range(NV)]
for v in me.vertices:
    for g in v.groups:
        if g.weight > 1e-5 and GN[g.group] in rig.data.bones and rig.data.bones[GN[g.group]].use_deform:
            WT[v.index][GN[g.group]] = g.weight
R = np.array([v.co[:] for v in me.vertices])


def posed():
    dg = bpy.context.evaluated_depsgraph_get(); m = bpy.data.meshes.new_from_object(body.evaluated_get(dg), depsgraph=dg); m.calc_loop_triangles()
    V = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", V); T = np.array([t.vertices[:] for t in m.loop_triangles]); bpy.data.meshes.remove(m)
    return V.reshape(-1, 3), T


def hop_near(a_, tgt):
    seen = {a_: 0}; q = deque([a_])
    while q:
        x = q.popleft()
        if x in tgt:
            return True
        if seen[x] >= FOLD_HOPS:
            continue
        for y in nbr[x]:
            if y not in seen:
                seen[y] = seen[x] + 1; q.append(y)
    return False


def folds(X, T):
    b = BVHTree.FromPolygons([tuple(p) for p in X], T.tolist(), all_triangles=True); out = set(); n = 0
    for i, j in b.overlap(b):
        if i < j and not set(T[i]) & set(T[j]) and hop_near(int(T[i][0]), set(T[j].tolist())):
            out |= set(T[i].tolist()) | set(T[j].tolist()); n += 1
    return out, n


def skin_inv():
    bm_ = {n: np.array(pb[n].matrix @ rig.data.bones[n].matrix_local.inverted())[:3, :3] for n in {b for w in WT for b in w}}
    M = np.zeros((NV, 3, 3))
    for i, w in enumerate(WT):
        s = sum(w.values())
        for n, x in w.items():
            M[i] += bm_[n] * (x / s)
    return np.linalg.inv(M)


rest = rest_capture(rig); rep = {"method": __doc__.split("usage")[0].strip(), "keys": [k[0] for k in KEYS], "results": {}}
for el, fw, elb, clv in KEYS:
    rest_restore(rig, rest)
    for sd in ("l", "r"):
        arm_pose(rig, sd, el, fw, elb, clv, hinge=True)
    bpy.context.view_layer.update(); Vp, T = posed(); X = Vp.copy(); f0 = None; moved = set()
    for it in range(ITERS):
        fv, n = folds(X, T)
        if f0 is None:
            f0 = n
        if not fv:
            break
        zone = set(fv)
        for _ in range(RINGS):
            zone |= {y for x in zone for y in nbr[x]}
        fixed = {y for x in zone for y in nbr[x]} - zone
        moved |= zone
        for _ in range(5):                                     # umbrella relaxation inside the zone, boundary fixed
            Xn = X.copy()
            for i in zone:
                Xn[i] = 0.5 * X[i] + 0.5 * X[nbr[i]].mean(0)
            X = Xn
    _, n1 = folds(X, T); delta = X - Vp; delta[[i for i in range(NV) if i not in moved]] = 0.0
    dr = np.einsum("nij,nj->ni", skin_inv(), delta)
    sk = body.shape_key_add(name=f"FOLD_{int(el)}", from_mix=False); sk.value = 0.0; sk.data.foreach_set("co", (R + dr).ravel())
    mv = np.linalg.norm(delta, axis=1)
    rep["results"][int(el)] = {"local_fold_pairs_before_after": [f0, n1], "moved_vertices": int((mv > 1e-5).sum()), "max_move_mm": round(float(mv.max()) * 1000, 2)}
    print("KEY", el, json.dumps(rep["results"][int(el)]), flush=True)
rest_restore(rig, rest)
kb = me.shape_keys.key_blocks; pts = [E_ON] + [k[0] for k in KEYS]
for k, (ek, *_r) in enumerate(KEYS):
    lo, hi = pts[k], (KEYS[k + 1][0] if k + 1 < len(KEYS) else None)
    fc = kb[f"FOLD_{int(ek)}"].driver_add("value"); d = fc.driver; d.type = "SCRIPTED"; terms = []
    for sd in ("l", "r"):
        qa = rig.data.bones[f"upperarm_{sd}"].matrix_local.to_quaternion(); qr = rig.data.bones[f"arm_ref_{sd}"].matrix_local.to_quaternion()
        e0 = math.degrees(qr.rotation_difference(qa).angle); u = (rig.matrix_world.to_3x3() @ (rig.data.bones[f"upperarm_{sd}"].tail_local - rig.data.bones[f"upperarm_{sd}"].head_local)).normalized()
        rel = math.degrees(math.acos(max(-1, min(1, -u.z))))
        v = d.variables.new(); v.name = f"e{sd}"; v.type = "ROTATION_DIFF"
        v.targets[0].id = rig; v.targets[0].bone_target = f"upperarm_{sd}"; v.targets[1].id = rig; v.targets[1].bone_target = f"arm_ref_{sd}"
        terms.append(f"(e{sd}*57.29578 - {e0:.3f} + {rel:.3f})")
    el_ = f"(max({terms[0]}, {terms[1]}))"                    # the key is shared: driven by the more raised arm
    up = f"max(0.0, min(1.0, ({el_} - {lo}) / {ek - lo}))"
    d.expression = up if hi is None else f"min({up}, max(0.0, min(1.0, ({hi} - {el_}) / {hi - ek})))"
body["FOLD_RELIEF"] = json.dumps({k: v for k, v in rep.items() if k != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = OUT.name; REP.write_text(json.dumps(rep, indent=1)); print("FOLD done")
