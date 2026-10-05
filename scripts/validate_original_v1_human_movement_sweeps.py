#!/usr/bin/env python3
"""Validate deterministic ORIGINAL-v1 human movement sweep definitions."""
from __future__ import annotations
import json, math, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PLAN.json"
MASTER=ROOT/"ORIGINAL_V1_HUMAN_BODY_MASTER_PLAN.json"
HUMAN=ROOT/"ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json"

REQUIRED_SWEEPS={
    "grip_release","trunk_flexion","trunk_extension","trunk_lateral_bend",
    "trunk_axial_rotation","loaded_hip_hinge","hip_abduction_adduction",
    "ankle_plantarflexion",
}

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def finite(v, where="root"):
    if isinstance(v,float) and not math.isfinite(v):
        raise ValueError(f"{where}: non-finite")
    if isinstance(v,dict):
        for k,x in v.items(): finite(x,f"{where}.{k}")
    elif isinstance(v,list):
        for i,x in enumerate(v): finite(x,f"{where}[{i}]")

def validate(plan, master, human):
    finite(plan)
    if plan.get("schema_version")!=1: raise ValueError("schema_version must be 1")
    if plan.get("status")!="PREPARED_HUMAN_MOVEMENT_SWEEPS": raise ValueError("unexpected sweep-plan status")
    if plan.get("production_approved") is not False: raise ValueError("sweep plan may not claim production approval")
    sweeps=plan.get("sweeps") or {}
    if set(sweeps)!=REQUIRED_SWEEPS:
        raise ValueError("sweep coverage must match the eight formerly-unstarted families")
    known_moves=set(master.get("movement_families") or [])
    if not REQUIRED_SWEEPS.issubset(known_moves):
        raise ValueError("sweep family missing from master movement list")
    evidence_ids={e["id"] for e in human.get("entries",[])}

    for name,row in sweeps.items():
        refs=row.get("evidence_ids") or []
        if not refs or not set(refs).issubset(evidence_ids):
            raise ValueError(f"{name}: missing/unknown evidence id")
        samples=row.get("samples") or []
        if len(samples)<6 or len(samples)!=len(set(samples)):
            raise ValueError(f"{name}: insufficient or duplicate samples")
        if not any("return" in str(x) or "neutral_return"==x for x in samples):
            raise ValueError(f"{name}: return-motion sample missing")
        cameras=row.get("cameras") or []
        if len(cameras)<3 or len(cameras)!=len(set(cameras)):
            raise ValueError(f"{name}: camera coverage insufficient")
        if not row.get("regions"): raise ValueError(f"{name}: regions missing")
        if not row.get("inspect"): raise ValueError(f"{name}: inspection contract missing")
        if not row.get("blocking_failures"): raise ValueError(f"{name}: blocking failures missing")
    return True

def main():
    try:
        validate(read(PLAN),read(MASTER),read(HUMAN))
        print("HUMAN MOVEMENT SWEEP PLAN: PASS")
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
