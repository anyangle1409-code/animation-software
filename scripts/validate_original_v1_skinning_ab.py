#!/usr/bin/env python3
"""Validate controlled read-only LBS vs Preserve Volume/DQ A/B evidence."""
from __future__ import annotations
import json,re,sys
from pathlib import Path
SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def validate(d):
    if d.get("schema_version")!=1 or d.get("status")!="READ_ONLY_BASE_SKINNING_AB_AUDIT": raise ValueError("invalid audit identity")
    if d.get("production_approved") is not False: raise ValueError("A/B audit may not claim production approval")
    if d.get("source_saved_or_modified") is not False: raise ValueError("audit must be read-only")
    if d.get("original_mode_restored") is not True: raise ValueError("original skinning mode was not restored")
    if d.get("corrective_layer")!="DISABLED_FOR_BOTH_MODES": raise ValueError("A/B must isolate base skinning with correctives disabled")
    for k in ("candidate_sha256","pose_definition_sha256","driver_sha256"):
        if not SHA_RE.fullmatch(str(d.get(k,""))): raise ValueError(f"{k} invalid")
    n=d.get("samples_per_pose")
    if not isinstance(n,int) or n<3: raise ValueError("samples_per_pose invalid")
    poses=d.get("poses") or {}
    if not poses: raise ValueError("poses missing")
    for name,row in poses.items():
        samples=row.get("samples") or []
        if len(samples)!=n: raise ValueError(f"{name}: sample count differs")
        if samples[0].get("fraction")!=0.0 or samples[-1].get("fraction")!=1.0: raise ValueError(f"{name}: endpoints missing")
        for s in samples:
            if set((s.get("lbs") or {}).keys())!={"surface_area_m2","bbox_extent_m"}: raise ValueError(f"{name}: LBS metrics incomplete")
            if set((s.get("preserve_volume") or {}).keys())!={"surface_area_m2","bbox_extent_m"}: raise ValueError(f"{name}: preserve-volume metrics incomplete")
            diff=s.get("mode_surface_difference") or {}
            for k in ("max_m","p95_m","p99_m","mean_m","top_vertices"):
                if k not in diff: raise ValueError(f"{name}: mode difference missing {k}")
    if "Do not select LBS or Preserve Volume/DQ from numeric difference magnitude alone" not in d.get("decision_rule",""):
        raise ValueError("human visual decision rule missing")
    return {"poses":len(poses),"samples_per_pose":n,"status":"PASS"}

def main():
    if len(sys.argv)!=2:
        print("Usage: validate_original_v1_skinning_ab.py <report.json>"); return 2
    try:
        out=validate(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
        print("BASE SKINNING A/B EVIDENCE: PASS"); print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
