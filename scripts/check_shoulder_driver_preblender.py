#!/usr/bin/env python3
"""Pre-Blender shoulder-complex structural/driver checks.

This is intentionally a static audit. It does not modify a .blend and does not
claim to replace the Blender bone-motion audit. It checks facts that are already
determinable from the exported skeleton + current pose driver:
  1) whether AC/scapular pivot and GH/upper-arm origin are collapsed;
  2) which shoulder-girdle DOFs are explicitly driven;
  3) whether elevation-dependent girdle outputs differ by plane;
  4) continuity/slope changes in the current piecewise scapular rule;
  5) current generic humeral axial-rotation rule by elevation.

Run from repository root:
  python scripts/check_shoulder_driver_preblender.py
"""
from __future__ import annotations
import json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKEL = ROOT / "ORIGINAL_V1_WORK/hgpt_canonical_v4_original_rev2c.json"
POSE = ROOT / "scripts/pose_test_original_v1_o4_candidate_blender.py"
R97_SCAP = ROOT / "scripts/r97/scapula_pivot.py"
R97_GH = ROOT / "scripts/r97/add_gh_helper.py"

ANGLES = (0, 30, 60, 90, 120, 150, 170)
PLANES = ("flexion", "scaption30", "abduction")


def dmm(a, b):
    return 1000.0 * math.sqrt(sum((x-y)**2 for x, y in zip(a, b)))


def scap_up(theta):
    if theta <= 30.0:
        return 0.025 * theta
    if theta <= 90.0:
        return 0.75 + 0.30 * (theta - 30.0)
    if theta <= 120.0:
        return 18.75 + 0.53 * (theta - 90.0)
    return 34.65 + 0.55 * (theta - 120.0)


def clav_elev(theta):
    return min(15.0, 0.09 * theta)


def humeral_er(theta):
    return min(80.0, 0.5 * max(0.0, theta - 30.0))


j = json.loads(SKEL.read_text(encoding="utf-8"))
bones = {b["name"]: b for b in j["bones"]}
pose_src = POSE.read_text(encoding="utf-8")
scap_src = R97_SCAP.read_text(encoding="utf-8")
gh_src = R97_GH.read_text(encoding="utf-8")

out = {"tests": []}

for side in ("l", "r"):
    c = bones[f"clavicle_{side}"]["tail"]
    u = bones[f"upperarm_{side}"]["head"]
    base_s = bones[f"scapula_{side}"]["head"]
    # r97 explicitly sets scapula head to clavicle tail.
    collapse = "off = cl.tail - sc.head" in scap_src and "sc.head += off" in scap_src
    out["tests"].append({
        "id": f"STRUCT_AC_GH_SEPARATION_{side.upper()}",
        "base_clavicle_tail_to_upperarm_head_mm": round(dmm(c, u), 4),
        "base_scapula_head_to_clavicle_tail_mm": round(dmm(base_s, c), 4),
        "r97_moves_scapula_head_to_clavicle_tail": collapse,
        "effective_r97_r98_ac_pivot_to_upperarm_head_mm": 0.0 if collapse and dmm(c,u) < 1e-6 else None,
        "result": "FAIL" if collapse and dmm(c,u) < 1e-6 else "REVIEW",
        "reason": "r97 labels scapula head as AC joint; add_gh_helper labels upperarm head as glenohumeral centre. They become coincident."
    })

explicit = {
    "clavicle_elevation": 'rot_toward(f"clavicle_{s}", F' in pose_src,
    "scapula_upward_rotation": 'rot_toward(f"scapula_{s}", F' in pose_src,
    "clavicle_retraction_protraction": False,
    "clavicle_axial_rotation": False,
    "scapula_posterior_anterior_tilt": False,
    "scapula_internal_external_rotation": False,
}
out["tests"].append({
    "id": "DRIVER_EXPLICIT_DOF_COVERAGE",
    "explicitly_driven": explicit,
    "result": "FAIL",
    "reason": "Current girdle driver explicitly commands only clavicle elevation and scapular upward rotation."
})

sweep = []
for a in ANGLES:
    row = {
        "elevation_deg": a,
        "clavicle_elevation_deg": round(clav_elev(a), 3),
        "scapular_upward_rotation_deg": round(scap_up(a), 3),
        "generic_humeral_external_rotation_deg": round(humeral_er(a), 3),
        "identical_driver_values_for_flexion_scaption_abduction": True,
    }
    sweep.append(row)
out["tests"].append({
    "id": "PLANE_DEPENDENCY",
    "samples": sweep,
    "result": "FAIL",
    "reason": "At the same elevation the current girdle and straight-arm axial-rotation formulas return the same values for every elevation plane."
})

eps = 1e-4
boundaries = []
for b in (30.0, 90.0, 120.0):
    left = (scap_up(b) - scap_up(b-eps))/eps
    right = (scap_up(b+eps) - scap_up(b))/eps
    boundaries.append({"boundary_deg": b, "left_slope": round(left,3), "right_slope": round(right,3), "slope_jump": round(right-left,3)})
out["tests"].append({
    "id": "SCAPULAR_RULE_SMOOTHNESS",
    "boundaries": boundaries,
    "position_continuous": True,
    "velocity_slope_continuous": False,
    "result": "FAIL_FOR_PRODUCTION_SMOOTHNESS",
    "reason": "The piecewise rule is C0-continuous but not C1-continuous; the contribution rate jumps at interval boundaries."
})

out["tests"].append({
    "id": "R97_GH_HELPER_SEMANTICS",
    "gh_helper_uses_upperarm_head": "h.head = ua.head.copy()" in gh_src,
    "gh_helper_documented_as_glenohumeral_centre": "glenohumeral centre" in gh_src,
    "result": "PASS_EVIDENCE",
    "reason": "Confirms the project itself treats upperarm head as the GH centre, making the AC/GH collapse test meaningful."
})

print(json.dumps(out, indent=2))
