"""Fail-closed grip/wrist recovery gate for ORIGINAL-v1.

The gate combines the existing whole-candidate regression comparison, the
read-only Blender grip/wrist diagnostic and explicit production-path visual
review for WB-GRP-009 and WB-WRI-010. It does not invent new biomechanical
thresholds from the diagnostic measurements and never grants production approval.
"""
from __future__ import annotations

import math
import re

REQUIRED_ISSUES = ("WB-GRP-009", "WB-WRI-010")
REQUIRED_POSES = ("grip", "curl_handle", "pullup_bar", "pushup_bottom")
HANDLE_POSES = ("curl_handle", "pullup_bar")
DIGITS = ("index", "middle", "ring", "pinky", "thumb")


def _sha256(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def validate_diagnostic(record: dict, expected_candidate_sha256: str) -> list[str]:
    errors: list[str] = []
    if record.get("schema_version") != 1 or record.get("status") != "GRIP_WRIST_DIAGNOSTIC":
        errors.append("diagnostic schema/status invalid")
    if record.get("production_approved") is not False:
        errors.append("diagnostic must not claim production approval")
    if record.get("source_candidate_sha256") != expected_candidate_sha256:
        errors.append("diagnostic candidate SHA differs")
    if record.get("saved_blend") is not False:
        errors.append("diagnostic must be read-only")
    if not _sha256(record.get("pose_definition_script_sha256")):
        errors.append("diagnostic pose-script SHA invalid")

    poses = record.get("poses")
    if not isinstance(poses, dict):
        return errors + ["diagnostic poses missing"]
    for pose in REQUIRED_POSES:
        row = poses.get(pose)
        if not isinstance(row, dict):
            errors.append("diagnostic pose missing: " + pose)
            continue
        for side in ("left", "right"):
            side_row = row.get(side)
            label = pose + ":" + side
            if not isinstance(side_row, dict):
                errors.append(label + ": side row missing")
                continue
            joints = side_row.get("joint_basis_rotation_deg")
            if not isinstance(joints, dict):
                errors.append(label + ": joint rotations missing")
            else:
                for digit in DIGITS:
                    bones = joints.get(digit)
                    if not isinstance(bones, dict) or len(bones) != 3 or any(not _finite(v) for v in bones.values()):
                        errors.append(label + ": invalid joint rotations for " + digit)
            for key in ("forearm_basis_rotation_deg", "hand_basis_rotation_deg", "forearm_to_hand_direction_deg"):
                if not _finite(side_row.get(key)):
                    errors.append(label + ": invalid " + key)
            for key in ("forearm_direction", "hand_direction", "palm_normal"):
                vec = side_row.get(key)
                if not isinstance(vec, list) or len(vec) != 3 or any(not _finite(v) for v in vec):
                    errors.append(label + ": invalid " + key)
            if pose in HANDLE_POSES:
                handle = side_row.get("handle")
                if not isinstance(handle, dict) or not _finite(handle.get("radius_m")):
                    errors.append(label + ": handle measurement missing")
                contacts = side_row.get("contacts")
                if not isinstance(contacts, dict):
                    errors.append(label + ": contact measurements missing")
                else:
                    for digit in DIGITS:
                        stats = contacts.get(digit)
                        if not isinstance(stats, dict):
                            errors.append(label + ": contact stats missing for " + digit)
                            continue
                        for key in (
                            "minimum_signed_distance_m",
                            "median_signed_distance_m",
                            "maximum_signed_distance_m",
                            "within_2mm_surface_fraction",
                        ):
                            if not _finite(stats.get(key)):
                                errors.append(label + ": invalid contact " + digit + ":" + key)
                        if not isinstance(stats.get("owned_vertex_count"), int) or stats["owned_vertex_count"] <= 0:
                            errors.append(label + ": invalid owned vertex count for " + digit)
    return list(dict.fromkeys(errors))


def validate_visual_review(record: dict, expected_candidate_sha256: str) -> list[str]:
    errors: list[str] = []
    if record.get("schema_version") != 1 or record.get("status") != "GRIP_WRIST_VISUAL_REVIEW":
        errors.append("visual review schema/status invalid")
    if record.get("production_approved") is not False:
        errors.append("visual review must not claim production approval")
    if record.get("candidate_sha256") != expected_candidate_sha256:
        errors.append("visual review candidate SHA differs")
    if not re.fullmatch(r"[0-9a-f]{40}", str(record.get("source_git_commit") or "")):
        errors.append("visual review source Git commit invalid")
    renders = record.get("renders")
    if not isinstance(renders, list) or not renders:
        errors.append("visual review renders missing")
    else:
        seen = set()
        for item in renders:
            if not isinstance(item, dict):
                errors.append("visual review render row invalid")
                continue
            if not _sha256(item.get("sha256")):
                errors.append("visual review render SHA invalid")
            pose, view, path = item.get("pose"), item.get("view"), item.get("path")
            if not all(isinstance(x, str) and x.strip() for x in (pose, view, path)):
                errors.append("visual review render identity invalid")
            key = (pose, view)
            if key in seen:
                errors.append("visual review duplicate pose/view")
            seen.add(key)

    for key in (
        "production_path_rendered",
        "visual_pass",
        "grip_contact_pass",
        "thumb_opposition_pass",
        "wrist_load_path_pass",
        "whole_body_regression_pass",
        "real_human_reference_checked",
    ):
        if record.get(key) is not True:
            errors.append("visual review " + key + " must be true")
    if record.get("required_issue_failures_remaining") != 0:
        errors.append("required grip/wrist issues remain")

    issue_rows = record.get("issue_reviews")
    by_id = {}
    if not isinstance(issue_rows, list):
        errors.append("visual review issue rows missing")
        issue_rows = []
    for row in issue_rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            errors.append("visual review issue row invalid")
            continue
        if row["id"] in by_id:
            errors.append("visual review duplicate issue: " + row["id"])
        by_id[row["id"]] = row
    for issue_id in REQUIRED_ISSUES:
        row = by_id.get(issue_id)
        if row is None:
            errors.append("visual review required issue missing: " + issue_id)
            continue
        if row.get("status") != "PASS":
            errors.append("visual review issue not passed: " + issue_id)
        if not isinstance(row.get("evidence_paths"), list) or not row["evidence_paths"]:
            errors.append("visual review issue evidence missing: " + issue_id)
        if not isinstance(row.get("human_evidence_ids"), list) or not row["human_evidence_ids"]:
            errors.append("visual review issue human evidence missing: " + issue_id)
        if not isinstance(row.get("review_note"), str) or not row["review_note"].strip():
            errors.append("visual review issue note missing: " + issue_id)
    return list(dict.fromkeys(errors))


def evaluate_gate(
    comparison: dict,
    diagnostic: dict,
    visual_review: dict,
    *,
    expected_candidate_sha256: str,
) -> dict:
    reasons: list[str] = []
    if comparison.get("status") == "REGRESSION" or int(comparison.get("regression_count", 0)) != 0:
        reasons.append("whole-candidate numerical regression present")
    base = comparison.get("baseline_failed_checks")
    cand = comparison.get("candidate_failed_checks")
    if not isinstance(base, int) or not isinstance(cand, int):
        reasons.append("comparison failed-check counts missing")
    elif cand > base:
        reasons.append("candidate failed-check count increased")
    reasons += ["diagnostic: " + x for x in validate_diagnostic(diagnostic, expected_candidate_sha256)]
    reasons += ["visual: " + x for x in validate_visual_review(visual_review, expected_candidate_sha256)]
    reasons = list(dict.fromkeys(reasons))
    return {
        "schema_version": 1,
        "status": "PASS" if not reasons else "BLOCKED",
        "grip_wrist_gate_pass": not reasons,
        "candidate_sha256": expected_candidate_sha256,
        "production_approved": False,
        "reasons": reasons,
        "rule": (
            "WB-GRP-009/WB-WRI-010 require a clean whole-candidate comparison, "
            "complete grip/wrist diagnostics and explicit production-path visual "
            "review against verified human evidence. Diagnostic measurements do "
            "not create new acceptance thresholds."
        ),
    }
