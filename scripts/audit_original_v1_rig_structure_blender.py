"""Read-only complete rig structure audit for hgpt_canonical_v4_original.

Usage:
  blender --background --factory-startup <candidate.blend> \
    --python scripts/audit_original_v1_rig_structure_blender.py -- <out.json>

Never saves the .blend. Dumps every armature bone, parent relation, rest head/tail,
length, roll, local matrix, deform flag and mirror-pair checks. Intended for the
owner-mandated skeleton-motion lock before Phase 4.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not args:
    raise SystemExit("Usage: ... -- <out.json>")
OUT = Path(args[0]).resolve()

rig = bpy.data.objects.get("HGPT_CANONICAL_V4_ORIGINAL")
if rig is None or rig.type != "ARMATURE":
    raise SystemExit("HGPT_CANONICAL_V4_ORIGINAL armature not found")

source_path = Path(bpy.data.filepath).resolve()
if not source_path.exists():
    raise SystemExit("Candidate .blend path is not readable")


def vec(v):
    return [round(float(x), 9) for x in v]


def mat4(m):
    return [[round(float(m[r][c]), 9) for c in range(4)] for r in range(4)]


def mirror_name(name):
    if name.endswith("_l"):
        return name[:-2] + "_r"
    if name.endswith("_r"):
        return name[:-2] + "_l"
    return None


bones = []
by_name = {b.name: b for b in rig.data.bones}
flags = []
mirror_checks = []

for b in rig.data.bones:
    row = {
        "name": b.name,
        "parent": b.parent.name if b.parent else None,
        "use_deform": bool(b.use_deform),
        "length_m": round(float(b.length), 9),
        "head_local": vec(b.head_local),
        "tail_local": vec(b.tail_local),
        "roll_rad": round(float(b.roll), 9),
        "matrix_local": mat4(b.matrix_local),
        "children": [c.name for c in b.children],
    }
    bones.append(row)

    if b.length <= 1e-8:
        flags.append({"bone": b.name, "issue": "zero_or_near_zero_length"})

    mate_name = mirror_name(b.name)
    if mate_name and b.name.endswith("_l"):
        mate = by_name.get(mate_name)
        if mate is None:
            mirror_checks.append({"left": b.name, "right": mate_name, "status": "missing"})
            flags.append({"bone": b.name, "issue": "missing_mirror", "expected": mate_name})
            continue

        # Expected mirror plane is X=0. Compare left against reflected right.
        lh = Vector(b.head_local)
        lt = Vector(b.tail_local)
        rh = Vector(mate.head_local)
        rt = Vector(mate.tail_local)
        rhm = Vector((-rh.x, rh.y, rh.z))
        rtm = Vector((-rt.x, rt.y, rt.z))
        head_err = (lh - rhm).length
        tail_err = (lt - rtm).length
        length_err = abs(b.length - mate.length)
        parent_expected = mirror_name(b.parent.name) if b.parent else None
        parent_ok = (mate.parent.name if mate.parent else None) == parent_expected
        rec = {
            "left": b.name,
            "right": mate.name,
            "head_mirror_error_m": round(float(head_err), 9),
            "tail_mirror_error_m": round(float(tail_err), 9),
            "length_error_m": round(float(length_err), 9),
            "parent_mirror_ok": bool(parent_ok),
        }
        mirror_checks.append(rec)
        if max(head_err, tail_err, length_err) > 1e-5 or not parent_ok:
            flags.append({"bone": b.name, "issue": "mirror_asymmetry", **rec})

roots = [b.name for b in rig.data.bones if b.parent is None]
deform = [b.name for b in rig.data.bones if b.use_deform]

required_named_groups = {
    "spine_chain": ["root", "pelvis", "spine_01", "spine_02", "spine_03", "neck", "head"],
    "left_shoulder_chain": ["clavicle_l", "scapula_l", "upperarm_l", "forearm_l", "hand_l"],
    "right_shoulder_chain": ["clavicle_r", "scapula_r", "upperarm_r", "forearm_r", "hand_r"],
    "left_leg_chain": ["thigh_l", "shin_l", "foot_l", "toe_l"],
    "right_leg_chain": ["thigh_r", "shin_r", "foot_r", "toe_r"],
}
for group, names in required_named_groups.items():
    missing = [n for n in names if n not in by_name]
    if missing:
        flags.append({"group": group, "issue": "missing_expected_bones", "missing": missing})

result = {
    "schema_version": 1,
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "purpose": "complete read-only rig inventory / rest-axis / symmetry audit before skeleton-motion lock",
    "source_candidate": source_path.name,
    "source_candidate_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
    "rig_name": rig.name,
    "bone_count": len(rig.data.bones),
    "deform_bone_count": len(deform),
    "roots": roots,
    "deform_bones": deform,
    "bones": bones,
    "mirror_checks": mirror_checks,
    "flags": flags,
    "policy": "docs/SKELETON_HUMAN_MOVEMENT_AND_BONE_SUFFICIENCY_POLICY.md",
    "notes": [
        "This structural audit does not by itself prove anatomical movement correctness.",
        "Use together with skeleton-motion, continuous-motion and external-reference evidence.",
        "A bone-count mismatch or a mirror/axis defect must be reconciled before final skeleton lock.",
    ],
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print("RIG STRUCTURE AUDIT", OUT, "bones", len(bones), "flags", len(flags))
