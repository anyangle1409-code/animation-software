"""Read-only ORIGINAL-v1 grip/wrist diagnostic for Blender.

Usage:
  blender --background <candidate.blend> --python scripts/audit_original_v1_grip_wrist_blender.py -- <out.json> [pose,pose,...]

The diagnostic does not save the Blend. It reuses the authoritative production
pose definitions and records per-digit joint rotations, handle contact distances,
palm orientation and forearm/hand alignment for the grip/wrist recovery.

These values are measurements, not new acceptance thresholds.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import tempfile

import bpy
import numpy as np

SCRIPT = Path(__file__).resolve()
POSE_SCRIPT = SCRIPT.with_name("pose_test_original_v1_o4_candidate_blender.py")
DEFAULT_POSES = ("grip", "curl_handle", "pullup_bar", "pushup_bottom")

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not args:
    raise SystemExit("output JSON path required")
OUT = Path(args[0]).resolve()
POSE_LIST = tuple(x for x in (args[1].split(",") if len(args) > 1 else DEFAULT_POSES) if x)
if OUT.exists():
    raise SystemExit("STOP — output collision; preserve existing diagnostic")

src = POSE_SCRIPT.read_text(encoding="utf-8")
marker = "# ---------------------------------------------------------------- metrics"
if marker not in src:
    raise SystemExit("authoritative pose script metrics marker missing")
saved_argv = sys.argv
sys.argv = ["blender", "--", tempfile.mkdtemp(), ""]
ns = {"__name__": "pose_defs", "__file__": str(POSE_SCRIPT)}
try:
    exec(compile(src[:src.index(marker)], "pose_test_defs", "exec"), ns)
finally:
    sys.argv = saved_argv

# Install the same flexion-corrective driver layer used by the production pose
# audit. It is a no-op for candidates that do not contain the keys.
fd_path = POSE_SCRIPT.with_name("original_v1_flexion_driver.py")
if fd_path.is_file():
    spec = importlib.util.spec_from_file_location("original_v1_flexion_driver", str(fd_path))
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    module.install(ns)

rig = ns["rig"]
body = ns["body"]
POSES = ns["POSES"]
reset = ns["reset"]
upd = ns["upd"]
pb = ns["pb"]
bdir = ns["bdir"]
palm_normal = ns["palm_normal"]
HANDLE = ns["HANDLE"]
handle_distance = ns["handle_distance"]
evaluated_positions = ns["evaluated_positions"]
bone_vertex_sets = ns["bone_vertex_sets"]
HANDLE_RADIUS = float(ns["HANDLE_RADIUS"])

mask = body.modifiers.get("HGPT_DRESSED_MASK")
if mask is not None:
    mask.show_viewport = False
    mask.show_render = False

OWNERS = bone_vertex_sets()


def q_angle_deg(name: str) -> float:
    return math.degrees(pb(name).matrix_basis.to_quaternion().angle)


def v3(vec) -> list[float]:
    return [round(float(vec[i]), 8) for i in range(3)]


def digit_chain(finger: str, side: str) -> list[str]:
    return [f"{finger}_0{k}_{side}" for k in (1, 2, 3)]


def contact_stats(chain: list[str], side: str) -> dict | None:
    ids = sorted({vertex for bone in chain for vertex in OWNERS.get(bone, [])})
    if not ids or side not in HANDLE:
        return None
    distances = np.asarray(handle_distance(evaluated_positions(ids), side), dtype=float)
    return {
        "owned_vertex_count": len(ids),
        "minimum_signed_distance_m": round(float(distances.min()), 8),
        "median_signed_distance_m": round(float(np.median(distances)), 8),
        "maximum_signed_distance_m": round(float(distances.max()), 8),
        "inside_handle_vertex_count": int((distances < 0.0).sum()),
        "within_2mm_surface_vertex_count": int((np.abs(distances) <= 0.002).sum()),
        "within_2mm_surface_fraction": round(float((np.abs(distances) <= 0.002).mean()), 6),
    }


def side_row(side: str) -> dict:
    joints = {}
    contacts = {}
    for finger in ("index", "middle", "ring", "pinky"):
        chain = digit_chain(finger, side)
        joints[finger] = {bone: round(q_angle_deg(bone), 5) for bone in chain}
        stats = contact_stats(chain, side)
        if stats is not None:
            contacts[finger] = stats
    thumb_chain = digit_chain("thumb", side)
    joints["thumb"] = {bone: round(q_angle_deg(bone), 5) for bone in thumb_chain}
    thumb_stats = contact_stats(thumb_chain, side)
    if thumb_stats is not None:
        contacts["thumb"] = thumb_stats

    forearm_dir = bdir(f"forearm_{side}").normalized()
    hand_dir = bdir(f"hand_{side}").normalized()
    return {
        "joint_basis_rotation_deg": joints,
        "contacts": contacts,
        "forearm_basis_rotation_deg": round(q_angle_deg(f"forearm_{side}"), 5),
        "hand_basis_rotation_deg": round(q_angle_deg(f"hand_{side}"), 5),
        "forearm_to_hand_direction_deg": round(math.degrees(forearm_dir.angle(hand_dir)), 5),
        "forearm_direction": v3(forearm_dir),
        "hand_direction": v3(hand_dir),
        "palm_normal": v3(palm_normal(side).normalized()),
        "handle": (
            {
                "center": [round(float(x), 8) for x in HANDLE[side][0]],
                "axis": [round(float(x), 8) for x in HANDLE[side][1]],
                "radius_m": HANDLE_RADIUS,
            }
            if side in HANDLE else None
        ),
    }


candidate = Path(bpy.data.filepath)
result = {
    "schema_version": 1,
    "status": "GRIP_WRIST_DIAGNOSTIC",
    "production_approved": False,
    "source_candidate": candidate.name,
    "source_candidate_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
    "pose_definition_script_sha256": hashlib.sha256(POSE_SCRIPT.read_bytes()).hexdigest(),
    "saved_blend": False,
    "poses": {},
    "measurement_note": (
        "Bone basis rotation magnitudes/contact distances are diagnostics only. "
        "They do not establish anatomy acceptance without production-path visual "
        "review against verified human evidence."
    ),
}

for pose_name in POSE_LIST:
    if pose_name not in POSES:
        raise SystemExit("unknown pose: " + pose_name)
    reset()
    rig.location = (0, 0, 0)
    HANDLE.clear()
    POSES[pose_name]()
    upd()
    result["poses"][pose_name] = {
        "left": side_row("l"),
        "right": side_row("r"),
    }

reset()
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print("GRIP WRIST DIAGNOSTIC", OUT)
