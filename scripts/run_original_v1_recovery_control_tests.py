#!/usr/bin/env python3
"""Run the non-Blender ORIGINAL-v1 recovery-control regression suite.

This is the preferred one-command laptop check for the fail-closed validation
infrastructure added during the whole-body recovery. It writes an immutable
JSON receipt that can be cited as process evidence for WB-QA-011 only when the
full suite returns zero.

It does not run Blender/model deformation tests and does not approve production.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

TEST_MODULES = (
    "test_original_v1_human_evidence",
    "test_original_v1_r96_task7_gate",
    "test_original_v1_r96_task7_arc_gate",
    "test_original_v1_grip_wrist_gate",
    "test_original_v1_whole_body_issues",
    "test_original_v1_anatomy_issue_closure",
    "test_original_v1_whole_body_audit_readiness",
    "test_original_v1_whole_body_audit_gate",
    "test_original_v1_phase4_preflight",
)


def git_head(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )
    value = result.stdout.strip()
    if len(value) != 40:
        raise ValueError("git HEAD is not a 40-character commit")
    return value


def run_suite(root: Path, modules=TEST_MODULES) -> dict:
    head = git_head(root)
    cmd = [sys.executable, "-m", "unittest", "-v", *modules]
    result = subprocess.run(
        cmd,
        cwd=root / "scripts",
        text=True,
        capture_output=True,
    )
    return {
        "schema_version": 1,
        "status": "RECOVERY_CONTROL_TESTS_PASS" if result.returncode == 0 else "RECOVERY_CONTROL_TESTS_FAIL",
        "production_approved": False,
        "source_git_commit": head,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "python_executable": sys.executable,
        "command": cmd,
        "test_modules": list(modules),
        "return_code": int(result.returncode),
        "passed": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "scope": "Non-Blender recovery-control regression suite only; no model deformation or production approval is inferred.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        receipt = run_suite(ROOT)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print("STOP — " + str(exc))
        return 2

    if args.out is None:
        out = (
            ROOT / "ORIGINAL_V1_WORK/candidates/repair_checks"
            / ("recovery_control_tests_" + receipt["source_git_commit"][:12] + ".json")
        )
    else:
        out = args.out if args.out.is_absolute() else ROOT / args.out
    out = out.resolve()
    if not out.is_relative_to(ROOT.resolve()):
        print("STOP — output must remain inside repository")
        return 2
    if out.exists():
        print("STOP — output collision; preserve existing test receipt")
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "source_git_commit": receipt["source_git_commit"],
        "return_code": receipt["return_code"],
        "receipt": out.relative_to(ROOT).as_posix(),
        "production_approved": False,
    }, indent=2))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
