#!/usr/bin/env python3
"""Validate the generic human movement sweep acceptance template."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_ACCEPTANCE_TEMPLATE.json"

def validate(d):
    if d.get("schema_version")!=1 or d.get("status")!="HUMAN_MOVEMENT_SWEEP_ACCEPTANCE_TEMPLATE":
        raise ValueError("invalid sweep acceptance template identity")
    if d.get("production_approved") is not False: raise ValueError("template may not claim production approval")
    required={
      "candidate_revision","candidate_sha256","sweep_id","raw_sweep_report_path",
      "runner_calibration_record_path","visual_capture_manifest_path","contact_report_path",
      "motion_continuity_evidence_path","motion_reversibility_evidence_path",
      "required_human_evidence_ids","human_evidence_review_refs","continuity_review_status","reversibility_review_status",
      "visual_review_status","contact_review_status","engineering_review","owner_review"
    }
    if not required.issubset(d): raise ValueError("template fields incomplete")
    rules="\n".join(d.get("rules") or [])
    for phrase in ("Raw sweep execution is diagnostic input","overall CALIBRATED runner record","every named sweep sample","Contact-bearing sweeps","Engineering PASS never implies"):
        if phrase not in rules: raise ValueError(f"acceptance rule missing: {phrase}")
    return {"status":"PASS"}

def main():
    try:
        out=validate(json.loads(PATH.read_text(encoding="utf-8"))); print("HUMAN SWEEP ACCEPTANCE TEMPLATE: PASS"); print(json.dumps(out)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
