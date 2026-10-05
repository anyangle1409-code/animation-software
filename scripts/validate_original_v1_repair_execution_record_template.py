#!/usr/bin/env python3
"""Validate post-edit repair execution record template structure."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
T=ROOT/"ORIGINAL_V1_REPAIR_EXECUTION_RECORD_TEMPLATE.json"

def validate(t):
    if t.get("schema_version")!=1 or t.get("status")!="REPAIR_EXECUTION_RECORD_TEMPLATE": raise ValueError("invalid template identity")
    if t.get("production_approved") is not False: raise ValueError("template may not claim production approval")
    required={"candidate_revision","repair_package_id","coupling_system_id","repair_declaration_path","repair_declaration_sha256","pre_edit_candidate_sha256","final_candidate_sha256","executed_operations","edited_vertex_ids","edited_bone_groups","evidence_refs","change_audit_path","regression_report_path"}
    if not required.issubset(t): raise ValueError("execution template fields incomplete")
    rules="\n".join(t.get("rules") or [])
    for phrase in ("declaration must predate","final candidate SHA","subset of the declaration","Protected-neighbour","never implies owner acceptance"):
        if phrase not in rules: raise ValueError(f"execution rule missing: {phrase}")
    return {"status":"PASS"}

def main():
    try:
        out=validate(json.loads(T.read_text(encoding="utf-8"))); print("REPAIR EXECUTION RECORD TEMPLATE: PASS"); print(json.dumps(out)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
