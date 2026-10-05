#!/usr/bin/env python3
"""Validate whole-body real-human surface visual evidence requirements."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REQ=ROOT/"ORIGINAL_V1_SURFACE_VISUAL_EVIDENCE_REQUIREMENTS.json"
MASTER=ROOT/"ORIGINAL_V1_HUMAN_BODY_MASTER_PLAN.json"
HUMAN=ROOT/"ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json"
VISUAL_TYPES={"photo_series","figure_series","supplementary_video","clinical_video"}

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def validate(req,master,human):
    if req.get("schema_version")!=1: raise ValueError("schema_version must be 1")
    if req.get("production_approved") is not False: raise ValueError("visual evidence requirements may not claim production approval")
    expected=[x["id"] for x in master.get("body_regions",[])]
    rows=req.get("regions") or []
    ids=[x.get("id") for x in rows]
    if ids!=expected: raise ValueError("visual evidence region order/coverage differs from master plan")
    known={x["id"]:x for x in human.get("entries",[])}
    for row in rows:
        if row.get("state") not in {"missing_surface_sequence","partial","complete"}:
            raise ValueError(f"{row.get('id')}: invalid state")
        refs=row.get("current_visual_evidence_ids") or []
        for rid in refs:
            if rid not in known: raise ValueError(f"{row['id']}: unknown evidence {rid}")
            if known[rid].get("source_type") not in VISUAL_TYPES:
                raise ValueError(f"{row['id']}: {rid} is not a visual source type")
        if row.get("state")=="complete":
            if not refs: raise ValueError(f"{row['id']}: complete without visual sources")
            if row.get("needs"): raise ValueError(f"{row['id']}: complete while needs remain")
        if not isinstance(row.get("needs"),list): raise ValueError(f"{row['id']}: needs must be a list")
    if set(req.get("required_states") or [])!={"neutral","lengthened_or_elevated","compressed_or_loaded","intermediate_transition","return_transition"}:
        raise ValueError("required visual states differ")
    return True

def main():
    try:
        validate(read(REQ),read(MASTER),read(HUMAN))
        print("SURFACE VISUAL EVIDENCE REQUIREMENTS: PASS")
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
