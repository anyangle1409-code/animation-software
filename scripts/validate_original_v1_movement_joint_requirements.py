#!/usr/bin/env python3
"""Validate the authoritative movement -> joint-family participation contract."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"ORIGINAL_V1_MOVEMENT_JOINT_FAMILY_REQUIREMENTS.json"
MASTER=ROOT/"ORIGINAL_V1_HUMAN_BODY_MASTER_PLAN.json"
TRIGGERS=ROOT/"ORIGINAL_V1_JOINT_TISSUE_TRIGGER_MAP.json"
ROLES={"control_only","active","active_contact"}

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def validate(d,master,triggers):
    if d.get("schema_version")!=1 or d.get("status")!="AUTHORITATIVE_MOVEMENT_JOINT_FAMILY_REQUIREMENTS":
        raise ValueError("invalid movement-joint authority identity")
    if d.get("production_approved") is not False:
        raise ValueError("movement-joint authority may not claim production approval")
    movements=d.get("movements") or {}
    master_moves=list(master.get("movement_families") or [])
    if list(movements)!=master_moves:
        raise ValueError("movement coverage/order differs from master plan")
    trigger_families={x.get("joint_family") for x in triggers.get("rules",[]) if x.get("joint_family")}
    declared=set(d.get("joint_families") or [])
    if declared!=trigger_families:
        raise ValueError(f"joint-family set differs from trigger map: expected {sorted(trigger_families)}")
    for move,row in movements.items():
        req=row.get("required_joint_families")
        opt=row.get("optional_joint_families")
        role=row.get("evidence_role")
        if not isinstance(req,list) or not isinstance(opt,list):
            raise ValueError(f"{move}: joint-family lists missing")
        if len(req)!=len(set(req)) or len(opt)!=len(set(opt)):
            raise ValueError(f"{move}: duplicate joint family")
        if set(req)&set(opt):
            raise ValueError(f"{move}: required/optional joint families overlap")
        unknown=(set(req)|set(opt))-declared
        if unknown:
            raise ValueError(f"{move}: unknown joint families {sorted(unknown)}")
        if role not in ROLES:
            raise ValueError(f"{move}: invalid evidence_role")
        if role!="control_only" and not req:
            raise ValueError(f"{move}: active movement requires at least one required joint family")
        if role=="control_only" and req:
            raise ValueError(f"{move}: control-only movement may not require active joint motion")
    rules="\n".join(d.get("rules") or [])
    if "cannot COMPLETE" not in rules:
        raise ValueError("fail-closed COMPLETE rule missing")
    if "does not define universal human ROM" not in rules:
        raise ValueError("ROM separation rule missing")
    return {"movements":len(movements),"joint_families":len(declared),"status":"PASS"}

def main():
    try:
        out=validate(read(PATH),read(MASTER),read(TRIGGERS))
        print("MOVEMENT JOINT-FAMILY REQUIREMENTS: PASS")
        print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
