#!/usr/bin/env python3
"""Validate the unified parent->candidate comparison manifest template."""
from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"ORIGINAL_V1_CANDIDATE_COMPARISON_MANIFEST_TEMPLATE.json"
SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def validate(d):
    if d.get("schema_version")!=1 or d.get("status")!="CANDIDATE_COMPARISON_MANIFEST_TEMPLATE": raise ValueError("invalid comparison template identity")
    if d.get("production_approved") is not False: raise ValueError("comparison template may not claim production approval")
    parent=d.get("parent") or {}
    if parent.get("revision")!="r95" or not SHA_RE.fullmatch(str(parent.get("sha256",""))): raise ValueError("r95 parent identity invalid")
    ev=d.get("evidence") or {}
    required={"weights_only_acceptance_path","anatomical_coupling_evidence_path","movement_coupling_evidence_path","motion_reversibility_path","motion_continuity_path","regression_report_path","contact_report_path","visual_capture_manifest_paths","change_audit_path"}
    if not required.issubset(ev): raise ValueError("comparison evidence fields incomplete")
    if "Owner review remains separate" not in "\n".join(d.get("comparison_rules",[])): raise ValueError("owner-review separation rule missing")
    return {"status":"PASS"}

def main():
    try:
        out=validate(json.loads(PATH.read_text(encoding="utf-8"))); print("CANDIDATE COMPARISON TEMPLATE: PASS"); print(json.dumps(out)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
