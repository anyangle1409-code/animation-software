#!/usr/bin/env python3
"""Build a reviewed-classification scaffold from validated raw sweep contact measurements.

No classification is inferred. Every required domain begins UNCLASSIFIED and
must be filled by engineering review against the raw measurements/visuals.
"""
from __future__ import annotations
import argparse,hashlib,importlib.util,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REQ=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CONTACT_REQUIREMENTS.json"
TEMPLATE=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CONTACT_REPORT_TEMPLATE.json"
RAW_VALIDATOR=ROOT/"scripts/validate_original_v1_human_movement_sweep_contact_raw.py"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def load_raw_validator():
    sp=importlib.util.spec_from_file_location("raw_contact_validator",RAW_VALIDATOR)
    if sp is None or sp.loader is None: raise ValueError("unable to load raw contact validator")
    m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m

def build(raw_path,out_path):
    raw_path=Path(raw_path); out_path=Path(out_path)
    raw=read(raw_path)
    rv=load_raw_validator(); rv.validate(raw)
    req=read(REQ); t=read(TEMPLATE)
    sweep=raw["sweep_id"]; authority=req["sweeps"][sweep]
    t["status"]="HUMAN_MOVEMENT_SWEEP_CONTACT_REPORT"
    t["candidate_revision"]=raw["candidate_revision"]
    t["candidate_sha256"]=raw["candidate_sha256"]
    t["sweep_id"]=sweep
    t["raw_contact_evidence_refs"]=[{
      "path":str(raw_path),
      "sha256":hashlib.sha256(raw_path.read_bytes()).hexdigest(),
      "candidate_sha256":raw["candidate_sha256"],
      "sweep_id":sweep
    }]
    t["samples"]=[]
    for raw_sample in raw["samples"]:
        label=raw_sample["label"]; ar=authority["samples"][label]
        domains={}
        for domain in authority.get("domains",[]):
            if domain not in raw_sample.get("domains",{}): continue
            domains[domain]={
              "classification":"UNCLASSIFIED",
              "raw_measurement_ref":f"{raw_path}#samples/{label}/domains/{domain}",
              "evidence_note":""
            }
        row={"label":label,"domains":domains}
        if "heel_state" in ar:
            row["heel_state_observed"]=None
        t["samples"].append(row)
    t["engineering_review"]="PENDING"; t["owner_review"]="PENDING"
    if out_path.exists(): raise ValueError(f"refusing to overwrite {out_path}")
    out_path.parent.mkdir(parents=True,exist_ok=True)
    out_path.write_text(json.dumps(t,indent=2)+"\n",encoding="utf-8")
    return t

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("raw_contact"); ap.add_argument("out")
    a=ap.parse_args()
    try:
        d=build(a.raw_contact,a.out)
        print("HUMAN SWEEP CONTACT REVIEW SCAFFOLD: BUILT")
        print(json.dumps({"sweep_id":d["sweep_id"],"samples":len(d["samples"]),"engineering_review":d["engineering_review"]},indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
