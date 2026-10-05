#!/usr/bin/env python3
"""Build pose -> connected tissue -> camera -> evidence plans.

Input is the read-only pose-coupling-scope report produced in Blender. Output is
pure planning metadata; it never edits a model and never makes pose identity a
runtime deformation input.
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
COUPLING=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json"
CAPTURE=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_CAPTURE_PLAN.json"
POSEMAP=ROOT/"ORIGINAL_V1_POSE_MOVEMENT_FAMILY_MAP.json"
VISUAL=ROOT/"ORIGINAL_V1_SURFACE_VISUAL_EVIDENCE_REQUIREMENTS.json"
HUMAN=ROOT/"ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def unique(seq):
    out=[]; seen=set()
    for x in seq:
        if x not in seen: out.append(x); seen.add(x)
    return out

def build(scope):
    coupling=read(COUPLING); capture=read(CAPTURE); posemap=read(POSEMAP); visual=read(VISUAL); human=read(HUMAN)
    coupling_by={x["id"]:x for x in coupling["coupling_systems"]}
    capture_by={x["id"]:x for x in capture["systems"]}
    visual_by={x["id"]:x for x in visual["regions"]}
    human_ids={x["id"] for x in human["entries"]}
    result={
      "schema_version":1,"status":"POSE_CAPTURE_EVIDENCE_PLAN",
      "candidate":scope.get("candidate"),"candidate_sha256":scope.get("candidate_sha256"),
      "source_pose_scope":scope.get("status"),"production_approved":False,
      "layers":capture["common_layers"],"motion_states":capture["common_motion_states"],
      "poses":{}
    }
    for pose,row in scope["poses"].items():
        movement_families=posemap["mappings"].get(pose,[])
        systems=[]
        all_views=[]; all_landmarks=[]; all_human=[]; all_surface=[]; all_needs=[]
        for cid in row["required_coupling_system_ids"]:
            c=coupling_by[cid]; cap=capture_by[cid]
            intersect=[m for m in movement_families if m in cap["proof_movements"]]
            vis_refs=[]; needs=[]
            for region in c["body_regions"]:
                vr=visual_by[region]
                vis_refs.extend(vr.get("current_visual_evidence_ids",[]))
                needs.extend([f"{region}: {x}" for x in vr.get("needs",[])])
            human_refs=unique(list(c.get("evidence_ids",[]))+vis_refs)
            unknown=[x for x in human_refs if x not in human_ids]
            if unknown: raise ValueError(f"{pose}/{cid}: unknown human evidence {unknown}")
            system={
              "coupling_system_id":cid,
              "body_regions":c["body_regions"],
              "triggered_by_moved_bones":True,
              "mapped_pose_movement_families":movement_families,
              "relevant_proof_movements":intersect,
              "required_views":cap["views"],
              "close_landmarks":cap["close_landmarks"],
              "special_samples":cap.get("special_samples",[]),
              "human_evidence_ids":human_refs,
              "open_surface_evidence_needs":unique(needs),
              "must_move":c["must_move"],
              "must_remain_rooted":c["must_remain_rooted"],
              "forbidden_failures":c["forbidden_failures"]
            }
            systems.append(system)
            all_views.extend(cap["views"]); all_landmarks.extend(cap["close_landmarks"])
            all_human.extend(human_refs); all_surface.extend(vis_refs); all_needs.extend(needs)
        result["poses"][pose]={
          "movement_families":movement_families,
          "moved_bone_count":row["moved_bone_count"],
          "required_coupling_system_ids":row["required_coupling_system_ids"],
          "systems":systems,
          "capture_views":unique(all_views),
          "close_landmarks":unique(all_landmarks),
          "human_evidence_ids":unique(all_human),
          "surface_visual_evidence_ids":unique(all_surface),
          "open_surface_evidence_needs":unique(all_needs),
          "required_layers":capture["common_layers"],
          "required_motion_states":capture["common_motion_states"],
          "completion_rule":"Every triggered system must have candidate-bound weights-only and final-corrected evidence through applicable intermediate/endpoint/return states; missing connected tissue makes the pose incomplete."
        }
    return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("pose_scope"); ap.add_argument("out")
    a=ap.parse_args()
    try:
        scope=read(a.pose_scope); outp=Path(a.out)
        if outp.exists(): raise ValueError(f"refusing to overwrite {outp}")
        result=build(scope); outp.parent.mkdir(parents=True,exist_ok=True)
        outp.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        print("POSE CAPTURE EVIDENCE PLAN WRITTEN",outp); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
