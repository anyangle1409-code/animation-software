#!/usr/bin/env python3
"""Validate the ORIGINAL-v1 joint-to-tissue trigger map."""
from __future__ import annotations
import json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TRIGGER=ROOT/"ORIGINAL_V1_JOINT_TISSUE_TRIGGER_MAP.json"
COUPLING=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def validate(t,c):
    if t.get("schema_version")!=1: raise ValueError("schema_version must be 1")
    if t.get("status")!="AUTHORITATIVE_JOINT_TISSUE_TRIGGER_MAP": raise ValueError("unexpected trigger-map status")
    if t.get("production_approved") is not False: raise ValueError("trigger map may not claim production approval")
    coupling_ids={x["id"] for x in c.get("coupling_systems",[])}
    rules=t.get("rules") or []
    if len(rules)<12: raise ValueError("joint trigger coverage incomplete")
    ids=[x.get("id") for x in rules]
    if len(ids)!=len(set(ids)): raise ValueError("duplicate trigger rule id")
    referenced=set()
    required_families={"head_cervical","trunk_pelvis","clavicle","scapula","humerus","elbow_forearm","wrist_hand","digits","hip_femur","knee_lower_leg","ankle_hindfoot","forefoot_toes"}
    seen_families=set()
    for row in rules:
        rid=row.get("id")
        if not isinstance(rid,str) or not re.fullmatch(r"JT-[A-Z]+-\d{3}",rid):
            raise ValueError(f"invalid trigger id {rid}")
        patterns=row.get("bone_patterns") or []
        if not patterns: raise ValueError(f"{rid}: bone_patterns missing")
        for p in patterns:
            try: re.compile(p)
            except re.error as exc: raise ValueError(f"{rid}: invalid regex {p}: {exc}")
        fam=row.get("joint_family")
        if not isinstance(fam,str) or not fam: raise ValueError(f"{rid}: joint_family missing")
        seen_families.add(fam)
        systems=set(row.get("required_coupling_system_ids") or [])
        if not systems: raise ValueError(f"{rid}: coupling systems missing")
        unknown=systems-coupling_ids
        if unknown: raise ValueError(f"{rid}: unknown coupling systems {sorted(unknown)}")
        referenced.update(systems)
        if not row.get("rationale"): raise ValueError(f"{rid}: rationale missing")
    if seen_families!=required_families:
        raise ValueError(f"joint families differ; missing={sorted(required_families-seen_families)} extra={sorted(seen_families-required_families)}")
    if referenced!=coupling_ids:
        raise ValueError(f"not every coupling system is reachable from a joint trigger; missing={sorted(coupling_ids-referenced)}")
    policy=t.get("trigger_policy") or {}
    for key in ("material_motion","response_requirement","quiescent_exception","propagation"):
        if not isinstance(policy.get(key),str) or not policy[key].strip():
            raise ValueError(f"trigger_policy.{key} missing")
    if not t.get("failure_rule"): raise ValueError("failure_rule missing")
    return True

def main():
    try:
        validate(read(TRIGGER),read(COUPLING))
        print("JOINT-TISSUE TRIGGER MAP: PASS")
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
