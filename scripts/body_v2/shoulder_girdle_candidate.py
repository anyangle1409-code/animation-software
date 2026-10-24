"""Candidate shoulder-girdle pose for the press (bpy) - CANDIDATE ONLY, the r57 coupled path is not changed.

Why: the r57 coupled path (build_functional_original_coupled_motion_blender.apply_coupled_pose) writes its six girdle
channels as bone-local Euler angles.  Measured on this rig, one channel at a time at +30 deg
(docs/R121_MOVEMENT_TRAJECTORIES_20261024.md):
  * "scapula_upward_rotation" moves the glenoid end DOWN 20 mm and the inferior end MEDIALLY 36 mm - downward rotation;
  * "scapula_posterior_tilt" moves the inferior end 37 mm POSTERIORLY (off the thorax) - anterior tilt;
  * "clavicle_posterior_rotation" turns the clavicle about its shaft and, the scapula being its rigid child, swings the
    scapula with it (inferior end 64 mm posterior, 56 mm up): the acromioclavicular joint does not transmit that roll.
Clavicle elevation (AC up) and retraction (AC back) move the AC joint the right way.

Here the same magnitudes (motion.pose_profile, unchanged) are applied about anatomical axes in the thorax frame:
  * clavicle: elevation and retraction about the sternoclavicular joint (the r57 local X / Z channels, verified above);
    its posterior axial rotation is kept on the clavicle bone (its own skin) but NOT passed to the scapula;
  * scapula (ISB Part II, Wu et al. 2005 - scapulothoracic angles): it follows the AC joint, and turns about the AC joint
    by posterior tilt (in-plane medio-lateral axis), upward rotation (axis normal to the scapular plane), internal
    rotation (vertical axis), each with its direction fixed by the anatomical sense - upward rotation swings the inferior
    angle laterally, posterior tilt brings it towards the thorax, internal rotation turns the glenoid forwards.  The
    scapular plane is taken 35 deg anterior to the frontal plane (the rig's three scapula points are nearly collinear).
  * humerus: the r57 target direction for the humerothoracic elevation in the 40 deg plane and its axial rotation
    (functional_shoulder_correction), applied after the girdle exactly as apply_corrected_pose does.
Magnitudes are the r57 project-authored profile (not a cohort fit); the directions are what this module corrects.
"""
import math

import bpy
from mathutils import Matrix, Vector

PLANE_DEG = 35.0


def _rot_about(pivot, axis, deg):
    return Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(deg), 4, axis.normalized()) @ Matrix.Translation(-pivot)


def _axes(rig, s):
    """thorax-frame axes for side s (rest armature space; the thorax is not moved by the press)"""
    lat = 1.0 if rig.data.bones[f"clavicle_{s}"].tail_local.x > 0 else -1.0
    a = math.radians(PLANE_DEG)
    normal = Vector((lat * math.sin(a), math.cos(a), 0.0))          # posterior normal of the scapular plane
    medlat = Vector((lat * math.cos(a), -math.sin(a), 0.0))         # in-plane, towards the acromion
    return lat, normal, medlat, Vector((0.0, 0.0, 1.0))


def _signed(rig, s, axis, pivot, probe, want):
    """sign for a rotation about axis such that the rest point probe moves along want"""
    p = rig.data.bones[f"scapula_{s}"]
    pt = {"AI": p.tail_local, "G": p.head_local}[probe]
    moved = _rot_about(pivot, axis, 5.0) @ pt
    return 1.0 if (moved - pt).dot(want) > 0 else -1.0


def apply_girdle(rig, profile):
    B = rig.data.bones
    for s in ("r", "l"):
        lat, normal, medlat, up = _axes(rig, s)
        cb = rig.pose.bones[f"clavicle_{s}"]
        sg = 1.0 if s == "r" else -1.0
        # clavicle: the verified r57 channels (elevation X, retraction Z) plus the axial roll on the clavicle itself
        cb.matrix_basis = (Matrix.Rotation(math.radians(sg * profile["clavicle_retraction_deg"]), 4, "Z")
                           @ Matrix.Rotation(math.radians(sg * profile["clavicle_posterior_rotation_deg"]), 4, "Y")
                           @ Matrix.Rotation(math.radians(profile["clavicle_elevation_deg"]), 4, "X"))
        bpy.context.view_layer.update()
        ac_rest = B[f"clavicle_{s}"].tail_local.copy()
        ac_now = cb.tail.copy()
        # scapula: rest orientation, turned about the AC joint in the thorax frame, then carried with the AC joint
        tilt_s = _signed(rig, s, medlat, ac_rest, "AI", Vector((0.0, -1.0, 0.0)))          # inferior angle forwards
        up_s = _signed(rig, s, normal, ac_rest, "AI", Vector((lat, 0.0, 0.0)))             # inferior angle laterally
        ir_s = _signed(rig, s, up, ac_rest, "G", Vector((0.0, -1.0, 0.0)))                 # glenoid forwards
        R = (_rot_about(ac_rest, up, ir_s * profile["scapula_internal_rotation_deg"])
             @ _rot_about(ac_rest, normal, up_s * profile["scapula_upward_rotation_deg"])
             @ _rot_about(ac_rest, medlat, tilt_s * profile["scapula_posterior_tilt_deg"]))
        sb = rig.pose.bones[f"scapula_{s}"]
        sb.matrix = Matrix.Translation(ac_now - ac_rest) @ R @ B[f"scapula_{s}"].matrix_local
        bpy.context.view_layer.update()


def apply_press_pose(rig, ht_elevation_deg, rest_axial_deg, axial=True):
    """girdle (above) + humerus as r57 apply_corrected_pose; rest_axial_deg as build_corrected_scene computes it"""
    import functional_original_coupled_motion as motion
    import functional_shoulder_correction as corr
    profile = motion.pose_profile(ht_elevation_deg)
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    apply_girdle(rig, profile)
    elevation = math.radians(profile["ht_elevation_deg"]); plane = math.radians(profile["plane_deg"])
    for side, sign, name in (("left", 1.0, "upperarm_r"), ("right", -1.0, "upperarm_l")):
        bone = rig.pose.bones[name]
        pivot = bone.head.copy(); cur = (bone.tail - bone.head).normalized()
        target = Vector((sign * math.sin(elevation) * math.cos(plane), -math.sin(elevation) * math.sin(plane), -math.cos(elevation)))
        bone.matrix = Matrix.Translation(pivot) @ cur.rotation_difference(target).to_matrix().to_4x4() @ Matrix.Translation(-pivot) @ bone.matrix
        bpy.context.view_layer.update()
        if axial:
            external = corr.humeral_external_rotation_deg(ht_elevation_deg)
            d = (bone.tail - bone.head).normalized()
            current = corr.humeral_axial_angle_deg(tuple(d), tuple(bone.x_axis), profile["plane_deg"], side)
            want = rest_axial_deg[name] + corr.external_rotation_sign(side) * external
            delta = ((want - current + 180.0) % 360.0) - 180.0
            piv = bone.head.copy()
            bone.matrix = Matrix.Translation(piv) @ Matrix.Rotation(math.radians(delta), 4, d) @ Matrix.Translation(-piv) @ bone.matrix
            bpy.context.view_layer.update()
    return profile
