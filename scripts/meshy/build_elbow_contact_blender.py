"""Elbow-fold contact (forearm flexors against biceps) driven by elbow flexion - writes a NEW file.

Measured on 06i (arms hanging, scapular-plane press start gives the same picture): no contact up to ~70 deg of
flexion, then forearm-upper-arm intersecting triangle pairs 31 / 75 / 123 / 154 / 198 / 316 at 80 / 90 / 110 / 120 /
140 / 150 deg (+ 2-16 pairs of upper-arm skin folding through itself in the crease). Linear skinning lets the two
soft masses pass through each other; real tissue compresses and flattens against each other. The joint limit
(150 deg flexion) is NOT changed.

Method (same solver as build_adduction_contact_blender.py, round AX3):
  * pose: both arms hanging at the rest elevation, elbow at each key flexion FLEX_KEYS about the anatomical hinge
    (shoulder_pose_lib.arm_pose hinge=True; the old aim-based posing bent the elbow up to 71 deg off its hinge);
  * region: vertices dominated by the upper arm / forearm within REGION of the elbow joint (the trunk and the hand
    are never moved);
  * contact surface = the plane through the elbow joint bisecting the angle between the upper arm and the forearm:
    on the flexor (inner) side, upper-arm skin that crosses it is put back onto it (+ GAP) and so is forearm skin
    from the other side - both masses flatten against each other, as soft tissue does; rounds of two smoothing
    passes of the correction FIELD (not the surface) spread the push into the surrounding skin, each followed by the
    flattening again. (The pairwise solver of the shoulder contact diverged here: at 115-150 deg the masses overlap
    by several cm and pushing triangle pairs apart kept creating new crossings - up to 160 mm moves, rejected);
  * the posed displacement is inverse-skinned into one key per side and flexion (ELBOW_<S>_<deg>); drivers on
    ROTATION_DIFF(upper arm, forearm) make piecewise-linear tents between the keys: the first key fades in from
    START deg, the last one is held to the joint limit. Below START every key is exactly zero.

usage: python3.13 build_elbow_contact_blender.py -- <bound .blend> <out NEW .blend> <report .json>
"""
import json
import math
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
sys.path.insert(0, str(Path(__file__).resolve().parent))
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
from shoulder_pose_lib import arm_pose, rest_capture, rest_restore  # noqa: E402
START, FLEX_KEYS, REGION, GAP, ITERS, ROUNDS = 70.0, (90.0, 115.0, 140.0, 150.0), 0.17, 0.0008, 40, 6
MAX_DEPTH, STEP = 0.02, 0.002
rig = bpy.data.objects["MESHY_RIG"]; body = bpy.data.objects["MESHY_BODY"]; me = body.data; pb = rig.pose.bones
NV = len(me.vertices); P = [tuple(p.vertices) for p in me.polygons]
nbr = [[] for _ in range(NV)]
for e in me.edges:
    i, j = e.vertices; nbr[i].append(j); nbr[j].append(i)
GN = {g.index: g.name for g in body.vertex_groups}
WT = [dict() for _ in range(NV)]
for v in me.vertices:
    for g in v.groups:
        if g.weight > 1e-5 and GN[g.group] in rig.data.bones and rig.data.bones[GN[g.group]].use_deform:
            WT[v.index][GN[g.group]] = g.weight
DOM = [max(w, key=w.get) if w else "" for w in WT]
TRI = []
for f in P:
    TRI += [(f[0], f[1], f[2]), (f[0], f[2], f[3])] if len(f) == 4 else [tuple(f[:3])]
TRI = np.array(TRI); TS = [set(t) for t in TRI]
if not me.shape_keys:
    body.shape_key_add(name="Basis", from_mix=False)
REMOVED = []                                                     # rebuilding on a changed mesh: old elbow keys go first
for kb_ in list(me.shape_keys.key_blocks):
    if kb_.name.startswith("ELBOW_"):
        try:
            kb_.driver_remove("value")
        except TypeError:
            pass
        REMOVED.append(kb_.name); body.shape_key_remove(kb_)


def evaluated():
    dg = bpy.context.evaluated_depsgraph_get(); m = bpy.data.meshes.new_from_object(body.evaluated_get(dg), depsgraph=dg)
    V = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", V); bpy.data.meshes.remove(m); return V.reshape(-1, 3)


def skin_inv():
    bm_ = {n: np.array(pb[n].matrix @ rig.data.bones[n].matrix_local.inverted())[:3, :3] for n in {b for w in WT for b in w}}
    M = np.zeros((NV, 3, 3))
    for i, w in enumerate(WT):
        s = sum(w.values())
        for n, x in w.items():
            M[i] += bm_[n] * (x / s)
    return np.linalg.inv(M)


def pairs_in(X, treg):
    b = BVHTree.FromPolygons([Vector(p) for p in X], TRI.tolist(), all_triangles=True)
    return [(i, j) for i, j in b.overlap(b) if i < j and treg[i] and treg[j] and not (TS[i] & TS[j])]


def solve(X, treg, iters):
    for _ in range(iters):
        Nf = np.cross(X[TRI[:, 1]] - X[TRI[:, 0]], X[TRI[:, 2]] - X[TRI[:, 0]]); Nf /= np.maximum(np.linalg.norm(Nf, axis=1)[:, None], 1e-12)
        pr = [(i, j) for i, j in pairs_in(X, treg) if Nf[i] @ Nf[j] < 0.3]
        if not pr:
            return X
        acc = np.zeros_like(X); cnt = np.zeros(NV)
        for i, j in pr:
            for A, B in ((i, j), (j, i)):
                for v in TRI[A]:
                    d = (X[v] - X[TRI[B][0]]) @ Nf[B]
                    if -MAX_DEPTH < d < GAP:                   # behind the other triangle - but not a vertex far off
                        acc[v] += Nf[B] * min((GAP - d) / 2, STEP); cnt[v] += 1   # to the side behind its plane
        m = cnt > 0; X = X.copy(); X[m] += acc[m] / cnt[m][:, None]
    return X


def smooth_field(delta, region):
    nd = delta.copy()
    for i in np.where(region)[0]:
        nb = [j for j in nbr[i] if region[j]]
        if nb:
            nd[i] = 0.5 * delta[i] + 0.5 * np.mean(delta[nb], axis=0)
    return nd


rest = rest_capture(rig); rep = {"method": __doc__.split("usage")[0].strip(), "start_deg": START, "keys_deg": FLEX_KEYS, "replaced_keys": REMOVED, "sides": {"l": {}, "r": {}}}
REST_EL = {}
for sd in ("l", "r"):
    u = (rig.matrix_world @ pb[f"upperarm_{sd}"].tail - rig.matrix_world @ pb[f"upperarm_{sd}"].head).normalized()
    REST_EL[sd] = math.degrees(math.acos(max(-1, min(1, -u.z))))
names = []
for fk in FLEX_KEYS:
    for sd in ("r", "l"):
        rest_restore(rig, rest); arm_pose(rig, sd, REST_EL[sd], 10, 180 - fk, 0, hinge=True); bpy.context.view_layer.update()
        Vp = evaluated(); el = np.array(rig.matrix_world @ pb[f"forearm_{sd}"].head)
        region = (np.linalg.norm(Vp - el, axis=1) < REGION) & np.array([d in (f"upperarm_{sd}", f"forearm_{sd}", f"forearm_tw1_{sd}") for d in DOM])
        treg = region[TRI].all(1); h0 = len(pairs_in(Vp, treg))
        J = el; au = np.array(rig.matrix_world @ pb[f"upperarm_{sd}"].head) - J; au /= np.linalg.norm(au)
        fu = np.array(rig.matrix_world @ pb[f"forearm_tw1_{sd}"].tail) - J; fu /= np.linalg.norm(fu)
        n = au - fu; n /= np.linalg.norm(n); inner = au + fu; inner /= np.linalg.norm(inner)
        isU = np.array([d == f"upperarm_{sd}" for d in DOM]) & region; isF = region & ~isU
        def flatten(X):                                       # the contact surface is the plane bisecting the elbow
            s_ = (X - J) @ n; w_ = (X - J) @ inner; X = X.copy()   # angle, on the flexor (inner) side only
            mU = isU & (w_ > 0) & (s_ < GAP); X[mU] += np.outer(GAP - s_[mU], n)
            mF = isF & (w_ > 0) & (s_ > -GAP); X[mF] -= np.outer(s_[mF] + GAP, n)
            return X
        X = flatten(Vp)
        for _ in range(ROUNDS):
            X = Vp + smooth_field(smooth_field(X - Vp, region), region); X = flatten(X)
        delta = X - Vp; h1 = len(pairs_in(X, treg))
        dr = np.einsum("nij,nj->ni", skin_inv(), delta)
        name = f"ELBOW_{sd.upper()}_{int(fk)}"; sk = body.shape_key_add(name=name, from_mix=False); names.append((name, sd, fk))
        co = np.array([v.co[:] for v in me.vertices]) + dr; sk.data.foreach_set("co", co.ravel())
        sk.value = 0.0
        mv = np.linalg.norm(delta, axis=1)
        rep["sides"][sd][int(fk)] = {"pairs_before_after": [h0, h1], "moved_vertices": int((mv > 1e-4).sum()), "max_move_mm": round(float(mv.max()) * 1000, 1)}
        print("KEY", name, json.dumps(rep["sides"][sd][int(fk)]), flush=True)
        # the key must be ON while the next flexion key is built (tent drivers are added below; set its value meanwhile)
rest_restore(rig, rest)
kb = me.shape_keys.key_blocks
for sd in ("r", "l"):
    e0 = math.degrees(rig.data.bones[f"upperarm_{sd}"].matrix_local.to_quaternion().rotation_difference(rig.data.bones[f"forearm_{sd}"].matrix_local.to_quaternion()).angle)
    pts = [START] + list(FLEX_KEYS)
    for k, fk in enumerate(FLEX_KEYS):
        lo, hi = pts[k], (FLEX_KEYS[k + 1] if k + 1 < len(FLEX_KEYS) else None)
        fc = kb[f"ELBOW_{sd.upper()}_{int(fk)}"].driver_add("value"); d = fc.driver; d.type = "SCRIPTED"
        v = d.variables.new(); v.name = "e"; v.type = "ROTATION_DIFF"
        v.targets[0].id = rig; v.targets[0].bone_target = f"upperarm_{sd}"; v.targets[1].id = rig; v.targets[1].bone_target = f"forearm_{sd}"
        f = "(e*57.29578)"                                        # flexion in degrees (the bones are aligned at rest:
        up = f"max(0.0, min(1.0, ({f} - {lo}) / {fk - lo}))"       # rest offset {e0:.1f} deg, measured below)
        d.expression = up if hi is None else f"min({up}, max(0.0, min(1.0, ({hi} - {f}) / {hi - fk})))"
    rep["sides"][sd]["rest_rotation_diff_deg"] = round(e0, 2)
body["ELBOW_CONTACT"] = json.dumps({k: v for k, v in rep.items() if k != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = OUT.name; REP.write_text(json.dumps(rep, indent=1)); print("ELBOW done")
