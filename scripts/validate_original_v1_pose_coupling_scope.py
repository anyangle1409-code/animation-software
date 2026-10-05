#!/usr/bin/env python3
"""Validate read-only pose -> anatomical-coupling scope evidence."""
from __future__ import annotations
import json, math, re, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
COUPLING=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json"
TRIGGER=ROOT/"ORIGINAL_V1_JOINT_TISSUE_TRIGGER_MAP.json"
SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def finite(v,where="root"):
    if isinstance(v,float) and not math.isfinite(v): raise ValueError(f"{where}: non-finite")
    if isinstance(v,dict):
        for k,x in v.items(): finite(x,f"{where}.{k}")
    elif isinstance(v,list):
        for i,x in enumerate(v): finite(x,f"{where}[{i}]")

def validate(report,coupling,trigger):
    finite(report)
    if report.get("schema_version")!=1: raise ValueError("schema_version must be 1")
    if report.get("status")!="READ_ONLY_POSE_COUPLING_SCOPE": raise ValueError("unexpected report status")
    if report.get("source_saved_or_modified") is not False: raise ValueError("report must state source_saved_or_modified=false")
    if not SHA_RE.fullmatch(str(report.get("candidate_sha256",""))): raise ValueError("candidate_sha256 invalid")
    for field in ("pose_definition_script_sha256","trigger_map_sha256","coupling_map_sha256"):
        if not SHA_RE.fullmatch(str(report.get(field,""))): raise ValueError(field+" invalid")
    systems=[x["id"] for x in coupling.get("coupling_systems",[])]
    system_set=set(systems)
    trigger_ids={x["id"] for x in trigger.get("rules",[])}
    poses=report.get("poses") or {}
    if not poses: raise ValueError("no poses recorded")
    for pose,row in poses.items():
        moved=row.get("moved_bones") or []
        if row.get("moved_bone_count")!=len(moved): raise ValueError(f"{pose}: moved_bone_count differs")
        names=[x.get("bone") for x in moved]
        if len(names)!=len(set(names)): raise ValueError(f"{pose}: duplicate moved bone")
        if any(x.get("moved") is not True for x in moved): raise ValueError(f"{pose}: moved_bones contains non-moved record")
        matches=row.get("trigger_matches") or []
        referenced=set()
        for match in matches:
            if match.get("trigger_rule_id") not in trigger_ids: raise ValueError(f"{pose}: unknown trigger rule")
            bones=match.get("matched_bones") or []
            if not bones or not set(bones).issubset(set(names)): raise ValueError(f"{pose}: trigger matched_bones invalid")
            req=match.get("required_coupling_system_ids") or []
            if not req or not set(req).issubset(system_set): raise ValueError(f"{pose}: trigger coupling systems invalid")
            referenced.update(req)
        ordered=row.get("required_coupling_system_ids") or []
        expected=[x for x in systems if x in referenced]
        if ordered!=expected: raise ValueError(f"{pose}: required coupling system order/coverage differs from trigger matches")
        if row.get("required_coupling_system_count")!=len(ordered): raise ValueError(f"{pose}: coupling count differs")
        if moved and not ordered:
            raise ValueError(f"{pose}: moved bones produced no connected-tissue review scope")
        if not row.get("review_rule"): raise ValueError(f"{pose}: review_rule missing")
    return {"poses":len(poses),"candidate_sha256":report["candidate_sha256"],"status":"PASS"}

def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if "--" in argv: argv=argv[argv.index("--")+1:]
    if len(argv)!=1:
        print("Usage: validate_original_v1_pose_coupling_scope.py <report.json>")
        return 2
    try:
        result=validate(read(argv[0]),read(COUPLING),read(TRIGGER))
        print("POSE COUPLING SCOPE: PASS")
        print(json.dumps(result,indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
