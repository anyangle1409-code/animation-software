#!/usr/bin/env python3
"""Orchestrate Phase 6 raw/evaluated surface evidence on a verified candidate.

Runs read-only Blender captures plus standard-Python audits into one fresh folder.
Requires an authored joint-support evidence file for the exact candidate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess

from original_v1_production_control import ROOT, CAND, build, digest, read
from original_v1_session_preflight import blender_path, process_info, repository_issues, run

SNAPSHOT = "scripts/snapshot_original_v1_model_blender.py"
RAW_AUDIT = "scripts/audit_original_v1_surface.py"
EVAL_CAPTURE = "scripts/capture_original_v1_surface_quality_blender.py"
COMBINE = "scripts/original_v1_phase6_surface_quality.py"


def inside(path: Path) -> Path:
    p = path.resolve()
    if not p.is_relative_to(ROOT.resolve()):
        raise ValueError("path must remain inside repository")
    return p


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("revision")
    ap.add_argument("--joint-support", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    try:
        if not re.fullmatch(r"r\d+", args.revision):
            raise ValueError("numbered candidate revision required")
        out = inside(args.out_dir)
        if out.exists():
            raise ValueError("Phase 6 output folder already exists; preserve evidence")
        joint = inside(args.joint_support)
        if not joint.is_file():
            raise ValueError("authored joint-support evidence missing")

        control = read(ROOT, "ORIGINAL_V1_PRODUCTION_CONTROL.json")
        branch = run(["git","branch","--show-current"])
        head = run(["git","rev-parse","HEAD"])
        live = run(["git","ls-remote","--exit-code","origin","refs/heads/"+control["branch"]]).split()[0]
        issues = repository_issues(
            branch, control["branch"], head, live,
            run(["git","status","--porcelain","--untracked-files=all"])
        )
        state, _ = build(ROOT)
        if state.get("phases", {}).get("5", {}).get("state") != "complete":
            issues.append("Phase 5 is incomplete; Phase 6 capture is not eligible")
        blender = blender_path()
        if not blender:
            issues.append("Blender unavailable; set BLENDER_EXE")
        if process_info().get("conflicts"):
            issues.append("conflicting Blender/optimiser processes")
        if shutil.disk_usage(ROOT).free < 2 * 1024**3:
            issues.append("less than 2 GiB free for Phase 6 evidence")
        if issues:
            raise ValueError("; ".join(issues))

        candidate = ROOT / CAND / f"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{args.revision}.blend"
        manifest = candidate.with_suffix(".json")
        if not candidate.is_file() or not manifest.is_file():
            raise ValueError("candidate Blend/manifest missing")
        data = json.loads(manifest.read_text(encoding="utf-8-sig"))
        if data.get("candidate") != candidate.name or digest(candidate) != data.get("candidate_sha256"):
            raise ValueError("candidate Blend/manifest identity differs")
        if state.get("last_known_candidate_sha256") != data.get("candidate_sha256"):
            raise ValueError("candidate is not latest complete model state")

        joint_data = json.loads(joint.read_text(encoding="utf-8-sig"))
        if joint_data.get("candidate_sha256") != data.get("candidate_sha256"):
            raise ValueError("joint-support evidence candidate differs")

        out.mkdir(parents=True)
        raw_snapshot = out / "raw_body_snapshot.json"
        raw_surface = out / "raw_surface_audit.json"
        raw_md = out / "raw_surface_audit.md"
        evaluated = out / "evaluated_surface_quality.json"
        combined = out / "phase6_surface_quality.json"

        subprocess.run([
            str(blender),"--background","--factory-startup",str(candidate),
            "--python-exit-code","1","--python",SNAPSHOT,"--",str(raw_snapshot)
        ],cwd=ROOT,check=True)
        subprocess.run([
            "python",RAW_AUDIT,str(raw_snapshot),"--candidate-manifest",str(manifest),
            "--json-out",str(raw_surface),"--markdown-out",str(raw_md)
        ],cwd=ROOT,check=True)
        subprocess.run([
            str(blender),"--background","--factory-startup",str(candidate),
            "--python-exit-code","1","--python",EVAL_CAPTURE,"--",str(evaluated)
        ],cwd=ROOT,check=True)
        completed = subprocess.run([
            "python",COMBINE,
            "--raw-surface",str(raw_surface),
            "--evaluated-surface",str(evaluated),
            "--joint-support",str(joint),
            "--candidate-manifest",str(manifest),
            "--json-out",str(combined)
        ],cwd=ROOT)
        print("PHASE 6 EVIDENCE FOLDER:", out)
        return completed.returncode
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print("STOP — " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
