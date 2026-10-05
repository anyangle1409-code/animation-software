#!/usr/bin/env python3
"""Validate the explicit ORIGINAL-v1 non-Blender preparation boundary."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STATUS=ROOT/"ORIGINAL_V1_NON_BLENDER_PREP_STATUS.json"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def validate(d):
    if d.get("schema_version")!=1 or d.get("status")!="NON_BLENDER_PREPARATION_READY_FOR_LAPTOP_EXECUTION":
        raise ValueError("invalid non-Blender prep identity")
    if d.get("production_approved") is not False: raise ValueError("prep ledger may not claim production approval")
    if d.get("anatomical_model_accepted") is not False: raise ValueError("prep ledger may not claim anatomical acceptance")
    if d.get("high_detail_anatomy_allowed") is not False: raise ValueError("prep ledger may not allow high-detail anatomy")
    if d.get("defined_non_blender_backlog_state")!="COMPLETE_TO_CURRENT_SCOPE":
        raise ValueError("defined non-Blender backlog must be COMPLETE_TO_CURRENT_SCOPE")
    if d.get("non_blender_tasks_remaining") not in ([],None):
        raise ValueError("non_blender_tasks_remaining must be empty for READY status")
    components=d.get("prepared_components") or []
    ids=[x.get("id") for x in components]
    if len(ids)!=len(set(ids)) or len(ids)<10: raise ValueError("prepared component coverage invalid")
    for row in components:
        if not str(row.get("state","")).strip(): raise ValueError(f"{row.get('id')}: state missing")
        evidence=row.get("evidence") or []
        if not evidence: raise ValueError(f"{row.get('id')}: evidence missing")
        for rel in evidence:
            if not (ROOT/rel).exists(): raise ValueError(f"{row.get('id')}: evidence file missing {rel}")
    required_component_ids={
        "stage1_orchestration","pre_edit_workspace","post_edit_workspace","candidate_comparison",
        "generic_movement_sweep_motion_runner","generic_movement_sweep_visual_capture",
        "generic_movement_sweep_contact_capture","generic_movement_sweep_acceptance",
        "post_repair_sweep_integration","workspace_sweep_acceptance_preflight",
        "laptop_workflow_integrity","contract_gates",
        "package_aware_sweep_pipeline","controlled_sweep_finalization","preferred_laptop_quickstart"
    }
    missing_components=sorted(required_component_ids-set(ids))
    if missing_components:
        raise ValueError(f"required non-Blender prepared components missing {missing_components}")
    remaining=d.get("blender_or_candidate_bound_remaining") or []
    if len(remaining)<8: raise ValueError("Blender/candidate-bound remainder unexpectedly empty")
    model=d.get("current_model_state") or {}
    if model.get("master_stage")!=1: raise ValueError("model must remain Stage 1")
    if not isinstance(model.get("open_critical_high_blockers"),int) or model["open_critical_high_blockers"]<=0:
        raise ValueError("prep ledger must preserve open body blockers")
    if model.get("candidate_proven_coupling_systems")!=0:
        raise ValueError("prep ledger may not invent candidate-proven coupling")
    if model.get("high_detail_anatomy_allowed") is not False:
        raise ValueError("model state may not allow high-detail anatomy")
    if d.get("required_entry_point")!="RUN_ORIGINAL_V1_STAGE1_LAPTOP_PICKUP_PLAN.bat":
        raise ValueError("preferred laptop entry point differs")
    rules="\n".join(d.get("rules") or [])
    for phrase in ("Do not convert READY tooling into a model PASS","Do not overwrite r95","Do not enter high-detail anatomy"):
        if phrase not in rules: raise ValueError(f"boundary rule missing: {phrase}")
    return {
      "prepared_components":len(components),
      "blender_only_remaining":len(remaining),
      "model_blockers":model["open_critical_high_blockers"],
      "status":"PASS"
    }

def main():
    try:
        out=validate(read(STATUS))
        print("NON-BLENDER PREPARATION STATUS: PASS")
        print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP - "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
