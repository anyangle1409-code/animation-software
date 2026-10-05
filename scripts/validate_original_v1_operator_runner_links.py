#!/usr/bin/env python3
"""Static audit of critical ORIGINAL-v1 operator batch-file links.

Ensures every referenced Python script and nested RUN_*.bat runner exists.
This catches laptop pickup failures caused by stale or mistyped paths before
Blender execution.
"""
from __future__ import annotations
import json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CRITICAL=[
 "RUN_ORIGINAL_V1_HUMAN_BODY_GATES.bat",
 "RUN_ORIGINAL_V1_PRE_REPAIR_DIAGNOSTIC_BUNDLE.bat",
 "RUN_ORIGINAL_V1_CREATE_REPAIR_WORKSPACE.bat",
 "RUN_ORIGINAL_V1_FINALIZE_REPAIR_WORKSPACE.bat",
 "RUN_ORIGINAL_V1_POST_REPAIR_VALIDATION_BUNDLE.bat",
 "RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PIPELINE.bat",
 "RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEPS.bat",
 "RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CALIBRATION.bat",
 "RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_VISUALS.bat",
 "RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CONTACT_RAW.bat",
 "RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_REVIEW_WORKSPACE.bat",
 "RUN_ORIGINAL_V1_STAGE1_WAVE_WORK_PACKAGE.bat",
 "RUN_ORIGINAL_V1_STAGE1_LAPTOP_PICKUP_PLAN.bat",
 "RUN_ORIGINAL_V1_STAGE1_POST_EDIT_CONTINUATION_PLAN.bat",
]

PY_RE=re.compile(r"scripts[\\/]([A-Za-z0-9_.-]+\.py)",re.I)
BAT_RE=re.compile(r"\bcall\s+(RUN_[A-Za-z0-9_.-]+\.bat)",re.I)

def validate(root=ROOT):
    missing_files=[]; missing_refs=[]; audited={}
    for name in CRITICAL:
        p=root/name
        if not p.is_file():
            missing_files.append(name); continue
        text=p.read_text(encoding="utf-8",errors="replace")
        py=sorted(set(PY_RE.findall(text)))
        bats=sorted(set(BAT_RE.findall(text)))
        audited[name]={"python_scripts":py,"nested_runners":bats}
        for x in py:
            target=root/"scripts"/x
            if not target.is_file(): missing_refs.append({"from":name,"missing":f"scripts/{x}"})
        for x in bats:
            target=root/x
            if not target.is_file(): missing_refs.append({"from":name,"missing":x})
    if missing_files: raise ValueError(f"critical operator files missing: {missing_files}")
    if missing_refs: raise ValueError(f"operator link targets missing: {missing_refs}")
    return {
      "critical_operator_files":len(CRITICAL),
      "python_links_checked":sum(len(x["python_scripts"]) for x in audited.values()),
      "nested_runner_links_checked":sum(len(x["nested_runners"]) for x in audited.values()),
      "status":"PASS"
    }

def main():
    try:
        out=validate()
        print("ORIGINAL v1 OPERATOR RUNNER LINKS: PASS")
        print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
