#!/usr/bin/env python3
"""Validate every required human-movement sweep acceptance record in a finalized repair workspace."""
from __future__ import annotations
import argparse,importlib.util,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ACCEPT=ROOT/"scripts/validate_original_v1_human_movement_sweep_acceptance.py"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def load_acceptance_validator():
    sp=importlib.util.spec_from_file_location("workspace_sweep_acceptance",ACCEPT)
    if sp is None or sp.loader is None: raise ValueError("unable to load sweep acceptance validator")
    m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
def stem(s): return str(s).lower().replace("-","_")

def validate_workspace(workspace,require_pass=True,acceptance_module=None):
    ws=Path(workspace)
    wm=read(ws/"workspace_manifest.json")
    fm=read(ws/"workspace_finalization_manifest.json")
    final=fm["final_candidate_sha256"]
    revision=fm["candidate_revision"]
    required=list((wm.get("validation_selection") or {}).get("sweep_only_movements_requiring_generic_runner",[]) or [])
    expected=list((wm.get("files") or {}).get("expected_sweep_acceptance_records",[]) or [])
    if len(expected)!=len(required):
        raise ValueError("workspace required-sweep/acceptance-record count differs")
    mod=acceptance_module or load_acceptance_validator()
    rows=[]; failures=[]
    for sid,path_name in zip(required,expected):
        p=ws/path_name
        if not p.is_file():
            failures.append({"sweep_id":sid,"path":path_name,"error":"acceptance record missing"})
            continue
        try:
            d=read(p)
            out=mod.validate(d,p.parent,require_pass)
            if out.get("sweep_id")!=sid: raise ValueError(f"sweep_id differs: {out.get('sweep_id')}")
            if out.get("candidate_sha256")!=final: raise ValueError("candidate SHA differs from workspace FINAL SHA")
            if d.get("candidate_revision")!=revision: raise ValueError("candidate revision differs from workspace")
            rows.append({"sweep_id":sid,"path":path_name,"engineering_review":out.get("engineering_review"),"status":"PASS"})
        except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
            failures.append({"sweep_id":sid,"path":path_name,"error":str(exc)})
    if failures:
        raise ValueError("workspace sweep acceptance incomplete: "+json.dumps(failures,sort_keys=True))
    return {
      "candidate_revision":revision,
      "candidate_sha256":final,
      "required_sweeps":required,
      "accepted":len(rows),
      "records":rows,
      "require_pass":require_pass,
      "status":"PASS"
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("workspace"); ap.add_argument("--allow-pending",action="store_true")
    a=ap.parse_args()
    try:
        out=validate_workspace(a.workspace,not a.allow_pending)
        print("WORKSPACE SWEEP ACCEPTANCE: PASS")
        print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
