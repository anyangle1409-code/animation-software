#!/usr/bin/env python3
"""Validate whole-body anatomical coupling capture plan."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_CAPTURE_PLAN.json"
COUPLING=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json"
MASTER=ROOT/"ORIGINAL_V1_HUMAN_BODY_MASTER_PLAN.json"

def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

def validate(plan,coupling,master):
    if plan.get("schema_version")!=1:
        raise ValueError("schema_version must be 1")
    if plan.get("status")!="PREPARED_ANATOMICAL_COUPLING_CAPTURE_PLAN":
        raise ValueError("unexpected capture-plan status")
    if plan.get("production_approved") is not False:
        raise ValueError("capture plan may not claim production approval")

    expected=[x["id"] for x in coupling.get("coupling_systems",[])]
    rows=plan.get("systems") or []
    ids=[x.get("id") for x in rows]
    if ids!=expected:
        raise ValueError("capture-plan coupling system order/coverage differs")

    known_moves=set(master.get("movement_families") or [])
    for row in rows:
        cid=row["id"]
        moves=row.get("proof_movements") or []
        if not moves:
            raise ValueError(f"{cid}: proof_movements missing")
        if not set(moves).issubset(known_moves):
            raise ValueError(f"{cid}: unknown proof movement")
        views=row.get("views") or []
        if len(views)<4 or len(views)!=len(set(views)):
            raise ValueError(f"{cid}: insufficient/duplicate views")
        if not row.get("close_landmarks"):
            raise ValueError(f"{cid}: close_landmarks missing")
        if row.get("priority")=="current_blocker":
            if not row.get("special_samples"):
                raise ValueError(f"{cid}: current blocker requires explicit special samples")
    if set(plan.get("common_layers") or [])!={"weights_only","final_corrected"}:
        raise ValueError("weights-only/final-corrected layer pair required")
    states=set(plan.get("common_motion_states") or [])
    if not {"start","intermediate_mid","endpoint","return_mid","return_start"}.issubset(states):
        raise ValueError("capture plan lacks intermediate/return states")
    return True

def main():
    try:
        validate(read(PLAN),read(COUPLING),read(MASTER))
        print("ANATOMICAL COUPLING CAPTURE PLAN: PASS")
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
