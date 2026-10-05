#!/usr/bin/env python3
"""Validate the authoritative ORIGINAL-v1 human-body master plan.

This verifier is intentionally fail-closed. It proves plan structure and that the
current whole-body issue state cannot silently authorize a later master stage.
It does not edit the model or infer owner/production acceptance.
"""
from __future__ import annotations
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "ORIGINAL_V1_HUMAN_BODY_MASTER_PLAN.json"
ISSUES = ROOT / "ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json"
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def finite(v, where="root"):
    if isinstance(v, float) and not math.isfinite(v):
        raise ValueError(f"{where}: non-finite number")
    if isinstance(v, dict):
        for k, x in v.items():
            finite(x, f"{where}.{k}")
    elif isinstance(v, list):
        for i, x in enumerate(v):
            finite(x, f"{where}[{i}]")


def validate_plan(plan):
    finite(plan)
    if plan.get("schema_version") != 1:
        raise ValueError("plan schema_version must be 1")
    if plan.get("status") != "AUTHORITATIVE_HUMAN_BODY_MASTER_PLAN":
        raise ValueError("unexpected master-plan status")
    if plan.get("production_approved") is not False:
        raise ValueError("master plan may not claim production approval")
    if plan.get("asset") != "HomeGymPT_Male_ORIGINAL_v1":
        raise ValueError("unexpected asset")
    if plan.get("rig") != "hgpt_canonical_v4_original":
        raise ValueError("unexpected rig")

    stages = plan.get("stages") or []
    ids = [x.get("id") for x in stages]
    if ids != list(range(1, 15)):
        raise ValueError("master stages must be exactly 1..14 in order")
    if stages[0].get("state") != "active":
        raise ValueError("Stage 1 must currently be active")
    if stages[4].get("state") != "blocked":
        raise ValueError("Stage 5 high-detail anatomy must currently be blocked")

    regions = [x.get("id") for x in plan.get("body_regions") or []]
    if len(regions) < 12 or len(regions) != len(set(regions)):
        raise ValueError("body-region coverage incomplete or duplicated")
    mandatory = {
        "chest_anterior_axilla", "back_posterior_axilla",
        "clavicle_shoulder_deltoid", "forearm_wrist",
        "palm_thumb_fingers", "pelvis_groin_glutes",
        "thigh_knee", "foot_toes",
    }
    if not mandatory.issubset(regions):
        raise ValueError("mandatory body regions missing")

    moves = plan.get("movement_families") or []
    if len(moves) < 20 or len(moves) != len(set(moves)):
        raise ValueError("movement-family coverage incomplete or duplicated")
    required_moves = {
        "shoulder_flexion_elevation", "shoulder_abduction_elevation",
        "vertical_push", "vertical_pull_hang", "horizontal_push",
        "horizontal_pull", "forearm_pronation_supination",
        "wrist_flexion_extension_loaded", "cylindrical_equipment_grip",
        "trunk_axial_rotation", "loaded_hip_hinge",
        "squat_deep_bilateral_flexion", "split_stance_lunge",
        "ankle_dorsiflexion", "loaded_foot_toe_contact",
    }
    if not required_moves.issubset(moves):
        raise ValueError("mandatory movement families missing")

    if plan.get("default_motion_sampling") != ["start","25%","50%","75%","end","return"]:
        raise ValueError("default motion sampling contract differs")
    sweep = plan.get("current_special_sweeps") or {}
    if sweep.get("shoulder_elevation_degrees") != [0,45,90,120,150,170]:
        raise ValueError("shoulder elevation sweep contract differs")
    if sweep.get("both_sides_required") is not True or sweep.get("return_required") is not True:
        raise ValueError("shoulder sweep must require both sides and return")

    pos = plan.get("current_position") or {}
    if pos.get("master_stage") != 1:
        raise ValueError("current master stage must be 1")
    if pos.get("comparator_revision") != "r95":
        raise ValueError("current comparator revision differs")
    if not SHA_RE.fullmatch(str(pos.get("comparator_sha256",""))):
        raise ValueError("current comparator SHA missing/invalid")
    if "continue Stage1 rather_than_jump_to_Stage5" not in (pos.get("next_sequence") or []):
        raise ValueError("current sequence does not explicitly forbid jumping to Stage 5")

    policy = plan.get("defect_policy") or {}
    if set(policy.get("blocking_severities") or []) != {"Critical","High"}:
        raise ValueError("blocking severity contract differs")
    if set(policy.get("blocking_states") or []) != {"Open","In Progress","Pending Review"}:
        raise ValueError("blocking-state contract differs")
    return plan


def issue_summary(plan, ledger):
    finite(ledger)
    candidate = ledger.get("candidate_under_review") or {}
    blocking_sev = set(plan["defect_policy"]["blocking_severities"])
    blocking_states = set(plan["defect_policy"]["blocking_states"])
    issues = ledger.get("issues") or []
    blockers = [
        row for row in issues
        if row.get("severity") in blocking_sev and row.get("state") in blocking_states
    ]
    return {
        "candidate_revision": candidate.get("revision"),
        "candidate_sha256": candidate.get("sha256"),
        "total_issues": len(issues),
        "blocking_issues": len(blockers),
        "blocking_ids": [x.get("id") for x in blockers],
    }


def next_action(plan, ledger):
    summary = issue_summary(plan, ledger)
    if summary["blocking_issues"]:
        return {
            "master_stage": 1,
            "stage_name": "Human movement foundation",
            "high_detail_anatomy_allowed": False,
            "reason": "Critical/High whole-body blockers remain open.",
            "blocking_issue_ids": summary["blocking_ids"],
            "next_action": plan["current_position"]["next_sequence"][0],
            "next_sequence": plan["current_position"]["next_sequence"],
        }
    return {
        "master_stage": 1,
        "stage_name": "Human movement foundation",
        "high_detail_anatomy_allowed": False,
        "reason": "No blocking issue is open, but Stage 1-4 exit evidence must still be explicitly verified before Stage 5.",
        "blocking_issue_ids": [],
        "next_action": "verify Stage 1 exit evidence and proceed through Stages 2-4; do not infer Stage 5 readiness",
        "next_sequence": plan["current_position"]["next_sequence"],
    }


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        plan = validate_plan(read(PLAN))
        ledger = read(ISSUES)
        action = next_action(plan, ledger)
        print("HUMAN BODY MASTER PLAN: PASS")
        print(json.dumps(action, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print("STOP — " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
