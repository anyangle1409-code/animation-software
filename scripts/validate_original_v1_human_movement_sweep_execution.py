#!/usr/bin/env python3
"""Validate ORIGINAL-v1 generic human movement sweep execution preparation."""
from __future__ import annotations
import argparse,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STATUS=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_STATUS.json"
PLAN=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PLAN.json"
PACKAGES=ROOT/"ORIGINAL_V1_ANATOMICAL_REPAIR_PACKAGES.json"
POSEMAP=ROOT/"ORIGINAL_V1_POSE_MOVEMENT_FAMILY_MAP.json"
GRAPH=ROOT/"ORIGINAL_V1_STAGE1_REPAIR_EXECUTION_GRAPH.json"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def validate(d,plan,packages,posemap,graph,require_bound=False,require_runner_evidence_ready=False,require_current_wave_evidence=False):
    if d.get("schema_version")!=1 or d.get("status")!="HUMAN_MOVEMENT_SWEEP_EXECUTION_PREPARATION":
        raise ValueError("invalid sweep execution status identity")
    if d.get("production_approved") is not False:
        raise ValueError("sweep execution status may not claim production approval")
    readiness=d.get("runner_evidence_readiness")
    calibration=d.get("runner_calibration_state")
    if readiness not in {"DIAGNOSTIC_ONLY_INCOMPLETE","EVIDENCE_READY"}:
        raise ValueError("runner evidence readiness invalid")
    if readiness=="DIAGNOSTIC_ONLY_INCOMPLETE" and calibration!="PREPARED_UNCALIBRATED":
        raise ValueError("diagnostic-only runner must remain PREPARED_UNCALIBRATED")
    if readiness=="EVIDENCE_READY" and calibration!="CALIBRATED":
        raise ValueError("evidence-ready runner requires CALIBRATED state")
    caps=d.get("runner_output_capabilities") or {}
    for key in ("deterministic_joint_state_sampling","per_sample_joint_state_hash","weights_only_surface_summary","corrective_contribution_summary","runner_script_hash","end_of_run_source_rehash"):
        if caps.get(key)!="IMPLEMENTED":
            raise ValueError(f"runner core capability missing {key}")
    if readiness=="EVIDENCE_READY":
        for key in ("visual_capture_manifest","required_regional_renders","contact_load_state"):
            if caps.get(key)!="IMPLEMENTED":
                raise ValueError(f"evidence-ready runner capability missing {key}")
        if d.get("acceptance_capable") is not True:
            raise ValueError("evidence-ready runner must be acceptance_capable")
        if d.get("acceptance_capability_blockers"):
            raise ValueError("evidence-ready runner may not retain acceptance blockers")
        cal_path=d.get("runner_calibration_evidence_path") or d.get("runner_calibration_record")
        if not cal_path or not (ROOT/cal_path).is_file():
            raise ValueError("evidence-ready runner calibration evidence missing")
    else:
        for key in ("visual_capture_manifest","required_regional_renders","contact_load_state"):
            if caps.get(key)!="NOT_IMPLEMENTED":
                raise ValueError(f"diagnostic-only runner capability state unexpected for {key}")
        if d.get("acceptance_capable") is not False:
            raise ValueError("diagnostic-only runner may not be acceptance_capable")
        if not d.get("acceptance_capability_blockers"):
            raise ValueError("diagnostic-only runner must expose acceptance blockers")
    for key in ("generic_runner_target","runner_wrapper_target","execution_spec"):
        p=d.get(key)
        if not p or not (ROOT/p).is_file():
            raise ValueError(f"{key} missing or file not found: {p}")
    producers=d.get("separate_evidence_producers") or {}
    expected_producers={
      "visual_capture":("IMPLEMENTED_UNCALIBRATED",("runner","script","validator")),
      "raw_contact":("IMPLEMENTED_UNCALIBRATED",("runner","script","validator")),
      "review_workspace":("READY_NON_BLENDER",("runner","builder","contact_scaffold_builder")),
    }
    for name,(state,fields) in expected_producers.items():
        row=producers.get(name)
        if not isinstance(row,dict):
            raise ValueError(f"separate evidence producer missing {name}")
        if row.get("state")!=state:
            raise ValueError(f"{name}: evidence producer state differs")
        for field in fields:
            p=row.get(field)
            if not p or not (ROOT/p).is_file():
                raise ValueError(f"{name}: {field} missing or file not found: {p}")
    plan_sweeps=plan.get("sweeps") or {}
    rows=d.get("sweeps") or []
    if [x.get("id") for x in rows]!=list(plan_sweeps):
        raise ValueError("sweep execution coverage/order differs from sweep plan")
    allowed_binding={"UNBOUND","BOUND"}
    bound=0
    for row in rows:
        sid=row["id"]; src=plan_sweeps[sid]
        if row.get("definition_status")!="READY":
            raise ValueError(f"{sid}: definition status must be READY")
        if row.get("samples")!=src.get("samples"):
            raise ValueError(f"{sid}: samples differ from sweep plan")
        if row.get("regions")!=src.get("regions"):
            raise ValueError(f"{sid}: regions differ from sweep plan")
        if row.get("cameras")!=src.get("cameras"):
            raise ValueError(f"{sid}: cameras differ from sweep plan")
        if row.get("evidence_ids")!=src.get("evidence_ids"):
            raise ValueError(f"{sid}: evidence ids differ from sweep plan")
        state=row.get("runner_binding_status")
        if state not in allowed_binding:
            raise ValueError(f"{sid}: invalid runner binding status")
        if state=="BOUND":
            bound+=1
            if row.get("blender_adapter_id")!="generic_human_movement_sweep_v1":
                raise ValueError(f"{sid}: BOUND without canonical blender adapter id")
        elif row.get("blender_adapter_id") is not None:
            raise ValueError(f"{sid}: UNBOUND may not claim blender_adapter_id")
        if row.get("candidate_execution_state") not in {"NOT_RUN","RUN_INCOMPLETE","EVIDENCE_READY"}:
            raise ValueError(f"{sid}: invalid candidate_execution_state")
        if len(row.get("required_outputs") or [])<8:
            raise ValueError(f"{sid}: required output contract incomplete")

    pby={x["id"]:x for x in packages.get("packages",[])}
    pose_moves=set(x for moves in (posemap.get("mappings") or {}).values() for x in moves)
    wave=next(x for x in graph.get("waves",[]) if x["id"]==d.get("current_stage1_wave"))
    proof=[]
    for pid in wave.get("package_ids",[]):
        for move in pby[pid].get("proof_movements",[]):
            if move not in proof: proof.append(move)
    expected=[x for x in proof if x in plan_sweeps and x not in pose_moves]
    if d.get("current_wave_required_sweeps")!=expected:
        raise ValueError(f"current-wave sweep requirement differs; expected {expected}")
    if "Do not modify or repin" not in d.get("frozen_pose_rule",""):
        raise ValueError("frozen pose protection rule missing")
    if require_bound and bound!=len(rows):
        raise ValueError(f"generic sweep runner binding incomplete: bound={bound} total={len(rows)}")
    ready_count=sum(1 for x in rows if x.get("candidate_execution_state")=="EVIDENCE_READY")
    if d.get("candidate_evidence_ready_count")!=ready_count:
        raise ValueError("candidate_evidence_ready_count differs from sweep rows")
    current_by={x["id"]:x for x in rows}
    current_ready=all(current_by[x].get("candidate_execution_state")=="EVIDENCE_READY" for x in expected)
    if require_runner_evidence_ready and readiness!="EVIDENCE_READY":
        raise ValueError("generic sweep runner is not evidence-ready")
    if require_current_wave_evidence and not current_ready:
        raise ValueError("current Stage 1 wave sweep evidence is incomplete")
    return {
      "sweeps_total":len(rows),
      "bound":bound,
      "unbound":len(rows)-bound,
      "current_wave_required_sweeps":expected,
      "fully_bound":bound==len(rows),
      "runner_calibration_state":calibration,
      "runner_evidence_readiness":readiness,
      "runner_evidence_ready":readiness=="EVIDENCE_READY",
      "acceptance_capable":bool(d.get("acceptance_capable")),
      "candidate_sweeps_executed":sum(1 for x in rows if x.get("candidate_execution_state")!="NOT_RUN"),
      "candidate_sweeps_evidence_ready":ready_count,
      "current_wave_evidence_ready":current_ready,
      "separate_evidence_producers_ready":True,
      "status":"PASS"
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--require-bound",action="store_true")
    ap.add_argument("--require-runner-evidence-ready",action="store_true")
    ap.add_argument("--require-current-wave-evidence",action="store_true")
    a=ap.parse_args()
    try:
        out=validate(
            read(STATUS),read(PLAN),read(PACKAGES),read(POSEMAP),read(GRAPH),
            a.require_bound,a.require_runner_evidence_ready,a.require_current_wave_evidence
        )
        print("HUMAN MOVEMENT SWEEP EXECUTION STATUS: PASS")
        print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError,StopIteration) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
