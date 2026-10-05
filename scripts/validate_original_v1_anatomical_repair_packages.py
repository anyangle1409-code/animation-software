#!/usr/bin/env python3
"""Validate practical ORIGINAL-v1 anatomical repair packages."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PACKAGES=ROOT/"ORIGINAL_V1_ANATOMICAL_REPAIR_PACKAGES.json"
COUPLING=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json"
CAPTURE=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_CAPTURE_PLAN.json"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def validate(d,cmap,capture):
    if d.get("schema_version")!=1: raise ValueError("schema_version must be 1")
    if d.get("status")!="PREPARED_WHOLE_BODY_REPAIR_PACKAGES": raise ValueError("unexpected status")
    if d.get("production_approved") is not False: raise ValueError("packages may not claim production approval")
    expected=[x["id"] for x in cmap.get("coupling_systems",[])]
    rows=d.get("packages") or []
    ids=[x.get("coupling_system_id") for x in rows]
    if ids!=expected: raise ValueError("repair-package coupling order/coverage differs")
    capture_by={x["id"]:x for x in capture.get("systems",[])}
    for row in rows:
        cid=row["coupling_system_id"]
        for key in ("foundational_question","preserve","repair_targets","weights_only_acceptance",
                    "residual_corrective_role","proof_movements","likely_failure_layers"):
            val=row.get(key)
            if isinstance(val,list):
                if not val: raise ValueError(f"{cid}: {key} empty")
            elif not isinstance(val,str) or not val.strip():
                raise ValueError(f"{cid}: {key} missing")
        c=set(capture_by[cid]["proof_movements"])
        if not set(row["proof_movements"]).issubset(c):
            raise ValueError(f"{cid}: repair proof movement outside capture plan")
    if "repair_smallest_foundational_layer" not in d.get("universal_edit_order",[]):
        raise ValueError("edit order must require smallest foundational repair")
    if "corrective_used_to_hide_wrong_base_weights" not in d.get("universal_forbidden_shortcuts",[]):
        raise ValueError("corrective masking shortcut must be forbidden")
    return {"packages":len(rows),"status":"PASS"}

def main():
    try:
        out=validate(read(PACKAGES),read(COUPLING),read(CAPTURE))
        print("ANATOMICAL REPAIR PACKAGES: PASS")
        print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
