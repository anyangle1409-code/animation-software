#!/usr/bin/env python3
"""Validate Stage 1 wave execution briefs against the authoritative graph."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BRIEFS=ROOT/"ORIGINAL_V1_STAGE1_WAVE_EXECUTION_BRIEFS.json"
GRAPH=ROOT/"ORIGINAL_V1_STAGE1_REPAIR_EXECUTION_GRAPH.json"
PACKAGES=ROOT/"ORIGINAL_V1_ANATOMICAL_REPAIR_PACKAGES.json"
POSES=ROOT/"ORIGINAL_V1_POSE_MOVEMENT_FAMILY_MAP.json"
SWEEPS=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PLAN.json"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def validate(b,g,p,pm,s):
    if b.get("schema_version")!=1 or b.get("status")!="AUTHORITATIVE_STAGE1_WAVE_EXECUTION_BRIEFS":
        raise ValueError("invalid brief identity")
    if b.get("production_approved") is not False: raise ValueError("briefs may not claim production approval")
    waves=b.get("waves") or []; gw=g.get("waves") or []
    if [x.get("id") for x in waves]!=[x.get("id") for x in gw]: raise ValueError("wave order/coverage differs from graph")
    known_packages={x["id"] for x in p.get("packages",[])}
    known_sweeps=set((s.get("sweeps") or {}).keys())
    pose_moves=set(m for moves in (pm.get("mappings") or {}).values() for m in moves)
    for row,auth in zip(waves,gw):
        wid=row["id"]
        if row.get("packages")!=(auth.get("package_ids") or []): raise ValueError(f"{wid}: packages differ")
        if row.get("depends")!=(auth.get("depends_on") or []): raise ValueError(f"{wid}: dependencies differ")
        if not set(row.get("packages") or []).issubset(known_packages): raise ValueError(f"{wid}: unknown package")
        val=row.get("validation") or {}
        integrated=val.get("integrated_movement_families") or []
        expected=auth.get("required_integrated_movements") or row.get("movements") or integrated
        if integrated!=expected: raise ValueError(f"{wid}: integrated movements differ from graph")
        sweeps_for_wave=val.get("deterministic_sweep_definitions") or []
        for sweep in sweeps_for_wave:
            if sweep not in known_sweeps: raise ValueError(f"{wid}: unknown sweep {sweep}")
        expected_runner_status="RUNNER_BOUND_CALIBRATION_AND_CANDIDATE_EXECUTION_REQUIRED" if sweeps_for_wave else "NOT_REQUIRED"
        if val.get("sweep_runner_status")!=expected_runner_status:
            raise ValueError(f"{wid}: sweep runner status differs from live execution state")
        if sweeps_for_wave:
            if val.get("sweep_runner_binding")!="BOUND_11_OF_11":
                raise ValueError(f"{wid}: sweep runner binding state stale")
            if val.get("candidate_sweep_acceptance")!="NOT_RUN":
                raise ValueError(f"{wid}: candidate sweep acceptance may not be inferred")
        uncovered=[m for m in integrated if m not in known_sweeps and m not in pose_moves]
        if val.get("uncovered_definition_count")!=len(uncovered): raise ValueError(f"{wid}: uncovered count differs")
        if uncovered: raise ValueError(f"{wid}: uncovered movement definitions {uncovered}")
        if "neutral" not in (val.get("frozen_pose_fixtures") or []): raise ValueError(f"{wid}: neutral fixture missing")
    if waves[-1].get("packages")!=[x["id"] for x in p["packages"]]:
        raise ValueError("whole-body wave must contain all repair packages in canonical order")
    return {"waves":len(waves),"status":"PASS"}

def main():
    try:
        out=validate(read(BRIEFS),read(GRAPH),read(PACKAGES),read(POSES),read(SWEEPS))
        print("STAGE1 WAVE EXECUTION BRIEFS: PASS"); print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
