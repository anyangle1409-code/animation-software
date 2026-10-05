#!/usr/bin/env python3
"""Build concise evidence briefs for selected anatomical repair packages."""
from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PACKAGES=ROOT/"ORIGINAL_V1_ANATOMICAL_REPAIR_PACKAGES.json"
COUPLING=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json"
HUMAN=ROOT/"ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json"
VISUAL=ROOT/"ORIGINAL_V1_SURFACE_VISUAL_EVIDENCE_REQUIREMENTS.json"
CAPTURE=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_CAPTURE_PLAN.json"
DEFECTS=ROOT/"ORIGINAL_V1_DEFECT_COUPLING_MAP.json"
WEIGHTS=ROOT/"ORIGINAL_V1_WEIGHTS_ONLY_ACCEPTANCE_CONTRACT.json"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def uniq(xs):
    out=[]; seen=set()
    for x in xs:
        if x not in seen: out.append(x); seen.add(x)
    return out

def build(ids):
    p=read(PACKAGES); c=read(COUPLING); h=read(HUMAN); v=read(VISUAL); cap=read(CAPTURE); defects=read(DEFECTS); w=read(WEIGHTS)
    pby={x["id"]:x for x in p["packages"]}; cby={x["id"]:x for x in c["coupling_systems"]}; hby={x["id"]:x for x in h["entries"]}
    vby={x["id"]:x for x in v["regions"]}; capby={x["id"]:x for x in cap["systems"]}; wby={x["id"]:x for x in w["regions"]}
    unknown=[x for x in ids if x not in pby]
    if unknown: raise ValueError(f"unknown repair packages {unknown}")
    briefs=[]
    for pid in ids:
        pkg=pby[pid]; cid=pkg["coupling_system_id"]; cp=cby[cid]; ca=capby[cid]
        region_ids=cp["body_regions"]
        visual_ids=uniq([eid for rid in region_ids for eid in vby[rid].get("current_visual_evidence_ids",[])])
        evidence_ids=uniq(cp.get("evidence_ids",[])+visual_ids)
        sources=[]
        for eid in evidence_ids:
            e=hby.get(eid)
            if e is None: raise ValueError(f"{pid}: missing human evidence {eid}")
            sources.append({
              "id":eid,"region":e.get("region"),"movement_primitive":e.get("movement_primitive"),
              "citation":(e.get("source") or {}).get("citation"),"url":(e.get("source") or {}).get("url"),
              "derived_observations":e.get("derived_observations",[]),
              "uncertainty":e.get("uncertainty"),
              "permissible_conclusions":e.get("permissible_conclusions",[])
            })
        linked=[x["issue_id"] for x in defects["mappings"] if cid in x["required_coupling_system_ids"]]
        visual_needs=uniq([f"{rid}: {n}" for rid in region_ids for n in vby[rid].get("needs",[])])
        weight_rows=[wby[rid] for rid in region_ids if rid in wby]
        briefs.append({
          "repair_package_id":pid,"name":pkg["name"],"coupling_system_id":cid,
          "priority":pkg["priority"],"body_regions":region_ids,"linked_defect_ids":linked,
          "foundational_question":pkg["foundational_question"],
          "proximal_anchors":cp["proximal_anchors"],"distal_anchors":cp["distal_anchors"],
          "driving_joints":cp["driving_joints"],"must_move":cp["must_move"],
          "must_remain_rooted":cp["must_remain_rooted"],"forbidden_failures":cp["forbidden_failures"],
          "weights_only_acceptance":pkg["weights_only_acceptance"],
          "regional_weights_only_criteria":{r["id"]:r["criteria"] for r in weight_rows},
          "residual_corrective_role":pkg["residual_corrective_role"],
          "proof_movements":pkg["proof_movements"],"capture_views":ca["views"],
          "close_landmarks":ca["close_landmarks"],"special_samples":ca.get("special_samples",[]),
          "human_evidence":sources,"open_surface_visual_needs":visual_needs,
          "interpretation":"Human sources constrain observable behavior/ranges only. Subject geometry, images, scans and coordinates are never copied into production."
        })
    return {"schema_version":1,"status":"REPAIR_EVIDENCE_BRIEFS","production_approved":False,"package_count":len(briefs),"briefs":briefs}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--packages",required=True); ap.add_argument("--out",required=True)
    a=ap.parse_args()
    try:
        ids=[x.strip() for x in a.packages.split(",") if x.strip()]
        d=build(ids); out=Path(a.out)
        if out.exists(): raise ValueError(f"refusing to overwrite {out}")
        out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
        print("REPAIR EVIDENCE BRIEFS WRITTEN",out); print(json.dumps({"packages":ids,"count":len(ids)},indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
