#!/usr/bin/env python3
"""Validate deformation failure-signature investigation guide."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"ORIGINAL_V1_DEFORMATION_FAILURE_SIGNATURES.json"
ALLOWED={"weights_only_ownership","topology_support","corrective_activation","base_skinning_mode","twist_distribution","corrective_driver","corrective_basis","evaluation_order","driver_state","secondary_dynamics","contact_constraints","joint_kinematics","local_contact_response","weights_data","corrective_driver_data","pose_definition","topology_asymmetry","coupling_model"}

def validate(d):
    if d.get("schema_version")!=1 or d.get("status")!="DEFORMATION_FAILURE_SIGNATURE_GUIDE": raise ValueError("invalid signature guide identity")
    if d.get("production_approved") is not False: raise ValueError("guide may not claim production approval")
    rows=d.get("signatures") or []
    if len(rows)<10: raise ValueError("failure-signature coverage too small")
    ids=[x.get("id") for x in rows]
    if len(ids)!=len(set(ids)): raise ValueError("duplicate failure-signature id")
    for row in rows:
        if not row.get("symptoms") or not row.get("questions") or not row.get("forbidden_shortcut"):
            raise ValueError(f"{row.get('id')}: incomplete guidance")
        layers=set(row.get("priority_layers") or [])
        if not layers or not layers.issubset(ALLOWED): raise ValueError(f"{row.get('id')}: invalid priority layer")
    if "do not prove cause" not in d.get("rule",""): raise ValueError("hypothesis-only rule missing")
    return {"signatures":len(rows),"status":"PASS"}

def main():
    try:
        out=validate(json.loads(PATH.read_text(encoding="utf-8"))); print("DEFORMATION FAILURE SIGNATURES: PASS"); print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
