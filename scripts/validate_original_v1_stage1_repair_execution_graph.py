#!/usr/bin/env python3
"""Validate dependency-aware Stage 1 whole-body repair execution graph."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GRAPH=ROOT/"ORIGINAL_V1_STAGE1_REPAIR_EXECUTION_GRAPH.json"
PACKAGES=ROOT/"ORIGINAL_V1_ANATOMICAL_REPAIR_PACKAGES.json"
MASTER=ROOT/"ORIGINAL_V1_HUMAN_BODY_MASTER_PLAN.json"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def validate(g,p,m):
    if g.get("schema_version")!=1 or g.get("status")!="AUTHORITATIVE_STAGE1_REPAIR_EXECUTION_GRAPH": raise ValueError("invalid graph identity")
    if g.get("production_approved") is not False: raise ValueError("graph may not claim production approval")
    waves=g.get("waves") or []
    if [x.get("wave") for x in waves]!=list(range(8)): raise ValueError("wave order must be 0..7")
    wave_ids={x["id"] for x in waves}
    pkg_ids={x["id"] for x in p.get("packages",[])}
    known_moves=set(m.get("movement_families",[]))
    for w in waves:
        if not set(w.get("package_ids",[])).issubset(pkg_ids): raise ValueError(f"{w['id']}: unknown repair package")
        if not set(w.get("depends_on",[])).issubset(wave_ids): raise ValueError(f"{w['id']}: unknown dependency")
        if not set(w.get("required_integrated_movements",[])).issubset(known_moves): raise ValueError(f"{w['id']}: unknown movement")
        if not w.get("exit"): raise ValueError(f"{w['id']}: exit missing")
    final=waves[-1]
    if set(final["package_ids"])!=pkg_ids: raise ValueError("whole-body integration must include every repair package")
    if g.get("current_position",{}).get("id")!="shoulder_yoke_foundation": raise ValueError("current position must remain shoulder-yoke foundation")
    if "enter high-detail anatomy before whole_body_integration exit" not in g.get("invalid_sequences",[]): raise ValueError("high-detail block missing")
    return {"waves":len(waves),"packages":len(pkg_ids),"status":"PASS"}

def main():
    try:
        out=validate(read(GRAPH),read(PACKAGES),read(MASTER)); print("STAGE1 REPAIR EXECUTION GRAPH: PASS"); print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
