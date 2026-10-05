#!/usr/bin/env python3
"""Validate the authoritative ORIGINAL-v1 anatomical coupling map."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAP=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json"
MASTER=ROOT/"ORIGINAL_V1_HUMAN_BODY_MASTER_PLAN.json"
HUMAN=ROOT/"ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def finite(v, where="root"):
    if isinstance(v,float) and not math.isfinite(v):
        raise ValueError(f"{where}: non-finite number")
    if isinstance(v,dict):
        for k,x in v.items(): finite(x,f"{where}.{k}")
    elif isinstance(v,list):
        for i,x in enumerate(v): finite(x,f"{where}[{i}]")

def validate(cmap, master, human):
    finite(cmap)
    if cmap.get("schema_version")!=1: raise ValueError("schema_version must be 1")
    if cmap.get("status")!="AUTHORITATIVE_ANATOMICAL_COUPLING_MAP": raise ValueError("unexpected coupling-map status")
    if cmap.get("production_approved") is not False: raise ValueError("coupling map may not claim production approval")
    if cmap.get("asset")!=master.get("asset") or cmap.get("rig")!=master.get("rig"):
        raise ValueError("asset/rig identity differs from master plan")

    evidence_ids={row["id"] for row in human.get("entries",[])}
    systems=cmap.get("coupling_systems") or []
    if len(systems)<14: raise ValueError("coupling-system coverage incomplete")
    ids=[row.get("id") for row in systems]
    if len(ids)!=len(set(ids)): raise ValueError("duplicate coupling-system id")

    master_regions={x["id"] for x in master.get("body_regions",[])}
    master_moves=set(master.get("movement_families",[]))
    covered_regions=set()
    covered_moves=set()

    for row in systems:
        cid=row.get("id")
        if not isinstance(cid,str) or not re.fullmatch(r"CP-[A-Z]+(?:-[A-Z]+)?-\d{3}",cid):
            raise ValueError(f"invalid coupling-system id {cid}")
        for field in ("name","body_regions","proximal_anchors","distal_anchors","driving_joints",
                      "movement_families","evidence_ids","must_move","must_remain_rooted","forbidden_failures"):
            val=row.get(field)
            if field=="name":
                if not isinstance(val,str) or not val.strip(): raise ValueError(f"{cid}: missing name")
            else:
                if not isinstance(val,list) or not val: raise ValueError(f"{cid}: {field} missing/empty")
        unknown_regions=set(row["body_regions"])-master_regions
        if unknown_regions: raise ValueError(f"{cid}: unknown body regions {sorted(unknown_regions)}")
        unknown_moves=set(row["movement_families"])-master_moves
        if unknown_moves: raise ValueError(f"{cid}: unknown movement families {sorted(unknown_moves)}")
        unknown_evidence=set(row["evidence_ids"])-evidence_ids
        if unknown_evidence: raise ValueError(f"{cid}: unknown human evidence {sorted(unknown_evidence)}")
        covered_regions.update(row["body_regions"])
        covered_moves.update(row["movement_families"])

    missing_regions=master_regions-covered_regions
    if missing_regions: raise ValueError(f"coupling map misses body regions {sorted(missing_regions)}")
    missing_moves=master_moves-covered_moves
    if missing_moves: raise ValueError(f"coupling map misses movement families {sorted(missing_moves)}")

    invariants=cmap.get("global_invariants") or []
    required_phrases=("all relevant attachment sides","weights-only","return motion","symmetric","contact/load")
    text="\n".join(invariants).lower()
    for phrase in required_phrases:
        if phrase.lower() not in text:
            raise ValueError(f"global invariant missing required concept: {phrase}")

    dims=set(cmap.get("acceptance_dimensions") or [])
    required_dims={
        "attachment_continuity","shared_ownership_gradient","lengthening_compression_logic",
        "volume_redistribution","fold_crease_logic","motion_continuity",
        "return_reversibility","bilateral_consistency","contact_load_propagation"
    }
    if dims!=required_dims: raise ValueError("acceptance dimensions differ")

    required_evidence=set(cmap.get("candidate_evidence_required") or [])
    for field in ("exact_candidate_sha256","weights_only_surface_evidence",
                  "outbound_intermediate_and_return_samples","corrective_isolation_if_correctives_exist",
                  "defect_ledger_links","owner_review_state_separate"):
        if field not in required_evidence: raise ValueError(f"candidate evidence contract missing {field}")
    return True

def main():
    try:
        validate(read(MAP),read(MASTER),read(HUMAN))
        print("ANATOMICAL COUPLING MAP: PASS")
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
