#!/usr/bin/env python3
"""Validate candidate-bound contact classification for contact-bearing human sweeps."""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REQ=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CONTACT_REQUIREMENTS.json"
SHA_RE=re.compile(r"^[0-9a-f]{64}$")
CLASS={"NO_FINDING","LEGITIMATE_CONTACT","REQUIRED_CLEARANCE","UNCLASSIFIED","UNEXPLAINED_DEFECT"}

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def resolve(base,p):
    q=Path(p); return q if q.is_absolute() else base/q

def validate(d,base,require_pass=False):
    req=read(REQ)
    if d.get("schema_version")!=1: raise ValueError("schema_version must be 1")
    if d.get("production_approved") is not False: raise ValueError("contact report may not claim production approval")
    if not re.fullmatch(r"r\d+[a-z]?",str(d.get("candidate_revision","")),re.I): raise ValueError("candidate_revision invalid")
    csha=str(d.get("candidate_sha256",""))
    if not SHA_RE.fullmatch(csha): raise ValueError("candidate_sha256 invalid")
    sweep=d.get("sweep_id")
    if sweep not in req.get("sweeps",{}): raise ValueError("sweep_id is not contact-bearing")
    refs=d.get("raw_contact_evidence_refs") or []
    if require_pass and not refs: raise ValueError("contact PASS requires raw contact evidence refs")
    for i,row in enumerate(refs):
        path=row.get("path"); digest=row.get("sha256")
        if not path or not SHA_RE.fullmatch(str(digest or "")): raise ValueError(f"raw contact evidence ref {i} invalid")
        p=resolve(base,path)
        if not p.is_file(): raise ValueError(f"raw contact evidence file missing: {path}")
        if hashlib.sha256(p.read_bytes()).hexdigest()!=digest: raise ValueError(f"raw contact evidence SHA mismatch: {path}")
        if row.get("candidate_sha256")!=csha: raise ValueError(f"raw contact evidence candidate mismatch: {path}")

    authority=req["sweeps"][sweep]
    expected=list(authority["samples"])
    rows=d.get("samples") or []
    if [x.get("label") for x in rows]!=expected: raise ValueError("contact sample order/coverage differs")
    for row in rows:
        label=row["label"]; ar=authority["samples"][label]
        domains=row.get("domains") or {}
        for domain in ar.get("required_domains",[]):
            rec=domains.get(domain)
            if rec is None: raise ValueError(f"{label}: missing required contact domain {domain}")
            cls=rec.get("classification")
            if cls not in CLASS: raise ValueError(f"{label}/{domain}: invalid classification")
            if cls!=ar["expected"]:
                raise ValueError(f"{label}/{domain}: expected {ar['expected']} got {cls}")
            if not rec.get("raw_measurement_ref"): raise ValueError(f"{label}/{domain}: raw measurement ref required")
            if not rec.get("evidence_note"): raise ValueError(f"{label}/{domain}: evidence note required")
        for domain,rec in domains.items():
            cls=rec.get("classification")
            if cls not in CLASS: raise ValueError(f"{label}/{domain}: invalid classification")
            if cls in {"UNCLASSIFIED","UNEXPLAINED_DEFECT"} and (require_pass or d.get("engineering_review")=="PASS"):
                raise ValueError(f"{label}/{domain}: blocking contact classification {cls}")
        if "heel_state" in ar:
            observed=row.get("heel_state_observed")
            allowed={
              "CONTACT_OR_NEAR_SUPPORT":{"CONTACT","NEAR_SUPPORT"},
              "RISING":{"RISING"},
              "CLEAR":{"CLEAR"},
              "RISING_OR_RETURNING":{"RISING","RETURNING"}
            }[ar["heel_state"]]
            if require_pass and observed not in allowed:
                raise ValueError(f"{label}: heel state {observed} incompatible with {ar['heel_state']}")
    review=d.get("engineering_review")
    if review not in {"PENDING","PASS","FAIL"}: raise ValueError("engineering_review invalid")
    if d.get("owner_review") not in {"PENDING","PASS","FAIL"}: raise ValueError("owner_review invalid")
    if require_pass and review!="PASS": raise ValueError("engineering contact PASS required")
    return {"sweep_id":sweep,"candidate_sha256":csha,"samples":len(rows),"engineering_review":review}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("report"); ap.add_argument("--require-pass",action="store_true")
    a=ap.parse_args(); p=Path(a.report)
    try:
        out=validate(read(p),p.parent,a.require_pass)
        print("HUMAN SWEEP CONTACT REPORT: PASS"); print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
