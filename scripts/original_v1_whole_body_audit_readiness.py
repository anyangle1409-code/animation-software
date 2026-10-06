#!/usr/bin/env python3
"""Validate that the ORIGINAL-v1 whole-body deformation audit is ready to execute.

This is an infrastructure/readiness check only. It never treats open anatomy
issues as a reason not to run the audit; instead it reports them separately as
model blockers that must be resolved before Phase 4 can be re-frozen.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from original_v1_whole_body_issues import blocking_issues, validate_ledger
from validate_original_v1_human_evidence import validate_coverage, validate_manifest

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "ORIGINAL_V1_WHOLE_BODY_DEFORMATION_AUDIT_PLAN.json"
MANIFEST = ROOT / "ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json"
COVERAGE = ROOT / "ORIGINAL_V1_HUMAN_EVIDENCE_COVERAGE.json"
ENVELOPE = ROOT / "ORIGINAL_V1_MOVEMENT_ENVELOPE.json"
LEDGER = ROOT / "ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json"

EXPECTED_ZONE_IDS = tuple(f"WBZ-{i:02d}" for i in range(1, 17))


def _load(value: Path | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, Path):
        data = json.loads(value.read_text(encoding="utf-8-sig"))
    else:
        data = value
    if not isinstance(data, dict):
        raise ValueError("expected JSON object")
    return data


def validate_plan(plan: dict[str, Any], envelope: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get("schema_version") != 1:
        errors.append("audit plan schema_version must be 1")
    if plan.get("status") != "PREPARED_WHOLE_BODY_DEFORMATION_AUDIT_PLAN":
        errors.append("audit plan status invalid")
    if plan.get("asset") != "HomeGymPT_Male_ORIGINAL_v1":
        errors.append("audit plan asset identity mismatch")
    if plan.get("production_approved") is not False:
        errors.append("audit plan must not claim production approval")

    categories = plan.get("movement_categories_required")
    if not isinstance(categories, list) or not categories or any(not isinstance(x, str) or not x for x in categories):
        errors.append("audit plan movement_categories_required invalid")
        categories = []
    required = [
        row.get("id") for row in envelope.get("required_categories", [])
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    ]
    if set(categories) != set(required) or len(categories) != len(set(categories)):
        errors.append("audit plan movement categories do not exactly match movement envelope")

    zones = plan.get("transition_zones")
    if not isinstance(zones, list):
        return errors + ["audit plan transition_zones missing"]
    ids = [row.get("id") for row in zones if isinstance(row, dict)]
    if tuple(ids) != EXPECTED_ZONE_IDS:
        errors.append("audit plan must contain ordered transition zones WBZ-01..WBZ-16 exactly once")
    category_set = set(required)
    for index, row in enumerate(zones):
        label = row.get("id", f"zone[{index}]") if isinstance(row, dict) else f"zone[{index}]"
        if not isinstance(row, dict):
            errors.append(label + ": zone must be an object")
            continue
        for field in ("name",):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(label + ": " + field + " missing")
        for field in ("structures", "movement_categories", "checks"):
            values = row.get(field)
            if not isinstance(values, list) or not values or any(not isinstance(x, str) or not x.strip() for x in values):
                errors.append(label + ": " + field + " invalid")
        for category in row.get("movement_categories", []) if isinstance(row.get("movement_categories"), list) else []:
            if category not in category_set:
                errors.append(label + ": unknown movement category " + str(category))

    used = {
        category for row in zones if isinstance(row, dict)
        for category in row.get("movement_categories", [])
        if isinstance(category, str)
    }
    missing = sorted(category_set - used)
    if missing:
        errors.append("movement categories not exercised by any transition zone: " + ", ".join(missing))

    temporal = plan.get("temporal_sampling") or {}
    classes = temporal.get("required_classes")
    needed = {
        "start", "outbound_intermediate", "peak_or_bottom",
        "return_intermediate", "end_or_loop_close", "turnaround_neighbourhood",
    }
    if not isinstance(classes, list) or not needed.issubset(set(classes)):
        errors.append("audit plan temporal sampling is incomplete")
    return list(dict.fromkeys(errors))


def assess(
    plan: dict[str, Any],
    manifest: dict[str, Any],
    coverage: dict[str, Any],
    envelope: dict[str, Any],
    ledger: dict[str, Any],
) -> dict[str, Any]:
    support_errors: list[str] = []
    support_errors += validate_plan(plan, envelope)
    support_errors += validate_manifest(manifest)
    support_errors += validate_coverage(coverage, manifest, envelope)
    ledger_errors = validate_ledger(ledger)
    support_errors += ["issue ledger: " + x for x in ledger_errors]

    blockers = [] if ledger_errors else blocking_issues(ledger)
    support_errors = list(dict.fromkeys(support_errors))
    return {
        "schema_version": 1,
        "status": "AUDIT_INFRASTRUCTURE_READY" if not support_errors else "AUDIT_INFRASTRUCTURE_BLOCKED",
        "audit_support_ready": not support_errors,
        "production_approved": False,
        "phase4_clear": not support_errors and not blockers,
        "support_errors": support_errors,
        "critical_high_blocker_count": len(blockers),
        "critical_high_blockers": [
            {
                "id": row.get("id"),
                "severity": row.get("severity"),
                "state": row.get("state"),
                "region": row.get("region"),
            }
            for row in blockers
        ],
        "next_rule": (
            "Run/fix the whole-body audit while blockers exist. Phase 4 re-freeze "
            "is eligible only after the blocker list is empty and the separate "
            "Phase 4 preflight also passes."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=PLAN)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--coverage", type=Path, default=COVERAGE)
    parser.add_argument("--movement-envelope", type=Path, default=ENVELOPE)
    parser.add_argument("--ledger", type=Path, default=LEDGER)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    try:
        result = assess(
            _load(args.plan),
            _load(args.manifest),
            _load(args.coverage),
            _load(args.movement_envelope),
            _load(args.ledger),
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        result = {
            "schema_version": 1,
            "status": "AUDIT_INFRASTRUCTURE_BLOCKED",
            "audit_support_ready": False,
            "production_approved": False,
            "phase4_clear": False,
            "support_errors": [str(exc)],
            "critical_high_blocker_count": 0,
            "critical_high_blockers": [],
        }
    payload = json.dumps(result, indent=2) + "\n"
    if args.json_out:
        if args.json_out.exists():
            raise SystemExit("STOP — output collision; preserve existing evidence")
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if result["audit_support_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
