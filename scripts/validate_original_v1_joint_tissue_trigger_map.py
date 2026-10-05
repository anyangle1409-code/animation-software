#!/usr/bin/env python3
"""Validate ORIGINAL-v1 joint-to-tissue trigger map and evaluate moved bones."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TRIGGERS=ROOT/"ORIGINAL_V1_JOINT_TISSUE_TRIGGER_MAP.json"
COUPLING=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json"

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def validate(data,coupling):
    if data.get("schema_version")!=1:
        raise ValueError("schema_version must be 1")
    if data.get("status")!="AUTHORITATIVE_JOINT_TISSUE_TRIGGER_MAP":
        raise ValueError("unexpected trigger-map status")
    if data.get("production_approved") is not False:
        raise ValueError("trigger map may not claim production approval")
    known={x["id"] for x in coupling.get("coupling_systems",[])}
    rows=data.get("rules") or []
    if not rows:
        raise ValueError("rules missing")
    ids=[r.get("id") for r in rows]
    if len(ids)!=len(set(ids)):
        raise ValueError("duplicate trigger rule id")
    for row in rows:
        rid=row.get("id")
        pats=row.get("bone_patterns") or []
        req=row.get("required_coupling_system_ids") or []
        if not pats or not req:
            raise ValueError(f"{rid}: patterns/coupling systems required")
        for pat in pats:
            try: re.compile(pat)
            except re.error as exc: raise ValueError(f"{rid}: invalid regex {pat}: {exc}")
        unknown=set(req)-known
        if unknown:
            raise ValueError(f"{rid}: unknown coupling ids {sorted(unknown)}")
        if not row.get("rationale"):
            raise ValueError(f"{rid}: rationale missing")
    if "absent from candidate evidence" not in str(data.get("failure_rule","")):
        raise ValueError("failure rule must make missing coupling evidence blocking")
    return True

def required_for_bones(data,bones):
    matched=[]
    required=set()
    for row in data.get("rules",[]):
        hits=[]
        for bone in bones:
            if any(re.fullmatch(pat,bone) for pat in row["bone_patterns"]):
                hits.append(bone)
        if hits:
            matched.append({"rule_id":row["id"],"joint_family":row["joint_family"],"bones":sorted(hits),
                            "required_coupling_system_ids":row["required_coupling_system_ids"]})
            required.update(row["required_coupling_system_ids"])
    unmatched=[b for b in bones if not any(re.fullmatch(pat,b) for r in data.get("rules",[]) for pat in r["bone_patterns"])]
    return {"matched_rules":matched,"required_coupling_system_ids":sorted(required),"unmatched_bones":sorted(unmatched)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bones",help="comma-separated moved bone names")
    args=ap.parse_args()
    try:
        data=read(TRIGGERS); coupling=read(COUPLING); validate(data,coupling)
        print("JOINT-TISSUE TRIGGER MAP: PASS")
        if args.bones:
            bones=[x.strip() for x in args.bones.split(",") if x.strip()]
            print(json.dumps(required_for_bones(data,bones),indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
