#!/usr/bin/env python3
"""Validate a candidate-specific coupling-zone declaration before Blender runs."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
COUPLING=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json"
HUMAN=ROOT/"ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json"
SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def validate(d,c,h):
    if d.get("schema_version")!=1: raise ValueError("schema_version must be 1")
    if d.get("production_approved") is not False: raise ValueError("declaration may not claim production approval")
    if not re.fullmatch(r"r\d+[a-z]?",str(d.get("candidate_revision","")),re.I): raise ValueError("candidate_revision invalid")
    if not SHA_RE.fullmatch(str(d.get("candidate_sha256",""))): raise ValueError("candidate_sha256 invalid")
    systems={x["id"] for x in c.get("coupling_systems",[])}
    if d.get("coupling_system_id") not in systems: raise ValueError("unknown coupling_system_id")
    ids=d.get("vertex_ids") or []
    if not ids or any(not isinstance(x,int) or x<0 for x in ids): raise ValueError("vertex_ids must be non-empty non-negative integers")
    if len(ids)!=len(set(ids)): raise ValueError("vertex_ids contain duplicates")
    groups=d.get("anchor_groups") or []
    if len(groups)<2: raise ValueError("at least two anchor_groups required")
    names=[g.get("name") for g in groups]
    if any(not isinstance(n,str) or not n for n in names) or len(names)!=len(set(names)): raise ValueError("anchor group names missing/duplicated")
    for g in groups:
        bones=g.get("bones") or []
        if not bones or any(not isinstance(x,str) or not x for x in bones): raise ValueError(f"anchor group {g.get('name')} bones missing")
    if d.get("topology_change_allowed") is not False: raise ValueError("diagnostic declaration must default topology_change_allowed=false")
    if d.get("rest_geometry_change_allowed") is not False: raise ValueError("diagnostic declaration must default rest_geometry_change_allowed=false")
    refs=set(d.get("human_evidence_ids") or [])
    known={x["id"] for x in h.get("entries",[])}
    if not refs: raise ValueError("human_evidence_ids required")
    if refs-known: raise ValueError(f"unknown human evidence ids {sorted(refs-known)}")
    if not d.get("expected_human_behaviour"): raise ValueError("expected_human_behaviour required")
    if not d.get("forbidden_visual_failures"): raise ValueError("forbidden_visual_failures required")
    return True

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("declaration"); args=ap.parse_args()
    try:
        validate(read(args.declaration),read(COUPLING),read(HUMAN))
        print("COUPLING ZONE DECLARATION: PASS")
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
