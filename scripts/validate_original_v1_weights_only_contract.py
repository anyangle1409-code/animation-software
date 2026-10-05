#!/usr/bin/env python3
"""Validate weights-only acceptance contract/template structure."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"ORIGINAL_V1_WEIGHTS_ONLY_ACCEPTANCE_CONTRACT.json"
TEMPLATE=ROOT/"ORIGINAL_V1_WEIGHTS_ONLY_ACCEPTANCE_TEMPLATE.json"
MASTER=ROOT/"ORIGINAL_V1_HUMAN_BODY_MASTER_PLAN.json"
COUPLING=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def validate(c,t,m,cm):
    if c.get("schema_version")!=1 or c.get("status")!="AUTHORITATIVE_WEIGHTS_ONLY_ACCEPTANCE_CONTRACT": raise ValueError("invalid contract identity")
    if c.get("production_approved") is not False or t.get("production_approved") is not False: raise ValueError("weights-only artifacts may not claim production approval")
    expected=[x["id"] for x in m.get("body_regions",[])]
    rows=c.get("regions") or []
    if [x.get("id") for x in rows]!=expected: raise ValueError("weights-only region coverage differs from master")
    known={x["id"] for x in cm.get("coupling_systems",[])}
    for row in rows:
        if not row.get("criteria"): raise ValueError(f"{row['id']}: criteria missing")
        if not row.get("coupling_ids") or not set(row["coupling_ids"]).issubset(known): raise ValueError(f"{row['id']}: coupling ids invalid")
    tr=t.get("regions") or []
    if [x.get("id") for x in tr]!=expected: raise ValueError("template region coverage differs")
    if set(c.get("universal_dimensions") or [])!={"attachment_continuity","shared_ownership_gradient","volume_conservation_and_redistribution","lengthening_compression_direction","fold_crease_mechanical_logic","silhouette_continuity","dense_motion_continuity","return_reversibility","bilateral_consistency","contact_load_path_if_applicable"}:
        raise ValueError("universal dimension contract differs")
    return {"regions":len(rows),"status":"PASS"}

def main():
    try:
        out=validate(read(CONTRACT),read(TEMPLATE),read(MASTER),read(COUPLING)); print("WEIGHTS-ONLY CONTRACT: PASS"); print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
