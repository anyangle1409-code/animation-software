#!/usr/bin/env python3
"""Validate read-only motion-continuity report structure (report-only, no anatomy pass)."""
from __future__ import annotations
import json,re,sys
from pathlib import Path
SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def validate(d):
    if d.get("schema_version")!=1: raise ValueError("schema_version must be 1")
    if d.get("status")!="READ_ONLY_MOTION_CONTINUITY_REPORT": raise ValueError("unexpected status")
    if d.get("source_saved_or_modified") is not False: raise ValueError("source must be read-only")
    for k in ("candidate_sha256","pose_definition_sha256","driver_sha256"):
        if not SHA_RE.fullmatch(str(d.get(k,""))): raise ValueError(f"{k} invalid")
    n=d.get("samples")
    if not isinstance(n,int) or n<5: raise ValueError("samples invalid")
    poses=d.get("poses") or {}
    if not poses: raise ValueError("poses missing")
    for name,row in poses.items():
        samples=row.get("samples") or []
        if len(samples)!=n: raise ValueError(f"{name}: sample count differs")
        if samples[0].get("fraction")!=0.0 or samples[-1].get("fraction")!=1.0:
            raise ValueError(f"{name}: endpoints missing")
        for key in (
          "final_surface_max_step_m","weights_only_max_step_m","corrective_contribution_max_step_m",
          "final_surface_max_second_difference_m","corrective_contribution_max_second_difference_m"
        ):
            val=row.get(key)
            if not isinstance(val,(int,float)) or val<0: raise ValueError(f"{name}: invalid {key}")
    return {"poses":len(poses),"samples":n,"status":"REPORT_VALID"}

def main():
    if len(sys.argv)!=2:
        print("Usage: validate_original_v1_motion_continuity.py <report.json>"); return 2
    try:
        out=validate(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
        print("MOTION CONTINUITY REPORT: PASS")
        print(json.dumps(out,indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
