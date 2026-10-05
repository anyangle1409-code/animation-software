#!/usr/bin/env python3
"""Validate generic human movement sweep execution spec."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_SPEC.json"
PLAN=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PLAN.json"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def validate(s,p):
    if s.get("schema_version")!=1 or s.get("status")!="PREPARED_GENERIC_HUMAN_SWEEP_EXECUTION_SPEC":
        raise ValueError("invalid execution spec identity")
    if s.get("production_approved") is not False: raise ValueError("execution spec may not claim production approval")
    if set((s.get("sweeps") or {}))!=set((p.get("sweeps") or {})): raise ValueError("execution sweep coverage differs from movement plan")
    for name,row in s["sweeps"].items():
        if row.get("implementation_status")!="READY_FOR_BLENDER_CALIBRATION": raise ValueError(f"{name}: implementation status invalid")
        labels=[x.get("label") for x in row.get("samples",[])]
        plan_labels=p["sweeps"][name]["samples"]
        if labels!=plan_labels: raise ValueError(f"{name}: sample labels differ from movement plan")
        if len(labels)!=len(set(labels)): raise ValueError(f"{name}: duplicate sample labels")
        if not any(bool(x.get("return_leg")) for x in row["samples"]): raise ValueError(f"{name}: return-leg sample not declared")
        if not row.get("construction") or not row.get("inspect"): raise ValueError(f"{name}: construction/inspect missing")
    rule=str(s.get("rule",""))
    if "never become runtime exercise definitions" not in rule: raise ValueError("runtime-separation rule missing")
    return {"sweeps":len(s["sweeps"]),"status":"PASS"}

def main():
    try:
        out=validate(read(SPEC),read(PLAN)); print("HUMAN SWEEP EXECUTION SPEC: PASS"); print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
