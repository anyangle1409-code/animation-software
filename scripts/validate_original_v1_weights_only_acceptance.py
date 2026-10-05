#!/usr/bin/env python3
"""Validate candidate-bound weights-only anatomical acceptance."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"ORIGINAL_V1_WEIGHTS_ONLY_ACCEPTANCE_CONTRACT.json"
SHA_RE=re.compile(r"^[0-9a-f]{64}$")
VALID={"NOT_RUN","FAIL","CLEAR"}

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def validate(d,c,require_exit=False):
    if d.get("schema_version")!=1: raise ValueError("schema_version must be 1")
    if d.get("production_approved") is not False: raise ValueError("weights-only evidence may not claim production approval")
    if not re.fullmatch(r"r\d+[a-z]?",str(d.get("candidate_revision","")),re.I): raise ValueError("candidate_revision invalid")
    if not SHA_RE.fullmatch(str(d.get("candidate_sha256",""))): raise ValueError("candidate_sha256 invalid")
    expected=[x["id"] for x in c.get("regions",[])]
    rows=d.get("regions") or []
    ids=[x.get("id") for x in rows]
    if ids!=expected: raise ValueError("region order/coverage differs from contract")
    contact={x["id"]:bool(x.get("contact_applicable")) for x in c["regions"]}
    clear=fail=notrun=0
    for row in rows:
        rid=row["id"]; state=row.get("state")
        if state not in VALID: raise ValueError(f"{rid}: invalid state")
        checks=row.get("checks") or {}
        required=[
          "attachment_continuity","shared_ownership_gradient","volume_conservation_and_redistribution",
          "lengthening_compression_direction","fold_crease_mechanical_logic","silhouette_continuity",
          "dense_motion_continuity","return_reversibility","bilateral_consistency"
        ]
        if state=="CLEAR":
            if not row.get("evidence_refs"): raise ValueError(f"{rid}: CLEAR without evidence_refs")
            for key in required:
                if checks.get(key) is not True: raise ValueError(f"{rid}: CLEAR without {key}=true")
            if contact[rid] and checks.get("contact_load_path_if_applicable") is not True:
                raise ValueError(f"{rid}: CLEAR without contact/load path=true")
            clear+=1
        elif state=="FAIL": fail+=1
        else: notrun+=1
    if require_exit and (fail or notrun):
        raise ValueError(f"exit blocked: clear={clear} fail={fail} not_run={notrun}")
    return {"clear":clear,"fail":fail,"not_run":notrun,"total":len(rows)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("evidence"); ap.add_argument("--require-exit",action="store_true")
    a=ap.parse_args()
    try:
        out=validate(read(a.evidence),read(CONTRACT),a.require_exit)
        print("WEIGHTS-ONLY ACCEPTANCE: PASS"); print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
