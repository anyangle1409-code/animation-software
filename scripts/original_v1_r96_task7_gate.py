"""Fail-closed promotion gate for ORIGINAL-v1 r96 Task 7 shoulder corrective work.

This module is intentionally Blender-free. It combines the existing numerical
comparison output with the Task 7 solve report and an explicit visual-review
record. It can never promote a candidate on numerical evidence alone.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Iterable

DEFAULT_REQUIRED_ISSUES = (
    "WB-AX-001",
    "WB-PEC-002",
    "WB-PEC-003",
    "WB-AX-004",
    "WB-SHO-005",
    "WB-SHO-006",
    "WB-CLV-007",
    "WB-SYM-008",
)


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _is_sha1(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def _sorted_unique_ints(value: object) -> bool:
    return (
        isinstance(value, list)
        and value
        and value == sorted(set(value))
        and all(isinstance(v, int) and v >= 0 for v in value)
    )


def validate_declaration(record: dict, expected_parent_sha256: str) -> list[str]:
    """Return declaration defects. Empty means safe to proceed with a solve."""
    problems: list[str] = []
    if not _is_sha256(expected_parent_sha256):
        problems.append("expected_parent_sha256_invalid")
        return problems
    if record.get("declared_before_edit") is not True:
        problems.append("declaration_not_pre_edit")
    if record.get("source_candidate_sha256") != expected_parent_sha256:
        problems.append("declaration_parent_mismatch")
    left = record.get("left_owned_vertex_ids")
    right = record.get("mirror_of_strict_left_vertex_ids")
    if not _sorted_unique_ints(left):
        problems.append("left_mask_invalid")
    if not _sorted_unique_ints(right):
        problems.append("right_mirror_mask_invalid")
    if isinstance(left, list) and isinstance(right, list) and set(left) & set(right):
        problems.append("left_right_masks_overlap")
    theta0 = record.get("theta0_deg")
    theta1 = record.get("theta1_deg")
    if (
        not isinstance(theta0, (int, float))
        or not isinstance(theta1, (int, float))
        or not math.isfinite(float(theta0))
        or not math.isfinite(float(theta1))
        or float(theta0) >= float(theta1)
    ):
        problems.append("activation_range_invalid")
    allowed = str(record.get("allowed_change", "")).lower()
    if "displacement" not in allowed or "shape key" not in allowed:
        problems.append("allowed_change_not_corrective_only")
    return problems


def validate_visual_review(
    record: dict,
    *,
    expected_parent_sha256: str,
    required_issue_ids: Iterable[str] = DEFAULT_REQUIRED_ISSUES,
) -> list[str]:
    """Validate the evidence binding of the explicit Task 7 anatomy review."""
    reasons: list[str] = []
    if record.get("schema_version") != 1:
        reasons.append("visual_review_schema_invalid")
    if record.get("status") != "TASK7_VISUAL_REVIEW":
        reasons.append("visual_review_status_invalid")
    if record.get("source_candidate_sha256") != expected_parent_sha256:
        reasons.append("visual_review_parent_mismatch")
    if not _is_sha256(record.get("candidate_sha256")):
        reasons.append("visual_review_candidate_sha_invalid")
    if not _is_sha1(record.get("source_git_commit")):
        reasons.append("visual_review_source_commit_invalid")

    renders = record.get("renders")
    if not isinstance(renders, list) or not renders:
        reasons.append("visual_review_renders_missing")
    else:
        seen = set()
        for item in renders:
            if not isinstance(item, dict):
                reasons.append("visual_review_render_row_invalid")
                continue
            path = item.get("path")
            sha = item.get("sha256")
            pose = item.get("pose")
            view = item.get("view")
            if not all(isinstance(v, str) and v.strip() for v in (path, pose, view)):
                reasons.append("visual_review_render_identity_invalid")
            if not _is_sha256(sha):
                reasons.append("visual_review_render_sha_invalid")
            key = (pose, view)
            if key in seen:
                reasons.append("visual_review_duplicate_pose_view")
            seen.add(key)

    required = set(required_issue_ids)
    issue_rows = record.get("issue_reviews")
    if not isinstance(issue_rows, list):
        reasons.append("visual_review_issue_rows_missing")
        issue_rows = []
    by_id = {}
    for row in issue_rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            reasons.append("visual_review_issue_row_invalid")
            continue
        issue_id = row["id"]
        if issue_id in by_id:
            reasons.append("visual_review_duplicate_issue:" + issue_id)
            continue
        by_id[issue_id] = row
    missing = sorted(required - set(by_id))
    if missing:
        reasons.append("unreviewed_required_issues:" + ",".join(missing))
    for issue_id in sorted(required & set(by_id)):
        row = by_id[issue_id]
        if row.get("status") != "PASS":
            reasons.append("visual_review_issue_not_passed:" + issue_id)
        if not isinstance(row.get("evidence_paths"), list) or not row["evidence_paths"]:
            reasons.append("visual_review_issue_evidence_missing:" + issue_id)
        if not isinstance(row.get("human_evidence_ids"), list) or not row["human_evidence_ids"]:
            reasons.append("visual_review_issue_human_evidence_missing:" + issue_id)
        note = row.get("review_note")
        if not isinstance(note, str) or not note.strip():
            reasons.append("visual_review_issue_note_missing:" + issue_id)

    return reasons


def evaluate_task7_gate(
    comparison: dict,
    solve_report: dict,
    visual_review: dict,
    *,
    expected_parent_sha256: str,
    required_issue_ids: Iterable[str] = DEFAULT_REQUIRED_ISSUES,
) -> dict:
    """Evaluate the r96 Task 7 promotion gate without weakening existing gates."""
    reasons: list[str] = []

    if comparison.get("status") == "REGRESSION":
        reasons.append("numerical_comparison_regression")
    if int(comparison.get("regression_count", 0)) != 0:
        reasons.append("numerical_regressions_present")
    baseline_failed = comparison.get("baseline_failed_checks")
    candidate_failed = comparison.get("candidate_failed_checks")
    if not isinstance(baseline_failed, int) or not isinstance(candidate_failed, int):
        reasons.append("failed_check_counts_missing")
    elif candidate_failed > baseline_failed:
        reasons.append("candidate_failed_checks_increased")

    if solve_report.get("source_candidate_sha256") != expected_parent_sha256:
        reasons.append("solve_parent_mismatch")
    delta = solve_report.get("max_abs_delta_m")
    if (
        not isinstance(delta, (int, float))
        or not math.isfinite(float(delta))
        or float(delta) < 0
    ):
        reasons.append("solve_delta_metric_invalid")
    if not solve_report.get("mask_file"):
        reasons.append("solve_mask_not_recorded")

    reasons.extend(
        validate_visual_review(
            visual_review,
            expected_parent_sha256=expected_parent_sha256,
            required_issue_ids=required_issue_ids,
        )
    )

    required_true = (
        "production_path_rendered",
        "visual_pass",
        "symmetry_pass",
        "arc_continuity_pass",
        "whole_body_regression_pass",
        "real_human_reference_checked",
    )
    for key in required_true:
        if visual_review.get(key) is not True:
            reasons.append(f"visual_review_{key}_not_passed")

    if visual_review.get("required_issue_failures_remaining") != 0:
        reasons.append("required_task7_shoulder_issues_remain")

    reasons = list(dict.fromkeys(reasons))
    return {
        "schema_version": 2,
        "status": "PASS" if not reasons else "BLOCKED",
        "production_approved": False,
        "task7_gate_pass": not reasons,
        "candidate_sha256": visual_review.get("candidate_sha256"),
        "source_candidate_sha256": expected_parent_sha256,
        "reasons": reasons,
        "rule": (
            "Task 7 requires zero material numerical regression AND explicit, "
            "candidate-bound production-path anatomical visual approval. "
            "This gate concerns the eight required Task 7 shoulder-complex issues only; other whole-body Critical/High blockers remain in the issue ledger and still block Phase 4. Numerical evidence alone can never promote r96."
        ),
    }


def _load(path: str) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"{path}: expected a JSON object")
    return data


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("comparison_json")
    ap.add_argument("solve_report_json")
    ap.add_argument("visual_review_json")
    ap.add_argument("--expected-parent", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()

    result = evaluate_task7_gate(
        _load(args.comparison_json),
        _load(args.solve_report_json),
        _load(args.visual_review_json),
        expected_parent_sha256=args.expected_parent,
    )
    payload = json.dumps(result, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
    print(payload, end="")
    raise SystemExit(0 if result["task7_gate_pass"] else 2)


if __name__ == "__main__":
    main()
