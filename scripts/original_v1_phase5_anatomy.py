#!/usr/bin/env python3
"""Phase 5 regional anatomy evidence contract and packet verifier.

Prepared tooling only. It does not edit Blender, decide anatomy quality, mark Phase 5
complete, or set production approval. Actual modelling and real evidence remain required.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess

from original_v1_production_control import ROOT, build, digest, ensure_finite, read
from verify_original_v1_production_promotion import safe_path

PLAN = "ORIGINAL_V1_PHASE5_ANATOMY_EXECUTION_PLAN.json"
CAPTURE_PLAN = "ORIGINAL_V1_PHASE5_REGION_CAPTURE_PLAN.json"
HELPER = "scripts/original_v1_phase5_anatomy.py"
REQUIRED_CHECKS = (
    "scope_bound",
    "provenance_clean",
    "topology_correspondence",
    "mesh_weight_audit",
    "full_deformation_evidence",
    "comparisons_epoch_parent_freeze",
    "contacts_preserved",
    "captures_complete",
    "lineage_complete",
)


def ref_file(root: Path, ref: dict, label: str) -> Path:
    if not isinstance(ref, dict) or not ref.get("path") or not re.fullmatch(r"[0-9a-f]{64}", str(ref.get("sha256", ""))):
        raise ValueError(f"{label} path/SHA-256 reference required")
    path = safe_path(root, ref["path"])
    if not path.is_file() or digest(path) != ref["sha256"]:
        raise ValueError(f"{label} hash/path differs")
    return path


def load_plan(root: Path) -> dict:
    path = root / PLAN
    plan = json.loads(path.read_text(encoding="utf-8"))
    ensure_finite(plan)
    if plan.get("schema_version") != 1 or plan.get("phase") != 5:
        raise ValueError("Phase 5 execution plan identity differs")
    if plan.get("status") != "PREPARED_PHASE5_EXECUTION_PLAN":
        raise ValueError("unexpected Phase 5 execution-plan status")
    if plan.get("production_approved") is not False or plan.get("phase_complete") is not False:
        raise ValueError("Phase 5 execution plan cannot claim approval/completion")
    order = plan.get("order")
    if order != ["5A", "5B", "5C", "5D", "5E", "5F", "5G"]:
        raise ValueError("Phase 5 region order differs")
    regions = plan.get("regions")
    if not isinstance(regions, dict) or set(regions) != set(order):
        raise ValueError("Phase 5 region definitions incomplete")
    for region in order:
        row = regions[region]
        package = root / row["work_package"]
        if not package.is_file():
            raise ValueError(f"{region} work package missing")
        if not row.get("focused_poses") or not row.get("required_views"):
            raise ValueError(f"{region} coverage definition incomplete")
    rig = plan.get("rig_contract")
    if not isinstance(rig, dict):
        raise ValueError("Phase 5 locked rig contract missing")
    lock = read(root, rig.get("lock_path", ""))
    lock_rig = lock.get("rig", {})
    expected = {
        "identity": lock_rig.get("identity"),
        "revision": lock_rig.get("revision"),
        "rig_structure_sha256": lock_rig.get("rig_structure_sha256"),
        "bone_count": lock_rig.get("bone_count"),
        "deform_bone_count": lock_rig.get("deform_bone_count"),
    }
    actual = {k: rig.get(k) for k in expected}
    if actual != expected:
        raise ValueError("Phase 5 locked rig contract disagrees with skeleton-motion lock")
    if rig.get("payload") != lock_rig.get("payload", {}).get("path") or rig.get("payload_sha256") != lock_rig.get("payload", {}).get("sha256"):
        raise ValueError("Phase 5 locked rig payload disagrees with skeleton-motion lock")
    helpers = lock.get("helper_decisions", {}).get("added", [])
    if rig.get("helper_bones") != helpers:
        raise ValueError("Phase 5 helper-bone contract disagrees with skeleton-motion lock")
    capture_plan = read(root, CAPTURE_PLAN)
    if capture_plan.get("schema_version") != 1 or capture_plan.get("status") != "PREPARED_PHASE5_REGION_CAPTURE_PLAN":
        raise ValueError("Phase 5 regional capture plan identity differs")
    if set(capture_plan.get("regions", {})) != set(order):
        raise ValueError("Phase 5 regional capture coverage incomplete")
    for region in order:
        capture_ids = [x.get("id") for x in capture_plan["regions"][region].get("captures", [])]
        if capture_ids != regions[region].get("required_views") or regions[region].get("required_capture_ids") != capture_ids:
            raise ValueError(f"{region} capture coverage differs from anatomy plan")
    return plan


def predecessor(plan: dict, region: str) -> str | None:
    order = plan["order"]
    if region not in order:
        raise ValueError("unsupported Phase 5 region")
    index = order.index(region)
    return None if index == 0 else order[index - 1]


def evidence_refs(root: Path, refs) -> set[tuple[str, str]]:
    if not isinstance(refs, list) or not refs:
        raise ValueError("source evidence list required")
    seen = set()
    for ref in refs:
        path = ref_file(root, ref, "source evidence")
        identity = (path.relative_to(root.resolve()).as_posix(), ref["sha256"])
        if identity in seen:
            raise ValueError("duplicate source evidence reference")
        seen.add(identity)
    return seen


def verify_previous_receipt(root: Path, ref: dict, expected_region: str, expected_candidate_sha: str) -> dict:
    path = ref_file(root, ref, "previous region receipt")
    receipt = json.loads(path.read_text(encoding="utf-8"))
    ensure_finite(receipt)
    if receipt.get("contract_status") != "REGION_EVIDENCE_VERIFIED":
        raise ValueError("previous region receipt is not verified")
    if receipt.get("region") != expected_region:
        raise ValueError("previous region receipt has wrong region")
    if receipt.get("candidate_sha256") != expected_candidate_sha:
        raise ValueError("previous region candidate does not equal current parent")
    if receipt.get("production_approved") is not False:
        raise ValueError("previous region receipt cannot claim production approval")
    return receipt


def verify_region_report(root: Path, report: dict, plan: dict, region: str, expected_freeze_sha: str | None = None, expected_epoch_revision: str | None = None, expected_epoch_sha: str | None = None) -> list[str]:
    issues = []
    if not isinstance(report, dict):
        return ["regional anatomy report must be an object"]
    try:
        ensure_finite(report)
    except ValueError as exc:
        issues.append(str(exc))
    row = plan["regions"].get(region)
    if row is None:
        return ["unsupported Phase 5 region"]
    sha = report.get("candidate_sha256")
    parent_sha = report.get("parent_candidate_sha256")
    freeze_sha = report.get("development_freeze_candidate_sha256")
    epoch_revision = report.get("active_epoch_baseline_revision")
    epoch_sha = report.get("active_epoch_baseline_candidate_sha256")

    if report.get("schema_version") != 1 or report.get("phase") != 5 or report.get("region") != region:
        issues.append("regional report identity/schema differs")
    if report.get("status") != "REGION_EVIDENCE_COMPLETE":
        issues.append("regional report must be REGION_EVIDENCE_COMPLETE")
    if report.get("production_approved") is not False or report.get("phase_complete") is not False:
        issues.append("regional report cannot claim phase/production completion")
    for value, label in ((sha, "candidate"), (parent_sha, "parent"), (freeze_sha, "development-freeze candidate")):
        if not re.fullmatch(r"[0-9a-f]{64}", str(value or "")):
            issues.append(f"invalid {label} SHA-256")
    if not isinstance(epoch_revision, str) or not epoch_revision:
        issues.append("active epoch baseline revision required")
    if not re.fullmatch(r"[0-9a-f]{64}", str(epoch_sha or "")):
        issues.append("invalid active epoch baseline candidate SHA-256")
    if expected_freeze_sha is not None and freeze_sha != expected_freeze_sha:
        issues.append("development-freeze candidate SHA differs from recorded Phase 4 freeze")
    if expected_epoch_revision is not None and epoch_revision != expected_epoch_revision:
        issues.append("active epoch baseline revision differs from generated state")
    if expected_epoch_sha is not None and epoch_sha != expected_epoch_sha:
        issues.append("active epoch baseline candidate SHA differs from generated state")
    if sha == parent_sha:
        issues.append("regional candidate must differ from its parent")
    if not re.fullmatch(r"r[0-9]+[a-z]?", str(report.get("candidate_revision", "")), re.I):
        issues.append("candidate revision missing/invalid")
    if not re.fullmatch(r"r[0-9]+[a-z]?", str(report.get("parent_revision", "")), re.I):
        issues.append("parent revision missing/invalid")
    if not re.fullmatch(r"[0-9a-f]{40}", str(report.get("source_git_commit", ""))):
        issues.append("exact source git commit required")
    try:
        stamp = datetime.fromisoformat(str(report.get("evidence_timestamp", "")).replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            raise ValueError("timezone")
    except (ValueError, TypeError):
        issues.append("timezone-aware evidence timestamp required")
    if report.get("owner_review") not in ("pending", "accepted", "rejected") or report.get("blocking") is not False:
        issues.append("owner review must be explicit and routine review non-blocking")
    if report.get("work_package") != row["work_package"]:
        issues.append("regional work-package identity differs")
    if report.get("permitted_scope") != row["permitted_scope"]:
        issues.append("permitted anatomy scope differs from frozen plan")

    poses = report.get("focused_poses")
    if poses != row["focused_poses"]:
        issues.append("focused-pose coverage differs from plan")
    views = report.get("required_views")
    if views != row["required_views"]:
        issues.append("required-view coverage differs from plan")

    checks = report.get("checks")
    if not isinstance(checks, list) or any(not isinstance(x, dict) for x in checks):
        issues.append("invalid regional check rows")
        checks = []
    ids = [x.get("id") for x in checks]
    if len(ids) != len(set(ids)):
        issues.append("duplicate regional check IDs")
    if set(ids) != set(REQUIRED_CHECKS):
        issues.append("regional checks must exactly cover required check IDs")
    if any(x.get("passed") is not True for x in checks):
        issues.append("regional report contains failing/unknown checks")

    try:
        sources = evidence_refs(root, report.get("source_evidence"))
        for check in checks:
            refs = evidence_refs(root, check.get("evidence"))
            if not refs.issubset(sources):
                raise ValueError(f"{check.get('id')}: check evidence absent from source_evidence")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        issues.append(str(exc))

    required_artifacts = plan["per_region_required_evidence"]
    artifacts = report.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != set(required_artifacts):
        issues.append("regional artifact inventory must exactly cover required evidence")
    else:
        for key in required_artifacts:
            try:
                ref_file(root, artifacts[key], key)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                issues.append(f"{key}: {exc}")

    prev = predecessor(plan, region)
    if prev is None:
        if report.get("previous_region_receipt") not in (None, {}):
            issues.append("5A must not claim a previous region receipt")
    else:
        try:
            verify_previous_receipt(root, report.get("previous_region_receipt"), prev, parent_sha)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            issues.append(str(exc))

    return list(dict.fromkeys(issues))


def make_template(plan: dict, region: str, state: dict, control: dict | None = None) -> dict:
    row = plan["regions"][region]
    prev = predecessor(plan, region)
    required_artifacts = {name: {"path": None, "sha256": None} for name in plan["per_region_required_evidence"]}
    control = control or {}
    freeze_record = (control.get("phase_completion_records") or {}).get("4") or {}
    pinned = state.get("pinned_baseline") or {}
    return {
        "schema_version": 1,
        "phase": 5,
        "region": region,
        "region_name": row["name"],
        "status": "INCOMPLETE",
        "phase_complete": False,
        "production_approved": False,
        "candidate_revision": None,
        "candidate_sha256": None,
        "parent_revision": state.get("current_candidate"),
        "parent_candidate_sha256": state.get("last_known_candidate_sha256"),
        "development_freeze_candidate_sha256": freeze_record.get("candidate_sha256"),
        "active_epoch_baseline_revision": pinned.get("revision"),
        "active_epoch_baseline_candidate_sha256": pinned.get("candidate_sha256"),
        "source_git_commit": None,
        "evidence_timestamp": None,
        "work_package": row["work_package"],
        "permitted_scope": row["permitted_scope"],
        "protected_boundaries": row["protected_boundaries"],
        "focused_poses": row["focused_poses"],
        "required_views": row["required_views"],
        "owner_review": "pending",
        "blocking": False,
        "previous_region_receipt": None if prev is None else {"path": None, "sha256": None},
        "checks": [{"id": name, "passed": None, "evidence": []} for name in REQUIRED_CHECKS],
        "source_evidence": [],
        "artifacts": required_artifacts,
        "entry_state": {
            "current_phase": state.get("current_phase"),
            "current_subphase": state.get("current_subphase"),
            "phase4_state": state.get("phases", {}).get("4", {}).get("state"),
            "region_predecessor": prev,
            "locked_rig_revision": plan["rig_contract"]["revision"],
            "locked_rig_bone_count": plan["rig_contract"]["bone_count"],
        },
        "note": "INCOMPLETE template only. Do not convert placeholders to PASS without actual Blender/model evidence.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report", type=Path, nargs="?")
    ap.add_argument("--region", required=True, choices=["5A","5B","5C","5D","5E","5F","5G"])
    ap.add_argument("--template", action="store_true")
    ap.add_argument("--json-out", type=Path, required=True)
    args = ap.parse_args()
    try:
        if args.json_out.exists():
            raise ValueError("Phase 5 anatomy output collision; preserve prior evidence")
        plan = load_plan(ROOT)
        state, _ = build(ROOT)
        control = read(ROOT, "ORIGINAL_V1_PRODUCTION_CONTROL.json")
        if args.template:
            if args.report is not None:
                raise ValueError("template mode takes no report")
            result = make_template(plan, args.region, state, control)
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            print(f"INCOMPLETE {args.region} ANATOMY TEMPLATE — Phase 5 not advanced")
            return 0
        if args.report is None:
            raise ValueError("regional report required unless --template")
        report_path = args.report.resolve()
        if not report_path.is_relative_to(ROOT.resolve()):
            raise ValueError("regional report must remain inside repository")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        freeze_record = (control.get("phase_completion_records") or {}).get("4") or {}
        pinned = state.get("pinned_baseline") or {}
        issues = verify_region_report(
            ROOT, report, plan, args.region,
            expected_freeze_sha=freeze_record.get("candidate_sha256"),
            expected_epoch_revision=pinned.get("revision"),
            expected_epoch_sha=pinned.get("candidate_sha256"),
        )
        if state.get("phases", {}).get("4", {}).get("state") != "complete":
            issues.append("Phase 4 development freeze is incomplete")
        elif not freeze_record.get("candidate_sha256"):
            issues.append("Phase 4 completion record lacks candidate SHA identity")
        if state.get("last_known_candidate_sha256") != report.get("candidate_sha256"):
            issues.append("regional report is not bound to latest complete candidate")
        result = {
            "schema_version": 1,
            "phase": 5,
            "region": args.region,
            "contract_status": "REFUSED" if issues else "REGION_EVIDENCE_VERIFIED",
            "phase_complete": False,
            "production_approved": False,
            "issues": list(dict.fromkeys(issues)),
            "candidate_sha256": report.get("candidate_sha256") if isinstance(report, dict) else None,
            "region_report": {
                "path": report_path.relative_to(ROOT).as_posix(),
                "sha256": digest(report_path),
            },
            "plan": {"path": PLAN, "sha256": digest(ROOT / PLAN)},
            "source_git_commit": subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
            "note": "Regional evidence verification only. Convincing anatomy remains a real modelling/review requirement; Phase 5 completion is separate.",
        }
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 1 if issues else 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print("STOP — " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
