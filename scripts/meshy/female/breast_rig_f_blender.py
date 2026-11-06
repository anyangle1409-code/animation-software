"""FEMALE F10e: her own breast weights + breast soft-tissue helpers; bra re-bound to them. NEW file; input unchanged.

The F10d structural test (chest_bra_elevation_test_f_blender.py) found the breast tissue carrying arm / girdle skin
weight from the bone-heat bind (mean 18 %, 720 of 2219 vertices over 20 %): the breasts stretched with the upper arm
(edge stretch p95 1.9 at 170 deg, centroids moving 24 mm in the sternum frame). This step:
  * BREAST REGION: body vertices under the bra cups (front chest: y < -0.04, 1.08 < z < 1.32, |x| < 0.15, the same
    box the structural test measures), feathered over 50 mm (distance over the mesh to the region's edge) so the axillary tail and the upper
    pectoral border keep a share of the arm's motion;
  * REWEIGHT: KEEP (25 %) of the arm / girdle share (upperarm, clavicle, scapula) stays - the pectoral base under the
    breast does follow the arm a little - the rest moves to spine_03 (the ribcage), times the feather;
  * HELPERS: breast_l / breast_r, deforming character helpers (not contract bones; docs/CANONICAL_SKELETON_FREEZE.md
    allows deformation helpers), child of spine_03, head at the breast's base centre on the chest wall, tail 6 cm
    forward through the breast's front-most point; Z axis up. Weight: up to CORE (0.55) at the breast's front,
    falling to 0 at the base and the region edge, taken proportionally from the vertex's spine shares. With identity
    pose they change nothing; they make breast motion controllable independently of the arm (soft-tissue follow-
    through, support) for the movement phase;
  * BRA: weights re-transferred from the body (nearest face, interpolated) so cups, band and straps move exactly
    with the skin under them (containment follows any breast-helper motion).

usage: python3.13 breast_rig_f_blender.py -- <in .blend> <out NEW .blend> <report .json>
"""
import heapq
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
KEEP, CORE, FEATHER = 0.25, 0.55, 0.05
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
rig = bpy.data.objects["HGPT_FEMALE_RIG"]; rig.data.pose_position = "REST"; bpy.context.view_layer.update()
body = bpy.data.objects["HGPT_Female_Body"]; me = body.data
P = np.array([v.co[:] for v in me.vertices]); N = len(P)
nbr = [[] for _ in range(N)]
for e in me.edges:
    nbr[e.vertices[0]].append(e.vertices[1]); nbr[e.vertices[1]].append(e.vertices[0])
rep = {"in": IN.name}


def dijkstra(seed, limit):
    dist = np.full(N, np.inf); pq = [(0.0, i) for i in np.where(seed)[0]]
    for _, i in pq:
        dist[i] = 0.0
    heapq.heapify(pq)
    while pq:
        d0, i = heapq.heappop(pq)
        if d0 > dist[i] or d0 > limit:
            continue
        for j in nbr[i]:
            nd = d0 + float(np.linalg.norm(P[i] - P[j]))
            if nd < dist[j]:
                dist[j] = nd; heapq.heappush(pq, (nd, j))
    return dist


# breast region: the front chest under the bra cups (the structural test's box: y < -0.04, 1.08 < z < 1.32,
# |x| < 0.15); apex = the front-most vertex on each side
region = (P[:, 1] < -0.04) & (P[:, 2] > 1.08) & (P[:, 2] < 1.32) & (np.abs(P[:, 0]) < 0.15); apex = {}
for sg in (1, -1):
    ids = np.where(region & (np.sign(P[:, 0]) == sg))[0]
    if len(ids):
        apex[sg] = P[ids[np.argmin(P[ids, 1])]].copy()
d_edge = dijkstra(~region, 0.1)
feather = np.clip(d_edge / FEATHER, 0, 1); feather[~region] = 0
rep["breast_region_vertices"] = int(region.sum())
# helper bones
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode="EDIT"); eb = rig.data.edit_bones
mi = rig.matrix_world.inverted(); heads = {}
for sg, s in ((1, None), (-1, None)):
    if sg not in apex:
        continue
    up = eb["upperarm_l"].head if (rig.matrix_world @ eb["upperarm_l"].head).x * sg > 0 else eb["upperarm_r"].head
    name = "breast_l" if up == eb["upperarm_l"].head else "breast_r"
    ids = np.where(region & (np.sign(P[:, 0]) == sg))[0]
    base = P[ids].mean(0); base[1] = P[ids, 1].max()                     # on the chest wall behind the breast
    tip = apex[sg].copy(); dvec = tip - base; dvec /= np.linalg.norm(dvec)
    e = eb.new(name); e.head = mi @ Vector(base); e.tail = mi @ Vector(base + dvec * 0.06); e.parent = eb["spine_03"]
    e.use_deform = True; e.align_roll(mi.to_3x3() @ Vector((0, 0, 1)))
    heads[name] = (base, tip, sg)
bpy.ops.object.mode_set(mode="OBJECT")
rep["helpers"] = {n: {"head": [round(float(x), 4) for x in v[0]], "front": [round(float(x), 4) for x in v[1]]} for n, v in heads.items()}
# weights
vg = body.vertex_groups; gid = {g.name: g.index for g in vg}
for n in heads:
    if n not in gid:
        vg.new(name=n)
gid = {g.name: g.index for g in vg}
moved_share = []
for i in map(int, np.where(region)[0]):
    v = me.vertices[i]; w = {vg[g.group].name: g.weight for g in v.groups}
    arm = [k for k in w if k.startswith(("upperarm", "clavicle", "scapula"))]
    s_arm = sum(w[k] for k in arm); take = s_arm * (1 - KEEP) * feather[i]
    if take > 0:
        for k in arm:
            w[k] -= w[k] / s_arm * take
        w["spine_03"] = w.get("spine_03", 0) + take
    moved_share.append(take)
    sg = int(np.sign(P[i, 0])); name = [n for n, h in heads.items() if h[2] == sg]
    if name:
        base, tip, _ = heads[name[0]]; ax = tip - base; t = np.clip(np.dot(P[i] - base, ax) / np.dot(ax, ax), 0, 1)
        wb = CORE * t * feather[i]
        sp_ = [k for k in w if k.startswith("spine")]; s_sp = sum(w[k] for k in sp_)
        wb = min(wb, s_sp)
        for k in sp_:
            w[k] -= w[k] / s_sp * wb if s_sp > 0 else 0
        w[name[0]] = wb
    tot = sum(x for x in w.values() if x > 1e-6)
    top = sorted(w.items(), key=lambda kv: -kv[1])[:4]; tt = sum(x for _, x in top)
    for g in list(v.groups):
        vg[g.group].remove([i])
    for k, x in top:
        if x > 1e-5:
            vg[gid[k]].add([i], x / tt, "REPLACE")
rep["arm_share_moved_to_ribcage"] = {"mean": round(float(np.mean(moved_share)), 3), "max": round(float(np.max(moved_share)), 3)}
# bra weights from the body
o = bpy.data.objects["HGPT_Female_Bra"]
for g in list(o.vertex_groups):
    if g.name in rig.data.bones:
        o.vertex_groups.remove(g)
for g in body.vertex_groups:
    if g.name in rig.data.bones and g.name not in o.vertex_groups:
        o.vertex_groups.new(name=g.name)
dt = o.modifiers.new("WT", "DATA_TRANSFER"); dt.object = body; dt.use_vert_data = True
dt.data_types_verts = {"VGROUP_WEIGHTS"}; dt.vert_mapping = "POLYINTERP_NEAREST"
dt.layers_vgroup_select_src = "ALL"; dt.layers_vgroup_select_dst = "NAME"
bpy.context.view_layer.objects.active = o
while o.modifiers.find("WT") > 0:
    bpy.ops.object.modifier_move_up(modifier="WT")
bpy.ops.object.modifier_apply(modifier="WT")
for v in o.data.vertices:
    gs = sorted([g for g in v.groups if o.vertex_groups[g.group].name in rig.data.bones and g.weight > 1e-6], key=lambda g: -g.weight)
    for g in gs[4:]:
        o.vertex_groups[g.group].remove([v.index])
    t_ = sum(g.weight for g in gs[:4])
    for g in gs[:4]:
        g.weight /= t_
rep["bra_weights"] = "re-transferred from the body (POLYINTERP_NEAREST), <= 4 influences, normalised"
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = str(OUT); REP.write_text(json.dumps(rep, indent=1)); print("BREAST", json.dumps(rep))
