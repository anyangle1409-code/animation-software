#!/usr/bin/env python3
"""Validate/capture static dressed evidence without granting Phase 7 authority."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess

from original_v1_production_control import ROOT, CAND, build, digest, ensure_finite, evidence, read
from original_v1_session_preflight import blender_path, power_info, process_info, repository_issues, run

POSES = {
    "neutral", "curl_peak", "press_bottom", "press_top", "press_top_rhythm",
    "squat_bottom", "pushup_bottom", "pullup_hang", "pullup_hang_rhythm",
    "pullup_top", "lunge", "row", "grip", "curl_handle", "pullup_bar",
}
REVIEW_KEYS = {
    ("neutral", "front"), ("neutral", "rear"), ("neutral", "side"),
    ("neutral", "three_quarter"), ("neutral", "waist_front"),
    ("neutral", "hem_front"), ("neutral", "seat_rear"),
    ("press_top", "three_quarter"), ("squat_bottom", "three_quarter"),
    ("squat_bottom", "waist_front"), ("lunge", "three_quarter"),
    ("lunge", "waist_front"), ("pushup_bottom", "three_quarter"),
    ("row", "three_quarter"), ("curl_handle", "three_quarter"),
    ("pullup_bar", "three_quarter"),
}
BLENDER_SCRIPT = "scripts/capture_original_v1_dressed_evidence_blender.py"
POSE_SCRIPT = "scripts/pose_test_original_v1_o4_candidate_blender.py"
HELPER = "scripts/original_v1_dressed_evidence.py"


def inside_root(path: Path) -> Path:
    path = path.resolve()
    root = ROOT.resolve()
    if not path.is_relative_to(root):
        raise ValueError("evidence path must stay inside repository")
    return path


def _capture_map(report: dict) -> dict:
    rows = report.get("review", {}).get("files")
    if not isinstance(rows, list):
        raise ValueError("matched review files required")
    groups = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid review row")
        key = (row.get("pose"), row.get("view"))
        presentation = row.get("presentation")
        if key not in REVIEW_KEYS or presentation not in ("bare", "dressed"):
            raise ValueError("unexpected review pose/view/presentation")
        if not isinstance(row.get("capture_key"), dict) or not row.get("sha256") or not row.get("file"):
            raise ValueError("review source receipt incomplete")
        if presentation in groups.setdefault(key, {}):
            raise ValueError("duplicate review presentation")
        groups[key][presentation] = row
    if set(groups) != REVIEW_KEYS:
        raise ValueError("matched review coverage incomplete")
    for pair in groups.values():
        if set(pair) != {"bare", "dressed"}:
            raise ValueError("bare/dressed review pair incomplete")
        if pair["bare"]["capture_key"] != pair["dressed"]["capture_key"]:
            raise ValueError("bare/dressed camera or presentation settings differ")
        if pair["bare"]["file"] == pair["dressed"]["file"]:
            raise ValueError("bare/dressed review files alias")
    return groups


def validate(report: dict, raw_pair: dict, manifest: dict) -> dict:
    if report.get("status") != "EVIDENCE_ONLY" or report.get("phase_complete") is not False or report.get("production_approved") is not False:
        raise ValueError("dressed report cannot claim approval or phase completion")
    if raw_pair.get("status") != "EVIDENCE_ONLY" or raw_pair.get("phase_complete") is not False or raw_pair.get("production_approved") is not False:
        raise ValueError("raw garment pair must remain EVIDENCE_ONLY")
    candidate_sha = manifest.get("candidate_sha256")
    if not candidate_sha or report.get("candidate_sha256") != candidate_sha or raw_pair.get("candidate_sha256") != candidate_sha:
        raise ValueError("candidate identity differs across dressed evidence")
    if report.get("candidate") != manifest.get("candidate"):
        raise ValueError("candidate filename differs")
    if report.get("rig_id") != "hgpt_canonical_v4_original":
        raise ValueError("canonical v4 rig identity required")
    rows = report.get("poses")
    if not isinstance(rows, list):
        raise ValueError("pose evidence rows required")
    by_pose = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("pose") in by_pose:
            raise ValueError("invalid or duplicate pose row")
        pose = row.get("pose")
        by_pose[pose] = row
        for key in (
            "body_vertex_count_evaluated", "garment_vertex_count_evaluated",
            "body_face_count_evaluated", "garment_face_count_evaluated",
            "body_garment_intersecting_face_pairs", "garment_vertices_below_floor",
        ):
            if type(row.get(key)) is not int or row[key] < 0:
                raise ValueError("invalid dressed count metric")
        for key in (
            "body_to_garment_min_vertex_surface_distance_mm",
            "garment_to_body_min_vertex_surface_distance_mm",
        ):
            if type(row.get(key)) not in (int, float) or row[key] < 0:
                raise ValueError("invalid clearance metric")
        if not isinstance(row.get("pose_state_sha256"), str) or len(row["pose_state_sha256"]) != 64:
            raise ValueError("pose state identity missing")
        if not isinstance(row.get("source_body_metrics"), dict) or row["source_body_metrics"].get("pose") != pose:
            raise ValueError("source body metric binding differs")
    if set(by_pose) != POSES:
        raise ValueError("frozen stress-pose coverage incomplete")
    _capture_map(report)
    if not isinstance(report.get("unresolved_checks"), list) or not report["unresolved_checks"]:
        raise ValueError("explicit unresolved dressed checks required")
    ensure_finite(report)
    return {
        "schema_version": 1,
        "status": "EVIDENCE_ONLY",
        "phase_complete": False,
        "production_approved": False,
        "candidate_revision": report.get("candidate_revision"),
        "candidate_sha256": candidate_sha,
        "pose_count": len(by_pose),
        "review_pair_count": len(REVIEW_KEYS),
        "max_body_garment_intersecting_face_pairs": max(row["body_garment_intersecting_face_pairs"] for row in by_pose.values()),
        "minimum_reported_surface_distance_mm": min(
            min(row["body_to_garment_min_vertex_surface_distance_mm"], row["garment_to_body_min_vertex_surface_distance_mm"])
            for row in by_pose.values()
        ),
        "poses_with_garment_below_floor": sorted(pose for pose, row in by_pose.items() if row["garment_vertices_below_floor"] > 0),
        "unresolved_checks": list(report["unresolved_checks"]),
        "limits": "Summary of measured evidence only; intersections/clearance are not classified as acceptable and no threshold PASS is inferred.",
    }


def verify_files(report_path: Path, report: dict) -> None:
    base = report_path.parent
    for key, expected in (
        ("source_pose_report", report.get("source_pose_report_sha256")),
        ("source_pose_manifest", report.get("source_pose_manifest_sha256")),
    ):
        rel = report.get(key)
        if not rel or not expected:
            raise ValueError("source pose receipt missing")
        path = inside_root(base / rel)
        if not path.is_file() or digest(path) != expected:
            raise ValueError("source pose receipt bytes differ")
    if report.get("source_pose_script_sha256") != digest(ROOT / POSE_SCRIPT):
        raise ValueError("authoritative pose script hash differs from capture")
    if report.get("capture_script_sha256") != digest(ROOT / BLENDER_SCRIPT):
        raise ValueError("dressed capture script hash differs from capture")
    for row in report["review"]["files"]:
        path = inside_root(base / row["file"])
        if not path.is_file() or digest(path) != row["sha256"]:
            raise ValueError("review image bytes differ")


def capture(revision: str, raw_pair_path: Path, trial: str) -> tuple[Path, Path]:
    if not re.fullmatch(r"r\d+", revision):
        raise ValueError("numbered candidate revision required")
    if not re.fullmatch(r"trial\d+", trial):
        raise ValueError("trial must be trialN")
    control = read(ROOT, "ORIGINAL_V1_PRODUCTION_CONTROL.json")
    branch = run(["git", "branch", "--show-current"])
    head = run(["git", "rev-parse", "HEAD"])
    live = run(["git", "ls-remote", "--exit-code", "origin", "refs/heads/" + control["branch"]]).split()[0]
    issues = repository_issues(branch, control["branch"], head, live, run(["git", "status", "--porcelain", "--untracked-files=all"]))
    build(ROOT)
    blender = blender_path()
    if not blender:
        issues.append("Blender unavailable; set BLENDER_EXE")
    if shutil.disk_usage(ROOT).free < 2 * 1024**3:
        issues.append("less than 2 GiB free for dressed evidence")
    processes = process_info()
    power = power_info()
    print(json.dumps({"power": power, "processes": processes, "local_head": head, "live_head": live}, indent=2))
    if processes.get("conflicts"):
        issues.append("conflicting Blender/optimiser processes; inspect PIDs")
    if issues:
        raise ValueError("; ".join(issues))

    raw_pair_path = inside_root(raw_pair_path)
    if not raw_pair_path.is_file():
        raise ValueError("raw garment pair evidence missing")
    candidate = ROOT / CAND / f"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{revision}.blend"
    manifest_path = candidate.with_suffix(".json")
    manifest = read(ROOT, manifest_path.relative_to(ROOT))
    if not candidate.is_file() or manifest.get("candidate") != candidate.name or digest(candidate) != manifest.get("candidate_sha256"):
        raise ValueError("local candidate hash/name mismatch")

    out = ROOT / CAND / "dressed_evidence" / f"{revision}_{trial}"
    if out.exists():
        raise ValueError("dressed evidence output collision; preserve existing evidence and use a fresh trial")
    subprocess.run([
        str(blender), "--background", "--factory-startup", str(candidate), "--python-exit-code", "1",
        "--python", BLENDER_SCRIPT, "--", str(out), revision,
    ], cwd=ROOT, check=True)
    return out / "dressed_pose_evidence.json", manifest_path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("revision")
    ap.add_argument("--raw-pair", type=Path, required=True)
    ap.add_argument("--trial", default="trial1")
    ap.add_argument("--capture", action="store_true")
    ap.add_argument("--report", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    try:
        if not re.fullmatch(r"r\d+", args.revision):
            raise ValueError("numbered candidate revision required")
        raw_path = inside_root(args.raw_pair)
        if args.capture:
            if args.report is not None:
                raise ValueError("--report cannot be combined with --capture")
            report_path, manifest_path = capture(args.revision, raw_path, args.trial)
        else:
            if args.report is None:
                raise ValueError("--report is required without --capture")
            report_path = inside_root(args.report)
            manifest_path = ROOT / CAND / f"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{args.revision}.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        raw_pair = json.loads(raw_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        if report.get("candidate_revision") != args.revision:
            raise ValueError("report revision differs")
        if report.get("candidate_manifest_sha256") != digest(manifest_path):
            raise ValueError("candidate manifest bytes differ from capture")
        verify_files(report_path, report)
        summary = validate(report, raw_pair, manifest)
        summary.update({
            "source_evidence": [
                evidence(ROOT, report_path.relative_to(ROOT).as_posix()),
                evidence(ROOT, raw_path.relative_to(ROOT).as_posix()),
                evidence(ROOT, manifest_path.relative_to(ROOT).as_posix()),
                evidence(ROOT, BLENDER_SCRIPT), evidence(ROOT, HELPER), evidence(ROOT, POSE_SCRIPT),
            ],
            "source_git_commit": run(["git", "rev-parse", "HEAD"]),
            "generated_utc": datetime.now(timezone.utc).isoformat(),
        })
        out = inside_root(args.json_out) if args.json_out else report_path.parent / "verified_dressed_evidence.json"
        if out.exists():
            raise ValueError("verified output collision; preserve evidence")
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(summary, indent=2) + "\n")
        print("DRESSED EVIDENCE VERIFIED — EVIDENCE_ONLY; unresolved checks remain")
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print("STOP — " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
