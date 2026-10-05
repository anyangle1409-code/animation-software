#!/usr/bin/env python3
"""Validate raw read-only contact/load measurements from human movement sweeps."""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REQ=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CONTACT_REQUIREMENTS.json"
SPEC=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_SPEC.json"
RUNNER=ROOT/"scripts/audit_original_v1_human_movement_sweeps_blender.py"
CAPTURE=ROOT/"scripts/audit_original_v1_human_movement_sweep_contact_blender.py"
SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def validate(d):
    req=read(REQ); spec=read(SPEC)
    if d.get("schema_version")!=1 or d.get("status")!="READ_ONLY_HUMAN_MOVEMENT_SWEEP_CONTACT_RAW":
        raise ValueError("invalid raw contact identity")
    if d.get("production_approved") is not False: raise ValueError("raw contact may not claim production approval")
    if d.get("source_saved_or_modified") is not False: raise ValueError("raw contact audit must remain read-only")
    if d.get("classification_state")!="RAW_MEASUREMENTS_ONLY": raise ValueError("raw contact may not claim classification")
    if d.get("engineering_review")!="PENDING" or d.get("owner_review")!="PENDING":
        raise ValueError("raw contact report may not infer review")
    if not re.fullmatch(r"r\d+[a-z]?",str(d.get("candidate_revision","")),re.I): raise ValueError("candidate_revision invalid")
    for key in ("candidate_sha256","candidate_sha256_before","candidate_sha256_after","runner_script_sha256","capture_script_sha256","contact_requirements_sha256"):
        if not SHA_RE.fullmatch(str(d.get(key,""))): raise ValueError(f"{key} invalid")
    if not (d["candidate_sha256"]==d["candidate_sha256_before"]==d["candidate_sha256_after"]):
        raise ValueError("candidate before/after identity differs")
    expected_hashes={
      "runner_script_sha256":hashlib.sha256(RUNNER.read_bytes()).hexdigest(),
      "capture_script_sha256":hashlib.sha256(CAPTURE.read_bytes()).hexdigest(),
      "contact_requirements_sha256":hashlib.sha256(REQ.read_bytes()).hexdigest(),
    }
    for key,want in expected_hashes.items():
        if d.get(key)!=want: raise ValueError(f"{key} differs from current authority")
    sweep=d.get("sweep_id")
    if sweep not in req.get("sweeps",{}): raise ValueError("sweep is not contact-bearing")
    rows=d.get("samples") or []
    expected_labels=list(req["sweeps"][sweep]["samples"])
    if [x.get("label") for x in rows]!=expected_labels: raise ValueError("raw contact sample order/coverage differs")
    for row in rows:
        label=row["label"]; ar=req["sweeps"][sweep]["samples"][label]
        domains=row.get("domains") or {}
        declared=set(req["sweeps"][sweep].get("domains",[]))
        if not declared.issubset(set(domains)): raise ValueError(f"{label}: raw contact domains incomplete")
        for domain in ar.get("required_domains",[]):
            rec=domains.get(domain)
            if rec is None: raise ValueError(f"{label}: required raw domain missing {domain}")
            if not isinstance(rec,dict): raise ValueError(f"{label}/{domain}: raw measurement invalid")
        if not SHA_RE.fullmatch(str(row.get("joint_state_sha256",""))):
            raise ValueError(f"{label}: joint_state_sha256 invalid")
        spec_sample=next((x for x in spec["sweeps"][sweep]["samples"] if x["label"]==label),None)
        if spec_sample is None: raise ValueError(f"{label}: sample absent from execution spec")
        if row.get("input")!={k:v for k,v in spec_sample.items() if k!="label"}:
            raise ValueError(f"{label}: input differs from execution spec")
    return {"sweep_id":sweep,"candidate_sha256":d["candidate_sha256"],"samples":len(rows),"status":"PASS"}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("report"); a=ap.parse_args()
    try:
        out=validate(read(a.report)); print("HUMAN SWEEP RAW CONTACT: PASS"); print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP - "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
