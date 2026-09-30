#!/usr/bin/env python3
"""Compare two ORIGINAL v1 deformation reports without hiding regressions.

A candidate is a REGRESSION if:
- a baseline pose/grip disappears;
- any pose/grip gains acceptance-gate failures; or
- deformation severity gets materially worse beyond the explicit comparison
  tolerances, even when the failed-check count stays unchanged.

A candidate is IMPROVED when there are no regressions and either the total
failed-check count drops or at least one tracked severity metric materially
improves. No blended quality score is used: an improvement in one region cannot
cancel a new regression elsewhere.
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
                    "metric": "failed_check_count",
                    "baseline": old,
                    "candidate": None,
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
                    "metric": "failed_check_count",
                    "baseline": old,
                    "candidate": new,
                    "reason": "failed_check_count_increased",
                }
            )
    return regressions


def index_by_pose(report: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for item in report:
        name = str(item.get("pose", "<unnamed>"))
        if name in indexed:
            raise ValueError(f"duplicate pose {name!r} in report")
        indexed[name] = item
    return indexed


def change(
    kind: str,
    name: str,
    metric: str,
    baseline: float,
    candidate: float,
    direction: str,
    tolerance: float,
    region: str | None = None,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "name": name,
        "region": region,
        "metric": metric,
        "baseline": baseline,
        "candidate": candidate,
        "delta": candidate - baseline,
        "direction": direction,
        "tolerance": tolerance,
    }


def compare_pose_severity(
    baseline_report: list[dict[str, Any]],
    candidate_report: list[dict[str, Any]],
    tolerances: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    regressions: list[dict[str, Any]] = []
    improvements: list[dict[str, Any]] = []
    base = index_by_pose(baseline_report)
    cand = index_by_pose(candidate_report)

    def lower_is_better(
        name: str,
        metric: str,
        old: float,
        new: float,
        tol: float,
        region: str | None = None,
    ) -> None:
        if new > old + tol:
            regressions.append(change("severity", name, metric, old, new, "lower_is_better", tol, region))
        elif new < old - tol:
            improvements.append(change("severity", name, metric, old, new, "lower_is_better", tol, region))

    def higher_is_better(
        name: str,
        metric: str,
        old: float,
        new: float,
        tol: float,
        region: str | None = None,
    ) -> None:
        if new < old - tol:
            regressions.append(change("severity", name, metric, old, new, "higher_is_better", tol, region))
        elif new > old + tol:
            improvements.append(change("severity", name, metric, old, new, "higher_is_better", tol, region))

    for name, old in sorted(base.items()):
        new = cand.get(name)
        if new is None:
            continue  # missing poses are already handled by compare_counts()

        old_volume_dev = abs(float(old["volume_ratio"]) - 1.0)
        new_volume_dev = abs(float(new["volume_ratio"]) - 1.0)
        lower_is_better(
            name,
            "volume_deviation_from_1",
            old_volume_dev,
            new_volume_dev,
            float(tolerances["volume_deviation_from_1_rise"]),
        )
        higher_is_better(
            name,
            "edge_ratio_p01",
            float(old["edge_ratio_p01"]),
            float(new["edge_ratio_p01"]),
            float(tolerances["edge_ratio_p01_drop"]),
        )
        lower_is_better(
            name,
            "edge_ratio_p99",
            float(old["edge_ratio_p99"]),
            float(new["edge_ratio_p99"]),
            float(tolerances["edge_ratio_p99_rise"]),
        )
        lower_is_better(
            name,
            "self_intersecting_face_pairs",
            float(old["self_intersecting_face_pairs"]),
            float(new["self_intersecting_face_pairs"]),
            float(tolerances["self_intersecting_face_pairs_rise"]),
        )
        higher_is_better(
            name,
            "lowest_z",
            float(old["lowest_z"]),
            float(new["lowest_z"]),
            float(tolerances["lowest_z_drop_m"]),
        )

        old_regions = old.get("by_region", {})
        new_regions = new.get("by_region", {})
        for region, old_stats in sorted(old_regions.items()):
            if region not in new_regions:
                regressions.append(
                    {
                        "kind": "severity",
                        "name": name,
                        "region": region,
                        "metric": "region_presence",
                        "baseline": "present",
                        "candidate": "missing",
                        "reason": "baseline_region_missing_from_candidate",
                    }
                )
                continue
            new_stats = new_regions[region]
            higher_is_better(
                name,
                "region_min_ratio",
                float(old_stats["min_ratio"]),
                float(new_stats["min_ratio"]),
                float(tolerances["region_min_ratio_drop"]),
                region,
            )
            lower_is_better(
                name,
                "region_max_ratio",
                float(old_stats["max_ratio"]),
                float(new_stats["max_ratio"]),
                float(tolerances["region_max_ratio_rise"]),
                region,
            )

    return regressions, improvements


def compare_grip_severity(
    baseline_report: list[dict[str, Any]] | None,
    candidate_report: list[dict[str, Any]] | None,
    tolerances: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not baseline_report and not candidate_report:
        return [], []
    if baseline_report is None or candidate_report is None:
        raise ValueError("supply both baseline and candidate grip reports, or neither")

    regressions: list[dict[str, Any]] = []
    improvements: list[dict[str, Any]] = []
    base = index_by_pose(baseline_report)
    cand = index_by_pose(candidate_report)
    pen_tol = float(tolerances["grip_penetration_rise_mm"])
    contact_tol = float(tolerances["grip_contact_fraction_drop"])

    for name, old in sorted(base.items()):
        new = cand.get(name)
        if new is None:
            continue  # compare_counts handles missing grip poses
        for side in ("grip_l", "grip_r"):
            old_grip = old.get(side)
            new_grip = new.get(side)
            if old_grip is None:
                continue
            if new_grip is None:
                regressions.append(
                    {
                        "kind": "severity",
                        "name": name,
                        "region": side,
                        "metric": "grip_presence",
                        "baseline": "present",
                        "candidate": "missing",
                        "reason": "baseline_grip_side_missing_from_candidate",
                    }
                )
                continue

            old_pen = float(old_grip["max_penetration_mm"])
            new_pen = float(new_grip["max_penetration_mm"])
            if new_pen > old_pen + pen_tol:
                regressions.append(change("severity", name, "grip_penetration_mm", old_pen, new_pen, "lower_is_better", pen_tol, side))
            elif new_pen < old_pen - pen_tol:
                improvements.append(change("severity", name, "grip_penetration_mm", old_pen, new_pen, "lower_is_better", pen_tol, side))

            old_vertices = float(old_grip.get("finger_vertices", 0))
            new_vertices = float(new_grip.get("finger_vertices", 0))
            if old_vertices <= 0 or new_vertices <= 0:
                regressions.append(
                    {
                        "kind": "severity",
                        "name": name,
                        "region": side,
                        "metric": "grip_contact_fraction",
                        "baseline": None if old_vertices <= 0 else float(old_grip["contact_vertices_within_2mm"]) / old_vertices,
                        "candidate": None if new_vertices <= 0 else float(new_grip["contact_vertices_within_2mm"]) / new_vertices,
                        "reason": "invalid_finger_vertex_count",
                    }
                )
                continue

            old_frac = float(old_grip["contact_vertices_within_2mm"]) / old_vertices
            new_frac = float(new_grip["contact_vertices_within_2mm"]) / new_vertices
            if new_frac < old_frac - contact_tol:
                regressions.append(change("severity", name, "grip_contact_fraction", old_frac, new_frac, "higher_is_better", contact_tol, side))
            elif new_frac > old_frac + contact_tol:
                improvements.append(change("severity", name, "grip_contact_fraction", old_frac, new_frac, "higher_is_better", contact_tol, side))

    return regressions, improvements


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
        tolerances = spec.get("comparison_tolerances")
        if not isinstance(tolerances, dict):
            raise ValueError("acceptance spec is missing comparison_tolerances")

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

        count_regressions = compare_counts(base_pose_counts, cand_pose_counts, "pose")
        count_regressions += compare_counts(base_grip_counts, cand_grip_counts, "grip")
        pose_regressions, pose_improvements = compare_pose_severity(baseline, candidate, tolerances)
        grip_regressions, grip_improvements = compare_grip_severity(base_grip, cand_grip, tolerances)

        regressions = count_regressions + pose_regressions + grip_regressions
        improvements = pose_improvements + grip_improvements

        baseline_total = sum(base_pose_counts.values()) + sum(base_grip_counts.values())
        candidate_total = sum(cand_pose_counts.values()) + sum(cand_grip_counts.values())

        if regressions:
            status = "REGRESSION"
        elif candidate_total < baseline_total or improvements:
            status = "IMPROVED"
        else:
            status = "UNCHANGED"

        result = {
            "schema_version": 2,
            "profile": args.profile,
            "status": status,
            "baseline_failed_checks": baseline_total,
            "candidate_failed_checks": candidate_total,
            "delta_failed_checks": candidate_total - baseline_total,
            "pose_failure_counts_baseline": base_pose_counts,
            "pose_failure_counts_candidate": cand_pose_counts,
            "grip_failure_counts_baseline": base_grip_counts,
            "grip_failure_counts_candidate": cand_grip_counts,
            "comparison_tolerances": tolerances,
            "regression_count": len(regressions),
            "improvement_count": len(improvements),
            "regressions": regressions,
            "improvements": improvements,
            "rule": "No baseline pose/grip may disappear, gain gate failures, or materially worsen a tracked severity metric while repairing another region.",
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
        f"candidate {candidate_total}; delta {candidate_total - baseline_total:+d}; "
        f"{len(regressions)} regressions; {len(improvements)} material improvements."
    )
    for regression in regressions[:20]:
        location = regression.get("name", "<unknown>")
        if regression.get("region"):
            location += f"/{regression['region']}"
        print(
            f"  REGRESSION {location}: {regression.get('metric')} "
            f"{regression.get('baseline')} -> {regression.get('candidate')}"
        )

    if args.report_only:
        return 0
    return 1 if status == "REGRESSION" else 0


if __name__ == "__main__":
    raise SystemExit(main())
