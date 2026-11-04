"""Shared arm posing for the Meshy rig copy (same rules as meshy_pose_test_blender.py) + corrective-key drive rule."""
import math

import bpy
from mathutils import Matrix, Vector


def _ctx(rig):
    MW = rig.matrix_world
    return rig.pose.bones, MW, MW.to_3x3().inverted(), (lambda v: MW @ v)


def subtree(rig, root):
    pb = rig.pose.bones
    return [root] + [c.name for c in pb[root].children_recursive]


def rot_rigid(rig, names, piv_w, axis_w, deg):
    pb, MW, W2A, _ = _ctx(rig)
    piv = W2A @ (Vector(piv_w) - MW.translation); R = Matrix.Rotation(math.radians(deg), 4, (W2A @ Vector(axis_w)).normalized())
    D = Matrix.Translation(piv) @ R @ Matrix.Translation(-piv); mats = {n: pb[n].matrix.copy() for n in names}
    for n in names:
        pb[n].matrix = D @ mats[n]; bpy.context.view_layer.update()


def aim(rig, root, bone, target_w):
    pb, _, _, wp = _ctx(rig)
    b = pb[bone]; cur = (wp(b.tail) - wp(b.head)).normalized(); tgt = Vector(target_w).normalized(); ax = cur.cross(tgt)
    if ax.length > 1e-7:
        rot_rigid(rig, subtree(rig, root), wp(b.head), ax, math.degrees(cur.angle(tgt)))


def arm_pose(rig, sd, elev, fwd, elbow, clav):
    pb, _, _, wp = _ctx(rig)
    lat = 1.0 if wp(pb[f"upperarm_{sd}"].head).x > 0 else -1.0
    if clav:
        rot_rigid(rig, subtree(rig, f"clavicle_{sd}"), wp(pb[f"clavicle_{sd}"].head), Vector((0, -lat, 0)), clav)
    e, p_ = math.radians(elev), math.radians(fwd)
    aim(rig, f"upperarm_{sd}", f"upperarm_{sd}", Vector((lat * math.sin(e) * math.cos(p_), -math.sin(e) * math.sin(p_), -math.cos(e))))
    u = (wp(pb[f"upperarm_{sd}"].tail) - wp(pb[f"upperarm_{sd}"].head)).normalized()
    ref = Vector((0, 0, 1)) if elev > 30 else Vector((0, -1, 0))
    w = ref - u * ref.dot(u); w = w.normalized() if w.length > 1e-4 else Vector((0, -1, 0))
    fl = math.radians(180 - elbow); fdir = u * math.cos(fl) + w * math.sin(fl)
    aim(rig, f"forearm_{sd}", f"forearm_{sd}", fdir)
    aim(rig, f"hand_{sd}", f"hand_{sd}", fdir)


def rest_capture(rig):
    return {n: p.matrix_basis.copy() for n, p in rig.pose.bones.items()}


def rest_restore(rig, rest):
    for n, m in rest.items():
        rig.pose.bones[n].matrix_basis = m
    bpy.context.view_layer.update()


def humerus_elevation(rig, sd):
    """angle (deg) of the upper arm from straight down, in world space; the corrective-key driver input"""
    pb, _, _, wp = _ctx(rig)
    u = (wp(pb[f"upperarm_{sd}"].tail) - wp(pb[f"upperarm_{sd}"].head)).normalized()
    return math.degrees(Vector((0, 0, -1)).angle(u))


def elevation_plane(rig, sd):
    """plane of elevation (deg): 0 = arm raised sideways in the frontal plane, 90 = raised straight forwards"""
    pb, _, _, wp = _ctx(rig)
    u = (wp(pb[f"upperarm_{sd}"].tail) - wp(pb[f"upperarm_{sd}"].head))
    return math.degrees(math.atan2(max(-u.y, 0.0), abs(u.x) + 1e-9))


def smoothstep(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)


def corrective_weights(elev):
    """CORR_SH_MID: 0 below 55 deg, peak 1 at 105, back to 0 at 170; CORR_SH_TOP: 0 at 105, 1 at 170"""
    mid = smoothstep((elev - 55) / 50) if elev <= 105 else 1 - smoothstep((elev - 105) / 65)
    return {"CORR_SH_MID": mid, "CORR_SH_TOP": smoothstep((elev - 105) / 65)}


def apply_correctives(rig, body):
    """the keys are shared by both shoulders: drive by the mean elevation of the two arms (poses here are symmetric)"""
    ks = body.data.shape_keys
    if ks is None:
        return {}
    elev = 0.5 * (humerus_elevation(rig, "l") + humerus_elevation(rig, "r")); w = corrective_weights(elev)
    # the keys were built for scapular-plane (press) elevation: fade them out for a forward raise (own key needed)
    plane = 0.5 * (elevation_plane(rig, "l") + elevation_plane(rig, "r")); gate = 1 - smoothstep((plane - 45) / 30)
    w = {k: v * gate for k, v in w.items()}
    for k, v in w.items():
        if k in ks.key_blocks:
            ks.key_blocks[k].value = v
    bpy.context.view_layer.update(); return {"elevation_deg": round(elev, 1), "plane_deg": round(plane, 1), "gate": round(gate, 3), **{k: round(v, 3) for k, v in w.items()}}
