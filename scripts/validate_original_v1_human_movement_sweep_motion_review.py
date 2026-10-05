#!/usr/bin/env python3
"""Validate candidate-bound human movement sweep continuity/reversibility review."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW_VALIDATOR=ROOT/"scripts/validate_original_v1_human_movement_sweep_report.py"
SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def resolve(base,p):
    q=Path(p); return q if q.is_absolute() else base/q
def raw_validator():
    sp=importlib.util.spec_from_file_location("raw_sweep_validator",RAW_VALIDATOR)
    m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
def norm_input(sample):
    d=dict(sample.get("input") or {}); d.pop("return_leg",None); return d

def expected_pairs(raw,sweep):
    rows=raw["sweeps"][sweep]["samples"]; variants=[]
    for s in rows:
        if s.get("variant") not in variants: variants.append(s.get("variant"))
    returns=[]; adjacent=[]
    for variant in variants:
        v=[x for x in rows if x.get("variant")==variant]
        for i,row in enumerate(v):
            if row.get("return_leg"):
                prior=next((x for x in reversed(v[:i]) if norm_input(x)==norm_input(row)),None)
                returns.append((variant,None if prior is None else prior["label"],row["label"]))
        adjacent.extend((variant,a["label"],b["label"]) for a,b in zip(v,v[1:]))
    return returns,adjacent

def validate(d,base,require_pass=False):
    if d.get("schema_version")!=1 or d.get("status")!="HUMAN_MOVEMENT_SWEEP_MOTION_REVIEW": raise ValueError("invalid motion review identity")
    if d.get("production_approved") is not False: raise ValueError("motion review may not claim production approval")
    if not re.fullmatch(r"r\d+[a-z]?",str(d.get("candidate_revision","")),re.I): raise ValueError("candidate_revision invalid")
    csha=str(d.get("candidate_sha256",""))
    if not SHA_RE.fullmatch(csha): raise ValueError("candidate_sha256 invalid")
    rawp=resolve(base,d.get("raw_sweep_report_path"))
    if not rawp.is_file(): raise ValueError("raw sweep report missing")
    if hashlib.sha256(rawp.read_bytes()).hexdigest()!=d.get("raw_sweep_report_sha256"): raise ValueError("raw sweep report SHA mismatch")
    raw=read(rawp); rv=raw_validator(); rv.validate(raw,rv.read(rv.SPEC))
    if raw.get("candidate_sha256")!=csha: raise ValueError("raw sweep candidate differs")
    sweep=d.get("sweep_id")
    if sweep not in raw.get("sweeps",{}): raise ValueError("raw report missing sweep")
    er,ea=expected_pairs(raw,sweep)
    gotr=[(x.get("variant"),x.get("outbound_label"),x.get("return_label")) for x in d.get("return_pairs",[])]
    gota=[(x.get("variant"),x.get("from_label"),x.get("to_label")) for x in d.get("adjacent_pairs",[])]
    if gotr!=er: raise ValueError("return-pair coverage/order differs")
    if gota!=ea: raise ValueError("adjacent-pair coverage/order differs")
    if not d.get("return_pairs"): raise ValueError("return-pair evidence missing")
    replay=all(x.get("joint_state_match") is True and x.get("snapshot_match") is True and not x.get("pairing_error") for x in d["return_pairs"])
    if d.get("deterministic_replay_status")!=("PASS" if replay else "FAIL"): raise ValueError("deterministic replay status differs")
    cont=d.get("continuity_review"); rev=d.get("reversibility_review"); eng=d.get("engineering_review")
    for name,val in (("continuity_review",cont),("reversibility_review",rev),("engineering_review",eng),("owner_review",d.get("owner_review"))):
        if val not in {"PENDING","PASS","FAIL"}: raise ValueError(f"{name} invalid")
    if require_pass:
        if not replay: raise ValueError("deterministic replay failed")
        for row in d["adjacent_pairs"]:
            if row.get("engineering_disposition")!="PASS" or not row.get("evidence_refs"):
                raise ValueError(f"adjacent transition not reviewed PASS: {row.get('from_label')}->{row.get('to_label')}")
        if cont!="PASS" or rev!="PASS" or eng!="PASS": raise ValueError("motion review PASS statuses incomplete")
    return {"sweep_id":sweep,"candidate_sha256":csha,"return_pairs":len(er),"adjacent_pairs":len(ea),"engineering_review":eng}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("review"); ap.add_argument("--require-pass",action="store_true")
    a=ap.parse_args(); p=Path(a.review)
    try:
        out=validate(read(p),p.parent,a.require_pass); print("HUMAN SWEEP MOTION REVIEW: PASS"); print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
