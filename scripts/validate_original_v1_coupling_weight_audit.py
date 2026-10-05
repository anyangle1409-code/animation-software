#!/usr/bin/env python3
"""Validate read-only anatomical coupling-zone weight audit evidence."""
from __future__ import annotations
import json,re,sys
from pathlib import Path
SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def validate(d):
    if d.get("schema_version")!=1: raise ValueError("schema_version must be 1")
    if d.get("status")!="READ_ONLY_COUPLING_ZONE_WEIGHT_AUDIT": raise ValueError("unexpected status")
    if d.get("source_saved_or_modified") is not False: raise ValueError("source must be read-only")
    for key in ("candidate_sha256","declaration_sha256"):
        if not SHA_RE.fullmatch(str(d.get(key,""))): raise ValueError(f"{key} invalid")
    if not d.get("coupling_system_id"): raise ValueError("coupling_system_id missing")
    groups=d.get("anchor_groups") or []
    if len(groups)<2: raise ValueError("at least two anchor groups required")
    names=[g.get("name") for g in groups]
    if len(names)!=len(set(names)): raise ValueError("duplicate anchor group names")
    if d.get("vertex_count",0)<=0: raise ValueError("vertex_count invalid")
    if d.get("zone_edge_count",0)<0: raise ValueError("zone_edge_count invalid")
    for name in names:
        if name not in (d.get("anchor_weight_summary") or {}):
            raise ValueError(f"anchor weight summary missing {name}")
    total=d.get("total_deform_weight") or {}
    for key in ("min","mean","max","n_below_0_999","n_above_1_001"):
        if key not in total: raise ValueError(f"total_deform_weight.{key} missing")
    residual=d.get("residual_other_bone_weight") or {}
    for key in ("mean","p95","max"):
        if key not in residual: raise ValueError(f"residual_other_bone_weight.{key} missing")
    jump=d.get("ownership_edge_jump") or {}
    for key in ("p50","p95","p99","max"):
        if key not in jump: raise ValueError(f"ownership_edge_jump.{key} missing")
    return {"candidate":d.get("candidate"),"coupling_system_id":d.get("coupling_system_id"),"vertex_count":d.get("vertex_count"),"status":"PASS"}

def main():
    if len(sys.argv)!=2:
        print("Usage: validate_original_v1_coupling_weight_audit.py <report.json>"); return 2
    try:
        out=validate(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
        print("COUPLING WEIGHT AUDIT: PASS")
        print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
