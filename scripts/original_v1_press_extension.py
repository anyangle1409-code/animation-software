"""Full-range overhead press for the ORIGINAL_v1 review candidates (bpy; review only).  Owner, 14 Oct 2026, comparing the
press with a reference photo series: "Yes, start with A then do B" (A = finish the movement: near-vertical lockout and the
shoulder rise at the top).

The coupled shoulder profile (anatomy_fit/functional_original_coupled_motion.pose_profile, Work's, unchanged) and the humeral
axial hypothesis stop at 160 deg humerothoracic elevation, so the press ended with the arms in a wide V.  This module:
  * extends the coupled profile past 160 deg (review layer only): the girdle components keep moving in the same directions,
    linearly, by EXT_PER_20_DEG over 160 -> 180 deg (project-authored extrapolation of the Ludewig 2009 directions; no
    cohort fit); humeral external rotation stays at its 160 deg value;
  * adds an ACTIVE shoulder shrug (extra clavicle elevation about the SC joint) that a lifter adds at lockout - the upper
    trapezius bunching seen in the reference; it is part of the press path, not of the passive coupling;
  * defines the full press path: elevation 85 -> LOCKOUT_HT, elbow 100 -> 0 deg, shrug 0 -> SHRUG_MAX_DEG over the last
    40 % of the lift.
Hooked into original_v1_shoulder_r4 (the R4+ shoulder drive) through _S["extend"]; with the hook unset, and at <= 160 deg
with no shrug, every pose is identical to before.
"""
from __future__ import annotations

import math

import bpy

EXT_PER_20_DEG = {"clavicle_elevation_deg": 3.0, "clavicle_retraction_deg": 4.0, "clavicle_posterior_rotation_deg": 6.0,
                  "scapula_upward_rotation_deg": 8.0, "scapula_posterior_tilt_deg": 6.0, "scapula_internal_rotation_deg": 0.0}
LOCKOUT_HT = 172.0
START_HT, START_ELBOW = 85.0, 100.0
SHRUG_MAX_DEG = 12.0
SHRUG_FROM = 0.6
_STATE = {"shrug_deg": 0.0}


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def extend(result, profile, ht):
    """r4 hook: profile computed at min(ht, 160) -> extended profile at ht (+ shrug); re-poses the clavicles."""
    import build_functional_original_coupled_motion_blender as coupled
    extra = max(0.0, ht - 160.0) / 20.0
    shrug = _STATE["shrug_deg"]
    if extra == 0.0 and shrug == 0.0:
        return profile
    p = dict(profile)
    for k, v in EXT_PER_20_DEG.items():
        p[k] = profile[k] + v * extra
    p["clavicle_elevation_deg"] += shrug
    p["ht_elevation_deg"] = float(ht)
    p["press_extension"] = {"beyond_160_deg": round(ht - 160.0, 2) if ht > 160 else 0.0, "shrug_deg": shrug}
    rig = result["runtime"]
    for s in ("r", "l"):
        rig.pose.bones[f"clavicle_{s}"].matrix_basis = coupled.clavicle_basis(p, 1.0 if s == "r" else -1.0)
    bpy.context.view_layer.update()
    return p


def install():
    import original_v1_shoulder_r4 as r4
    if not r4._S.get("installed"):
        raise RuntimeError("the R4+ shoulder drive must be installed first (drives.setup)")
    r4._S["extend"] = extend


def apply_pose(result, ht, shrug_deg=0.0):
    """As build_functional_shoulder_correction_blender.apply_corrected_pose, for 0..180 deg and an optional shrug."""
    import build_functional_original_coupled_motion_blender as coupled
    import build_functional_shoulder_correction_blender as correction
    import functional_shoulder_correction as corr
    from mathutils import Matrix
    _STATE["shrug_deg"] = float(shrug_deg)
    external = corr.humeral_external_rotation_deg(min(ht, 160.0))
    profile = coupled.apply_coupled_pose(result, ht)
    runtime = result["runtime"]
    for side, name in correction.HUMERI:
        bone = runtime.pose.bones[name]
        d = (bone.tail - bone.head).normalized()
        current = corr.humeral_axial_angle_deg(tuple(d), tuple(bone.x_axis), profile["plane_deg"], side)
        target = result["humeral_rest_axial_deg"][name] + corr.external_rotation_sign(side) * external
        delta = math.radians(((target - current + 180.0) % 360.0) - 180.0)
        pivot = bone.head.copy()
        bone.matrix = Matrix.Translation(pivot) @ Matrix.Rotation(delta, 4, d) @ Matrix.Translation(-pivot) @ bone.matrix
        bpy.context.view_layer.update()
    _STATE["shrug_deg"] = 0.0
    return profile


def press_state(t):
    """Full press path at t in 0..1: (humerothoracic elevation, elbow flexion, shrug) in degrees."""
    k = _smooth(t)
    ht = START_HT + (LOCKOUT_HT - START_HT) * k
    elbow = START_ELBOW * (1.0 - k)
    shrug = SHRUG_MAX_DEG * _smooth((k - SHRUG_FROM) / (1.0 - SHRUG_FROM))
    return ht, elbow, shrug


def pose_press_full(result, t):
    import build_original_movement_benchmarks_blender as bench
    ht, elbow, shrug = press_state(t)
    rig = result["runtime"]
    bench._reset(rig)
    apply_pose(result, ht, shrug)
    for s in ("l", "r"):
        bench._rot(rig.pose.bones[f"forearm_{s}"], x=-elbow)
    bpy.context.view_layer.update()
    return {"humerothoracic_elevation": ht, "elbow_flexion": elbow, "shrug": shrug}
