"""Read-only shoulder-complex overhead kinematics audit.

Run from Blender on a candidate .blend:

blender --background --factory-startup <candidate.blend> \
  --python scripts/audit_shoulder_complex_overhead_blender.py -- <out.json>

The script never saves the .blend. It samples the CURRENT generic shoulder driver at
0/30/60/90/120/150/170 degrees in flexion, 30-degree scaption and abduction,
then records the actual 3-D bone transforms. It does not judge skin, weights or shape keys.

This audit intentionally records raw transforms before hard-coding literature ranges.
The review layer can then compare them with sourced human kinematic envelopes.
"""
from __future__ import annotations

import json
import math
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not args:
    raise SystemExit("Usage: ... -- <out.json>")
OUT = Path(args[0]).resolve()

pose_script = Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py")
src = pose_script.read_text(encoding="utf-8")
src_defs = src[:src.index("# ---------------------------------------------------------------- metrics")]

saved_argv = sys.argv
sys.argv = ["blender", "--", tempfile.mkdtemp(), ""]
ns = {"__name__": "shoulder_pose_defs", "__file__": str(pose_script)}
exec(compile(src_defs, str(pose_script), "exec"), ns)
sys.argv = saved_argv

rig = ns["rig"]
reset = ns["reset"]
upd = ns["upd"]
aim = ns["aim"]
girdle_for_elevation = ns["girdle_for_elevation"]
external_rotation_for_elevation = ns["external_rotation_for_elevation"]
lat = ns["lat"]

F = ns["F"]
U = ns["U"]
D = ns["D"]

ANGLES = [0, 30, 60, 90, 120, 150, 170]
PLANES = ("flexion", "scaption30", "abduction")


def horizontal_direction(side: str, plane: str) -> Vector:
    lateral = lat(side).normalized()
    if plane == "flexion":
        return F.normalized()
    if plane == "abduction":
        return lateral
    if plane == "scaption30":
        # 30 degrees anterior to the frontal plane.
        return (lateral * math.cos(math.radians(30.0)) +
                F.normalized() * math.sin(math.radians(30.0))).normalized()
    raise ValueError(plane)


def target_for(side: str, plane: str, elevation_deg: float) -> Vector:
    h = horizontal_direction(side, plane)
    a = math.radians(elevation_deg)
    return (D * math.cos(a) + h * math.sin(a)).normalized()


def rest3(name: str) -> Matrix:
    return rig.data.bones[name].matrix_local.to_3x3()


def world_q(name: str) -> Quaternion:
    p = rig.pose.bones[name]
    return (p.matrix.to_3x3() @ rest3(name).inverted()).to_quaternion()


def joint_q(name: str) -> Quaternion:
    q = world_q(name)
    p = rig.pose.bones[name]
    if p.parent is not None:
        q = world_q(p.parent.name).inverted() @ q
    q.normalize()
    return q


def quat_rotvec_deg(q: Quaternion) -> list[float]:
    q = q.copy()
    q.normalize()
    axis, angle = q.to_axis_angle()
    if angle > math.pi:
        angle -= 2.0 * math.pi
    v = axis * math.degrees(angle)
    return [round(float(v.x), 5), round(float(v.y), 5), round(float(v.z), 5)]


def armature_point_to_world(v: Vector) -> list[float]:
    p = rig.matrix_world @ v
    return [round(float(p.x), 6), round(float(p.y), 6), round(float(p.z), 6)]


def bone_snapshot(name: str) -> dict:
    p = rig.pose.bones[name]
    qj = joint_q(name)
    qw = world_q(name)
    return {
        "parent": p.parent.name if p.parent else None,
        "head_world_m": armature_point_to_world(p.head),
        "tail_world_m": armature_point_to_world(p.tail),
        "joint_rotvec_world_axes_deg": quat_rotvec_deg(qj),
        "world_rotvec_deg": quat_rotvec_deg(qw),
        "joint_quaternion_wxyz": [
            round(float(qj.w), 8), round(float(qj.x), 8),
            round(float(qj.y), 8), round(float(qj.z), 8)
        ],
    }


def upperarm_twist_deg(side: str) -> float:
    name = f"upperarm_{side}"
    q = joint_q(name)
    axis = (rig.data.bones[name].tail_local - rig.data.bones[name].head_local).normalized()
    v = Vector((q.x, q.y, q.z))
    proj = axis * v.dot(axis)
    tw = Quaternion((q.w, proj.x, proj.y, proj.z))
    if tw.magnitude < 1e-12:
        return 0.0
    tw.normalize()
    a = 2.0 * math.atan2(Vector((tw.x, tw.y, tw.z)).dot(axis), tw.w)
    a = (a + math.pi) % (2.0 * math.pi) - math.pi
    return round(math.degrees(a), 5)


def relative_head_in_scapula(side: str) -> list[float]:
    scap = rig.pose.bones[f"scapula_{side}"]
    hum = rig.pose.bones[f"upperarm_{side}"]
    local = scap.matrix.inverted() @ hum.head
    return [round(float(local.x), 6), round(float(local.y), 6), round(float(local.z), 6)]


def sample(side: str, plane: str, elevation_deg: float) -> dict:
    reset()
    rig.location = (0, 0, 0)
    target = target_for(side, plane, elevation_deg)

    # Exercise the current generic model, not an exercise-name pose.
    girdle_for_elevation(side, target, 1.0)
    aim(f"upperarm_{side}", target)
    external_rotation_for_elevation(side)
    upd()

    bones = [f"clavicle_{side}", f"scapula_{side}", f"upperarm_{side}"]
    for optional in (f"glenohumeral_ref_{side}", f"glenohumeral_half_{side}"):
        if optional in rig.pose.bones:
            bones.append(optional)

    return {
        "side": side,
        "plane": plane,
        "target_elevation_deg": elevation_deg,
        "target_world": [round(float(x), 7) for x in target],
        "driver_nominals": {
            "clavicle_elevation_deg": round(min(15.0, 0.09 * elevation_deg), 5),
            "scapular_upward_rotation_deg": round(float(ns["scapular_upward_rotation"](elevation_deg)), 5),
            "scapular_rule_is_extrapolated_above_120": bool(elevation_deg > 120.0),
            "humeral_external_rotation_rule_deg": round(min(80.0, 0.5 * max(0.0, elevation_deg - 30.0)), 5),
        },
        "upperarm_joint_twist_deg": upperarm_twist_deg(side),
        "upperarm_head_in_scapula_frame_m": relative_head_in_scapula(side),
        "bones": {name: bone_snapshot(name) for name in bones},
    }


result = {
    "schema_version": 1,
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "purpose": "bone-only shoulder-complex overhead biomechanics audit",
    "read_only": True,
    "candidate": Path(bpy.data.filepath).name,
    "pose_definition_script": pose_script.name,
    "angles_deg": ANGLES,
    "planes": list(PLANES),
    "scaption_definition": "30 degrees anterior to frontal plane",
    "current_driver_structure": {
        "explicit_clavicle_dofs": ["elevation"],
        "explicit_scapula_dofs": ["upward_rotation"],
        "explicit_upperarm_dofs": ["elevation_aim", "elevation_coupled_axial_rotation"],
        "not_explicitly_driven": [
            "clavicle_retraction_protraction",
            "clavicle_posterior_axial_rotation",
            "scapular_posterior_anterior_tilt",
            "scapular_internal_external_rotation",
            "plane_specific_humeral_axial_rotation_profile",
        ],
        "known_project_heuristics": [
            "clavicle elevation = min(15 deg, 0.09 * humerothoracic elevation)",
            "scapular upward-rotation curve is extrapolated above 120 deg at slope 0.55",
            "straight-arm humeral external rotation = min(80 deg, 0.5 * (elevation - 30 deg))",
        ],
    },
    "samples": [],
}

for side in ("l", "r"):
    for plane in PLANES:
        for angle in ANGLES:
            result["samples"].append(sample(side, plane, float(angle)))

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print("SHOULDER COMPLEX AUDIT", OUT, "samples", len(result["samples"]))
