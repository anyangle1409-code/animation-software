#!/usr/bin/env python3
"""Static integrity gate for the preferred ORIGINAL-v1 laptop recovery workflow.

Non-Blender only. It verifies that the preferred operator entry points and their
critical command chain still exist and that current handoffs point to the packet
generators rather than historical Phase-5/fallback paths.
"""
from __future__ import annotations
import json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

REQUIRED_FILES=[
  "RUN_ORIGINAL_V1_STAGE1_LAPTOP_PICKUP_PLAN.bat",
  "scripts/build_original_v1_stage1_laptop_pickup_plan.py",
  "RUN_ORIGINAL_V1_STAGE1_POST_EDIT_CONTINUATION_PLAN.bat",
  "scripts/build_original_v1_stage1_post_edit_continuation_plan.py",
  "RUN_ORIGINAL_V1_HUMAN_BODY_GATES.bat",
  "RUN_ORIGINAL_V1_PRE_REPAIR_DIAGNOSTIC_BUNDLE.bat",
  "RUN_ORIGINAL_V1_STAGE1_WAVE_WORK_PACKAGE.bat",
  "RUN_ORIGINAL_V1_CREATE_REPAIR_WORKSPACE.bat",
  "RUN_ORIGINAL_V1_FINALIZE_REPAIR_WORKSPACE.bat",
  "RUN_ORIGINAL_V1_POST_REPAIR_VALIDATION_BUNDLE.bat",
  "RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEPS.bat",
  "RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CALIBRATION.bat",
  "RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_VISUALS.bat",
  "RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CONTACT_RAW.bat",
  "RUN_ORIGINAL_V1_COLLECT_WORKSPACE_SWEEP_EVIDENCE.bat",
  "RUN_ORIGINAL_V1_VALIDATE_WORKSPACE_SWEEP_ACCEPTANCE.bat",
  "RUN_ORIGINAL_V1_CANDIDATE_COMPARISON.bat",
  "scripts/collect_original_v1_workspace_sweep_evidence.py",
  "scripts/validate_original_v1_workspace_sweep_acceptance.py",
  "docs/CURRENT_HANDOFF.md",
  "docs/WORK_LAPTOP_HUMAN_BODY_RECOVERY_HANDOFF_20261005.md",
  "docs/ORIGINAL_V1_WHOLE_BODY_REPAIR_GUIDE.md",
  "ORIGINAL_V1_HUMAN_BODY_MASTER_PLAN.json",
  "ORIGINAL_V1_HUMAN_BODY_STATUS.json",
  "ORIGINAL_V1_STAGE1_PROGRESS.json",
  "ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_STATUS.json",
]

PICKUP_REQUIRED=[
  "RUN_ORIGINAL_V1_HUMAN_BODY_GATES.bat",
  "RUN_ORIGINAL_V1_STAGE1_WAVE_WORK_PACKAGE.bat",
  "RUN_ORIGINAL_V1_PRE_REPAIR_DIAGNOSTIC_BUNDLE.bat",
  "RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEPS.bat",
  "RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CALIBRATION.bat",
  "RUN_ORIGINAL_V1_CREATE_REPAIR_WORKSPACE.bat",
]

POST_REQUIRED=[
  "RUN_ORIGINAL_V1_FINALIZE_REPAIR_WORKSPACE.bat",
  "RUN_ORIGINAL_V1_POST_REPAIR_VALIDATION_BUNDLE.bat",
  "RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEPS.bat",
  "RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_VISUALS.bat",
  "RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CONTACT_RAW.bat",
  "RUN_ORIGINAL_V1_COLLECT_WORKSPACE_SWEEP_EVIDENCE.bat",
  "RUN_ORIGINAL_V1_VALIDATE_WORKSPACE_SWEEP_ACCEPTANCE.bat",
  "RUN_ORIGINAL_V1_CANDIDATE_COMPARISON.bat",
]

HANDOFF_REQUIRED={
 "docs/CURRENT_HANDOFF.md":[
   "RUN_ORIGINAL_V1_STAGE1_LAPTOP_PICKUP_PLAN.bat",
   "RUN_ORIGINAL_V1_STAGE1_POST_EDIT_CONTINUATION_PLAN.bat",
   "PRE-EDIT repair workspace",
   "unified candidate comparison",
 ],
 "docs/WORK_LAPTOP_HUMAN_BODY_RECOVERY_HANDOFF_20261005.md":[
   "RUN_ORIGINAL_V1_STAGE1_LAPTOP_PICKUP_PLAN.bat",
   "RUN_ORIGINAL_V1_STAGE1_POST_EDIT_CONTINUATION_PLAN.bat",
   "RUN_ORIGINAL_V1_COLLECT_WORKSPACE_SWEEP_EVIDENCE.bat",
   "RUN_ORIGINAL_V1_VALIDATE_WORKSPACE_SWEEP_ACCEPTANCE.bat",
 ],
 "docs/ORIGINAL_V1_WHOLE_BODY_REPAIR_GUIDE.md":[
   "RUN_ORIGINAL_V1_STAGE1_LAPTOP_PICKUP_PLAN.bat",
   "RUN_ORIGINAL_V1_STAGE1_POST_EDIT_CONTINUATION_PLAN.bat",
   "RUN_ORIGINAL_V1_VALIDATE_WORKSPACE_SWEEP_ACCEPTANCE.bat",
   "lower-level",
 ],
}

def text(path):
    return (ROOT/path).read_text(encoding="utf-8")

def validate(files_exist=None, contents=None):
    missing=[]
    if files_exist is None:
        for p in REQUIRED_FILES:
            if not (ROOT/p).is_file(): missing.append(p)
    else:
        missing=[p for p in REQUIRED_FILES if p not in files_exist]
    if missing:
        raise ValueError("required laptop workflow files missing: "+json.dumps(missing))

    def get(p):
        return contents[p] if contents is not None and p in contents else text(p)

    pickup=get("scripts/build_original_v1_stage1_laptop_pickup_plan.py")
    missing_pickup=[x for x in PICKUP_REQUIRED if x not in pickup]
    if missing_pickup:
        raise ValueError("pickup planner command chain incomplete: "+json.dumps(missing_pickup))

    post=get("scripts/build_original_v1_stage1_post_edit_continuation_plan.py")
    missing_post=[x for x in POST_REQUIRED if x not in post]
    if missing_post:
        raise ValueError("post-edit planner command chain incomplete: "+json.dumps(missing_post))
    order=[post.index(x) for x in (
        "RUN_ORIGINAL_V1_FINALIZE_REPAIR_WORKSPACE.bat",
        "RUN_ORIGINAL_V1_POST_REPAIR_VALIDATION_BUNDLE.bat",
        "RUN_ORIGINAL_V1_COLLECT_WORKSPACE_SWEEP_EVIDENCE.bat",
        "RUN_ORIGINAL_V1_VALIDATE_WORKSPACE_SWEEP_ACCEPTANCE.bat",
        "RUN_ORIGINAL_V1_CANDIDATE_COMPARISON.bat",
    )]
    if order!=sorted(order):
        raise ValueError("post-edit critical command order is invalid")

    collector=get("scripts/collect_original_v1_workspace_sweep_evidence.py")
    for token in ("MOTION_BUILDER","workspace_sweep_evidence_index.json","motion_records","acceptance_records"):
        if token not in collector:
            raise ValueError("workspace sweep collector contract token missing: "+token)

    preflight=get("scripts/validate_original_v1_workspace_sweep_acceptance.py")
    for token in ("workspace_finalization_manifest.json","expected_sweep_acceptance_records","candidate SHA differs from workspace FINAL SHA","require_pass"):
        if token not in preflight:
            raise ValueError("workspace sweep acceptance preflight token missing: "+token)

    for p,tokens in HANDOFF_REQUIRED.items():
        body=get(p)
        for token in tokens:
            if token not in body:
                raise ValueError(f"{p}: preferred workflow token missing: {token}")

    current=get("docs/CURRENT_HANDOFF.md")
    preferred=current.split("## Separate standalone runtime track",1)[0]
    if "EXECUTE Phase 5A anatomy" in preferred and "NOT operational" not in preferred:
        raise ValueError("current handoff may not present historical Phase 5A as operational")

    status=json.loads(get("ORIGINAL_V1_HUMAN_BODY_STATUS.json"))
    if status.get("master_stage")!=1 or status.get("high_detail_anatomy_allowed") is not False:
        raise ValueError("body status no longer blocks high-detail anatomy during Stage 1")
    if status.get("production_approved") is not False:
        raise ValueError("body status may not claim production approval")
    authority=status.get("authority") or {}
    for key,path in (
       ("stage1_laptop_pickup_plan_runner","RUN_ORIGINAL_V1_STAGE1_LAPTOP_PICKUP_PLAN.bat"),
       ("stage1_post_edit_continuation_plan_runner","RUN_ORIGINAL_V1_STAGE1_POST_EDIT_CONTINUATION_PLAN.bat"),
       ("workspace_sweep_acceptance_preflight","RUN_ORIGINAL_V1_VALIDATE_WORKSPACE_SWEEP_ACCEPTANCE.bat"),
    ):
        if authority.get(key)!=path:
            raise ValueError(f"status authority mismatch for {key}")

    return {
      "required_files":len(REQUIRED_FILES),
      "pickup_commands":len(PICKUP_REQUIRED),
      "post_edit_commands":len(POST_REQUIRED),
      "handoff_documents":len(HANDOFF_REQUIRED),
      "master_stage":status.get("master_stage"),
      "high_detail_anatomy_allowed":status.get("high_detail_anatomy_allowed"),
      "production_approved":status.get("production_approved"),
      "status":"PASS",
    }

def main():
    try:
        out=validate()
        print("LAPTOP WORKFLOW INTEGRITY: PASS")
        print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
