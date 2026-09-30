#!/usr/bin/env python3
"""Evaluate ORIGINAL v1 Blender deformation reports against project-owned gates.

This script is deliberately Blender-independent so report JSON produced on the
laptop can be reviewed in CI or from any standard Python installation.

Example:
    python scripts/evaluate_original_v1_deformation_report.py \
      ORIGINAL_V1_WORK/candidates/pose_test_report_r2.json \
      --grip-report ORIGINAL_V1_WORK/candidates/grip_test_report_r1.json \
      --profile development_blocker \
      --markdown-out ORIGINAL_V1_WORK/candidates/deformation_acceptance_r2.md

Exit codes:
    0 = selected profile passes (or --report-only was supplied)
    1 = selected profile fails
    2 = input/specification error
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_SPEC = Path(__file__).resolve().parents[1] / "ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json"


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path}: {exc}") from exc


def check_range(
    failures: list[dict[str, Any]],
    pose: str,
    metric: str,
    value: float,
    low: float | None = None,
    high: float | None = None,
    region: str | None = None,
) -> None:
    if low is not None and value < low:
        failures.append(
            {
                "pose": pose,
                "region": region,
                "metric": metric,
                "value": value,
                "rule": f">= {low}",
            }
        )
    if high is not None and value > high:
        failures.append(
            {
                "pose": pose,
                "region": region,
                "metric": metric,
                "value": value,
                "rule": f"<= {high}",
            }
        )


def evaluate_pose(pose: dict[str, Any], limits: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    name = str(pose.get("pose", "<unnamed>"))

    check_range(
        failures,
        name,
        "volume_ratio",
        float(pose["volume_ratio"]),
        float(limits["volume_ratio_min"]),
        float(limits["volume_ratio_max"]),
    )
    check_range(
        failures,
        name,
        "edge_ratio_p01",
        float(pose["edge_ratio_p01"]),
        float(limits["edge_ratio_p01_min"]),
        None,
    )
    check_range(
        failures,
        name,
        "edge_ratio_p99",
        float(pose["edge_ratio_p99"]),
        None,
        float(limits["edge_ratio_p99_max"]),
    )
    check_range(
        failures,
        name,
        "self_intersecting_face_pairs",
        float(pose["self_intersecting_face_pairs"]),
        None,
        float(limits["self_intersecting_face_pairs_max"]),
    )
    check_range(
        failures,
        name,
        "lowest_z_m",
        float(pose["lowest_z"]),
        float(limits["lowest_z_min_m"]),
        None,
    )

    for region, stats in sorted(pose.get("by_region", {}).items()):
        check_range(
            failures,
            name,
            "region_min_ratio",
            float(stats["min_ratio"]),
            float(limits["region_min_ratio_min"]),
            None,
            region,
        )
        check_range(
            failures,
            name,
            "region_max_ratio",
            float(stats["max_ratio"]),
            None,
            float(limits["region_max_ratio_max"]),
            region,
        )

    return failures


def evaluate_grip(report: list[dict[str, Any]], limits: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for item in report:
        pose = str(item.get("pose", "<unnamed>"))
        for side in ("grip_l", "grip_r"):
            grip = item.get(side)
            if not grip:
                continue
            penetration = float(grip["max_penetration_mm"])
            contact = float(grip["contact_vertices_within_2mm"])
            check_range(
                failures,
                pose,
                "grip_max_penetration_mm",
                penetration,
                None,
                float(limits["grip_max_penetration_mm"]),
                side,
            )
            check_range(
                failures,
                pose,
                "grip_contact_vertices_within_2mm",
                contact,
                float(limits["grip_min_contact_vertices_within_2mm"]),
                None,
                side,
            )
    return failures


def required_poses(spec: dict[str, Any], group: str | None) -> set[str]:
    if not group:
        return set()
    groups = spec.get("required_pose_groups", {})
    if group not in groups:
        raise ValueError(f"unknown required pose group {group!r}; choose from {sorted(groups)}")
    return set(groups[group])


def make_summary(
    pose_report: list[dict[str, Any]],
    grip_report: list[dict[str, Any]] | None,
    spec: dict[str, Any],
    profile: str,
    require_group: str | None,
) -> dict[str, Any]:
    profiles = spec.get("profiles", {})
    if profile not in profiles:
        raise ValueError(f"unknown profile {profile!r}; choose from {sorted(profiles)}")
    limits = profiles[profile]

    pose_failures: list[dict[str, Any]] = []
    for pose in pose_report:
        pose_failures.extend(evaluate_pose(pose, limits))

    grip_failures = evaluate_grip(grip_report or [], limits)

    present = {str(p.get("pose")) for p in pose_report}
    required = required_poses(spec, require_group)
    missing = sorted(required - present)

    failures = pose_failures + grip_failures
    if missing:
        failures.append(
            {
                "pose": None,
                "region": None,
                "metric": "missing_required_poses",
                "value": missing,
                "rule": f"all poses in group {require_group!r} must be present",
            }
        )

    by_pose: dict[str, int] = {}
    by_region: dict[str, int] = {}
    by_metric: dict[str, int] = {}
    for failure in failures:
        p = failure.get("pose") or "<report>"
        r = failure.get("region")
        m = str(failure.get("metric"))
        by_pose[p] = by_pose.get(p, 0) + 1
        if r:
            by_region[str(r)] = by_region.get(str(r), 0) + 1
        by_metric[m] = by_metric.get(m, 0) + 1

    return {
        "schema_version": 1,
        "asset": spec.get("asset"),
        "rig": spec.get("rig"),
        "profile": profile,
        "status": "PASS" if not failures else "FAIL",
        "pose_count": len(pose_report),
        "grip_report_present": grip_report is not None,
        "required_pose_group": require_group,
        "missing_required_poses": missing,
        "failure_count": len(failures),
        "failures": failures,
        "failure_counts_by_pose": dict(sorted(by_pose.items(), key=lambda kv: (-kv[1], kv[0]))),
        "failure_counts_by_region": dict(sorted(by_region.items(), key=lambda kv: (-kv[1], kv[0]))),
        "failure_counts_by_metric": dict(sorted(by_metric.items(), key=lambda kv: (-kv[1], kv[0]))),
        "notes": [
            "This is a deformation gate, not an exercise-biomechanics approval.",
            "Historical V-series/V15f assets may inform failure cases only; implementation data must remain independently authored.",
            "Production promotion still requires provenance, anatomy review, runtime contacts/movement, dressed review and release gates.",
        ],
    }


def to_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# ORIGINAL v1 deformation acceptance",
        "",
        f"- Profile: `{summary['profile']}`",
        f"- Status: **{summary['status']}**",
        f"- Poses evaluated: **{summary['pose_count']}**",
        f"- Failures: **{summary['failure_count']}**",
    ]
    if summary["required_pose_group"]:
        lines.append(f"- Required group: `{summary['required_pose_group']}`")
    if summary["missing_required_poses"]:
        lines.append("- Missing poses: " + ", ".join(summary["missing_required_poses"]))

    lines += ["", "## Highest-priority failing poses", ""]
    if summary["failure_counts_by_pose"]:
        for pose, count in list(summary["failure_counts_by_pose"].items())[:10]:
            lines.append(f"- `{pose}`: {count} failed checks")
    else:
        lines.append("- None.")

    lines += ["", "## Failing regions", ""]
    if summary["failure_counts_by_region"]:
        for region, count in summary["failure_counts_by_region"].items():
            lines.append(f"- `{region}`: {count} failed checks")
    else:
        lines.append("- None.")

    lines += ["", "## Failed checks", ""]
    if summary["failures"]:
        for failure in summary["failures"]:
            location = str(failure.get("pose") or "report")
            if failure.get("region"):
                location += f" / {failure['region']}"
            lines.append(
                f"- `{location}` — `{failure['metric']}` = `{failure['value']}`; expected {failure['rule']}."
            )
    else:
        lines.append("- None.")

    lines += [
        "",
        "## Interpretation",
        "",
        "Passing this report does **not** promote the asset to production. It only proves the selected numerical deformation profile. Human anatomy review, provenance, runtime movement/contact validation, garment review and release acceptance remain separate gates.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pose_report", type=Path)
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--grip-report", type=Path)
    parser.add_argument("--profile", default="development_blocker")
    parser.add_argument("--require-group")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()

    try:
        spec = load_json(args.spec)
        poses = load_json(args.pose_report)
        grip = load_json(args.grip_report) if args.grip_report else None
        if not isinstance(poses, list):
            raise ValueError("pose report must contain a JSON list")
        if grip is not None and not isinstance(grip, list):
            raise ValueError("grip report must contain a JSON list")
        summary = make_summary(poses, grip, spec, args.profile, args.require_group)
    except (ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    report_text = json.dumps(summary, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(report_text, encoding="utf-8")
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(to_markdown(summary), encoding="utf-8")

    print(
        f"{summary['status']}: {summary['failure_count']} failed checks across "
        f"{summary['pose_count']} poses using profile {summary['profile']}."
    )
    for pose, count in list(summary["failure_counts_by_pose"].items())[:8]:
        print(f"  {pose}: {count}")

    if args.report_only:
        return 0
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
