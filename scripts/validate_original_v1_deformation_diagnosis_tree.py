#!/usr/bin/env python3
"""Validate the fail-closed ORIGINAL-v1 deformation diagnosis tree."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"ORIGINAL_V1_DEFORMATION_DIAGNOSIS_TREE.json"

def validate(d):
    if d.get("schema_version")!=1: raise ValueError("schema_version must be 1")
    if d.get("status")!="AUTHORITATIVE_DEFORMATION_DIAGNOSIS_TREE": raise ValueError("unexpected status")
    if d.get("production_approved") is not False: raise ValueError("tree may not claim production approval")
    rows=d.get("nodes") or []; ids=[x.get("id") for x in rows]
    expected=["D0_SOURCE","D1_KINEMATICS","D2_SKINNING_MODE","D3_WEIGHTS_ONLY","D4_TOPOLOGY","D5_CORRECTIVES","D6_CONTACT","D7_CONTINUITY","D8_REGRESSION","D9_HUMAN_VISUAL"]
    if ids!=expected: raise ValueError("diagnosis node order/coverage differs")
    by={x["id"]:x for x in rows}
    if "corrective_shape" not in by["D3_WEIGHTS_ONLY"]["if_no"].get("forbidden",[]): raise ValueError("weights failure must forbid corrective masking")
    if by["D5_CORRECTIVES"]["if_yes"]["action"]!="FIT_GENERIC_JOINT_STATE_CORRECTIVE": raise ValueError("corrective action must be generic joint-state")
    if "exercise_name_driver" not in by["D5_CORRECTIVES"]["if_yes"].get("forbidden",[]): raise ValueError("exercise-name corrective driver must be forbidden")
    if by["D9_HUMAN_VISUAL"]["if_yes"]["action"]!="ENGINEERING_CLEAR_ELIGIBLE_NOT_OWNER_ACCEPTED": raise ValueError("visual pass may not infer owner acceptance")
    if "earliest failing node" not in str(d.get("global_rule","")): raise ValueError("earliest-failing-layer rule missing")
    return {"nodes":len(rows),"status":"PASS"}

def main():
    try:
        out=validate(json.loads(PATH.read_text(encoding="utf-8"))); print("DEFORMATION DIAGNOSIS TREE: PASS"); print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
