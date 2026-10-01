#!/usr/bin/env python3
"""Combine ORIGINAL-v1 Phase 6 raw/evaluated/joint-support surface evidence.

This is a fail-closed evidence verifier, not a topology repairer or anatomy judge.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

from original_v1_production_control import ROOT, digest, ensure_finite
from verify_original_v1_production_promotion import safe_path

JOINT_TEMPLATE = "ORIGINAL_V1_PHASE6_JOINT_SUPPORT_PLAN.json"
HELPER = "scripts/original_v1_phase6_surface_quality.py"


def load_ref(root: Path, path: Path, label: str) -> tuple[Path, dict]:
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"{label} must remain inside repository")
    if not resolved.is_file():
        raise ValueError(f"{label} missing")
    data = json.loads(resolved.read_text(encoding="utf-8-sig"))
    ensure_finite(data)
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a JSON object")
    return resolved, data


def ref(path: Path, root: Path) -> dict:
    return {"path": path.relative_to(root.resolve()).as_posix(), "sha256": digest(path)}


def evidence_refs(root: Path, refs, label: str) -> list[dict]:
    if not isinstance(refs, list) or not refs:
        raise ValueError(f"{label} evidence required")
    seen = set()
    out = []
    for item in refs:
        if not isinstance(item, dict) or not item.get("path") or not re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", ""))):
            raise ValueError(f"{label} evidence path/SHA-256 required")
        p = safe_path(root, item["path"])
        if not p.is_file() or digest(p) != item["sha256"]:
            raise ValueError(f"{label} evidence hash/path differs")
        key = (item["path"], item["sha256"])
        if key in seen:
            raise ValueError(f"duplicate {label} evidence")
        seen.add(key)
        out.append(item)
    return out


def validate_joint_support(root: Path, joint: dict, candidate_sha: str, raw_vertex_count: int) -> list[str]:
    issues = []
    template = json.loads((root / JOINT_TEMPLATE).read_text(encoding="utf-8"))
    expected = {row["id"]: row for row in template["joints"]}
    if joint.get("schema_version") != 1 or joint.get("status") != "JOINT_SUPPORT_EVIDENCE_COMPLETE":
        issues.append("joint-support evidence identity/status differs")
    if joint.get("phase_complete") is not False or joint.get("production_approved") is not False:
        issues.append("joint-support evidence cannot claim phase/production completion")
    if joint.get("candidate_sha256") != candidate_sha:
        issues.append("joint-support candidate differs")
    rows = joint.get("joints")
    if not isinstance(rows, list) or {r.get("id") for r in rows if isinstance(r, dict)} != set(expected):
        return issues + ["joint-support rows must exactly cover declared joints"]
    for row in rows:
        jid = row["id"]
        ids = row.get("support_vertex_ids")
        if not isinstance(ids, list) or not ids or any(type(v) is not int or v < 0 or v >= raw_vertex_count for v in ids):
            issues.append(f"{jid}: authored support vertex IDs missing/invalid")
        elif len(ids) != len(set(ids)):
            issues.append(f"{jid}: duplicate support vertex IDs")
        if row.get("loaded_poses") != expected[jid]["loaded_poses"]:
            issues.append(f"{jid}: loaded-pose coverage differs")
        try:
            evidence_refs(root, row.get("evidence"), jid)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            issues.append(str(exc))
    return list(dict.fromkeys(issues))


def raw_surface_blockers(raw: dict) -> list[str]:
    fields = (
        "boundary_edges",
        "nonmanifold_edges",
        "winding_conflict_edges",
        "nonmanifold_vertex_ids",
        "isolated_vertex_ids",
        "repeated_vertex_face_ids",
        "duplicate_face_groups",
        "exact_zero_area_face_ids",
        "near_degenerate_face_ids",
        "zero_area_fan_face_ids",
        "coincident_coordinate_groups",
    )
    blockers = []
    for field in fields:
        value = raw.get(field)
        if not isinstance(value, list):
            blockers.append(field + " missing")
        elif value:
            blockers.append(field + f" has {len(value)} finding(s)")
    return blockers


def verify_packet(root: Path, raw: dict, evaluated: dict, joint: dict, manifest: dict) -> dict:
    candidate = manifest.get("candidate_sha256")
    if not re.fullmatch(r"[0-9a-f]{64}", str(candidate or "")):
        raise ValueError("candidate manifest SHA-256 invalid")
    if raw.get("candidate_sha256") != candidate or evaluated.get("candidate_sha256") != candidate:
        raise ValueError("raw/evaluated surface candidate differs from manifest")
    if raw.get("status") != "EVIDENCE_ONLY" or raw.get("phase_complete") is not False or raw.get("production_approved") is not False:
        raise ValueError("raw surface report status differs")
    if evaluated.get("status") != "EVIDENCE_ONLY" or evaluated.get("phase_complete") is not False or evaluated.get("production_approved") is not False:
        raise ValueError("evaluated surface report status differs")

    blockers = raw_surface_blockers(raw)
    symmetry = raw.get("symmetry", {})
    if not symmetry.get("full_vertex_coverage"):
        blockers.append("raw symmetry vertex coverage incomplete")
    if symmetry.get("unmatched_face_ids"):
        blockers.append("raw symmetry has unmatched faces")

    normals = evaluated.get("normals", {})
    for field in ("invalid_polygon_normal_ids", "invalid_vertex_normal_ids"):
        rows = normals.get(field)
        if not isinstance(rows, list):
            blockers.append(field + " missing")
        elif rows:
            blockers.append(field + f" has {len(rows)} finding(s)")
    if normals.get("custom_normals_state") == "UNAVAILABLE_IN_THIS_BLENDER_API":
        blockers.append("custom/split-normal state unavailable in capture API")

    intersections = evaluated.get("self_intersection", {})
    pairs = intersections.get("intersecting_face_pairs")
    count = intersections.get("intersecting_face_pair_count")
    if not isinstance(pairs, list) or type(count) is not int or count != len(pairs):
        blockers.append("evaluated self-intersection pair evidence invalid")
    elif count:
        blockers.append(f"evaluated self-intersection has {count} non-adjacent face pair(s)")

    raw_count = raw.get("vertex_count")
    if type(raw_count) is not int or raw_count <= 0:
        raise ValueError("raw surface vertex count invalid")
    joint_issues = validate_joint_support(root, joint, candidate, raw_count)
    blockers.extend("joint_support: " + x for x in joint_issues)

    result = {
        "schema_version": 1,
        "status": "EVIDENCE_ONLY",
        "phase_complete": False,
        "production_approved": False,
        "candidate_sha256": candidate,
        "surface_quality_status": "BLOCKED" if blockers else "EVIDENCE_COMPLETE",
        "blockers": blockers,
        "raw_surface_summary": {
            "vertex_count": raw.get("vertex_count"),
            "face_count": raw.get("face_count"),
            "symmetry": raw.get("symmetry"),
        },
        "evaluated_surface_summary": {
            "vertex_count": evaluated.get("evaluated", {}).get("vertex_count"),
            "face_count": evaluated.get("evaluated", {}).get("face_count"),
            "custom_normals_state": normals.get("custom_normals_state"),
            "self_intersection_pair_count": count,
        },
        "joint_support_status": "BLOCKED" if joint_issues else "CONTRACT_COMPLETE",
        "limits": [
            "EVIDENCE_COMPLETE is not Phase 6 completion.",
            "Joint-support contract verification does not judge whether the authored loops look anatomically correct.",
            "Owner wire/surface review and full deformation/change audits remain separate Phase 6 evidence.",
            "No geometry, normals, weights, modifiers or topology are modified by this verifier.",
        ],
    }
    ensure_finite(result)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw-surface", type=Path, required=True)
    ap.add_argument("--evaluated-surface", type=Path, required=True)
    ap.add_argument("--joint-support", type=Path, required=True)
    ap.add_argument("--candidate-manifest", type=Path, required=True)
    ap.add_argument("--json-out", type=Path, required=True)
    args = ap.parse_args()
    try:
        if args.json_out.exists():
            raise ValueError("Phase 6 surface-quality output collision")
        inputs = [
            load_ref(ROOT, args.raw_surface, "raw surface"),
            load_ref(ROOT, args.evaluated_surface, "evaluated surface"),
            load_ref(ROOT, args.joint_support, "joint support"),
            load_ref(ROOT, args.candidate_manifest, "candidate manifest"),
        ]
        result = verify_packet(ROOT, inputs[0][1], inputs[1][1], inputs[2][1], inputs[3][1])
        result["source_evidence"] = [ref(path, ROOT) for path, _ in inputs]
        result["joint_support_template"] = {
            "path": JOINT_TEMPLATE,
            "sha256": digest(ROOT / JOINT_TEMPLATE),
        }
        result["verifier"] = {"path": HELPER, "sha256": digest(ROOT / HELPER)}
        result["source_git_commit"] = subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
        result["generated_utc"] = datetime.now(timezone.utc).isoformat()
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print("PHASE 6 SURFACE QUALITY", result["surface_quality_status"], "— evidence only")
        return 0 if result["surface_quality_status"] == "EVIDENCE_COMPLETE" else 1
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print("STOP — " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
