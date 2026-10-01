#!/usr/bin/env python3
"""Validate/capture sampled dressed range evidence and explicit contact classifications."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

from original_v1_production_control import ROOT, CAND, build, digest, ensure_finite, evidence, read
from original_v1_session_preflight import blender_path, power_info, process_info, repository_issues, run

PLAN = "ORIGINAL_V1_DRESSED_RANGE_PLAN.json"
BLENDER_SCRIPT = "scripts/capture_original_v1_dressed_range_blender.py"
POSE_SCRIPT = "scripts/pose_test_original_v1_o4_candidate_blender.py"
HELPER = "scripts/original_v1_dressed_range_evidence.py"
CLASS_VALUES = {"NO_FINDING", "UNCLASSIFIED", "LEGITIMATE_CONTACT", "UNEXPLAINED_DEFECT"}


def inside_root(path: Path) -> Path:
    path = path.resolve()
    root = ROOT.resolve()
    if not path.is_relative_to(root):
        raise ValueError("evidence path must stay inside repository")
    return path


def sample_key(row: dict) -> str:
    return f'{row["path_id"]}:{row["path_sample_index"]}'


def expected_samples(plan: dict) -> list[dict]:
    policy = plan.get("sample_policy", {})
    n = policy.get("samples_per_segment")
    if type(n) is not int or n < 3:
        raise ValueError("invalid plan sample count")
    dedupe = policy.get("deduplicate_shared_waypoints") is True
    out = []
    path_ids = set()
    for path in plan.get("paths", []):
        pid, waypoints = path.get("id"), path.get("waypoints")
        if not isinstance(pid, str) or pid in path_ids or not isinstance(waypoints, list) or len(waypoints) < 2:
            raise ValueError("invalid or duplicate range path")
        path_ids.add(pid)
        pindex = 0
        for seg in range(len(waypoints) - 1):
            for i in range(n):
                if seg > 0 and i == 0 and dedupe:
                    continue
                out.append({
                    "path_id": pid, "path_sample_index": pindex, "segment_index": seg,
                    "segment_start": waypoints[seg], "segment_end": waypoints[seg + 1],
                    "segment_sample_index": i, "segment_t": round(i / (n - 1), 8),
                })
                pindex += 1
    return out


def validate_report(report: dict, static: dict, manifest: dict, plan: dict) -> dict:
    if report.get("status") != "EVIDENCE_ONLY" or report.get("phase_complete") is not False or report.get("production_approved") is not False:
        raise ValueError("range report cannot claim approval or phase completion")
    candidate_sha = manifest.get("candidate_sha256")
    if not candidate_sha or report.get("candidate_sha256") != candidate_sha or static.get("candidate_sha256") != candidate_sha:
        raise ValueError("candidate identity differs across range/static evidence")
    if static.get("status") != "EVIDENCE_ONLY" or static.get("phase_complete") is not False or static.get("production_approved") is not False:
        raise ValueError("static dressed evidence must remain EVIDENCE_ONLY")
    if report.get("candidate") != manifest.get("candidate") or report.get("rig_id") != "hgpt_canonical_v4_original":
        raise ValueError("candidate filename or rig identity differs")
    expected = expected_samples(plan)
    rows = report.get("samples")
    if not isinstance(rows, list) or len(rows) != len(expected):
        raise ValueError("sample coverage incomplete")
    for row, exp in zip(rows, expected):
        if not isinstance(row, dict) or any(row.get(k) != v for k, v in exp.items()):
            raise ValueError("sample order/path/time differs from plan")
        if not isinstance(row.get("pose_state_sha256"), str) or len(row["pose_state_sha256"]) != 64:
            raise ValueError("sample pose identity missing")
        pairs = row.get("body_garment_face_pairs")
        if not isinstance(pairs, list) or any(not isinstance(p, list) or len(p) != 2 or any(type(v) is not int or v < 0 for v in p) for p in pairs):
            raise ValueError("invalid body/garment face-pair evidence")
        if row.get("body_garment_intersecting_face_pairs") != len(pairs):
            raise ValueError("intersection count differs from pair evidence")
        pair_hash = hashlib.sha256(json.dumps(pairs, separators=(",", ":")).encode()).hexdigest()
        if row.get("body_garment_face_pairs_sha256") != pair_hash:
            raise ValueError("intersection pair hash differs")
        for key in ("body_vertices_below_floor", "garment_vertices_below_floor", "body_vertices_within_2mm_floor", "garment_vertices_within_2mm_floor"):
            ids = row.get(key)
            if not isinstance(ids, list) or any(type(v) is not int or v < 0 for v in ids) or len(ids) != len(set(ids)):
                raise ValueError("invalid floor vertex evidence")
        for key in ("body_to_garment_min_vertex_surface_distance_mm", "garment_to_body_min_vertex_surface_distance_mm", "body_lowest_z_mm", "garment_lowest_z_mm"):
            if type(row.get(key)) not in (int, float):
                raise ValueError("invalid sampled numeric metric")
    if report.get("classification_status") != "UNCLASSIFIED":
        raise ValueError("raw range capture must remain UNCLASSIFIED")
    if not isinstance(report.get("unresolved_checks"), list) or not report["unresolved_checks"]:
        raise ValueError("range capture must retain unresolved checks")
    ensure_finite(report)
    findings = sum(
        bool(r["body_garment_face_pairs"]) or bool(r["body_vertices_below_floor"]) or bool(r["garment_vertices_below_floor"])
        for r in rows
    )
    return {
        "schema_version": 1,
        "status": "EVIDENCE_ONLY",
        "phase_complete": False,
        "production_approved": False,
        "candidate_revision": report.get("candidate_revision"),
        "candidate_sha256": candidate_sha,
        "path_count": len(plan["paths"]),
        "sample_count": len(rows),
        "samples_with_raw_contact_findings": findings,
        "classification_complete": findings == 0,
        "limits": "Sample coverage and evidence integrity only. A raw finding is unresolved until source-bound classification is supplied; no acceptance threshold is inferred.",
    }


def classification_template(report: dict) -> dict:
    rows = []
    for sample in report["samples"]:
        rows.append({
            "sample_key": sample_key(sample),
            "path_id": sample["path_id"],
            "path_sample_index": sample["path_sample_index"],
            "body_garment": {
                "raw_face_pairs_sha256": sample["body_garment_face_pairs_sha256"],
                "raw_count": sample["body_garment_intersecting_face_pairs"],
                "classification": "UNCLASSIFIED" if sample["body_garment_intersecting_face_pairs"] else "NO_FINDING",
                "evidence_note": "",
            },
            "body_floor": {
                "raw_vertex_ids": sample["body_vertices_below_floor"],
                "classification": "UNCLASSIFIED" if sample["body_vertices_below_floor"] else "NO_FINDING",
                "evidence_note": "",
            },
            "garment_floor": {
                "raw_vertex_ids": sample["garment_vertices_below_floor"],
                "classification": "UNCLASSIFIED" if sample["garment_vertices_below_floor"] else "NO_FINDING",
                "evidence_note": "",
            },
        })
    return {
        "schema_version": 1,
        "status": "INCOMPLETE",
        "candidate_sha256": report["candidate_sha256"],
        "range_report_sha256": None,
        "production_approved": False,
        "rows": rows,
        "rule": "Replace UNCLASSIFIED only from inspected source-bound evidence. LEGITIMATE_CONTACT requires a concrete contact rationale; UNEXPLAINED_DEFECT remains a blocking finding for later production validation. Never alter raw counts/IDs/hashes.",
    }


def validate_classification(classification: dict, report: dict, report_sha: str) -> dict:
    if classification.get("candidate_sha256") != report.get("candidate_sha256") or classification.get("range_report_sha256") != report_sha:
        raise ValueError("classification source identity differs")
    rows = classification.get("rows")
    if not isinstance(rows, list) or len(rows) != len(report["samples"]):
        raise ValueError("classification coverage incomplete")
    raw = {sample_key(r): r for r in report["samples"]}
    seen = set()
    unresolved = defects = legitimate = 0
    for row in rows:
        key = row.get("sample_key")
        if key in seen or key not in raw:
            raise ValueError("classification sample key invalid or duplicate")
        seen.add(key)
        sample = raw[key]
        domains = (
            ("body_garment", sample["body_garment_intersecting_face_pairs"], sample["body_garment_face_pairs_sha256"]),
            ("body_floor", len(sample["body_vertices_below_floor"]), sample["body_vertices_below_floor"]),
            ("garment_floor", len(sample["garment_vertices_below_floor"]), sample["garment_vertices_below_floor"]),
        )
        for domain, count, identity in domains:
            item = row.get(domain)
            if not isinstance(item, dict) or item.get("classification") not in CLASS_VALUES:
                raise ValueError("invalid contact classification")
            status = item["classification"]
            if domain == "body_garment":
                if item.get("raw_count") != count or item.get("raw_face_pairs_sha256") != identity:
                    raise ValueError("classification body/garment raw evidence differs")
            elif item.get("raw_vertex_ids") != identity:
                raise ValueError("classification floor raw evidence differs")
            if count == 0 and status != "NO_FINDING":
                raise ValueError("zero raw finding must remain NO_FINDING")
            if count > 0 and status == "NO_FINDING":
                raise ValueError("raw finding cannot be classified NO_FINDING")
            if status in ("LEGITIMATE_CONTACT", "UNEXPLAINED_DEFECT") and not str(item.get("evidence_note", "")).strip():
                raise ValueError("classified finding requires evidence note")
            unresolved += status == "UNCLASSIFIED"
            defects += status == "UNEXPLAINED_DEFECT"
            legitimate += status == "LEGITIMATE_CONTACT"
    if seen != set(raw):
        raise ValueError("classification missing sample")
    return {
        "classification_complete": unresolved == 0,
        "unclassified_findings": unresolved,
        "unexplained_defects": defects,
        "legitimate_contacts": legitimate,
        "production_pass_inferred": False,
    }


def verify_files(report_path: Path, report: dict) -> None:
    base = report_path.parent
    for key, expected in (("source_pose_report", report.get("source_pose_report_sha256")), ("source_pose_manifest", report.get("source_pose_manifest_sha256"))):
        rel = report.get(key)
        if not rel or not expected:
            raise ValueError("source pose receipt missing")
        path = inside_root(base / rel)
        if not path.is_file() or digest(path) != expected:
            raise ValueError("source pose receipt bytes differ")
    for key, path in (("plan_sha256", ROOT / PLAN), ("source_pose_script_sha256", ROOT / POSE_SCRIPT), ("capture_script_sha256", ROOT / BLENDER_SCRIPT)):
        if report.get(key) != digest(path):
            raise ValueError("range source hash differs from capture")


def capture(revision: str, static_path: Path, trial: str) -> tuple[Path, Path]:
    if not re.fullmatch(r"r\d+", revision) or not re.fullmatch(r"trial\d+", trial):
        raise ValueError("revision must be rN and trial must be trialN")
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
        issues.append("less than 2 GiB free for range evidence")
    processes = process_info()
    print(json.dumps({"power": power_info(), "processes": processes, "local_head": head, "live_head": live}, indent=2))
    if processes.get("conflicts"):
        issues.append("conflicting Blender/optimiser processes; inspect PIDs")
    if issues:
        raise ValueError("; ".join(issues))
    static_path = inside_root(static_path)
    if not static_path.is_file():
        raise ValueError("verified static dressed evidence missing")
    candidate = ROOT / CAND / f"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{revision}.blend"
    manifest_path = candidate.with_suffix(".json")
    manifest = read(ROOT, manifest_path.relative_to(ROOT))
    if not candidate.is_file() or manifest.get("candidate") != candidate.name or digest(candidate) != manifest.get("candidate_sha256"):
        raise ValueError("local candidate hash/name mismatch")
    static = json.loads(static_path.read_text(encoding="utf-8"))
    if static.get("candidate_sha256") != manifest["candidate_sha256"]:
        raise ValueError("static evidence candidate differs")
    out = ROOT / CAND / "dressed_range" / f"{revision}_{trial}"
    if out.exists():
        raise ValueError("range evidence output collision; preserve existing evidence and use a fresh trial")
    subprocess.run([
        str(blender), "--background", "--factory-startup", str(candidate), "--python-exit-code", "1",
        "--python", BLENDER_SCRIPT, "--", str(out), revision,
    ], cwd=ROOT, check=True)
    return out / "dressed_range_evidence.json", manifest_path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("revision")
    ap.add_argument("--static-evidence", type=Path, required=True)
    ap.add_argument("--trial", default="trial1")
    ap.add_argument("--capture", action="store_true")
    ap.add_argument("--report", type=Path)
    ap.add_argument("--classification", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    try:
        if not re.fullmatch(r"r\d+", args.revision):
            raise ValueError("numbered candidate revision required")
        static_path = inside_root(args.static_evidence)
        if args.capture:
            if args.report is not None:
                raise ValueError("--report cannot be combined with --capture")
            report_path, manifest_path = capture(args.revision, static_path, args.trial)
        else:
            if args.report is None:
                raise ValueError("--report is required without --capture")
            report_path = inside_root(args.report)
            manifest_path = ROOT / CAND / f"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{args.revision}.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        static = json.loads(static_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        plan = json.loads((ROOT / PLAN).read_text(encoding="utf-8"))
        if report.get("candidate_revision") != args.revision or report.get("candidate_manifest_sha256") != digest(manifest_path):
            raise ValueError("range report revision/manifest differs")
        verify_files(report_path, report)
        summary = validate_report(report, static, manifest, plan)
        report_sha = digest(report_path)
        class_path = report_path.parent / "contact_classification.json"
        if args.classification:
            class_path = inside_root(args.classification)
            classification = json.loads(class_path.read_text(encoding="utf-8"))
            summary["classification"] = validate_classification(classification, report, report_sha)
        else:
            if class_path.exists():
                raise ValueError("classification template collision; preserve evidence")
            classification = classification_template(report)
            classification["range_report_sha256"] = report_sha
            with class_path.open("x", encoding="utf-8") as handle:
                handle.write(json.dumps(classification, indent=2) + "\n")
            summary["classification"] = validate_classification(classification, report, report_sha)
        summary.update({
            "source_evidence": [
                evidence(ROOT, report_path.relative_to(ROOT).as_posix()),
                evidence(ROOT, static_path.relative_to(ROOT).as_posix()),
                evidence(ROOT, manifest_path.relative_to(ROOT).as_posix()),
                evidence(ROOT, PLAN), evidence(ROOT, BLENDER_SCRIPT), evidence(ROOT, HELPER), evidence(ROOT, POSE_SCRIPT),
            ],
            "classification_file": class_path.relative_to(ROOT).as_posix(),
            "classification_sha256": digest(class_path),
            "source_git_commit": run(["git", "rev-parse", "HEAD"]),
            "generated_utc": datetime.now(timezone.utc).isoformat(),
        })
        out = inside_root(args.json_out) if args.json_out else report_path.parent / "verified_dressed_range_evidence.json"
        if out.exists():
            raise ValueError("verified range output collision; preserve evidence")
        with out.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(summary, indent=2) + "\n")
        print("DRESSED RANGE VERIFIED — EVIDENCE_ONLY; classification complete:", summary["classification"]["classification_complete"])
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print("STOP — " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
