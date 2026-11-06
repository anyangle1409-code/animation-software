"""FEMALE bind + natural standing pose (basic rig checks only; no exercise or deformation development). NEW file.

* Body: Blender bone-heat weights from her own skeleton (HGPT_FEMALE_RIG), then rule-based clean-up by the builders'
  part tags: finger vertices (t4_part 10-13) follow only their own finger chain + its metacarpal + the hand; thumb
  vertices (20, 21) only the thumb chain + hand; palm vertices (1) only hand / metacarpal / thumb_01 / forearm_tw1;
  no left / right bleed off the midline; unweighted vertices take their nearest weighted neighbour's weights; at most
  4 influences, normalised.
* Bra / shorts: weights transferred from the body (nearest face, interpolated); ponytail: the head bone.
* Natural standing pose (stored as the rig's pose; rest stays the A-pose): upper arms 10 deg from vertical, 6 deg
  forward; elbows 12 deg flexed; everything else as bound.
* Checks: body self-intersections at rest and in the pose (by region), skin through the garments in the pose, the
  smallest clearance hand / forearm -> thigh / hip in the pose, weight sanity (unweighted, >4 influences).

usage: python3.13 bind_f_pose_blender.py -- <skeleton .blend> <out NEW .blend> <report .json>
"""
import json
import math
import sys
from collections import Counter
from pathlib import Path

import bpy
import bmesh  # noqa: E402
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
rig = bpy.data.objects["HGPT_FEMALE_RIG"]; body = bpy.data.objects["HGPT_Female_Body"]
garms = [o for o in (bpy.data.objects.get("HGPT_Female_Bra"), bpy.data.objects.get("HGPT_Female_Shorts")) if o]
pony = bpy.data.objects.get("HGPT_Female_Ponytail")
vl = bpy.context.view_layer
for o in bpy.data.objects:
    o.select_set(False)
body.select_set(True); rig.select_set(True); vl.objects.active = rig
with bpy.context.temp_override(active_object=rig, selected_objects=[body, rig], selected_editable_objects=[body, rig]):
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
me = body.data; nv = len(me.vertices)
bones = [b.name for b in rig.data.bones if b.use_deform]
vg = {g.name: g.index for g in body.vertex_groups}
W = np.zeros((nv, len(body.vertex_groups)))
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
gname = {i: n for n, i in vg.items()}
P4 = np.zeros(nv, int); me.attributes["t4_part"].data.foreach_get("value", P4)
X = np.array([v.co.x for v in me.vertices])
rest = {b.name: (rig.matrix_world @ b.head_local, rig.matrix_world @ b.tail_local) for b in rig.data.bones}
FING = ["index", "middle", "ring", "pinky"]


def seg_dist(p, h, t):
    d = t - h; u = max(0.0, min(1.0, (p - h).dot(d) / max(d.length_squared, 1e-12))); return (p - (h + d * u)).length


allowed = {}
for side in ("l", "r"):
    sg = -1 if side == "l" else 1
    for f in range(4):
        idx = np.where((P4 == 10 + f) & (X * sg > 0))[0]
        if not len(idx):
            continue
        c = Vector(np.array([me.vertices[i].co[:] for i in idx]).mean(0))
        best = min(FING, key=lambda n: min(seg_dist(c, *rest[f"{n}_{k}_{side}"]) for k in ("01", "02", "03")) if f"{n}_01_{side}" in rest else 9)
        ok = {f"{best}_01_{side}", f"{best}_02_{side}", f"{best}_03_{side}", f"metacarpal_{best}_{side}", f"hand_{side}"}
        for i in idx:
            allowed[i] = ok
    for code in (20, 21):
        for i in np.where((P4 == code) & (X * sg > 0))[0]:
            allowed[i] = {f"thumb_01_{side}", f"thumb_02_{side}", f"thumb_03_{side}", f"hand_{side}"}
    for i in np.where((P4 == 1) & (X * sg > 0))[0]:
        allowed[i] = {f"hand_{side}", f"thumb_01_{side}", f"forearm_tw1_{side}"} | {f"metacarpal_{n}_{side}" for n in FING}
for i in range(nv):
    for gi in np.nonzero(W[i])[0]:
        n = gname[gi]
        if i in allowed and n not in allowed[i]:
            W[i, gi] = 0
        if X[i] > 0.01 and n.endswith("_l") or X[i] < -0.01 and n.endswith("_r"):
            W[i, gi] = 0
# unweighted -> nearest weighted neighbour (graph walk)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
filled = 0
for _ in range(20):
    empty = np.where(W.sum(1) == 0)[0]
    if not len(empty):
        break
    for i in empty:
        nb = [e.other_vert(bm.verts[i]).index for e in bm.verts[i].link_edges]
        ws = [W[j] for j in nb if W[j].sum() > 0]
        if ws:
            W[i] = np.mean(ws, 0); filled += 1
for i in range(nv):                                      # at most 4 influences, normalised
    nz = np.argsort(-W[i])[4:]; W[i, nz] = 0; s = W[i].sum()
    if s > 0:
        W[i] /= s
for g in body.vertex_groups:
    g.remove(list(range(nv)))
for gi, g in enumerate(body.vertex_groups):
    for i in np.nonzero(W[:, gi])[0]:
        g.add([int(i)], float(W[i, gi]), "REPLACE")
unweighted = int((W.sum(1) == 0).sum())
# garments: transfer weights from the body; ponytail: head
for o in garms:
    o.parent = rig
    for n in vg:
        o.vertex_groups.new(name=n)
    dt = o.modifiers.new("WeightsFromBody", "DATA_TRANSFER"); dt.object = body; dt.use_vert_data = True
    dt.data_types_verts = {"VGROUP_WEIGHTS"}; dt.vert_mapping = "POLYINTERP_NEAREST"
    dt.layers_vgroup_select_src = "ALL"; dt.layers_vgroup_select_dst = "NAME"
    with bpy.context.temp_override(object=o, active_object=o):
        bpy.ops.object.modifier_apply(modifier=dt.name)
    am = o.modifiers.new("Armature", "ARMATURE"); am.object = rig
    o.modifiers.move(len(o.modifiers) - 1, 0)                 # armature before solidify
if pony:
    pony.parent = rig; g = pony.vertex_groups.new(name="head"); g.add(list(range(len(pony.data.vertices))), 1.0, "REPLACE")
    am = pony.modifiers.new("Armature", "ARMATURE"); am.object = rig


def eval_mesh(o):
    dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); m = oe.to_mesh()
    V = [o.matrix_world @ v.co for v in m.vertices]; F = [tuple(p.vertices) for p in m.polygons]; oe.to_mesh_clear(); return V, F


def self_hits():
    V, F = eval_mesh(body)
    T = []
    for f in F:
        T += [(f[0], f[1], f[2]), (f[0], f[2], f[3])] if len(f) == 4 else [tuple(f[:3])]
    t = BVHTree.FromPolygons(V, T, all_triangles=True)
    c = Counter()
    for i, j in t.overlap(t):
        if not set(T[i]) & set(T[j]):
            p = V[T[i][0]]; reg = "hands" if P4[T[i][0]] > 0 else ("head" if p.z > 1.40 else ("legs_feet" if p.z < 0.80 else "trunk_arms"))
            c[reg] += 1
    return dict(c), V


rest_hits, _ = self_hits()
# ---- natural standing pose
rig.data.pose_position = "POSE"
for pb in rig.pose.bones:
    pb.rotation_mode = "QUATERNION"


def aim(pb_name, target):
    pb = rig.pose.bones[pb_name]; vl.update()
    M = pb.matrix.copy(); h = M.to_translation(); d = (pb.tail - pb.head).normalized()
    q = d.rotation_difference(Vector(target).normalized())
    pb.matrix = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ M; vl.update()


def turn(pb_name, axis, deg):
    pb = rig.pose.bones[pb_name]; vl.update(); M = pb.matrix.copy(); h = M.to_translation()
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, Vector(axis).normalized()) @ Matrix.Translation(-h) @ M; vl.update()


ARM_DOWN, ARM_FWD, ELBOW = 10.0, 6.0, 12.0
for side, sg in (("r", 1), ("l", -1)):
    t = Vector((sg * math.sin(math.radians(ARM_DOWN)), -math.sin(math.radians(ARM_FWD)), -math.cos(math.radians(ARM_DOWN))))
    aim(f"upperarm_{side}", t)
    pb = rig.pose.bones[f"forearm_{side}"]; d = (pb.tail - pb.head).normalized(); ax = d.cross(Vector((0, -1, 0)))
    turn(f"forearm_{side}", ax, ELBOW)
pose_hits, PV = self_hits()
# skin through the garments (posed): body vertices outside a garment surface where the garment covers them
through = 0
for o in garms:
    Vg, Fg = eval_mesh(o); gb = BVHTree.FromPolygons(Vg, Fg)
    for p in PV:
        h = gb.find_nearest(p, 0.01)
        if h[0] is not None and (p - h[0]).dot(h[1]) > 0.0002:
            through += 1
# hand / forearm to thigh clearance (posed)
hand_idx = [i for i in range(nv) if P4[i] > 0 or (0.75 < PV[i].z < 0.95 and abs(PV[i].x) > 0.17)]
thigh_idx = [i for i in range(nv) if P4[i] == 0 and 0.70 < PV[i].z < 0.98 and abs(PV[i].x) < 0.20 and abs(PV[i].x) > 0.05]
tb = BVHTree.FromPolygons([PV[i] for i in thigh_idx], []) if False else None
from mathutils.kdtree import KDTree  # noqa: E402
kd = KDTree(len(thigh_idx))
for k, i in enumerate(thigh_idx):
    kd.insert(PV[i], k)
kd.balance()
clear = min((kd.find(PV[i])[2] for i in hand_idx if kd.find(PV[i])[2] is not None), default=None)
rep = {"in": IN.name, "deform_bones": len(bones), "weights": {"unweighted_vertices": unweighted, "filled_from_neighbours": filled, "max_influences": 4},
       "self_intersections_rest": rest_hits, "self_intersections_pose": pose_hits, "pose": {"arm_from_vertical_deg": ARM_DOWN, "arm_forward_deg": ARM_FWD, "elbow_flex_deg": ELBOW},
       "skin_through_garments_vertices_pose": through, "min_hand_forearm_to_hip_thigh_mm_pose": round(clear * 1000, 1) if clear else None}
rig["NATURAL_POSE"] = json.dumps(rep["pose"])
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = str(OUT); REP.write_text(json.dumps(rep, indent=1)); print("BIND", json.dumps(rep))
