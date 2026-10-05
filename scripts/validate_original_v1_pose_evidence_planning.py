#!/usr/bin/env python3
"""Validate static pose->movement->capture planning authorities."""
from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
POSEMAP=ROOT/"ORIGINAL_V1_POSE_MOVEMENT_FAMILY_MAP.json"
MASTER=ROOT/"ORIGINAL_V1_HUMAN_BODY_MASTER_PLAN.json"
CAPTURE=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_CAPTURE_PLAN.json"
POSESCRIPT=ROOT/"scripts/pose_test_original_v1_o4_candidate_blender.py"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def validate(pm,m,c):
    if pm.get("schema_version")!=1 or pm.get("status")!="AUTHORITATIVE_POSE_TO_MOVEMENT_FAMILY_MAP": raise ValueError("invalid pose-map identity")
    if pm.get("production_approved") is not False: raise ValueError("pose map may not claim production approval")
    known=set(m.get("movement_families",[]))
    for pose,moves in (pm.get("mappings") or {}).items():
        if not moves or not set(moves).issubset(known): raise ValueError(f"{pose}: movement mapping invalid")
    src=POSESCRIPT.read_text(encoding="utf-8")
    block=re.search(r"POSES\s*=\s*\{([\s\S]*?)\n\}",src)
    if not block: raise ValueError("POSES dictionary not found")
    pose_keys=set(re.findall(r'"([^"]+)"\s*:',block.group(1)))
    if set(pm["mappings"])!=pose_keys:
        raise ValueError(f"pose-map keys differ from pose definitions; missing={sorted(pose_keys-set(pm['mappings']))} extra={sorted(set(pm['mappings'])-pose_keys)}")
    capture_moves={x for row in c.get("systems",[]) for x in row.get("proof_movements",[])}
    if not set().union(*[set(v) for v in pm["mappings"].values()]).issubset(known):
        raise ValueError("pose mapping contains unknown movement")
    if "Pose names are validation fixtures only" not in pm.get("rule",""): raise ValueError("runtime-identity prohibition missing")
    return {"poses":len(pose_keys),"status":"PASS"}

def main():
    try:
        out=validate(read(POSEMAP),read(MASTER),read(CAPTURE)); print("POSE EVIDENCE PLANNING: PASS"); print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
