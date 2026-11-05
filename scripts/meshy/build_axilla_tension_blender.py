"""Axilla at full elevation: concave fossa between taut folds - corrective keys driven by elevation - writes a NEW file.

STATUS: TRIAL on 06j, not adopted yet (round AX4): coronal-slice fold-over at the 170 deg apex 120 -> 15-20 deg (turn
angle), armpit sharp edges at 170 deg 4 -> 1-2, one folded face; to be rebuilt and judged on 07a.

Measured on 06i/06j (smooth-shaded renders, coronal and sagittal slices): at 135-170 deg the axillary hollow is
FLAT (coronal apex slice a straight line) and the anterior fold reads as a V-shaped valley along the inner arm, not
as the taut, rounded lower border of pectoralis major. Weights are not the tool for this (the chest / scapula weight
history must not be reverted): skin under tension spans the folds like a membrane, and the axillary fossa is held
in by the axillary fascia (suspensory ligament) between them. This is a posed-shape response, so it is a corrective:
  * pose: both arms in the sweep posture (scapular plane, elbow 175, clavicle 25*e/170) at each key elevation E_KEYS;
  * zones (rest space, relative to the shoulder joint, trunk-facing side of the arm root): depth 50-210 mm below the
    joint, from 95 mm medial to 30 mm lateral of it; front fold (dy < 0), back fold (dy > 0), fossa (|dy| small);
  * FOSSA: vault vertices (cap rings 1..7 on the trunk side) move inward along the posed vertex normal by
    DEPTH(e) * window(dy) * window(ring) - a smooth dome-shaped hollow, deepest at the vault centre;
  * FOLDS: where the posed skin is stretched (edge length ratio > T_MIN), concave valleys (umbrella vector along the
    normal > 0) are lifted OUTWARD only, by a fraction of their concavity, in a few passes - the membrane response of
    taut skin. Convex ridges and unstretched skin are never moved, nothing is moved inward on the folds;
  * the displacement field is smoothed twice (field, not surface), inverse-skinned per vertex and stored as
    AXILLA_<S>_<deg>; drivers on ROTATION_DIFF(upper arm, arm_ref) make tents: 0 below E_ON, the first key at its
    elevation, cross-fade to the next, the last held to 180. Below E_ON every key is exactly zero, so the batwing and
    the arms-down contact fixes are untouched.

usage: python3.13 build_axilla_tension_blender.py -- <bound .blend> <out NEW .blend> <report .json> [depth170 mm]
"""
import json
import math
import sys
from collections import deque
from pathlib import Path

import bpy
import bmesh  # noqa: E402
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2]); D170 = float(a[3]) / 1000 if len(a) > 3 else 0.012
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
sys.path.insert(0, str(Path(__file__).resolve().parent))
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
from shoulder_pose_lib import arm_pose, rest_capture, rest_restore  # noqa: E402
E_ON, E_KEYS, T_MIN, LIFT, PASSES = 100.0, (135.0, 170.0), 1.3, 0.5, 6
DEPTH = {135.0: D170 * 0.6, 170.0: D170}
rig = bpy.data.objects["MESHY_RIG"]; body = bpy.data.objects["MESHY_BODY"]; me = body.data; pb = rig.pose.bones
NV = len(me.vertices); bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
LR, LC = bm.verts.layers.int["t3_row"], bm.verts.layers.int["t3_col"]; L4, L5 = bm.verts.layers.int["t4_part"], bm.verts.layers.int["t5_part"]
shell = [(v[LR] > 0 or v[LC] > 0) for v in bm.verts]; cap = [(not shell[v.index]) and v[L4] == 0 and v[L5] == 0 and v.co.z > 0.95 for v in bm.verts]
nbr = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
EDG = np.array([e.vertices[:] for e in me.edges]); R = np.array([v.co[:] for v in me.vertices])
P = [tuple(p.vertices) for p in me.polygons]; TRI = []
for f in P:
    TRI += [(f[0], f[1], f[2]), (f[0], f[2], f[3])] if len(f) == 4 else [tuple(f[:3])]
TRI = np.array(TRI)
GN = {g.index: g.name for g in body.vertex_groups}; WT = [dict() for _ in range(NV)]
for v in me.vertices:
    for g in v.groups:
        if g.weight > 1e-5 and GN[g.group] in rig.data.bones and rig.data.bones[GN[g.group]].use_deform:
            WT[v.index][GN[g.group]] = g.weight


def sm(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def evaluated():
    dg = bpy.context.evaluated_depsgraph_get(); m = bpy.data.meshes.new_from_object(body.evaluated_get(dg), depsgraph=dg)
    V = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", V); N = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("normal", N)
    bpy.data.meshes.remove(m); return V.reshape(-1, 3), N.reshape(-1, 3)


def skin_inv():
    bm_ = {n: np.array(pb[n].matrix @ rig.data.bones[n].matrix_local.inverted())[:3, :3] for n in {b for w in WT for b in w}}
    M = np.zeros((NV, 3, 3))
    for i, w in enumerate(WT):
        s = sum(w.values())
        for n, x in w.items():
            M[i] += bm_[n] * (x / s)
    return np.linalg.inv(M)


def hits(V, region):
    b = BVHTree.FromPolygons([Vector(p) for p in V], TRI.tolist(), all_triangles=True)
    return sum(1 for i, j in b.overlap(b) if i < j and not set(TRI[i]) & set(TRI[j]) and (region[TRI[i][0]] or region[TRI[j][0]]))


rest = rest_capture(rig); REST_EL = {}
for sd in ("l", "r"):
    u = (rig.matrix_world @ pb[f"upperarm_{sd}"].tail - rig.matrix_world @ pb[f"upperarm_{sd}"].head).normalized()
    REST_EL[sd] = math.degrees(math.acos(max(-1, min(1, -u.z))))
rep = {"method": __doc__.split("usage")[0].strip(), "params": {"e_on": E_ON, "keys": E_KEYS, "depth_mm": {str(k): round(v * 1000, 1) for k, v in DEPTH.items()}, "t_min": T_MIN, "lift": LIFT}, "sides": {"l": {}, "r": {}}}
ZONE = {}
for sd, sg in (("r", 1), ("l", -1)):
    gh = np.array(rig.matrix_world @ rig.data.bones[f"upperarm_{sd}"].head_local)
    rim = [v for v in bm.verts if shell[v.index] and v.co.x * sg > 0.1 and any(cap[e.other_vert(v).index] for e in v.link_edges)]
    ring = np.full(NV, -1); q = deque(rim)
    for v in rim:
        ring[v.index] = 0
    while q:
        v = q.popleft()
        for e in v.link_edges:
            w = e.other_vert(v)
            if cap[w.index] and ring[w.index] < 0 and w.co.x * sg > 0.05:
                ring[w.index] = ring[v.index] + 1; q.append(w)
    dy = R[:, 1] - gh[1]; dz = gh[2] - R[:, 2]; dx = (R[:, 0] - gh[0]) * sg
    box = (dz > 0.05) & (dz < 0.21) & (dx > -0.095) & (dx < 0.03) & (R[:, 0] * sg > 0.05)
    fossa_w = np.where(box & (ring >= 1) & (ring <= 7), sm(1 - np.abs(dy) / 0.045) * sm(1 - np.abs(ring - 3.5) / 4.0), 0.0)
    fold = box & (np.abs(dy) > 0.012)
    ZONE[sd] = (box, fossa_w, fold)
names = []
for ek in E_KEYS:
    for sd in ("r", "l"):
        box, fossa_w, fold = ZONE[sd]
        rest_restore(rig, rest); arm_pose(rig, sd, ek, 30, 175, 25.0 * ek / 170.0); bpy.context.view_layer.update()
        Vp, Np = evaluated(); h0 = hits(Vp, box)
        st = np.zeros(NV); L0 = np.linalg.norm(R[EDG[:, 0]] - R[EDG[:, 1]], axis=1); L1 = np.linalg.norm(Vp[EDG[:, 0]] - Vp[EDG[:, 1]], axis=1)
        np.maximum.at(st, EDG[:, 0], L1 / np.maximum(L0, 1e-6)); np.maximum.at(st, EDG[:, 1], L1 / np.maximum(L0, 1e-6))
        X = Vp - Np * (DEPTH[ek] * fossa_w)[:, None]                      # fossa: inward along the normal
        tense = fold & (st > T_MIN); lifted = 0
        for _ in range(PASSES):                                            # taut folds: lift concave valleys outward
            U = np.array([X[nbr[i]].mean(0) - X[i] if nbr[i] else np.zeros(3) for i in range(NV)])
            c = np.einsum("ij,ij->i", U, Np)
            m = tense & (c > 0); X[m] += Np[m] * (LIFT * c[m])[:, None]; lifted = max(lifted, int(m.sum()))
        delta = X - Vp; reg = box
        for _ in range(2):
            nd = delta.copy()
            for i in np.where(reg)[0]:
                nb = [j for j in nbr[i] if reg[j]]
                if nb:
                    nd[i] = 0.5 * delta[i] + 0.5 * np.mean(delta[nb], axis=0)
            delta = nd
        delta[~box] = 0.0
        h1 = hits(Vp + delta, box)
        dr = np.einsum("nij,nj->ni", skin_inv(), delta)
        name = f"AXILLA_{sd.upper()}_{int(ek)}"; sk = body.shape_key_add(name=name, from_mix=False); sk.value = 0.0
        sk.data.foreach_set("co", (R + dr).ravel())
        mv = np.linalg.norm(delta, axis=1); inward = -np.einsum("ij,ij->i", delta, Np)
        rep["sides"][sd][int(ek)] = {"intersections_zone_before_after": [h0, h1], "moved_vertices": int((mv > 1e-4).sum()), "max_move_mm": round(float(mv.max()) * 1000, 1),
                                     "max_inward_mm": round(float(inward.max()) * 1000, 1), "max_outward_mm": round(float(-inward.min()) * 1000, 1), "tense_fold_vertices_lifted": lifted}
        print("KEY", name, json.dumps(rep["sides"][sd][int(ek)]), flush=True)
rest_restore(rig, rest)
kb = me.shape_keys.key_blocks
for sd in ("r", "l"):
    qa = rig.data.bones[f"upperarm_{sd}"].matrix_local.to_quaternion(); qr = rig.data.bones[f"arm_ref_{sd}"].matrix_local.to_quaternion()
    e0 = math.degrees(qr.rotation_difference(qa).angle); el = f"(e*57.29578 - {e0:.3f} + {REST_EL[sd]:.3f})"
    pts = [E_ON] + list(E_KEYS)
    for k, ek in enumerate(E_KEYS):
        lo, hi = pts[k], (E_KEYS[k + 1] if k + 1 < len(E_KEYS) else None)
        fc = kb[f"AXILLA_{sd.upper()}_{int(ek)}"].driver_add("value"); d = fc.driver; d.type = "SCRIPTED"
        v = d.variables.new(); v.name = "e"; v.type = "ROTATION_DIFF"
        v.targets[0].id = rig; v.targets[0].bone_target = f"upperarm_{sd}"; v.targets[1].id = rig; v.targets[1].bone_target = f"arm_ref_{sd}"
        up = f"max(0.0, min(1.0, ({el} - {lo}) / {ek - lo}))"
        d.expression = up if hi is None else f"min({up}, max(0.0, min(1.0, ({hi} - {el}) / {hi - ek})))"
body["AXILLA_TENSION"] = json.dumps({k: v for k, v in rep.items() if k != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = OUT.name; REP.write_text(json.dumps(rep, indent=1)); print("AXILLA done")
