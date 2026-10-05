"""Read-only pose -> anatomical-coupling review scope audit.

Never saves the Blend.

Usage:
  blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
    --python scripts/audit_original_v1_pose_coupling_scope_blender.py -- ^
    <out.json> [pose,pose,...]

The script reuses the current ORIGINAL-v1 pose definitions, records every pose
bone whose matrix_basis differs materially from identity, matches those bones
against ORIGINAL_V1_JOINT_TISSUE_TRIGGER_MAP.json, and emits the complete set of
anatomical coupling systems that MUST be reviewed for that pose.

This does not judge whether deformation is good. It prevents a pose from being
reviewed only at the visibly moving limb while connected tissue chains are
silently ignored.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import tempfile
from pathlib import Path

import bpy
from mathutils import Matrix

ARGS=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if not ARGS:
    raise SystemExit("Usage: ... -- <out.json> [pose,pose,...]")
OUT=Path(ARGS[0]).resolve()
if OUT.exists():
    raise SystemExit(f"Refusing to overwrite {OUT}")
POSE_FILTER=ARGS[1].split(",") if len(ARGS)>1 and ARGS[1] else None

ROOT=Path(__file__).resolve().parents[1]
TRIGGER_PATH=ROOT/"ORIGINAL_V1_JOINT_TISSUE_TRIGGER_MAP.json"
COUPLING_PATH=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json"
POSE_SCRIPT=Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py")

trigger=json.loads(TRIGGER_PATH.read_text(encoding="utf-8"))
coupling=json.loads(COUPLING_PATH.read_text(encoding="utf-8"))
known_coupling={x["id"] for x in coupling["coupling_systems"]}

src=POSE_SCRIPT.read_text(encoding="utf-8")
marker="# ---------------------------------------------------------------- metrics"
if marker not in src:
    raise SystemExit("pose script metrics marker missing")
saved=sys.argv
sys.argv=["blender","--",tempfile.mkdtemp(),""]
ns={"__name__":"pose_defs","__file__":POSE_SCRIPT.name}
exec(compile(src[:src.index(marker)],"pose_test_defs","exec"),ns)

# Install evaluation-time flexion/scapular drivers so pose replay follows the
# same production review path where those keys/configs exist.
import importlib.util as _ilu
fd_path=POSE_SCRIPT.with_name("original_v1_flexion_driver.py")
spec=_ilu.spec_from_file_location("original_v1_flexion_driver",str(fd_path))
fd=_ilu.module_from_spec(spec)
spec.loader.exec_module(fd)
fd.install(ns)
sys.argv=saved

rig=ns["rig"]
POSES=ns["POSES"]
reset=ns["reset"]
upd=ns["upd"]

pose_names=list(POSES)
if POSE_FILTER is not None:
    unknown=[p for p in POSE_FILTER if p not in POSES]
    if unknown:
        raise SystemExit(f"unknown poses: {unknown}")
    pose_names=POSE_FILTER

rules=[]
for row in trigger["rules"]:
    compiled=[re.compile(p) for p in row["bone_patterns"]]
    systems=list(row["required_coupling_system_ids"])
    if not set(systems).issubset(known_coupling):
        raise SystemExit(f"trigger {row['id']} references unknown coupling system")
    rules.append((row,compiled))

def bone_motion_record(p):
    # matrix_basis is identity for rest. Use numerical-noise-only thresholds:
    # they are NOT anatomy thresholds and only distinguish exact/noise identity.
    t=p.matrix_basis.to_translation()
    q=p.matrix_basis.to_quaternion()
    q.normalize()
    angle=math.degrees(q.angle)
    trans=float(t.length)
    moved=angle>1e-7 or trans>1e-9
    return {
        "bone":p.name,
        "rotation_deg":round(float(angle),9),
        "translation_m":round(trans,12),
        "moved":bool(moved),
    }

candidate=Path(bpy.data.filepath)
candidate_sha=hashlib.sha256(candidate.read_bytes()).hexdigest()
result={
    "schema_version":1,
    "status":"READ_ONLY_POSE_COUPLING_SCOPE",
    "candidate":candidate.name,
    "candidate_sha256":candidate_sha,
    "pose_definition_script":POSE_SCRIPT.name,
    "pose_definition_script_sha256":hashlib.sha256(POSE_SCRIPT.read_bytes()).hexdigest(),
    "trigger_map":"ORIGINAL_V1_JOINT_TISSUE_TRIGGER_MAP.json",
    "trigger_map_sha256":hashlib.sha256(TRIGGER_PATH.read_bytes()).hexdigest(),
    "coupling_map":"ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json",
    "coupling_map_sha256":hashlib.sha256(COUPLING_PATH.read_bytes()).hexdigest(),
    "poses":{},
    "source_saved_or_modified":False,
}

for pose_name in pose_names:
    reset()
    rig.location=(0,0,0)
    if "HANDLE" in ns:
        ns["HANDLE"].clear()
    POSES[pose_name]()
    upd()

    motion=[bone_motion_record(p) for p in rig.pose.bones]
    moved=[x for x in motion if x["moved"]]
    matches=[]
    required=set()
    for row,patterns in rules:
        bones=sorted({m["bone"] for m in moved if any(p.fullmatch(m["bone"]) for p in patterns)})
        if bones:
            systems=list(row["required_coupling_system_ids"])
            required.update(systems)
            matches.append({
                "trigger_rule_id":row["id"],
                "joint_family":row["joint_family"],
                "matched_bones":bones,
                "required_coupling_system_ids":systems,
                "rationale":row["rationale"],
            })
    # Keep authoritative coupling order rather than set/alphabetical order.
    ordered=[x["id"] for x in coupling["coupling_systems"] if x["id"] in required]
    result["poses"][pose_name]={
        "moved_bone_count":len(moved),
        "moved_bones":moved,
        "trigger_matches":matches,
        "required_coupling_system_ids":ordered,
        "required_coupling_system_count":len(ordered),
        "review_rule":"Every listed coupling system is mandatory review scope for this pose; absence from candidate evidence makes the pose anatomically incomplete.",
    }
    print("POSE COUPLING SCOPE",pose_name,"moved",len(moved),"systems",len(ordered))

reset()
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print("POSE COUPLING SCOPE WRITTEN",OUT)
