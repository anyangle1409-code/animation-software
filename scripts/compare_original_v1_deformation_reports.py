#!/usr/bin/env python3
"""Compare two ORIGINAL v1 deformation reports without hiding regressions.

The selected acceptance profile is evaluated for both reports. A candidate is a
REGRESSION if any pose gains failed checks, if a required baseline pose is
missing, or if grip failures increase. It is IMPROVED when there are no
regressions and the total failed-check count decreases.

This is intentionally based on gate failures rather than a single blended score:
an improvement in one body region must not numerically cancel a new blocker in
another region.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
EVAL_PATH = HERE / "evaluate_original_v1_deformation_report.py"
MOD_SPEC = importlib.util.spec_from_file_location("deformation_eval", EVAL_PATH)
if MOD_SPEC is None or MOD_SPEC.loader is None:
    raise RuntimeError(f"unable to load {EVAL_PATH}")
deval = importlib.util.module_from_spec(MOD_SPEC)
MOD_SPEC.loader.exec_module(deval)


def pose_failure_counts(report: list[dict[str, Any]], limits: dict[str, Any]) -> dict[str, int]:
    result: dict[str, int] = {}
    for pose in report:
        name = str(pose.get("pose", "<unnamed>"))
        result[name] = len(deval.evaluate_pose(pose, limits))
    return result


def grip_failure_counts(report: list[dict[str, Any]] | None, limits: dict[str, Any]) -> dict[str, int]:
    if not report:
        return {}
    result: dict[str, int] = {}
    for item in report:
        name = str(item.get("pose", "<unnamed>"))
        result[name] = len(deval.evaluate_grip([item], limits))
    return result


def compare_counts(base: dict[str, int], cand: dict[str, int], kind: str) -> list[dict[str, Any]]:
    regressions: list[dict[str, Any]] = []
    for name, old in sorted(base.items()):
        if name not in cand:
            regressions.append(
                {
                    "kind": kind,
                    "name": name,
                    "baseline_failed_checks": old,
                    "candidate_failed_checks": None,
                    "reason": "missing_from_candidate",
                }
            )
            continue
        new = cand[name]
        if new > old:
            regressions.append(
                {
                    "kind": kind,
                    "name": name,
                    "baseline_failed_checks": old,
                    "candidate_failed_checks": new,
                    "reason": "failed_check_count_increased",
                }
            )
    return regressions


def load_optional(path: Path | None) -> list[dict[str, Any]] | None:
    if path is None:
        return None
    data = deval.load_json(path)
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON list")
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline_pose_report", type=Path)
    parser.add_argument("candidate_pose_report", type=Path)
    parser.add_argument("--spec", type=Path, default=deval.DEFAULT_SPEC)
    parser.add_argument("--profile", default="development_blocker")
    parser.add_argument("--baseline-grip-report", type=Path)
    parser.add_argument("--candidate-grip-report", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()

    try:
        spec = deval.load_json(args.spec)
        profiles = spec.get("profiles", {})
        if args.profile not in profiles:
            raise ValueError(f"unknown profile {args.profile!r}")
        limits = profiles[args.profile]

        baseline = load_optional(args.baseline_pose_report)
        candidate = load_optional(args.candidate_pose_report)
        assert baseline is not None and candidate is not None

        base_grip = load_optional(args.baseline_grip_report)
        cand_grip = load_optional(args.candidate_grip_report)
        if (base_grip is None) != (cand_grip is None):
            raise ValueError("supply both baseline and candidate grip reports, or neither")

        base_pose_counts = pose_failure_counts(baseline, limits)
        cand_pose_counts = pose_failure_counts(candidate, limits)
        base_grip_counts = grip_failure_counts(base_grip, limits)
        cand_grip_counts = grip_failure_counts(cand_grip, limits)

        regressions = compare_counts(base_pose_counts, cand_pose_counts, "pose")
        regressions += compare_counts(base_grip_counts, cand_grip_counts, "grip")

        baseline_total = sum(base_pose_counts.values()) + sum(base_grip_counts.values())
        candidate_total = sum(cand_pose_counts.values()) + sum(cand_grip_counts.values())

        if regressions:
            status = "REGRESSION"
        elif candidate_total < baseline_total:
            status = "IMPROVED"
        else:
            status = "UNCHANGED"

        result = {
            "schema_version": 1,
            "profile": args.profile,
            "status": status,
            "baseline_failed_checks": baseline_total,
            "candidate_failed_checks": candidate_total,
            "delta_failed_checks": candidate_total - baseline_total,
            "pose_failure_counts_baseline": base_pose_counts,
            "pose_failure_counts_candidate": cand_pose_counts,
            "grip_failure_counts_baseline": base_grip_counts,
            "grip_failure_counts_candidate": cand_grip_counts,
            "regressions": regressions,
            "rule": "No pose or grip may gain gate failures while repairing another region.",
        }
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    output = json.dumps(result, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(output, encoding="utf-8")
    print(
        f"{status}: baseline {baseline_total} failed checks; "
        f"candidate {candidate_total}; delta {candidate_total - baseline_total:+d}."
    )
    for regression in regressions:
        print(
            "  "
            f"{regression['kind']} {regression['name']}: "
            f"{regression['baseline_failed_checks']} -> "
            f"{regression['candidate_failed_checks']} "
            f"({regression['reason']})"
        )

    if args.report_only:
        return 0
    return 1 if status == "REGRESSION" else 0


if __name__ == "__main__":
    raise SystemExit(main())
