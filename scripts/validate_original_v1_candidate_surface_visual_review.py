#!/usr/bin/env python3
"""Validate candidate-bound human surface visual review."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MASTER=ROOT/"ORIGINAL_V1_HUMAN_BODY_MASTER_PLAN.json"
HUMAN=ROOT/"ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json"
SHA_RE=re.compile(r"^[0-9a-f]{64}$")
VALID={"NOT_RUN","PASS","FAIL"}
REQUIRED={"neutral","lengthened_or_elevated","compressed_or_loaded","intermediate_transition","return_transition"}

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def validate(d,master,human,require_exit=False):
    if d.get("schema_version")!=1: raise ValueError("schema_version must be 1")
    if d.get("production_approved") is not False: raise ValueError("visual review may not claim production approval")
    if not re.fullmatch(r"r\d+[a-z]?",str(d.get("candidate_revision","")),re.I): raise ValueError("candidate_revision invalid")
    if not SHA_RE.fullmatch(str(d.get("candidate_sha256",""))): raise ValueError("candidate_sha256 invalid")
    if set(d.get("required_states") or [])!=REQUIRED: raise ValueError("required visual states differ")

    expected=[x["id"] for x in master.get("body_regions",[])]
    rows=d.get("regions") or []
    ids=[x.get("id") for x in rows]
    if ids!=expected: raise ValueError("region order/coverage differs from master")
    scope=d.get("scope_region_ids") or []
    if len(scope)!=len(set(scope)) or not set(scope).issubset(set(expected)): raise ValueError("scope_region_ids invalid")
    known_human={x["id"] for x in human.get("entries",[])}
    by={x["id"]:x for x in rows}
    incomplete=[]
    for rid in scope:
        row=by[rid]
        state=row.get("state")
        if state not in VALID: raise ValueError(f"{rid}: invalid state")
        if state=="PASS":
            refs=row.get("human_evidence_ids") or []
            if not refs: raise ValueError(f"{rid}: PASS without human evidence")
            unknown=set(refs)-known_human
            if unknown: raise ValueError(f"{rid}: unknown human evidence {sorted(unknown)}")
            if not row.get("whole_body_evidence_refs"): raise ValueError(f"{rid}: PASS without whole-body evidence")
            if not row.get("regional_close_evidence_refs"): raise ValueError(f"{rid}: PASS without regional close evidence")
            se=row.get("state_evidence") or {}
            if set(se)!=REQUIRED: raise ValueError(f"{rid}: state evidence keys differ")
            for s in REQUIRED:
                if not se.get(s): raise ValueError(f"{rid}: PASS without {s} evidence")
            if row.get("blocking_defect_ids"): raise ValueError(f"{rid}: PASS with blocking visual defects")
        else:
            incomplete.append(rid)
    review=d.get("engineering_review")
    if review not in {"PENDING","PASS","FAIL"}: raise ValueError("engineering_review invalid")
    if review=="PASS" and incomplete: raise ValueError("engineering review PASS with incomplete scope regions")
    if require_exit and (incomplete or review!="PASS"):
        raise ValueError(f"exit blocked: incomplete={incomplete} engineering_review={review}")
    return {"scope_regions":len(scope),"incomplete":incomplete,"engineering_review":review}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("review"); ap.add_argument("--require-exit",action="store_true")
    a=ap.parse_args()
    try:
        out=validate(read(a.review),read(MASTER),read(HUMAN),a.require_exit)
        print("CANDIDATE SURFACE VISUAL REVIEW: PASS")
        print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
