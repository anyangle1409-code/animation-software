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

def validate(d,plan,packages,posemap,graph,require_bound=False):
    if d.get("schema_version")!=1 or d.get("status")!="HUMAN_MOVEMENT_SWEEP_EXECUTION_PREPARATION":
        raise ValueError("invalid sweep execution status identity")
    if d.get("production_approved") is not False:
        raise ValueError("sweep execution status may not claim production approval")
    if d.get("runner_calibration_state")!="PREPARED_UNCALIBRATED":
        raise ValueError("runner calibration state must remain PREPARED_UNCALIBRATED until Blender calibration")
    for key in ("generic_runner_target","runner_wrapper_target","execution_spec"):
        p=d.get(key)
        if not p or not (ROOT/p).is_file():
            raise ValueError(f"{key} missing or file not found: {p}")
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
    return {
      "sweeps_total":len(rows),
      "bound":bound,
      "unbound":len(rows)-bound,
      "current_wave_required_sweeps":expected,
      "fully_bound":bound==len(rows),
      "runner_calibration_state":d.get("runner_calibration_state"),
      "candidate_sweeps_executed":sum(1 for x in rows if x.get("candidate_execution_state")!="NOT_RUN"),
      "status":"PASS"
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--require-bound",action="store_true")
    a=ap.parse_args()
    try:
        out=validate(read(STATUS),read(PLAN),read(PACKAGES),read(POSEMAP),read(GRAPH),a.require_bound)
        print("HUMAN MOVEMENT SWEEP EXECUTION STATUS: PASS")
        print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError,StopIteration) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
