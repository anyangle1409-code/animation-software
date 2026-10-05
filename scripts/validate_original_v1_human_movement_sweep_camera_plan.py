#!/usr/bin/env python3
"""Validate authoritative camera geometry for human movement sweep renders."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CAM=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CAMERA_PLAN.json"
PLAN=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PLAN.json"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def validate(c,p):
    if c.get("schema_version")!=1 or c.get("status")!="AUTHORITATIVE_HUMAN_SWEEP_CAMERA_PLAN":
        raise ValueError("invalid camera-plan identity")
    if c.get("production_approved") is not False: raise ValueError("camera plan may not claim production approval")
    expected={x for row in p.get("sweeps",{}).values() for x in row.get("cameras",[])}
    cams=c.get("cameras") or {}
    if set(cams)!=expected:
        raise ValueError(f"camera coverage differs: missing={sorted(expected-set(cams))} extra={sorted(set(cams)-expected)}")
    for cid,row in cams.items():
        bones=row.get("focus_bones") or []
        if not bones: raise ValueError(f"{cid}: focus bones missing")
        if row.get("anchor") not in {"head","tail","mid"}: raise ValueError(f"{cid}: anchor invalid")
        for k in ("azimuth_deg","elevation_deg","ortho_scale"):
            if not isinstance(row.get(k),(int,float)): raise ValueError(f"{cid}: {k} invalid")
        if not 0.15 <= float(row["ortho_scale"]) <= 3.0: raise ValueError(f"{cid}: ortho scale unreasonable")
    render=c.get("renderer") or {}
    if render.get("engine")!="BLENDER_WORKBENCH" or render.get("bare_body") is not True:
        raise ValueError("renderer contract differs")
    res=render.get("resolution")
    if not isinstance(res,list) or len(res)!=3 or any(not isinstance(x,int) or x<=0 for x in res):
        raise ValueError("resolution invalid")
    return {"cameras":len(cams),"status":"PASS"}

def main():
    try:
        out=validate(read(CAM),read(PLAN)); print("HUMAN SWEEP CAMERA PLAN: PASS"); print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP - "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
