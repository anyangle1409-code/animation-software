#!/usr/bin/env python3
"""Build an ordered ORIGINAL v1 deformation repair queue from a pose report.

The queue is intentionally rule-based and project-owned. It does not use a
blended quality score and does not infer anatomy from legacy/reference assets.

A failure is "owned" by a repair priority when:
- its pose is listed in that priority; and
- it is a pose-global metric, or its region is listed in that priority.
Equipment grip-side failures are owned by priorities that include hand/finger/
thumb work.

Any acceptance failure with no owner is reported explicitly so the repair plan
cannot silently ignore a blocker.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVAL_PATH = ROOT / "scripts/evaluate_original_v1_deformation_report.py"
SPEC = importlib.util.spec_from_file_location("deformation_eval", EVAL_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"unable to load {EVAL_PATH}")
deval = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(deval)


def owns_failure(priority: dict[str, Any], failure: dict[str, Any]) -> bool:
    pose = failure.get("pose")
    if pose not in set(priority.get("poses", [])):
        return False
    region = failure.get("region")
    if region is None:
        return True
    regions = set(priority.get("regions", []))
    if region in regions:
        return True
    if str(region).startswith("grip_") and regions.intersection({"hand", "finger", "thumb"}):
        return True
    return False


def count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in items:
        value = item.get(key)
        if value is None:
            continue
        name = str(value)
        result[name] = result.get(name, 0) + 1
    return dict(sorted(result.items(), key=lambda kv: (-kv[1], kv[0])))


def build_queue(
    pose_report: list[dict[str, Any]],
    grip_report: list[dict[str, Any]],
    spec: dict[str, Any],
    profile: str,
) -> dict[str, Any]:
    summary = deval.make_summary(pose_report, grip_report, spec, profile, None)
    failures = list(summary["failures"])
    priorities = sorted(spec.get("repair_priority", []), key=lambda p: int(p["priority"]))
    queue: list[dict[str, Any]] = []

    owned_indices: set[int] = set()
    for priority in priorities:
        related: list[dict[str, Any]] = []
        for index, failure in enumerate(failures):
            if owns_failure(priority, failure):
                related.append(failure)
                owned_indices.add(index)

        queue.append(
            {
                "priority": int(priority["priority"]),
                "regions": list(priority.get("regions", [])),
                "poses": list(priority.get("poses", [])),
                "reason": priority.get("reason"),
                "status": "BLOCKED" if related else "CLEAR",
                "owned_failure_count": len(related),
                "failure_counts_by_pose": count_by(related, "pose"),
                "failure_counts_by_region": count_by(related, "region"),
                "failures": related,
            }
        )

    unmapped = [failure for index, failure in enumerate(failures) if index not in owned_indices]
    blocked = [item for item in queue if item["status"] == "BLOCKED"]
    next_priority = blocked[0]["priority"] if blocked else None

    return {
        "schema_version": 1,
        "asset": spec.get("asset"),
        "rig": spec.get("rig"),
        "profile": profile,
        "acceptance_failure_count": int(summary["failure_count"]),
        "repair_priority_count": len(queue),
        "next_priority": next_priority,
        "all_repair_priorities_clear": next_priority is None,
        "ownership_complete": len(unmapped) == 0,
        "unmapped_failure_count": len(unmapped),
        "unmapped_failures": unmapped,
        "queue": queue,
        "rules": [
            "Work the lowest numbered BLOCKED priority first.",
            "A later priority does not override an earlier blocker.",
            "Do not weaken acceptance thresholds to clear a priority.",
            "Use V8-V15f only for historical failure lessons/quality expectations, never implementation data.",
            "After each Blender repair, compare against the pinned R2 baseline and reject severity regressions.",
        ],
    }


def to_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# ORIGINAL v1 deformation repair queue",
        "",
        f"- Profile: `{result['profile']}`",
        f"- Acceptance failures: **{result['acceptance_failure_count']}**",
        f"- Next priority: **{result['next_priority'] if result['next_priority'] is not None else 'none'}**",
        f"- Failure ownership complete: **{'YES' if result['ownership_complete'] else 'NO'}**",
        "",
    ]
    for item in result["queue"]:
        lines += [
            f"## Priority {item['priority']} — {item['status']}",
            "",
            f"Regions: {', '.join(item['regions'])}",
            "",
            f"Owned failed checks: **{item['owned_failure_count']}**",
            "",
        ]
        if item["failure_counts_by_pose"]:
            lines.append("Failing poses:")
            lines.append("")
            for pose, count in item["failure_counts_by_pose"].items():
                lines.append(f"- `{pose}`: {count}")
            lines.append("")
        if item["failure_counts_by_region"]:
            lines.append("Failing regions:")
            lines.append("")
            for region, count in item["failure_counts_by_region"].items():
                lines.append(f"- `{region}`: {count}")
            lines.append("")
        lines += [f"Reason: {item['reason']}", ""]

    if result["unmapped_failures"]:
        lines += ["## Unmapped blockers", ""]
        for failure in result["unmapped_failures"]:
            location = failure.get("pose") or "<report>"
            if failure.get("region"):
                location += f" / {failure['region']}"
            lines.append(
                f"- `{location}`: `{failure.get('metric')}` = "
                f"`{failure.get('value')}` ({failure.get('rule')})"
            )
        lines.append("")

    lines += [
        "## Boundary",
        "",
        "This queue is a deformation-repair plan only. It does not approve anatomy, biomechanics, provenance, garments or production release.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pose_report", type=Path)
    parser.add_argument("--grip-report", type=Path)
    parser.add_argument("--spec", type=Path, default=ROOT / "ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json")
    parser.add_argument("--profile", default="development_blocker")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    parser.add_argument("--require-complete-ownership", action="store_true")
    parser.add_argument("--expect-next-priority", type=int)
    args = parser.parse_args()

    try:
        pose_report = deval.load_json(args.pose_report)
        grip_report = deval.load_json(args.grip_report or args.pose_report)
        spec = deval.load_json(args.spec)
        if not isinstance(pose_report, list) or not isinstance(grip_report, list):
            raise ValueError("pose/grip reports must contain JSON lists")
        if not isinstance(spec, dict):
            raise ValueError("acceptance spec must contain a JSON object")
        if args.profile not in spec.get("profiles", {}):
            raise ValueError(f"unknown profile {args.profile!r}")

        result = build_queue(pose_report, grip_report, spec, args.profile)
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(to_markdown(result), encoding="utf-8")

    print(
        f"REPAIR QUEUE: {result['acceptance_failure_count']} failures; "
        f"next priority={result['next_priority']}; "
        f"unmapped={result['unmapped_failure_count']}."
    )

    if args.require_complete_ownership and not result["ownership_complete"]:
        return 1
    if args.expect_next_priority is not None and result["next_priority"] != args.expect_next_priority:
        print(
            f"ERROR: expected next priority {args.expect_next_priority}, "
            f"got {result['next_priority']}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
