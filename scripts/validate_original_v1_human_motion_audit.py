#!/usr/bin/env python3
"""Validate ORIGINAL v1 whole-body human-motion audit plans and candidate ledgers."""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "ORIGINAL_V1_HUMAN_MOTION_AUDIT_PLAN.json"
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
VALID_OWNER = {"pending", "accepted", "rejected"}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_finite(value, where="root"):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{where}: non-finite number")
    if isinstance(value, dict):
        for key, child in value.items():
            ensure_finite(child, f"{where}.{key}")
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            ensure_finite(child, f"{where}[{idx}]")


def validate_plan(plan):
    ensure_finite(plan)
    if plan.get("schema_version") != 1:
        raise ValueError("plan schema_version must be 1")
    if plan.get("status") != "PREPARED_HUMAN_MOTION_REALISM_AUDIT":
        raise ValueError("unexpected plan status")
    if plan.get("production_approved") is not False:
        raise ValueError("plan may not claim production approval")

    required_states = set(plan.get("required_states") or [])
    expected_states = {
        "neutral", "lengthened_or_elevated", "compressed_or_loaded",
        "intermediate_transition",
    }
    if required_states != expected_states:
        raise ValueError("required state contract differs")

    dimensions = plan.get("realism_dimensions") or []
    if len(dimensions) != len(set(dimensions)) or len(dimensions) < 8:
        raise ValueError("realism dimensions incomplete or duplicated")

    regions = plan.get("regions") or []
    region_ids = [row.get("id") for row in regions]
    if len(regions) < 12 or len(region_ids) != len(set(region_ids)):
        raise ValueError("whole-body region coverage incomplete or duplicated")
    for row in regions:
        if not row.get("name") or not row.get("transitions"):
            raise ValueError(f"{row.get('id')}: missing transitions")
        if not row.get("movement_families") or not row.get("expected"):
            raise ValueError(f"{row.get('id')}: missing movement/expected behaviour")

    families = plan.get("movement_families") or []
    family_ids = [row.get("id") for row in families]
    if len(family_ids) != len(set(family_ids)) or len(family_ids) < 14:
        raise ValueError("movement-family coverage incomplete or duplicated")
    known_families = set(family_ids)
    for row in regions:
        unknown = set(row["movement_families"]) - known_families
        if unknown:
            raise ValueError(f"{row['id']}: unknown movement families {sorted(unknown)}")
    for row in families:
        if not row.get("samples"):
            raise ValueError(f"{row.get('id')}: no motion samples")

    sweep = plan.get("axilla_chest_sweep") or {}
    if sweep.get("required") is not True:
        raise ValueError("axilla/chest sweep must be required")
    if sweep.get("sides") != ["left", "right"]:
        raise ValueError("axilla/chest sweep must cover both sides")
    elevations = sweep.get("arm_elevation_degrees") or []
    if elevations != [0, 45, 90, 120, 150, 170]:
        raise ValueError("axilla/chest elevation sweep differs")
    if sweep.get("include_return_transition") is not True:
        raise ValueError("axilla/chest return transition missing")

    severities = plan.get("severities") or {}
    if set(severities) != {"CRITICAL", "HIGH", "MEDIUM", "LOW"}:
        raise ValueError("severity contract differs")
    if not severities["CRITICAL"].get("blocks") or not severities["HIGH"].get("blocks"):
        raise ValueError("critical/high defects must block")

    fields = plan.get("defect_ledger_required_fields") or []
    if len(fields) != len(set(fields)) or "candidate_sha256" not in fields:
        raise ValueError("defect-ledger field contract invalid")

    statuses = set(plan.get("allowed_defect_status") or [])
    expected_statuses = {
        "OPEN", "FIX_IN_PROGRESS", "FIXED_VERIFIED",
        "ACCEPTED_LIMITATION", "REJECTED_CANDIDATE",
    }
    if statuses != expected_statuses:
        raise ValueError("defect status contract differs")
    return plan


def validate_ledger(plan, ledger, require_exit=False):
    ensure_finite(ledger)
    if ledger.get("schema_version") != 1:
        raise ValueError("ledger schema_version must be 1")
    if ledger.get("production_approved") is not False:
        raise ValueError("human-motion ledger may not claim production approval")

    revision = ledger.get("candidate_revision")
    sha = ledger.get("candidate_sha256")
    if not isinstance(revision, str) or not re.fullmatch(r"r\d+[a-z]?", revision, re.I):
        raise ValueError("candidate_revision missing/invalid")
    if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
        raise ValueError("candidate_sha256 missing/invalid")

    known_regions = {row["id"] for row in plan["regions"]}
    known_families = {row["id"] for row in plan["movement_families"]}
    required_states = set(plan["required_states"])
    allowed_status = set(plan["allowed_defect_status"])
    required_fields = set(plan["defect_ledger_required_fields"])

    refs = ledger.get("reference_observations") or []
    ref_ids = []
    for row in refs:
        rid = row.get("id")
        if not isinstance(rid, str) or not rid:
            raise ValueError("reference observation missing id")
        ref_ids.append(rid)
        if row.get("source_kind") not in {"real_human_video", "real_human_photo_sequence", "anatomy_kinesiology"}:
            raise ValueError(f"{rid}: invalid source_kind")
        if not row.get("title") or not row.get("locator") or not row.get("observations"):
            raise ValueError(f"{rid}: incomplete reference observation")
    if len(ref_ids) != len(set(ref_ids)):
        raise ValueError("duplicate reference observation id")

    coverage = ledger.get("coverage") or []
    by_region = {}
    for row in coverage:
        region = row.get("region")
        if region not in known_regions:
            raise ValueError(f"unknown coverage region {region}")
        if row.get("candidate_sha256") != sha:
            raise ValueError(f"{region}: coverage candidate SHA differs")
        states = set(row.get("states") or [])
        if not states.issubset(required_states):
            raise ValueError(f"{region}: unknown coverage state")
        families = set(row.get("movement_families") or [])
        if not families.issubset(known_families):
            raise ValueError(f"{region}: unknown movement family")
        if not row.get("capture_ids"):
            raise ValueError(f"{region}: no capture evidence")
        by_region.setdefault(region, {"states": set(), "families": set(), "captures": set()})
        by_region[region]["states"].update(states)
        by_region[region]["families"].update(families)
        by_region[region]["captures"].update(row["capture_ids"])

    defects = ledger.get("defects") or []
    defect_ids = []
    open_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for row in defects:
        missing = [key for key in required_fields if key not in row]
        if missing:
            raise ValueError(f"defect missing fields: {sorted(missing)}")
        did = row["defect_id"]
        defect_ids.append(did)
        if row["candidate_revision"] != revision or row["candidate_sha256"] != sha:
            raise ValueError(f"{did}: candidate identity differs")
        if row["region"] not in known_regions:
            raise ValueError(f"{did}: unknown region")
        if row["movement_family"] not in known_families:
            raise ValueError(f"{did}: unknown movement family")
        severity = row["severity"]
        if severity not in plan["severities"]:
            raise ValueError(f"{did}: unknown severity")
        if row["status"] not in allowed_status:
            raise ValueError(f"{did}: unknown status")
        if row["owner_review"] not in VALID_OWNER:
            raise ValueError(f"{did}: invalid owner review")
        for rid in row.get("reference_observations") or []:
            if rid not in ref_ids:
                raise ValueError(f"{did}: unknown reference observation {rid}")
        if row["status"] in {"OPEN", "FIX_IN_PROGRESS"}:
            open_counts[severity] += 1
        if row["status"] == "FIXED_VERIFIED":
            if not row.get("after_evidence") or not row.get("regression_contact_result"):
                raise ValueError(f"{did}: fixed verification lacks after/regression evidence")
    if len(defect_ids) != len(set(defect_ids)):
        raise ValueError("duplicate defect id")

    sweep_rows = ledger.get("axilla_chest_sweep") or []
    sweep_required = {
        (side, deg)
        for side in plan["axilla_chest_sweep"]["sides"]
        for deg in plan["axilla_chest_sweep"]["arm_elevation_degrees"]
    }
    sweep_seen = set()
    return_seen = set()
    for row in sweep_rows:
        if row.get("candidate_sha256") != sha:
            raise ValueError("axilla sweep candidate SHA differs")
        key = (row.get("side"), row.get("elevation_degrees"))
        if key not in sweep_required:
            raise ValueError(f"unexpected axilla sweep checkpoint {key}")
        if not row.get("capture_id"):
            raise ValueError(f"axilla sweep {key}: capture missing")
        sweep_seen.add(key)
        if row.get("direction") == "return":
            return_seen.add(row.get("side"))

    if require_exit:
        missing_regions = sorted(known_regions - set(by_region))
        if missing_regions:
            raise ValueError(f"exit blocked: missing regions {missing_regions}")
        incomplete_states = sorted(
            region for region in known_regions
            if not required_states.issubset(by_region[region]["states"])
        )
        if incomplete_states:
            raise ValueError(f"exit blocked: incomplete state coverage {incomplete_states}")
        missing_sweep = sorted(sweep_required - sweep_seen)
        if missing_sweep:
            raise ValueError(f"exit blocked: axilla/chest sweep incomplete {missing_sweep}")
        if set(plan["axilla_chest_sweep"]["sides"]) - return_seen:
            raise ValueError("exit blocked: axilla/chest return-transition evidence incomplete")
        if open_counts["CRITICAL"] or open_counts["HIGH"]:
            raise ValueError(
                "exit blocked: open critical/high defects "
                f"{open_counts['CRITICAL']}/{open_counts['HIGH']}"
            )

    return {
        "candidate_revision": revision,
        "candidate_sha256": sha,
        "regions_with_evidence": len(by_region),
        "total_regions": len(known_regions),
        "reference_observations": len(refs),
        "defects": len(defects),
        "open_by_severity": open_counts,
        "axilla_checkpoints": len(sweep_seen),
        "axilla_required_checkpoints": len(sweep_required),
        "exit_checked": bool(require_exit),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default=str(PLAN_PATH))
    ap.add_argument("--ledger")
    ap.add_argument("--require-exit", action="store_true")
    args = ap.parse_args()
    try:
        plan = validate_plan(read_json(Path(args.plan)))
        print("HUMAN MOTION AUDIT PLAN: PASS")
        if args.ledger:
            summary = validate_ledger(plan, read_json(Path(args.ledger)), args.require_exit)
            print(json.dumps(summary, indent=2))
        elif args.require_exit:
            raise ValueError("--require-exit requires --ledger")
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print("STOP — " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
