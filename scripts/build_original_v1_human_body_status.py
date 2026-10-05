#!/usr/bin/env python3
"""Build the authoritative ORIGINAL-v1 human-body status dashboard.

Reads:
  ORIGINAL_V1_HUMAN_BODY_MASTER_PLAN.json
  ORIGINAL_V1_HUMAN_BODY_COVERAGE_MATRIX.json
  ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json
  ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json

Writes:
  ORIGINAL_V1_HUMAN_BODY_STATUS.json
  docs/ORIGINAL_V1_HUMAN_BODY_STATUS.md

This generator never edits a model and never infers owner or production approval.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "ORIGINAL_V1_HUMAN_BODY_MASTER_PLAN.json"
COVERAGE = ROOT / "ORIGINAL_V1_HUMAN_BODY_COVERAGE_MATRIX.json"
ISSUES = ROOT / "ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json"
HUMAN = ROOT / "ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json"
SWEEPS = ROOT / "ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PLAN.json"
COUPLING = ROOT / "ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json"
OUT_JSON = ROOT / "ORIGINAL_V1_HUMAN_BODY_STATUS.json"
OUT_MD = ROOT / "docs/ORIGINAL_V1_HUMAN_BODY_STATUS.md"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def build():
    plan, cov, ledger, human, sweeps, coupling = map(read, (PLAN, COVERAGE, ISSUES, HUMAN, SWEEPS, COUPLING))
    blocking_sev = set(plan["defect_policy"]["blocking_severities"])
    blocking_states = set(plan["defect_policy"]["blocking_states"])
    blockers = [
        i for i in ledger.get("issues", [])
        if i.get("severity") in blocking_sev and i.get("state") in blocking_states
    ]
    sev_counts = {}
    for row in ledger.get("issues", []):
        sev = row.get("severity", "Unknown")
        sev_counts[sev] = sev_counts.get(sev, 0) + 1

    region_counts = {}
    for row in cov.get("regions", []):
        region_counts[row["state"]] = region_counts.get(row["state"], 0) + 1
    movement_counts = {}
    for row in cov.get("movement_family_status", []):
        movement_counts[row["state"]] = movement_counts.get(row["state"], 0) + 1

    human_entries = human.get("entries", [])
    refs_by_region = {}
    for row in human_entries:
        region = row.get("region", "unknown")
        refs_by_region[region] = refs_by_region.get(region, 0) + 1

    status = {
        "schema_version": 1,
        "status": "HUMAN_BODY_FOUNDATION_ACTIVE" if blockers else "HUMAN_BODY_FOUNDATION_REVIEW",
        "asset": plan["asset"],
        "rig": plan["rig"],
        "production_approved": False,
        "master_stage": plan["current_position"]["master_stage"],
        "master_stage_name": next(
            x["name"] for x in plan["stages"]
            if x["id"] == plan["current_position"]["master_stage"]
        ),
        "current_focus": next(x for x in plan["stages"] if x["id"] == 1)["current_focus"],
        "comparator": {
            "revision": plan["current_position"]["comparator_revision"],
            "sha256": plan["current_position"]["comparator_sha256"],
        },
        "blocking_issue_count": len(blockers),
        "blocking_issue_ids": [x["id"] for x in blockers],
        "severity_counts": sev_counts,
        "regional_coverage_counts": region_counts,
        "movement_coverage_counts": movement_counts,
        "human_evidence_entry_count": len(human_entries),
        "human_evidence_regions": refs_by_region,
        "prepared_movement_sweep_count": len((sweeps.get("sweeps") or {})),
        "prepared_movement_sweeps": list((sweeps.get("sweeps") or {}).keys()),
        "anatomical_coupling": {
            "authority": "ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json",
            "coupling_system_count": len(coupling.get("coupling_systems") or []),
            "candidate_proven_clear_count": 0,
            "status": "BLOCKED_NOT_YET_CANDIDATE_PROVEN",
            "blocking_issue_id": "WB-QA-012",
            "rule": "Every multi-anchor tissue system must prove weights-only shared ownership and outbound/intermediate/endpoint/return motion before dependent progression.",
        },
        "high_detail_anatomy_allowed": False,
        "why_not_high_detail": (
            "Critical/High whole-body issues remain open."
            if blockers else
            "Master Stages 1-4 still require explicit exit evidence; readiness is never inferred."
        ),
        "next_sequence": plan["current_position"]["next_sequence"],
        "current_blocking_focus": cov["current_blocking_focus"],
        "authority": {
            "master_plan": "docs/ORIGINAL_V1_HUMAN_BODY_MASTER_PLAN.md",
            "machine_plan": "ORIGINAL_V1_HUMAN_BODY_MASTER_PLAN.json",
            "coverage": "ORIGINAL_V1_HUMAN_BODY_COVERAGE_MATRIX.json",
            "issues": "ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json",
            "human_evidence": "ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json",
            "movement_sweeps": "ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PLAN.json",
            "anatomical_coupling": "ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json",
            "anatomical_coupling_contract": "docs/ORIGINAL_V1_ANATOMICAL_COUPLING_CONTRACT.md",
            "anatomical_coupling_evidence_template": "ORIGINAL_V1_ANATOMICAL_COUPLING_EVIDENCE_TEMPLATE.json",
        },
        "note": "Historical Phase 4/r95 evidence is preserved but does not override the current whole-body anatomical gate.",
    }
    return status


def markdown(s):
    lines = [
        "# ORIGINAL v1 human-body status",
        "",
        f"**Master stage:** {s['master_stage']} — {s['master_stage_name']}",
        f"**Current focus:** {s['current_focus'].replace('_',' ')}",
        f"**Comparator:** {s['comparator']['revision']} — {s['comparator']['sha256']}",
        "**Production approved:** NO",
        "",
        "## Blocking state",
        "",
        f"- Critical/High blockers: **{s['blocking_issue_count']}**",
    ]
    for issue in s["blocking_issue_ids"]:
        lines.append(f"- {issue}")
    lines += [
        "",
        "## Coverage",
        "",
        f"- Regions with evidence scaffolding: **{sum(s['regional_coverage_counts'].values())} / 12**",
        f"- Movement families with evidence scaffolding: **{sum(s['movement_coverage_counts'].values())} / 27**",
        f"- Human-evidence entries: **{s['human_evidence_entry_count']}**",
        f"- Prepared deterministic movement sweeps: **{s['prepared_movement_sweep_count']}**",
        "",
        "> Evidence scaffolding is not anatomical acceptance. Actual candidate-bound renders/motion/regression evidence are still required.",
        "",
        "## Anatomical coupling / shared tissue",
        "",
        f"- Coupling systems defined: **{s['anatomical_coupling']['coupling_system_count']}**",
        f"- Candidate-proven CLEAR: **{s['anatomical_coupling']['candidate_proven_clear_count']}**",
        "- Status: **BLOCKED — NOT YET CANDIDATE-PROVEN**",
        f"- Blocking issue: `{s['anatomical_coupling']['blocking_issue_id']}`",
        "",
        s["anatomical_coupling"]["rule"],
        "",
        "## High-detail anatomy",
        "",
        "**BLOCKED**",
        "",
        s["why_not_high_detail"],
        "",
        "## Next sequence",
        "",
    ]
    for i, step in enumerate(s["next_sequence"], 1):
        lines.append(f"{i}. {step.replace('_',' ')}")
    lines += [
        "",
        "Historical Phase 4/r95 evidence remains immutable history; it is not current anatomical sign-off.",
        "",
    ]
    return "\n".join(lines)


def main():
    s = build()
    OUT_JSON.write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(markdown(s) + "\n", encoding="utf-8")
    print("HUMAN BODY STATUS WRITTEN")
    print(json.dumps({
        "stage": s["master_stage"],
        "blocking": s["blocking_issue_count"],
        "high_detail_allowed": s["high_detail_anatomy_allowed"],
        "next": s["next_sequence"][0],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
