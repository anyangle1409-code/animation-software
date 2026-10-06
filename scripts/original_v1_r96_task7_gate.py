"""Fail-closed promotion gate for ORIGINAL-v1 r96 Task 7 shoulder corrective work.

This module is intentionally Blender-free. It combines the existing numerical
comparison output with the Task 7 solve report and an explicit visual-review
record. It can never promote a candidate on numerical evidence alone.
"""
from __future__ import annotations

import argparse
import json
import math
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
    return isinstance(value, str) and len(value) == 64 and all(
        ch in "0123456789abcdef" for ch in value.lower()
    )


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

    if visual_review.get("critical_high_remaining") != 0:
        reasons.append("critical_or_high_shoulder_issues_remain")

    reviewed = set(visual_review.get("reviewed_issue_ids", []))
    missing = sorted(set(required_issue_ids) - reviewed)
    if missing:
        reasons.append("unreviewed_required_issues:" + ",".join(missing))

    return {
        "schema_version": 1,
        "status": "PASS" if not reasons else "BLOCKED",
        "production_approved": False,
        "task7_gate_pass": not reasons,
        "reasons": reasons,
        "rule": (
            "Task 7 requires zero material numerical regression AND explicit "
            "production-path anatomical visual approval; numerical evidence "
            "alone can never promote r96."
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
