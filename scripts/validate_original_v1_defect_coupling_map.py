#!/usr/bin/env python3
"""Validate mapping of every current blocking whole-body defect to coupling proof."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAP=ROOT/"ORIGINAL_V1_DEFECT_COUPLING_MAP.json"
ISSUES=ROOT/"ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json"
COUPLING=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def validate(d,issues,coupling):
    if d.get("schema_version")!=1: raise ValueError("schema_version must be 1")
    if d.get("status")!="ACTIVE_DEFECT_TO_COUPLING_MAP": raise ValueError("unexpected status")
    if d.get("production_approved") is not False: raise ValueError("map may not claim production approval")
    blocking=[i["id"] for i in issues.get("issues",[]) if i.get("severity") in {"Critical","High"} and i.get("state") in {"Open","In Progress","Pending Review"}]
    rows=d.get("mappings") or []
    ids=[r.get("issue_id") for r in rows]
    if len(ids)!=len(set(ids)): raise ValueError("duplicate issue mapping")
    if set(ids)!=set(blocking): raise ValueError(f"blocking issue coverage differs: expected {sorted(blocking)}")
    known={x["id"] for x in coupling.get("coupling_systems",[])}
    for row in rows:
        iid=row["issue_id"]
        req=row.get("required_coupling_system_ids") or []
        if not req: raise ValueError(f"{iid}: required coupling systems missing")
        unknown=set(req)-known
        if unknown: raise ValueError(f"{iid}: unknown coupling systems {sorted(unknown)}")
        if not row.get("closure_focus"): raise ValueError(f"{iid}: closure_focus missing")
    all_ids=known
    qa=next((r for r in rows if r["issue_id"]=="WB-QA-012"),None)
    if qa is None or set(qa["required_coupling_system_ids"])!=all_ids:
        raise ValueError("WB-QA-012 must require every coupling system")
    return {"blocking_issues":len(blocking),"mapped":len(rows)}

def main():
    try:
        out=validate(read(MAP),read(ISSUES),read(COUPLING))
        print("DEFECT-TO-COUPLING MAP: PASS")
        print(json.dumps(out,indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
