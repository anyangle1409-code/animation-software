#!/usr/bin/env python3
"""Validate candidate-bound ORIGINAL-v1 anatomical coupling evidence."""
from __future__ import annotations
import argparse, json, math, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAP=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json"
SHA_RE=re.compile(r"^[0-9a-f]{64}$")
ENGINEERING_STATES={"NOT_RUN","IN_PROGRESS","CLEAR","BLOCKED","REJECTED_CANDIDATE"}
OWNER_STATES={"pending","accepted","rejected"}

def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

def finite(v,where="root"):
    if isinstance(v,float) and not math.isfinite(v):
        raise ValueError(f"{where}: non-finite")
    if isinstance(v,dict):
        for k,x in v.items():
            finite(x,f"{where}.{k}")
    elif isinstance(v,list):
        for i,x in enumerate(v):
            finite(x,f"{where}[{i}]")

def validate(evidence,cmap,require_exit=False):
    finite(evidence)
    if evidence.get("schema_version")!=1:
        raise ValueError("schema_version must be 1")
    if evidence.get("production_approved") is not False:
        raise ValueError("coupling evidence may not claim production approval")
    rev=evidence.get("candidate_revision")
    sha=evidence.get("candidate_sha256")
    if not isinstance(rev,str) or not re.fullmatch(r"r\d+[a-z]?",rev,re.I):
        raise ValueError("candidate_revision missing/invalid")
    if not isinstance(sha,str) or not SHA_RE.fullmatch(sha):
        raise ValueError("candidate_sha256 missing/invalid")

    required_ids=[x["id"] for x in cmap["coupling_systems"]]
    rows=evidence.get("systems") or []
    ids=[r.get("coupling_system_id") for r in rows]
    if ids!=required_ids:
        raise ValueError("coupling evidence system order/coverage differs from authoritative map")

    clear=0
    blocked=[]
    contact_moves={"horizontal_push","vertical_pull_hang","wrist_flexion_extension_loaded","loaded_foot_toe_contact","ankle_plantarflexion"}
    for row,maprow in zip(rows,cmap["coupling_systems"]):
        cid=maprow["id"]
        state=row.get("engineering_disposition")
        if state not in ENGINEERING_STATES:
            raise ValueError(f"{cid}: invalid engineering disposition")
        if row.get("owner_review") not in OWNER_STATES:
            raise ValueError(f"{cid}: invalid owner review")
        moves=set(row.get("movement_families") or [])
        if not moves.issubset(set(maprow["movement_families"])):
            raise ValueError(f"{cid}: evidence cites movement outside coupling map")
        ev=row.get("evidence") or {}
        for key in ("weights_only","corrected_surface","intermediate_motion","return_motion","whole_body_renders","regional_renders","numerical_regression","contact_load"):
            if key not in ev or not isinstance(ev[key],list):
                raise ValueError(f"{cid}: evidence.{key} missing")
        checks=[
            "attachment_sides_verified","shared_ownership_gradient_verified",
            "lengthening_compression_verified","volume_redistribution_verified",
            "fold_logic_verified","motion_continuity_verified",
            "return_reversibility_verified","bilateral_consistency_verified"
        ]
        if state=="CLEAR":
            for key in checks:
                if row.get(key) is not True:
                    raise ValueError(f"{cid}: CLEAR without {key}=true")
            for key in ("weights_only","corrected_surface","intermediate_motion","return_motion","whole_body_renders","regional_renders","numerical_regression"):
                if not ev[key]:
                    raise ValueError(f"{cid}: CLEAR without {key} evidence")
            if contact_moves.intersection(maprow["movement_families"]):
                if row.get("contact_load_propagation_verified") is not True:
                    raise ValueError(f"{cid}: CLEAR without contact/load propagation verification")
                if not ev["contact_load"]:
                    raise ValueError(f"{cid}: CLEAR without contact/load evidence")
            clear+=1
        else:
            blocked.append(cid)

    if require_exit and blocked:
        raise ValueError(f"exit blocked: coupling systems not CLEAR {blocked}")
    return {
        "candidate_revision":rev,
        "candidate_sha256":sha,
        "clear":clear,
        "total":len(rows),
        "blocking":blocked,
        "exit_checked":bool(require_exit)
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("evidence")
    ap.add_argument("--require-exit",action="store_true")
    args=ap.parse_args()
    try:
        result=validate(read(args.evidence),read(MAP),args.require_exit)
        print("ANATOMICAL COUPLING EVIDENCE: PASS")
        print(json.dumps(result,indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
