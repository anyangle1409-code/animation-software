#!/usr/bin/env python3
"""Validate candidate surface visual review template structure."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
T=ROOT/"ORIGINAL_V1_CANDIDATE_SURFACE_VISUAL_REVIEW_TEMPLATE.json"
M=ROOT/"ORIGINAL_V1_HUMAN_BODY_MASTER_PLAN.json"
REQ={"neutral","lengthened_or_elevated","compressed_or_loaded","intermediate_transition","return_transition"}

def validate(t,m):
    if t.get("schema_version")!=1 or t.get("status")!="CANDIDATE_SURFACE_VISUAL_REVIEW_TEMPLATE": raise ValueError("invalid template identity")
    if t.get("production_approved") is not False: raise ValueError("template may not claim production approval")
    expected=[x["id"] for x in m.get("body_regions",[])]
    rows=t.get("regions") or []
    if [x.get("id") for x in rows]!=expected: raise ValueError("region coverage differs from master")
    if set(t.get("required_states") or [])!=REQ: raise ValueError("required states differ")
    for row in rows:
        if set((row.get("state_evidence") or {}).keys())!=REQ: raise ValueError(f"{row['id']}: state evidence keys differ")
        if row.get("state")!="NOT_RUN": raise ValueError(f"{row['id']}: template state must be NOT_RUN")
    if t.get("engineering_review")!="PENDING" or t.get("owner_review")!="PENDING": raise ValueError("template reviews must begin pending")
    return {"regions":len(rows),"status":"PASS"}

def main():
    try:
        t=json.loads(T.read_text(encoding="utf-8")); m=json.loads(M.read_text(encoding="utf-8")); out=validate(t,m)
        print("CANDIDATE SURFACE VISUAL REVIEW TEMPLATE: PASS"); print(json.dumps(out)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
