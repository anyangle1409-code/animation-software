#!/usr/bin/env python3
"""Build deterministic replay and transition-review scaffold from a raw human sweep report."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW_VALIDATOR=ROOT/"scripts/validate_original_v1_human_movement_sweep_report.py"
SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def raw_validator():
    sp=importlib.util.spec_from_file_location("raw_sweep_validator",RAW_VALIDATOR)
    m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
def norm_input(sample):
    d=dict(sample.get("input") or {}); d.pop("return_leg",None); return d

def build(raw_path,sweep,revision):
    raw_path=Path(raw_path); raw=read(raw_path)
    rv=raw_validator(); rv.validate(raw,rv.read(rv.SPEC))
    csha=raw["candidate_sha256"]
    if not re.fullmatch(r"r\d+[a-z]?",revision,re.I): raise ValueError("candidate revision invalid")
    if sweep not in raw.get("sweeps",{}): raise ValueError("raw report missing sweep")
    samples=raw["sweeps"][sweep]["samples"]
    variants=[]
    for s in samples:
        if s.get("variant") not in variants: variants.append(s.get("variant"))
    return_pairs=[]; adjacent=[]
    for variant in variants:
        rows=[x for x in samples if x.get("variant")==variant]
        for i,row in enumerate(rows):
            if row.get("return_leg"):
                target=norm_input(row)
                prior=next((x for x in reversed(rows[:i]) if norm_input(x)==target),None)
                if prior is None:
                    return_pairs.append({"variant":variant,"outbound_label":None,"return_label":row["label"],"input":target,
                                         "joint_state_match":False,"snapshot_match":False,"pairing_error":"no prior sample with equal normalized input"})
                else:
                    return_pairs.append({"variant":variant,"outbound_label":prior["label"],"return_label":row["label"],"input":target,
                                         "joint_state_match":prior.get("joint_state_sha256")==row.get("joint_state_sha256"),
                                         "snapshot_match":prior.get("snapshot_sha256")==row.get("snapshot_sha256"),
                                         "pairing_error":None})
        for a,b in zip(rows,rows[1:]):
            adjacent.append({"variant":variant,"from_label":a["label"],"to_label":b["label"],
                             "from_snapshot_sha256":a.get("snapshot_sha256"),"to_snapshot_sha256":b.get("snapshot_sha256"),
                             "engineering_disposition":"PENDING","evidence_refs":[],"notes":[]})
    replay="PASS" if return_pairs and all(x["joint_state_match"] and x["snapshot_match"] and not x["pairing_error"] for x in return_pairs) else "FAIL"
    return {
      "schema_version":1,"status":"HUMAN_MOVEMENT_SWEEP_MOTION_REVIEW","production_approved":False,
      "candidate_revision":revision,"candidate_sha256":csha,"sweep_id":sweep,
      "raw_sweep_report_path":str(raw_path),"raw_sweep_report_sha256":hashlib.sha256(raw_path.read_bytes()).hexdigest(),
      "return_pairs":return_pairs,"adjacent_pairs":adjacent,"deterministic_replay_status":replay,
      "continuity_review":"PENDING","reversibility_review":"PENDING","engineering_review":"PENDING","owner_review":"PENDING",
      "interpretation":"Deterministic replay hashes are automatic evidence. Adjacent transition continuity and final reversibility remain explicit engineering review."
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("raw_report"); ap.add_argument("sweep_id"); ap.add_argument("candidate_revision"); ap.add_argument("out")
    a=ap.parse_args()
    try:
        outp=Path(a.out)
        if outp.exists(): raise ValueError(f"refusing to overwrite {outp}")
        d=build(a.raw_report,a.sweep_id,a.candidate_revision)
        outp.parent.mkdir(parents=True,exist_ok=True); outp.write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
        print("HUMAN SWEEP MOTION REVIEW: BUILT"); print(json.dumps({"sweep_id":d["sweep_id"],"return_pairs":len(d["return_pairs"]),"adjacent_pairs":len(d["adjacent_pairs"]),"deterministic_replay_status":d["deterministic_replay_status"]},indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
