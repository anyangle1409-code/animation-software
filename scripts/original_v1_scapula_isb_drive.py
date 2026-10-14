"""Anatomical-frame (ISB) scapula drive for the ORIGINAL_v1 coupled shoulder motion (bpy; review-only diagnostic/candidate).

Finding (14 Oct 2026): build_functional_original_coupled_motion_blender.apply_coupled_pose applies the profile's scapular
angles as an XYZ Euler in the runtime `scapula_<s>` BONE's local axes (x = posterior tilt, y = internal rotation,
z = upward rotation).  That bone runs infero-medially with an arbitrary roll: its local Z is (-0.23, 0.80, 0.55) in world
(mostly posterior), and +30 deg of "upward rotation" on `_r` LOWERS the glenoid 21 mm and swings the inferior end 36 mm
toward the spine, i.e. anatomical DOWNWARD rotation.  The arm (aimed in world) then has to turn ~elevation + scapular
rotation relative to the scapula (162 deg at 160 HT instead of ~110), so the girdle/arm skin blend collapses overhead.

This module re-drives the scapula in the anatomical frame the model's own landmarks define (ISB: Zs = TS -> AA along the
scapular spine, Xs = normal to the blade plane (AA, TS, AI), Ys = Zs x Xs), with ISB order: internal rotation about Ys,
then upward rotation about Xs', then posterior tilt about Zs'', about the AC joint (the runtime clavicle tail).  Each
sign is fixed GEOMETRICALLY per side, not by convention: upward rotation must swing the inferior angle (AI) laterally,
posterior tilt must bring AI anteriorly (-Y), internal rotation must bring the acromion (AA) anteriorly.  The arm is then
re-aimed to the profile's world direction exactly as the original function does.  The source file is not edited; install()
wraps apply_coupled_pose in memory.  Runtime `_r` pairs with the anatomical-LEFT landmarks (F-SIDE-001).
"""
from __future__ import annotations

import math

import bpy
from mathutils import Matrix, Vector

LM = "LM_scapula_{side}__{name}"
ANAT = {"r": "left", "l": "right"}          # F-SIDE-001: runtime _r is anatomical left (+X)
_STATE = {}


def _landmarks(side_anat):
    return {n: bpy.data.objects[LM.format(side=side_anat, name=n)].matrix_world.translation.copy() for n in ("AA", "TS", "AI")}


def rest_frames():
    """Per runtime side: rest ISB axes (world) and landmark points, read once from the unposed anatomical landmarks."""
    out = {}
    for s, a in ANAT.items():
        p = _landmarks(a)
        z = (p["AA"] - p["TS"]).normalized()
        x = (p["AI"] - p["TS"]).cross(p["AA"] - p["TS"]).normalized()
        if x.y > 0:                                   # Xs points anteriorly (-Y is front in this model)
            x = -x
        y = z.cross(x).normalized()
        if y.z < 0:
            y = -y
        x = y.cross(z).normalized()
        out[s] = {"axes": (x, y, z), "points": p}
    return out


def _signed(axis, angle_deg, pivot, point, want):
    """Rotation about `axis` by angle_deg, where POSITIVE angles move `point` along `want` (a world direction); the sign is
    probed once with +1 deg, so negative angles (e.g. external rotation) rotate the opposite way."""
    probe = Matrix.Rotation(math.radians(1.0), 3, axis)
    sgn = 1.0 if (probe @ (point - pivot) - (point - pivot)).dot(want) > 0 else -1.0
    return Matrix.Rotation(math.radians(sgn * angle_deg), 3, axis)


def scapula_rotation(s, profile, angles=None):
    """World rotation (3x3, about the AC joint) of the runtime scapula `s` for the profile's ISB angles, or for explicit
    (internal, upward, tilt) degrees in `angles`."""
    if angles is not None:
        profile = {"scapula_internal_rotation_deg": angles[0], "scapula_upward_rotation_deg": angles[1],
                   "scapula_posterior_tilt_deg": angles[2]}
    f = _STATE["frames"][s]
    x, y, z = f["axes"]
    p = f["points"]
    lateral = Vector((1.0 if s == "r" else -1.0, 0.0, 0.0))
    anterior = Vector((0.0, -1.0, 0.0))
    ac = _STATE["ac_rest"][s]
    R1 = _signed(y, profile["scapula_internal_rotation_deg"], ac, p["AA"], anterior)
    x1, z1 = R1 @ x, R1 @ z
    AI1 = ac + R1 @ (p["AI"] - ac)
    R2 = _signed(x1, profile["scapula_upward_rotation_deg"], ac, AI1, lateral)
    z2 = R2 @ z1
    AI2 = ac + R2 @ (AI1 - ac)
    R3 = _signed(z2, profile["scapula_posterior_tilt_deg"], ac, AI2, anterior)
    return R3 @ R2 @ R1


def apply_coupled_pose_isb(result, ht_elevation_deg):
    coupled = _STATE["coupled"]
    profile = _STATE["orig"](result, ht_elevation_deg)        # clavicle + (wrong-frame) scapula + arm aim
    rig = result["runtime"]
    for s in ("r", "l"):
        sc = rig.pose.bones[f"scapula_{s}"]
        sc.matrix_basis.identity()
    bpy.context.view_layer.update()
    for s in ("r", "l"):
        sc = rig.pose.bones[f"scapula_{s}"]
        cl = rig.pose.bones[f"clavicle_{s}"]
        # rest -> clavicle-carried frame: the scapula with identity basis follows the clavicle rigidly
        carry = sc.matrix.to_3x3() @ rig.data.bones[f"scapula_{s}"].matrix_local.to_3x3().inverted()
        ac = cl.tail.copy()
        R = carry @ scapula_rotation(s, profile) @ carry.inverted()
        sc.matrix = Matrix.Translation(ac) @ R.to_4x4() @ Matrix.Translation(-ac) @ sc.matrix
    bpy.context.view_layer.update()
    elevation, plane = math.radians(profile["ht_elevation_deg"]), math.radians(profile["plane_deg"])
    for sign, name in ((1.0, "upperarm_r"), (-1.0, "upperarm_l")):          # re-aim exactly as the original
        bone = rig.pose.bones[name]
        pivot = bone.head.copy()
        current = (bone.tail - bone.head).normalized()
        target = Vector((sign * math.sin(elevation) * math.cos(plane), -math.sin(elevation) * math.sin(plane),
                         -math.cos(elevation)))
        corr = current.rotation_difference(target).to_matrix().to_4x4()
        bone.matrix = Matrix.Translation(pivot) @ corr @ Matrix.Translation(-pivot) @ bone.matrix
    bpy.context.view_layer.update()
    return dict(profile, scapula_drive="ISB anatomical frame (original_v1_scapula_isb_drive)")


def install(result):
    """Wrap the coupled pose in memory (idempotent).  Call after build_corrected_scene(), with the rig at rest."""
    import build_functional_original_coupled_motion_blender as coupled
    if _STATE.get("installed"):
        return
    rig = result["runtime"]
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    _STATE.update(coupled=coupled, orig=coupled.apply_coupled_pose, frames=rest_frames(),
                  ac_rest={s: rig.pose.bones[f"clavicle_{s}"].tail.copy() for s in ("r", "l")}, installed=True)
    coupled.apply_coupled_pose = apply_coupled_pose_isb


def taper_scapula_weights(result, r0=0.10, r1=0.18):
    """Diagnostic weight taper for the ISB drive: each vertex's scapula weight is kept in full within r0 of the AC joint
    (runtime clavicle tail, rest) and faded (smoothstep) to zero at r1; the removed weight goes to the thorax (spine_03,
    or spine_02 where that is already the vertex's spine influence).  Returns the number of vertices changed."""
    body, rig = result["body"], result["runtime"]
    names = {g.index: g.name for g in body.vertex_groups}
    G = body.vertex_groups
    moved = 0
    for s in ("r", "l"):
        ac = rig.data.bones[f"clavicle_{s}"].tail_local
        for v in body.data.vertices:
            w = {names[g.group]: g.weight for g in v.groups}
            ws = w.get(f"scapula_{s}", 0.0)
            if ws <= 0:
                continue
            d = (v.co - ac).length
            if d <= r0:
                continue
            u = min(1.0, (d - r0) / (r1 - r0))
            take = ws * u * u * (3 - 2 * u)
            G[f"scapula_{s}"].add([v.index], ws - take, "REPLACE")
            tgt = "spine_03" if "spine_03" in w or "spine_02" not in w else "spine_02"
            G[tgt].add([v.index], w.get(tgt, 0.0) + take, "REPLACE")
            moved += 1
    return moved
