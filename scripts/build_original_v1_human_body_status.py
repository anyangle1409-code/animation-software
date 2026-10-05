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
SWEEP_EXEC = ROOT / "ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_STATUS.json"
COUPLING = ROOT / "ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json"
TRIGGERS = ROOT / "ORIGINAL_V1_JOINT_TISSUE_TRIGGER_MAP.json"
VISUAL = ROOT / "ORIGINAL_V1_SURFACE_VISUAL_EVIDENCE_REQUIREMENTS.json"
GRAPH = ROOT / "ORIGINAL_V1_STAGE1_REPAIR_EXECUTION_GRAPH.json"
PROGRESS = ROOT / "ORIGINAL_V1_STAGE1_PROGRESS.json"
OUT_JSON = ROOT / "ORIGINAL_V1_HUMAN_BODY_STATUS.json"
OUT_MD = ROOT / "docs/ORIGINAL_V1_HUMAN_BODY_STATUS.md"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def build():
    plan, cov, ledger, human, sweeps, sweep_exec, coupling, triggers, visual, graph, progress = map(read, (PLAN, COVERAGE, ISSUES, HUMAN, SWEEPS, SWEEP_EXEC, COUPLING, TRIGGERS, VISUAL, GRAPH, PROGRESS))
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

    visual_counts = {}
    for row in visual.get("regions", []):
        visual_counts[row["state"]] = visual_counts.get(row["state"], 0) + 1

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
        "movement_sweep_execution": {
            "authority": "ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_STATUS.json",
            "definitions_total": len(sweep_exec.get("sweeps") or []),
            "runner_bound_count": sum(1 for x in sweep_exec.get("sweeps",[]) if x.get("runner_binding_status")=="BOUND"),
            "runner_unbound_count": sum(1 for x in sweep_exec.get("sweeps",[]) if x.get("runner_binding_status")!="BOUND"),
            "current_wave_required_sweeps": sweep_exec.get("current_wave_required_sweeps",[]),
            "generic_runner_target": sweep_exec.get("generic_runner_target"),
            "status": "RUNNER_UNBOUND" if any(x.get("runner_binding_status")!="BOUND" for x in sweep_exec.get("sweeps",[])) else "RUNNER_BOUND",
            "rule": sweep_exec.get("exit_rule"),
        },
        "anatomical_coupling": {
            "authority": "ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json",
            "coupling_system_count": len(coupling.get("coupling_systems") or []),
            "candidate_proven_clear_count": 0,
            "status": "BLOCKED_NOT_YET_CANDIDATE_PROVEN",
            "blocking_issue_id": "WB-QA-012",
            "joint_tissue_trigger_map": "ORIGINAL_V1_JOINT_TISSUE_TRIGGER_MAP.json",
            "stage1_repair_execution_graph": "ORIGINAL_V1_STAGE1_REPAIR_EXECUTION_GRAPH.json",
            "stage1_progress": "ORIGINAL_V1_STAGE1_PROGRESS.json",
            "pre_edit_repair_workspace_runner": "RUN_ORIGINAL_V1_CREATE_REPAIR_WORKSPACE.bat",
            "post_edit_workspace_finalizer": "RUN_ORIGINAL_V1_FINALIZE_REPAIR_WORKSPACE.bat",
            "post_repair_validation_bundle": "RUN_ORIGINAL_V1_POST_REPAIR_VALIDATION_BUNDLE.bat",
            "anatomical_repair_packages": "ORIGINAL_V1_ANATOMICAL_REPAIR_PACKAGES.json",
            "deformation_diagnosis_tree": "ORIGINAL_V1_DEFORMATION_DIAGNOSIS_TREE.json",
            "weights_only_acceptance": "ORIGINAL_V1_WEIGHTS_ONLY_ACCEPTANCE_CONTRACT.json",
            "candidate_surface_visual_review_template": "ORIGINAL_V1_CANDIDATE_SURFACE_VISUAL_REVIEW_TEMPLATE.json",
            "repair_execution_record_template": "ORIGINAL_V1_REPAIR_EXECUTION_RECORD_TEMPLATE.json",
            "candidate_comparison_template": "ORIGINAL_V1_CANDIDATE_COMPARISON_MANIFEST_TEMPLATE.json",
            "whole_body_repair_guide": "docs/ORIGINAL_V1_WHOLE_BODY_REPAIR_GUIDE.md",
            "surface_visual_evidence_requirements": "ORIGINAL_V1_SURFACE_VISUAL_EVIDENCE_REQUIREMENTS.json",
            "joint_trigger_rule_count": len(triggers.get("rules") or []),
            "trigger_rule": "Material motion of a rig joint/bone family automatically makes every mapped connected tissue system required review scope.",
            "rule": "Every multi-anchor tissue system must prove weights-only shared ownership and outbound/intermediate/endpoint/return motion before dependent progression.",
        },
        "surface_visual_evidence": {
            "authority": "ORIGINAL_V1_SURFACE_VISUAL_EVIDENCE_REQUIREMENTS.json",
            "counts": visual_counts,
            "complete_region_count": visual_counts.get("complete", 0),
            "partial_region_count": visual_counts.get("partial", 0),
            "missing_surface_sequence_count": visual_counts.get("missing_surface_sequence", 0),
            "status": "INCOMPLETE" if visual_counts.get("missing_surface_sequence", 0) else "REVIEW",
            "rule": "Biomechanics/anatomy evidence cannot close exterior skin/muscle appearance; real-human surface photo/video sequences are required before Stage 4 exit.",
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
            "movement_sweep_execution": "ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_STATUS.json",
            "stage1_wave_work_package_runner": "RUN_ORIGINAL_V1_STAGE1_WAVE_WORK_PACKAGE.bat",
            "anatomical_coupling": "ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json",
            "anatomical_coupling_contract": "docs/ORIGINAL_V1_ANATOMICAL_COUPLING_CONTRACT.md",
            "anatomical_coupling_evidence_template": "ORIGINAL_V1_ANATOMICAL_COUPLING_EVIDENCE_TEMPLATE.json",
            "joint_tissue_trigger_map": "ORIGINAL_V1_JOINT_TISSUE_TRIGGER_MAP.json",
            "anatomical_repair_packages": "ORIGINAL_V1_ANATOMICAL_REPAIR_PACKAGES.json",
            "deformation_diagnosis_tree": "ORIGINAL_V1_DEFORMATION_DIAGNOSIS_TREE.json",
            "weights_only_acceptance": "ORIGINAL_V1_WEIGHTS_ONLY_ACCEPTANCE_CONTRACT.json",
            "stage1_repair_execution_graph": "ORIGINAL_V1_STAGE1_REPAIR_EXECUTION_GRAPH.json",
            "pre_edit_repair_workspace_runner": "RUN_ORIGINAL_V1_CREATE_REPAIR_WORKSPACE.bat",
            "post_edit_workspace_finalizer": "RUN_ORIGINAL_V1_FINALIZE_REPAIR_WORKSPACE.bat",
            "post_repair_validation_bundle": "RUN_ORIGINAL_V1_POST_REPAIR_VALIDATION_BUNDLE.bat",
            "candidate_comparison_template": "ORIGINAL_V1_CANDIDATE_COMPARISON_MANIFEST_TEMPLATE.json",
        },
        "stage1_progress": {
            "active_wave_id": progress.get("active_wave_id"),
            "operational_next_action": "complete_global_pre_repair_diagnostics" if next((x for x in progress.get("waves",[]) if x.get("id")=="global_foundation"),{}).get("state")!="CLEAR" else "execute_active_wave_packages",
            "waves_total": len(progress.get("waves") or []),
            "waves_clear": sum(1 for x in progress.get("waves",[]) if x.get("state")=="CLEAR"),
            "packages_total": progress.get("overall",{}).get("packages_total",14),
            "packages_clear": progress.get("overall",{}).get("packages_clear",0),
            "note": "Shoulder-yoke remains the repair focus, but no shoulder package may clear until exact-candidate global pre-repair diagnostics are complete.",
        },
        "non_blender_preparation": {
            "status": "SUBSTANTIALLY_PREPARED",
            "anatomical_repair_packages": 14,
            "deformation_diagnosis_tree": "READY",
            "weights_only_region_contracts": 12,
            "stage1_dependency_waves": len(graph.get("waves") or []),
            "pose_to_tissue_camera_evidence_planner": "READY",
            "pre_repair_diagnostic_bundle": "READY",
            "pre_edit_repair_workspace": "READY",
            "post_edit_workspace_finalizer": "READY",
            "post_repair_validation_bundle": "READY",
            "pre_edit_post_edit_provenance_split": "ENFORCED",
            "unified_candidate_comparison": "READY",
            "deterministic_movement_sweep_definitions": len(sweep_exec.get("sweeps") or []),
            "generic_blender_sweep_runner_bound": sum(1 for x in sweep_exec.get("sweeps",[]) if x.get("runner_binding_status")=="BOUND"),
            "generic_blender_sweep_runner_unbound": sum(1 for x in sweep_exec.get("sweeps",[]) if x.get("runner_binding_status")!="BOUND"),
            "stage1_wave_work_package": "READY",
            "real_human_evidence_records": len(human_entries),
            "interpretation": "Prepared rules/tools reduce Blender experimentation but do not count as candidate anatomical clearance.",
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
        "## Movement sweep execution",
        "",
        f"- Deterministic sweep definitions: **{s['movement_sweep_execution']['definitions_total']}**",
        f"- Bound to generic Blender runner: **{s['movement_sweep_execution']['runner_bound_count']}**",
        f"- Not yet bound: **{s['movement_sweep_execution']['runner_unbound_count']}**",
        "- Current-wave sweep requirements: " + (", ".join(s['movement_sweep_execution']['current_wave_required_sweeps']) or "none"),
        "",
        "> Sweep definitions are planning authority. A movement is not candidate-proven until the separate runner executes it against the exact candidate and candidate-bound evidence is reviewed.",
        "",
        "## Anatomical coupling / shared tissue",
        "",
        f"- Coupling systems defined: **{s['anatomical_coupling']['coupling_system_count']}**",
        f"- Candidate-proven CLEAR: **{s['anatomical_coupling']['candidate_proven_clear_count']}**",
        "- Status: **BLOCKED — NOT YET CANDIDATE-PROVEN**",
        f"- Blocking issue: `{s['anatomical_coupling']['blocking_issue_id']}`",
        "",
        s["anatomical_coupling"]["rule"],
        f"- Joint-to-tissue trigger rules: **{s['anatomical_coupling']['joint_trigger_rule_count']}**",
        s["anatomical_coupling"]["trigger_rule"],
        "",
        "## Real-human surface visual evidence",
        "",
        f"- Complete regions: **{s['surface_visual_evidence']['complete_region_count']}**",
        f"- Partial regions: **{s['surface_visual_evidence']['partial_region_count']}**",
        f"- Missing full surface sequences: **{s['surface_visual_evidence']['missing_surface_sequence_count']}**",
        "",
        s["surface_visual_evidence"]["rule"],
        "",
        "## Stage 1 progress",
        "",
        f"- Active repair wave: **{s['stage1_progress']['active_wave_id']}**",
        f"- Operational next action: **{s['stage1_progress']['operational_next_action'].replace('_',' ')}**",
        f"- Waves clear: **{s['stage1_progress']['waves_clear']} / {s['stage1_progress']['waves_total']}**",
        f"- Repair packages clear: **{s['stage1_progress']['packages_clear']} / {s['stage1_progress']['packages_total']}**",
        "",
        s["stage1_progress"]["note"],
        "",
        "## Non-Blender preparation",
        "",
        f"- Anatomical repair packages: **{s['non_blender_preparation']['anatomical_repair_packages']} / 14**",
        f"- Stage 1 dependency waves: **{s['non_blender_preparation']['stage1_dependency_waves']}**",
        f"- Pre-repair diagnostic bundle: **{s['non_blender_preparation']['pre_repair_diagnostic_bundle']}**",
        f"- Pre-edit repair workspace: **{s['non_blender_preparation']['pre_edit_repair_workspace']}**",
        f"- Post-edit workspace finalizer: **{s['non_blender_preparation']['post_edit_workspace_finalizer']}**",
        f"- Post-repair validation bundle: **{s['non_blender_preparation']['post_repair_validation_bundle']}**",
        f"- Pre-edit/post-edit provenance split: **{s['non_blender_preparation']['pre_edit_post_edit_provenance_split']}**",
        f"- Unified candidate comparison: **{s['non_blender_preparation']['unified_candidate_comparison']}**",
        f"- Deterministic movement sweep definitions: **{s['non_blender_preparation']['deterministic_movement_sweep_definitions']}**",
        f"- Generic Blender sweep runner bound: **{s['non_blender_preparation']['generic_blender_sweep_runner_bound']} / {s['non_blender_preparation']['deterministic_movement_sweep_definitions']}**",
        f"- Stage 1 wave work package: **{s['non_blender_preparation']['stage1_wave_work_package']}**",
        "",
        "> These are preparation/control tools, not evidence that the body itself is clear.",
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
