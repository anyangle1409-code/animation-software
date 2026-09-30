#!/usr/bin/env python3
"""Verify that the pinned ORIGINAL v1 R2 deformation baseline is reproducible.

This protects the comparison anchor from silent edits to:
- the pose report;
- the grip report;
- the acceptance specification; or
- the recorded O4 candidate identity.

It also recomputes the expected development/production failure counts.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "ORIGINAL_V1_WORK/candidates/DEFORMATION_BASELINE_R2.json"
EVAL_PATH = ROOT / "scripts/evaluate_original_v1_deformation_report.py"

SPEC = importlib.util.spec_from_file_location("deformation_eval", EVAL_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"unable to load {EVAL_PATH}")
deval = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(deval)


def git_blob_sha(path: Path) -> str:
    proc = subprocess.run(
        ["git", "hash-object", str(path.relative_to(ROOT))],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise ValueError(f"git hash-object failed for {path}: {proc.stderr.strip()}")
    return proc.stdout.strip()


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def find_pose(report: list[dict[str, Any]], name: str) -> dict[str, Any]:
    matches = [p for p in report if p.get("pose") == name]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one pose {name!r}, found {len(matches)}")
    return matches[0]


def main() -> int:
    errors: list[str] = []

    try:
        baseline = deval.load_json(BASELINE_PATH)
        if not isinstance(baseline, dict):
            raise ValueError("baseline file must contain a JSON object")

        inputs = baseline["inputs"]
        resolved: dict[str, Path] = {}
        for key in ("pose_report", "grip_report", "acceptance_spec"):
            path = ROOT / inputs[key]["path"]
            resolved[key] = path
            if not path.is_file():
                fail(errors, f"missing pinned input: {path}")
                continue
            actual_sha = git_blob_sha(path)
            expected_sha = str(inputs[key]["git_blob_sha"])
            if actual_sha != expected_sha:
                fail(
                    errors,
                    f"{key} blob changed: expected {expected_sha}, got {actual_sha}",
                )

        pose_report = deval.load_json(resolved["pose_report"])
        grip_report = deval.load_json(resolved["grip_report"])
        spec = deval.load_json(resolved["acceptance_spec"])
        if not isinstance(pose_report, list) or not isinstance(grip_report, list):
            raise ValueError("pose/grip reports must contain JSON lists")
        if not isinstance(spec, dict):
            raise ValueError("acceptance spec must contain a JSON object")

        dev = deval.make_summary(
            pose_report,
            grip_report,
            spec,
            "development_blocker",
            None,
        )
        prod = deval.make_summary(
            pose_report,
            grip_report,
            spec,
            "production_target",
            None,
        )

        expected_dev = int(baseline["evaluation"]["development_blocker_failed_checks"])
        expected_prod = int(baseline["evaluation"]["production_target_failed_checks"])
        if int(dev["failure_count"]) != expected_dev:
            fail(
                errors,
                f"development failure count changed: expected {expected_dev}, got {dev['failure_count']}",
            )
        if int(prod["failure_count"]) != expected_prod:
            fail(
                errors,
                f"production failure count changed: expected {expected_prod}, got {prod['failure_count']}",
            )

        expected_by_pose = baseline["evaluation"]["development_failure_counts_by_pose"]
        actual_by_pose = {name: 0 for name in expected_by_pose}
        actual_by_pose.update(dev["failure_counts_by_pose"])
        if actual_by_pose != expected_by_pose:
            fail(
                errors,
                "development failure counts by pose changed: "
                + json.dumps({"expected": expected_by_pose, "actual": actual_by_pose}, sort_keys=True),
            )

        expected_by_region = baseline["evaluation"]["development_failure_counts_by_region"]
        actual_by_region = dev["failure_counts_by_region"]
        if actual_by_region != expected_by_region:
            fail(
                errors,
                "development failure counts by region changed: "
                + json.dumps({"expected": expected_by_region, "actual": actual_by_region}, sort_keys=True),
            )

        neutral = find_pose(pose_report, "neutral")
        if float(neutral["volume_ratio"]) != float(baseline["known_control"]["neutral_volume_ratio"]):
            fail(errors, "neutral volume ratio no longer matches pinned baseline")
        if int(neutral["self_intersecting_face_pairs"]) != int(
            baseline["known_control"]["neutral_self_intersections"]
        ):
            fail(errors, "neutral self-intersection count no longer matches pinned baseline")

        grip = find_pose(grip_report, "curl_handle")
        left = float(grip["grip_l"]["max_penetration_mm"])
        right = float(grip["grip_r"]["max_penetration_mm"])
        if left != float(baseline["known_grip_blocker"]["curl_handle_max_penetration_mm_left"]):
            fail(errors, "left curl-handle penetration no longer matches pinned baseline")
        if right != float(baseline["known_grip_blocker"]["curl_handle_max_penetration_mm_right"]):
            fail(errors, "right curl-handle penetration no longer matches pinned baseline")

        build = deval.load_json(ROOT / "ORIGINAL_V1_WORK/candidates/O4_CANDIDATE_BUILD.json")
        if build["candidate_sha256"] != baseline["candidate_sha256"]:
            fail(errors, "O4 candidate SHA-256 no longer matches pinned baseline")
        if build["source_o2_blend_sha256"] != baseline["source_o2_blend_sha256"]:
            fail(errors, "O2 source SHA-256 no longer matches pinned baseline")

    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    result = {
        "pass": not errors,
        "baseline": str(BASELINE_PATH.relative_to(ROOT)).replace("\\", "/"),
        "errors": errors,
    }
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
