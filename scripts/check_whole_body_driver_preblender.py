#!/usr/bin/env python3
"""Static whole-body skeleton/driver audit. Read-only; no Blender required."""
from __future__ import annotations
import json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sk=json.loads((ROOT/"ORIGINAL_V1_WORK/hgpt_canonical_v4_original_rev2c.json").read_text(encoding="utf-8"))
pose=(ROOT/"scripts/pose_test_original_v1_o4_candidate_blender.py").read_text(encoding="utf-8")
names={b["name"] for b in sk["bones"]}

def present(pattern):
    return sorted(n for n in names if re.search(pattern,n))

tests=[]

def add(i,status,evidence,meaning):
    tests.append({"id":i,"status":status,"evidence":evidence,"meaning":meaning})

add("CERVICAL_SEGMENTATION","REVIEW",
    {"neck_bones":present(r"^neck"),"head_bones":present(r"^head")},
    "Current rig has one neck segment plus head; test whether upper-cervical axial rotation and lower-cervical flexion/extension need separate controls.")

add("ELBOW_FOREARM_STRUCTURE","REVIEW",
    {"upperarm":present(r"^upperarm_"),"forearm":present(r"^forearm_[lr]$"),
     "forearm_twist_helpers":present(r"^forearm_tw")},
    "Gross elbow and forearm rotation are represented, but radius/ulna are not separate anatomical segments; validate carrying angle and pronation/supination axis.")

add("WRIST_STRUCTURE","HIGH_PRIORITY_REVIEW",
    {"hand":present(r"^hand_"),"carpal_named_bones":present(r"carpal|scaphoid|lunate|triquet|capitate|hamate|trapez")},
    "A single hand bone represents gross wrist motion; no explicit radiocarpal/midcarpal stage exists.")

add("LONG_FINGER_STRUCTURE","STRUCTURE_PRESENT_MOTION_REVIEW",
    {"metacarpals":present(r"^metacarpal_"),"phalanges":present(r"^(index|middle|ring|pinky)_0[123]_")},
    "Long-finger segment count is broadly adequate for MCP/PIP/DIP motion; movement coupling still needs revalidation.")

uniform_finger = all(s in pose for s in ('("index", "middle", "ring", "pinky")','((1, 70), (2, 88), (3, 55))'))
add("LONG_FINGER_GRIP_DRIVER","FAIL" if uniform_finger else "REVIEW",
    {"uniform_fixed_angles_detected":uniform_finger},
    "Current generic grip uses the same MCP/PIP/DIP flexion recipe for all four long fingers.")

thumb_parallel = "thumb MCP/IP joints are parallel hinges too" in pose
add("THUMB_OPPOSITION_DRIVER","FAIL" if thumb_parallel else "REVIEW",
    {"parallel_hinge_model_detected":thumb_parallel,"thumb_bones":present(r"^thumb_")},
    "Thumb opposition is multi-axis; current generic driver explicitly treats the chain as parallel hinges.")

add("HIP_STRUCTURE","REVIEW",
    {"pelvis":present(r"^pelvis$"),"thigh":present(r"^thigh_"),"femoral_head_or_neck_helpers":present(r"femoral|hip_")},
    "Single thigh-at-pelvis ball-joint representation may be sufficient if the joint centre is correct; verify it dynamically.")

add("KNEE_STRUCTURE","HIGH_PRIORITY_REVIEW",
    {"thigh":present(r"^thigh_"),"shin":present(r"^shin_"),"patella":present(r"patella|kneecap"),
     "knee_helpers":present(r"knee")},
    "No patella or dedicated coupled knee mechanism is represented in the canonical skeleton.")

knee_explicit_twist = bool(re.search(r'rot\(f?"shin_',pose))
add("KNEE_COUPLED_ROTATION_DRIVER","REVIEW" if knee_explicit_twist else "FAIL",
    {"explicit_shin_axial_rotation_in_pose_driver":knee_explicit_twist},
    "Squat/lunge currently aim the shin but do not clearly encode native coupled tibial axial rotation/screw-home behaviour.")

add("LOWER_LEG_STRUCTURE","REVIEW",
    {"shin":present(r"^shin_"),"tibia_named":present(r"tibia"),"fibula_named":present(r"fibula")},
    "Tibia/fibula are collapsed to one shin segment; verify whether this abstraction preserves knee/ankle landmarks and deformation.")

add("ANKLE_HINDFOOT_STRUCTURE","FAIL_FOR_FULL_COMPLEX",
    {"foot":present(r"^foot_"),"talus":present(r"talus"),"calcaneus_or_heel":present(r"calcane|heel"),"subtalar":present(r"subtalar")},
    "One foot segment represents the ankle/hindfoot; talocrural and subtalar functions cannot be independently controlled.")

add("FOREFOOT_TOE_STRUCTURE","HIGH_PRIORITY_REVIEW",
    {"toe":present(r"^toe_"),"hallux":present(r"hallux|bigtoe"),"lesser_toe":present(r"toe.*[2-5]|lesser")},
    "All toes are represented as one toe segment per foot; hallux cannot move independently from lesser toes.")

out={"schema_version":1,"skeleton_revision":sk.get("revision"),"bone_count":sk.get("bone_count"),"tests":tests}
print(json.dumps(out,indent=2))
