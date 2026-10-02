"""Read-only skeleton-motion audit for ORIGINAL v1 Phase 3/4 validation.

Usage:
  blender --background --factory-startup <candidate.blend> \
    --python scripts/audit_original_v1_skeleton_motion_blender.py -- \
    <out.json> [pose,pose,...]

This script never saves the .blend. It reuses the exact pose constructors from
pose_test_original_v1_o4_candidate_blender.py, then records bone directions,
joint-chain angles and support-orientation diagnostics with the body deformation
removed from the question.

Purpose:
  distinguish a rig/pose/constraint error from a skinning/topology error before
  Phase 4 deformation freeze.

The automated finger check is intentionally narrow: in an intended flexed grip,
a distal interphalangeal bend that reverses sign relative to the preceding bend
is flagged for inspection. This is not a full anatomical-range validator; human
range/reference evidence remains required by
docs/EXTERNAL_HUMAN_MOVEMENT_REFERENCE_POLICY.md.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not args:
    raise SystemExit("Usage: ... -- <out.json> [pose,pose,...]")
OUT = Path(args[0]).resolve()
ONLY = set(args[1].split(",")) if len(args) > 1 and args[1] else None

pose_script = Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py")
src = pose_script.read_text(encoding="utf-8")
src_defs = src[:src.index("# ---------------------------------------------------------------- metrics")]
tmp = tempfile.mkdtemp()
saved_argv = sys.argv
sys.argv = ["blender", "--", tmp, ""]
ns = {"__name__": "pose_defs", "__file__": pose_script.name}
exec(compile(src_defs, "pose_test_defs", "exec"), ns)
sys.argv = saved_argv

rig = ns["rig"]
_mask = ns["body"].modifiers.get("HGPT_DRESSED_MASK")   # the pose script's closing search expects the undressed body
if _mask is not None:
    _mask.show_viewport = False
    _mask.show_render = False
POSES = ns["POSES"]
pb = ns["pb"]
reset = ns["reset"]
upd = ns["upd"]
palm_normal = ns["palm_normal"]

F = Vector((0, -1, 0))
D = Vector((0, 0, -1))


def v3(v):
    return [round(float(x), 7) for x in v]


def direction(name):
    p = pb(name)
    d = p.tail - p.head
    if d.length < 1e-12:
        return Vector((0, 0, 0))
    return d.normalized()


def angle_deg(a, b):
    if a.length < 1e-12 or b.length < 1e-12:
        return None
    return round(math.degrees(a.angle(b)), 5)


def signed_angle_deg(a, b, axis):
    """Signed angle from a to b about axis, in degrees."""
    if a.length < 1e-12 or b.length < 1e-12 or axis.length < 1e-12:
        return None
    aa = a.normalized()
    bb = b.normalized()
    ax = axis.normalized()
    y = ax.dot(aa.cross(bb))
    x = max(-1.0, min(1.0, aa.dot(bb)))
    return round(math.degrees(math.atan2(y, x)), 5)


def bone_record(name):
    p = pb(name)
    return {
        "head": v3(p.head),
        "tail": v3(p.tail),
        "direction": v3(direction(name)),
        "parent": p.parent.name if p.parent else None,
    }


def rest_finger_axes():
    """Hinge axis per finger in the hand bone's local frame, taken ONCE from the neutral rest pose (finger direction x palm normal)."""
    reset()
    out = {}
    for side in "lr":
        hand_inv = pb(f"hand_{side}").matrix.to_3x3().inverted()
        for finger in ("index", "middle", "ring", "pinky"):
            out[(side, finger)] = hand_inv @ direction(f"{finger}_01_{side}").cross(palm_normal(side)).normalized()
    return out


REST_FINGER_AXES = rest_finger_axes()


def finger_chain_record(side, finger):
    """Joint bends about the FIXED hinge axis (the parallel-hinge model). The earlier version re-derived the axis from each already
    curled segment (d x palm_normal), which flips sign once the cumulative curl passes 90 degrees: a reversed distal bend then
    still read as positive and no reversal was ever flagged (and a correct deep curl was flagged). See
    scripts/audit_original_v1_finger_flexion_blender.py for the full per-joint report incl. the metacarpal->proximal joint."""
    n1 = f"{finger}_01_{side}"
    n2 = f"{finger}_02_{side}"
    n3 = f"{finger}_03_{side}"
    d1, d2, d3 = direction(n1), direction(n2), direction(n3)
    axis = (pb(f"hand_{side}").matrix.to_3x3() @ REST_FINGER_AXES[(side, finger)]).normalized()
    a12 = signed_angle_deg(d1, d2, axis)
    a23 = signed_angle_deg(d2, d3, axis)
    reversal = (a12 is not None and a23 is not None and (a12 < -2.0 or a23 < -2.0))
    return {
        "bones": [n1, n2, n3],
        "proximal_to_middle_signed_deg": a12,
        "middle_to_distal_signed_deg": a23,
        "distal_bend_sign_reversal": bool(reversal),
        "segment_directions": [v3(d1), v3(d2), v3(d3)],
    }


def thumb_chain_record(side):
    names = [f"thumb_01_{side}", f"thumb_02_{side}", f"thumb_03_{side}"]
    ds = [direction(n) for n in names]
    return {
        "bones": names,
        "segment_angles_deg": [angle_deg(ds[0], ds[1]), angle_deg(ds[1], ds[2])],
        "segment_directions": [v3(d) for d in ds],
    }


def support_record(side):
    hand = direction(f"hand_{side}")
    forearm = direction(f"forearm_{side}")
    foot = direction(f"foot_{side}")
    toe = direction(f"toe_{side}")
    pn = palm_normal(side)
    return {
        "palm_normal": v3(pn),
        "palm_normal_to_down_deg": angle_deg(pn, D),
        "hand_direction": v3(hand),
        "hand_direction_to_character_forward_deg": angle_deg(hand, F),
        "forearm_direction": v3(forearm),
        "forearm_to_hand_deg": angle_deg(forearm, hand),
        "foot_direction": v3(foot),
        "toe_direction": v3(toe),
        "foot_to_toe_deg": angle_deg(foot, toe),
    }


def shoulder_record(side):
    names = [f"clavicle_{side}", f"scapula_{side}", f"upperarm_{side}", f"forearm_{side}"]
    return {
        "bones": {n: bone_record(n) for n in names},
        "clavicle_to_upperarm_deg": angle_deg(direction(names[0]), direction(names[2])),
        "scapula_to_upperarm_deg": angle_deg(direction(names[1]), direction(names[2])),
        "upperarm_to_forearm_deg": angle_deg(direction(names[2]), direction(names[3])),
    }


source_path = Path(bpy.data.filepath).resolve()
if not source_path.exists():
    raise SystemExit("Candidate .blend path is not readable.")

result = {
    "schema_version": 1,
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "purpose": "read-only skeleton/pose diagnostic before ORIGINAL v1 Phase 4 deformation freeze",
    "source_candidate": source_path.name,
    "source_candidate_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
    "pose_definition_script": pose_script.name,
    "pose_definition_script_sha256": hashlib.sha256(pose_script.read_bytes()).hexdigest(),
    "reference_policy": "docs/EXTERNAL_HUMAN_MOVEMENT_REFERENCE_POLICY.md",
    "notes": [
        "This report does not validate anatomy ranges by itself.",
        "Finger sign-reversal flags identify suspicious chain direction only.",
        "Compare skeleton-only results with external human reference, then compare the skinned mesh separately.",
    ],
    "poses": [],
    "flags": [],
}

for pose_name, fn in POSES.items():
    if ONLY and pose_name not in ONLY:
        continue
    reset()
    rig.location = (0, 0, 0)
    rig.rotation_euler = (0, 0, 0)
    upd()
    ns["HANDLE"].clear()
    fn()
    upd()

    pose = {
        "pose": pose_name,
        "hands": {},
        "support": {},
        "shoulders": {},
    }
    for side in "lr":
        fingers = {
            f: finger_chain_record(side, f)
            for f in ("index", "middle", "ring", "pinky")
        }
        pose["hands"][side] = {
            "palm_normal": v3(palm_normal(side)),
            "fingers": fingers,
            "thumb": thumb_chain_record(side),
        }
        pose["support"][side] = support_record(side)
        pose["shoulders"][side] = shoulder_record(side)

        if pose_name in {"curl_peak", "grip", "curl_handle", "pullup_bar", "pullup_top", "pullup_hang", "pullup_hang_rhythm"}:
            for finger, rec in fingers.items():
                if rec["distal_bend_sign_reversal"]:
                    result["flags"].append({
                        "severity": "inspect_pre_freeze",
                        "pose": pose_name,
                        "side": side,
                        "chain": finger,
                        "issue": "distal_bend_sign_reversal",
                        "detail": "distal bend sign opposes preceding flexion bend; inspect bone axes/pose/limits before blaming skinning",
                    })

    result["poses"].append(pose)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print("SKELETON MOTION AUDIT", OUT, "poses", len(result["poses"]), "flags", len(result["flags"]))
