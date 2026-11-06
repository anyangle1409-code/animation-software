"""FEMALE F10d: rig contract check + left thumb joint fix + bind check. NEW file; input unchanged.

Contract (src/rig/boneNames.ts, src/rig/frozen.test.ts, skeleton id hgpt_canonical_v3): the 63 canonical bones -
25 core, 8 metacarpals, 30 finger bones - each under its frozen parent. Character deformation helpers are allowed on
top (docs/CANONICAL_SKELETON_FREEZE.md: "twist bones, correctives" are not frozen). Conventions: each bone's Z axis
(roll) is compared with the approved male 07c's in the PARENT bone's frame (canonical_rig_local_frames.json, derived
from the 07c rig: orientation only) and aligned to it; deform flags must match the male's (canonical_rig_conventions.json).

Male-only helpers (shoulder_cap, muscle_lat / pec / trap, arm_ref, scap_glide, hip_crease) are deformation helpers
of the male's corrective system, not contract bones: they are listed and NOT copied (her correctives, including the
breast family, are authored in the movement phase on her own anatomy).

Joint check: every deform bone's head must lie inside her closed body (ray parity, 3 axes, majority). A head outside
is moved along the line to the centroid of the body vertices weighted most to that bone until it is 4 mm inside
(the left thumb's CMC joint, thumb_01_l, sat just outside after F08a).

Bind check: unweighted vertices, influences per vertex, weight sums, on the body and the three garment / hair meshes.

usage: python3.13 rig_contract_f_blender.py -- <in .blend> <out NEW .blend> <report .json> <conventions .json> <local frames .json>
"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP, CONV, LOCAL = Path(a[0]), Path(a[1]), Path(a[2]), Path(a[3]), Path(a[4])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
rig = bpy.data.objects["HGPT_FEMALE_RIG"]; rig.data.pose_position = "REST"; bpy.context.view_layer.update()
body = bpy.data.objects["HGPT_Female_Body"]
rep = {"in": IN.name, "skeleton_id": "hgpt_canonical_v3"}

# ---------------- contract (mirrors src/rig/boneNames.ts + the frozen hierarchy)
H = {"root": None, "pelvis": "root", "spine_01": "pelvis", "spine_02": "spine_01", "spine_03": "spine_02",
     "neck": "spine_03", "head": "neck"}
for s in ("l", "r"):
    H.update({f"clavicle_{s}": "spine_03", f"scapula_{s}": f"clavicle_{s}", f"upperarm_{s}": f"scapula_{s}",
              f"forearm_{s}": f"upperarm_{s}", f"hand_{s}": f"forearm_{s}", f"thigh_{s}": "pelvis",
              f"shin_{s}": f"thigh_{s}", f"foot_{s}": f"shin_{s}", f"toe_{s}": f"foot_{s}",
              f"thumb_01_{s}": f"hand_{s}", f"thumb_02_{s}": f"thumb_01_{s}", f"thumb_03_{s}": f"thumb_02_{s}"})
    for f in ("index", "middle", "ring", "pinky"):
        H.update({f"metacarpal_{f}_{s}": f"hand_{s}", f"{f}_01_{s}": f"metacarpal_{f}_{s}",
                  f"{f}_02_{s}": f"{f}_01_{s}", f"{f}_03_{s}": f"{f}_02_{s}"})
assert len(H) == 63
B = rig.data.bones
missing = [n for n in H if n not in B]
wrong_parent = [n for n in H if n in B and (B[n].parent.name if B[n].parent else None) != H[n]]
extra = sorted(b.name for b in B if b.name not in H)
conv = {c["name"]: c for c in json.load(open(CONV))["bones"]}
roll_dev, deform_mismatch = {}, []
for n in H:
    if n not in B or n not in conv:
        continue
    z = (rig.matrix_world.to_3x3() @ B[n].matrix_local.to_3x3().col[2]).normalized()
    roll_dev[n] = round(float(np.degrees(np.arccos(np.clip(z.dot(Vector(conv[n]["roll_z"])), -1, 1)))), 1)
    if B[n].use_deform != conv[n]["deform"]:
        deform_mismatch.append(n)
male_helpers = sorted(n for n in conv if n not in H and n not in B)
rep["contract"] = {"canonical_bones": 63, "missing": missing, "wrong_parent": wrong_parent,
                   "character_helpers_present": extra, "deform_flag_mismatch": deform_mismatch,
                   "male_only_helpers_not_copied": male_helpers}

# ---------------- joints inside the body
dg = bpy.context.evaluated_depsgraph_get(); be = body.evaluated_get(dg); bm_ = be.to_mesh()
BV = np.array([v.co[:] for v in bm_.vertices]); bvh = BVHTree.FromPolygons([Vector(p) for p in BV], [tuple(p.vertices) for p in bm_.polygons])
be.to_mesh_clear()


def inside(p):
    votes = 0
    for d in (Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))):
        n = 0; o = Vector(p)
        while True:
            h = bvh.ray_cast(o, d, 5.0)
            if h[0] is None:
                break
            n += 1; o = h[0] + d * 1e-5
        votes += n % 2
    return votes >= 2


gidx = {g.name: g.index for g in body.vertex_groups}
W = {}
for v in body.data.vertices:
    for g in v.groups:
        W.setdefault(g.group, []).append((v.index, g.weight))
outside, moved = [], {}
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode="EDIT")
eb = rig.data.edit_bones
for b in [b for b in B if b.use_deform]:
    hd = rig.matrix_world @ b.head_local
    if inside(hd):
        continue
    outside.append(b.name)
    g = gidx.get(b.name)
    if g is None or g not in W:
        continue
    # target: centroid of her body's cross-section through the joint, perpendicular to the bone (the joint keeps its
    # position along the bone: only the off-centre component is corrected)
    ax = (rig.matrix_world.to_3x3() @ (b.tail_local - b.head_local)).normalized(); R_ = BV - np.array(hd[:])
    al = R_ @ np.array(ax[:]); rad = np.linalg.norm(R_ - np.outer(al, ax[:]), axis=1)
    sel = (np.abs(al) < 0.008) & (rad < 0.035)
    if sel.sum() < 6:
        continue
    c = Vector(BV[sel].mean(0))
    best = None
    for t in np.linspace(0, 1, 201):
        p = hd.lerp(c, t)
        if inside(p):
            dd = bvh.find_nearest(p)[3]
            if best is None or dd > best[1] + 1e-4:
                best = (p, dd)
            if dd >= 0.004:
                break
    if best is not None:
        p = best[0]
        e = eb[b.name]; delta = rig.matrix_world.inverted().to_3x3() @ (p - hd)
        e.head += delta
        moved[b.name] = {"from": [round(x, 4) for x in hd], "to": [round(x, 4) for x in p], "moved_mm": round((p - hd).length * 1000, 1),
                         "depth_mm": round(best[1] * 1000, 1)}
# roll, in the PARENT frame: her hands, feet and limbs rest in other orientations than the male's (palms back, thumbs
# forward), so world-space Z axes are not comparable. For each contract bone (root first) the male's local frame
# (canonical_rig_local_frames.json: Y and Z in the parent bone's frame) is turned onto her bone's local Y by the
# smallest rotation, and her roll is set so her local Z matches the turned male Z. Deviation = the angle between the
# two before / after (the roll convention in the parent frame, independent of rest pose).
LF = {c["name"]: c for c in json.load(open(LOCAL))["bones"]}


def pframe(e):
    return e.parent.matrix.to_3x3().normalized() if e.parent else rig.matrix_world.inverted().to_3x3() @ Matrix.Identity(3)


def local_dev(e):
    P_ = pframe(e); ly = (P_.transposed() @ e.y_axis).normalized(); lz = (P_.transposed() @ e.z_axis).normalized()
    my = Vector(LF[e.name]["local_y"]); mz = Vector(LF[e.name]["local_z"])
    q = my.rotation_difference(ly); mz2 = (q @ mz).normalized()
    return float(np.degrees(np.arccos(np.clip(lz.dot(mz2), -1, 1)))), P_ @ mz2


order = [n for n in H]                     # H lists parents before children
roll_before, roll_after = {}, {}
for n in order:
    if n not in eb or n not in LF:
        continue
    e = eb[n]; d0, zw = local_dev(e); roll_before[n] = round(d0, 1)
    e.align_roll(zw.normalized()); roll_after[n] = round(local_dev(e)[0], 1)
rep["roll_parent_frame_deviation_before_deg"] = {"max": max(roll_before.values()), "over_10": {k: v for k, v in roll_before.items() if v > 10}}
rep["roll_parent_frame_deviation_after_deg"] = {"max": max(roll_after.values()), "over_2": {k: v for k, v in roll_after.items() if v > 2}}
bpy.ops.object.mode_set(mode="OBJECT")
rep["joints_outside_before"] = outside; rep["joints_moved"] = moved
rep["joints_outside_after"] = [b.name for b in rig.data.bones if b.use_deform and not inside(rig.matrix_world @ b.head_local)]

# ---------------- bind: weights normalised over the deform bones, at most 4 influences
for n in ("HGPT_Female_Body", "HGPT_Female_Bra", "HGPT_Female_Shorts", "HGPT_Female_Ponytail"):
    o = bpy.data.objects[n]; dn = {g.index for g in o.vertex_groups if g.name in B and B[g.name].use_deform}
    for v in o.data.vertices:
        gs = sorted([g for g in v.groups if g.group in dn and g.weight > 1e-6], key=lambda g: -g.weight)
        for g in gs[4:]:
            o.vertex_groups[g.group].remove([v.index])
        gs = gs[:4]; t = sum(g.weight for g in gs)
        if t > 0:
            for g in gs:
                g.weight = g.weight / t
bind = {}
for n in ("HGPT_Female_Body", "HGPT_Female_Bra", "HGPT_Female_Shorts", "HGPT_Female_Ponytail"):
    o = bpy.data.objects[n]; dn = {g.index for g in o.vertex_groups if g.name in B and B[g.name].use_deform}
    unw = 0; mx = 0; bad_sum = 0
    for v in o.data.vertices:
        ws = [g.weight for g in v.groups if g.group in dn and g.weight > 1e-6]
        if not ws:
            unw += 1
        mx = max(mx, len(ws))
        if ws and abs(sum(ws) - 1) > 0.02:
            bad_sum += 1
    bind[n] = {"vertices": len(o.data.vertices), "unweighted": unw, "max_influences": mx, "weight_sum_off_by_2pct": bad_sum}
rep["bind"] = bind
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = str(OUT); REP.write_text(json.dumps(rep, indent=1)); print("RIG", json.dumps(rep))
