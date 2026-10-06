#!/usr/bin/env python3
"""Fail-closed whole-body deformation audit gate for ORIGINAL-v1.

This gate is candidate-bound and requires all 16 anatomical transition zones,
all movement-envelope categories, start/intermediate/peak/return/reversal
coverage, numerical evidence, production-path visual evidence, real-human
reference binding, whole-body regression success and a clear Critical/High
anatomy ledger.

It never mutates the model, ledger, phase state or production approval.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

from original_v1_anatomy_issue_closure import verify_closed_issues
from original_v1_production_control import digest
from original_v1_whole_body_issues import blocking_issues, validate_ledger
from original_v1_whole_body_audit_readiness import validate_plan
from validate_original_v1_human_evidence import validate_coverage, validate_manifest

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "ORIGINAL_V1_WHOLE_BODY_DEFORMATION_AUDIT_PLAN.json"
ENVELOPE = ROOT / "ORIGINAL_V1_MOVEMENT_ENVELOPE.json"
MANIFEST = ROOT / "ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json"
COVERAGE = ROOT / "ORIGINAL_V1_HUMAN_EVIDENCE_COVERAGE.json"
LEDGER = ROOT / "ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json"

STATUS = "WHOLE_BODY_AUDIT_EVIDENCE"
REQUIRED_TEMPORAL_CLASSES = {
    "start",
    "outbound_intermediate",
    "peak_or_bottom",
    "return_intermediate",
    "end_or_loop_close",
    "turnaround_neighbourhood",
}


def _load(path_or_record: Path | dict[str, Any]) -> dict[str, Any]:
    if isinstance(path_or_record, Path):
        data = json.loads(path_or_record.read_text(encoding="utf-8-sig"))
    else:
        data = path_or_record
    if not isinstance(data, dict):
        raise ValueError("expected JSON object")
    return data


def _safe_ref(root: Path, ref: object, label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(ref, dict):
        return [label + ": evidence ref must be an object"]
    relative = ref.get("path")
    sha = ref.get("sha256")
    if not isinstance(relative, str) or not relative:
        errors.append(label + ": evidence path missing")
        return errors
    if not re.fullmatch(r"[0-9a-f]{64}", str(sha or "")):
        errors.append(label + ": evidence SHA-256 invalid")
        return errors
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        errors.append(label + ": evidence path missing/outside repository")
        return errors
    if digest(path) != sha:
        errors.append(label + ": evidence hash differs")
    if ref.get("passed") is not True:
        errors.append(label + ": passed=true required")
    return errors


def _refs(root: Path, value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        return [label + " evidence refs missing"]
    errors: list[str] = []
    for index, ref in enumerate(value):
        errors += _safe_ref(root, ref, f"{label}[{index}]")
    return errors


def verify_audit(
    root: Path,
    record: dict[str, Any],
    plan: dict[str, Any],
    envelope: dict[str, Any],
    manifest: dict[str, Any],
    coverage: dict[str, Any],
    ledger: dict[str, Any],
    *,
    expected_revision: str,
    expected_candidate_sha256: str,
) -> list[str]:
    errors: list[str] = []

    if record.get("schema_version") != 1 or record.get("status") != STATUS:
        errors.append("audit record schema/status invalid")
    if record.get("production_approved") is not False:
        errors.append("audit record must not claim production approval")
    if record.get("candidate_revision") != expected_revision:
        errors.append("audit candidate revision differs")
    if record.get("candidate_sha256") != expected_candidate_sha256:
        errors.append("audit candidate SHA differs")
    if not re.fullmatch(r"r\d+", str(expected_revision or "")):
        errors.append("expected candidate revision invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", str(expected_candidate_sha256 or "")):
        errors.append("expected candidate SHA invalid")
    if not re.fullmatch(r"[0-9a-f]{40}", str(record.get("source_git_commit") or "")):
        errors.append("audit source Git commit invalid")
    if record.get("production_path_rendered") is not True:
        errors.append("production_path_rendered must be true")
    if record.get("whole_body_regression_pass") is not True:
        errors.append("whole_body_regression_pass must be true")

    plan_errors = validate_plan(plan, envelope)
    errors += ["audit plan: " + x for x in plan_errors]
    manifest_errors = validate_manifest(manifest)
    errors += ["human evidence: " + x for x in manifest_errors]
    coverage_errors = validate_coverage(coverage, manifest, envelope)
    errors += ["human evidence coverage: " + x for x in coverage_errors]
    ledger_errors = validate_ledger(ledger, root)
    errors += ["issue ledger: " + x for x in ledger_errors]
    blockers = [] if ledger_errors else blocking_issues(ledger)
    if blockers:
        errors.append("Critical/High whole-body anatomy blockers remain")
        errors += [
            f"blocking issue {row.get('id')} [{row.get('severity')}] {row.get('state')}"
            for row in blockers
        ]
    elif not ledger_errors:
        errors += ["issue closure: " + x for x in verify_closed_issues(root, ledger, manifest)]

    verified_human = {
        row.get("id") for row in manifest.get("entries", [])
        if isinstance(row, dict) and row.get("review_status") == "verified"
    }
    coverage_by_category = {
        row.get("id"): set(row.get("evidence_ids", []))
        for row in coverage.get("categories", [])
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    }
    plan_zones = plan.get("transition_zones")
    if not isinstance(plan_zones, list) or not plan_zones:
        return list(dict.fromkeys(errors + ["audit plan transition zones missing"]))
    plan_by_zone = {row.get("id"): row for row in plan_zones if isinstance(row, dict)}
    expected_zone_ids = [row.get("id") for row in plan_zones if isinstance(row, dict)]

    zone_rows = record.get("transition_zones")
    if not isinstance(zone_rows, list):
        zone_rows = []
        errors.append("audit transition_zones missing")
    zone_ids = [row.get("id") for row in zone_rows if isinstance(row, dict)]
    if zone_ids != expected_zone_ids or len(zone_ids) != len(set(zone_ids)):
        errors.append("audit transition zones do not exactly match ordered plan zones")
    record_by_zone = {
        row.get("id"): row for row in zone_rows
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    }

    for zone_id in expected_zone_ids:
        row = record_by_zone.get(zone_id)
        zone = plan_by_zone.get(zone_id) or {}
        if not isinstance(row, dict):
            errors.append(zone_id + ": audit row missing")
            continue
        if row.get("status") != "PASS":
            errors.append(zone_id + ": status PASS required")
        if row.get("candidate_sha256") != expected_candidate_sha256:
            errors.append(zone_id + ": candidate SHA differs")
        temporal = row.get("temporal_classes")
        if not isinstance(temporal, list) or not REQUIRED_TEMPORAL_CLASSES.issubset(set(temporal)):
            errors.append(zone_id + ": temporal coverage incomplete")
        errors += _refs(root, row.get("visual_evidence"), zone_id + " visual")
        errors += _refs(root, row.get("numerical_evidence"), zone_id + " numerical")
        human_ids = row.get("human_evidence_ids")
        if not isinstance(human_ids, list) or not human_ids:
            errors.append(zone_id + ": human evidence ids missing")
            human_ids = []
        for evidence_id in human_ids:
            if evidence_id not in verified_human:
                errors.append(zone_id + ": unknown/unverified human evidence " + str(evidence_id))
        for category in zone.get("movement_categories", []):
            allowed = coverage_by_category.get(category, set())
            if allowed and not (set(human_ids) & allowed):
                errors.append(zone_id + ": no human evidence bound for movement category " + category)
        note = row.get("review_note")
        if not isinstance(note, str) or not note.strip():
            errors.append(zone_id + ": review note required")

    expected_categories = [
        row.get("id") for row in envelope.get("required_categories", [])
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    ]
    movement_rows = record.get("movement_categories")
    if not isinstance(movement_rows, list):
        movement_rows = []
        errors.append("audit movement_categories missing")
    movement_ids = [row.get("id") for row in movement_rows if isinstance(row, dict)]
    if movement_ids != expected_categories or len(movement_ids) != len(set(movement_ids)):
        errors.append("audit movement categories do not exactly match movement envelope")
    movement_by_id = {
        row.get("id"): row for row in movement_rows
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    }

    for category in expected_categories:
        row = movement_by_id.get(category)
        if not isinstance(row, dict):
            errors.append(category + ": movement audit row missing")
            continue
        if row.get("status") != "PASS":
            errors.append(category + ": movement status PASS required")
        zone_refs = row.get("transition_zone_ids")
        if not isinstance(zone_refs, list) or not zone_refs:
            errors.append(category + ": transition_zone_ids missing")
            zone_refs = []
        for zone_id in zone_refs:
            if zone_id not in plan_by_zone:
                errors.append(category + ": unknown transition zone " + str(zone_id))
            elif category not in (plan_by_zone[zone_id].get("movement_categories") or []):
                errors.append(category + ": transition zone does not declare this movement category: " + zone_id)
        if not any(
            category in (plan_by_zone.get(zone_id, {}).get("movement_categories") or [])
            for zone_id in zone_refs
        ):
            errors.append(category + ": no valid transition-zone coverage")
        human_ids = row.get("human_evidence_ids")
        if not isinstance(human_ids, list) or not human_ids:
            errors.append(category + ": human evidence ids missing")
        else:
            allowed = coverage_by_category.get(category, set())
            if allowed and not (set(human_ids) & allowed):
                errors.append(category + ": movement row does not bind declared evidence coverage")
            for evidence_id in human_ids:
                if evidence_id not in verified_human:
                    errors.append(category + ": unknown/unverified human evidence " + str(evidence_id))
        note = row.get("review_note")
        if not isinstance(note, str) or not note.strip():
            errors.append(category + ": review note required")

    return list(dict.fromkeys(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("audit_record", type=Path)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--candidate-sha256", required=True)
    parser.add_argument("--plan", type=Path, default=PLAN)
    parser.add_argument("--movement-envelope", type=Path, default=ENVELOPE)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--coverage", type=Path, default=COVERAGE)
    parser.add_argument("--ledger", type=Path, default=LEDGER)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    try:
        record = _load(args.audit_record)
        errors = verify_audit(
            ROOT,
            record,
            _load(args.plan),
            _load(args.movement_envelope),
            _load(args.manifest),
            _load(args.coverage),
            _load(args.ledger),
            expected_revision=args.candidate,
            expected_candidate_sha256=args.candidate_sha256,
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        errors = [str(exc)]

    result = {
        "schema_version": 1,
        "status": "PASS" if not errors else "BLOCKED",
        "production_approved": False,
        "candidate_revision": args.candidate,
        "candidate_sha256": args.candidate_sha256,
        "whole_body_audit_pass": not errors,
        "issues": errors,
        "rule": "Every movement category and anatomical transition zone requires candidate-bound numerical, production-path visual and verified human-evidence review before Phase 4 re-freeze.",
    }
    payload = json.dumps(result, indent=2) + "\n"
    if args.json_out:
        if args.json_out.exists():
            raise SystemExit("STOP — output collision; preserve existing evidence")
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
