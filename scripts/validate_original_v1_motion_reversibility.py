#!/usr/bin/env python3
"""Validate read-only ORIGINAL-v1 motion reversibility audit output."""
from __future__ import annotations
import json,re,sys
from pathlib import Path

SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def validate(d):
    if d.get("schema_version")!=1: raise ValueError("schema_version must be 1")
    if d.get("status")!="READ_ONLY_MOTION_REVERSIBILITY_AUDIT": raise ValueError("unexpected status")
    if d.get("source_saved_or_modified") is not False: raise ValueError("source must be read-only")
    for k in ("candidate_sha256","pose_definition_sha256","driver_sha256"):
        if not SHA_RE.fullmatch(str(d.get(k,""))): raise ValueError(f"{k} invalid")
    if d.get("overall_status") not in {"CLEAN","REVERSIBILITY_FAILURE"}: raise ValueError("invalid overall_status")
    poses=d.get("poses") or {}
    if not poses: raise ValueError("poses missing")
    tol=float(d.get("surface_tolerance_m"))
    ktol=float(d.get("shape_key_tolerance"))
    worst=0.0; kworst=0.0
    for name,row in poses.items():
        samples=row.get("samples") or []
        if len(samples)!=d.get("samples_per_direction"): raise ValueError(f"{name}: sample count differs")
        if samples[0].get("fraction")!=0.0 or samples[-1].get("fraction")!=1.0: raise ValueError(f"{name}: endpoints missing")
        m=float(row.get("max_surface_difference_m",0.0)); km=float(row.get("max_shape_key_difference",0.0))
        expected="CLEAN" if m<=tol and km<=ktol else "REVERSIBILITY_FAILURE"
        if row.get("status")!=expected: raise ValueError(f"{name}: status inconsistent with tolerances")
        worst=max(worst,m); kworst=max(kworst,km)
    expected="CLEAN" if worst<=tol and kworst<=ktol else "REVERSIBILITY_FAILURE"
    if d.get("overall_status")!=expected: raise ValueError("overall status inconsistent")
    return {"candidate":d.get("candidate"),"poses":len(poses),"status":expected,"max_surface_difference_m":worst,"max_shape_key_difference":kworst}

def main():
    if len(sys.argv)!=2:
        print("Usage: validate_original_v1_motion_reversibility.py <report.json>"); return 2
    try:
        out=validate(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
        print("MOTION REVERSIBILITY EVIDENCE: PASS")
        print(json.dumps(out,indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__":
    raise SystemExit(main())
