#!/usr/bin/env python3
"""Build focused + whole-body regression scope for one or more repair packages."""
from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PACKAGES=ROOT/"ORIGINAL_V1_ANATOMICAL_REPAIR_PACKAGES.json"
COUPLING=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json"
CAPTURE=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_CAPTURE_PLAN.json"
DEFECTS=ROOT/"ORIGINAL_V1_DEFECT_COUPLING_MAP.json"
GRAPH=ROOT/"ORIGINAL_V1_STAGE1_REPAIR_EXECUTION_GRAPH.json"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def uniq(xs):
    out=[]; seen=set()
    for x in xs:
        if x not in seen: out.append(x); seen.add(x)
    return out

def build(package_ids):
    packages=read(PACKAGES); coupling=read(COUPLING); capture=read(CAPTURE); defects=read(DEFECTS); graph=read(GRAPH)
    pby={x["id"]:x for x in packages["packages"]}; cby={x["id"]:x for x in coupling["coupling_systems"]}; cap={x["id"]:x for x in capture["systems"]}
    unknown=[x for x in package_ids if x not in pby]
    if unknown: raise ValueError(f"unknown repair packages {unknown}")
    selected_cids=[pby[x]["coupling_system_id"] for x in package_ids]
    selected=[cby[x] for x in selected_cids]
    regions=set(r for c in selected for r in c["body_regions"])
    joints=set(j for c in selected for j in c["driving_joints"])
    neighbors=[]
    reasons={}
    for c in coupling["coupling_systems"]:
        if c["id"] in selected_cids: continue
        shared_regions=sorted(regions & set(c["body_regions"]))
        shared_joints=sorted(joints & set(c["driving_joints"]))
        if shared_regions or shared_joints:
            neighbors.append(c["id"])
            reasons[c["id"]]={"shared_body_regions":shared_regions,"shared_driving_joints":shared_joints}
    focused=uniq(selected_cids+neighbors)
    movements=uniq([m for cid in focused for m in cby[cid]["movement_families"]])
    views=uniq([v for cid in focused for v in cap[cid]["views"]])
    landmarks=uniq([x for cid in focused for x in cap[cid]["close_landmarks"]])
    linked_defects=uniq([row["issue_id"] for row in defects["mappings"] if set(row["required_coupling_system_ids"]) & set(focused)])
    selected_waves=sorted({w["wave"] for w in graph["waves"] if set(w.get("package_ids",[])) & set(package_ids)})
    return {
      "schema_version":1,"status":"REPAIR_REGRESSION_PLAN","production_approved":False,
      "selected_repair_package_ids":package_ids,
      "selected_coupling_system_ids":selected_cids,
      "focused_neighbor_coupling_system_ids":neighbors,
      "neighbor_reasons":reasons,
      "focused_coupling_system_ids":focused,
      "body_regions":uniq([r for cid in focused for r in cby[cid]["body_regions"]]),
      "movement_families":movements,
      "capture_views":views,
      "close_landmarks":landmarks,
      "linked_defect_ids":linked_defects,
      "execution_waves":selected_waves,
      "whole_body_regression_required":True,
      "required_global_checks":[
        "existing_complete_pose_test_suite","floor_and_equipment_contact","bilateral_symmetry",
        "motion_continuity","motion_reversibility","all_open_Critical_High_defects","change_audit",
        "unrelated_protected_regions","candidate_sha_and_pose_hash_identity"
      ],
      "rule":"Focused neighbors receive explicit close review, but focused scope never replaces the full whole-body regression suite."
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--packages",required=True); ap.add_argument("--out",required=True)
    a=ap.parse_args()
    try:
        ids=[x.strip() for x in a.packages.split(",") if x.strip()]
        if not ids: raise ValueError("at least one package required")
        outp=Path(a.out)
        if outp.exists(): raise ValueError(f"refusing to overwrite {outp}")
        d=build(ids); outp.parent.mkdir(parents=True,exist_ok=True); outp.write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
        print("REPAIR REGRESSION PLAN WRITTEN",outp)
        print(json.dumps({"selected":ids,"focused_systems":d["focused_coupling_system_ids"],"defects":d["linked_defect_ids"]},indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
