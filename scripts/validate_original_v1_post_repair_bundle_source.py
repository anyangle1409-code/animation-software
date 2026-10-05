#!/usr/bin/env python3
"""Static source contract for the Stage-1 post-repair validation batch."""
from __future__ import annotations
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/"RUN_ORIGINAL_V1_POST_REPAIR_VALIDATION_BUNDLE.bat"

def validate(text):
    required=[
      "validate_original_v1_repair_workspace_identity.py",
      "get_original_v1_workspace_sweep_requirements.py",
      "validate_original_v1_human_movement_sweep_runner_calibration.py",
      "--require-calibrated",
      "RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEPS.bat",
      "RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_VISUALS.bat",
      "RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CONTACT_RAW.bat",
      "build_original_v1_workspace_sweep_motion_reviews.py",
      "collect_original_v1_workspace_sweep_evidence.py",
      "collect_original_v1_post_repair_evidence.py",
    ]
    for token in required:
        if token not in text: raise ValueError("post-repair bundle token missing: "+token)
    order=[
      "validate_original_v1_repair_workspace_identity.py",
      "RUN_ORIGINAL_V1_MOTION_CONTINUITY_AUDIT.bat",
      "get_original_v1_workspace_sweep_requirements.py",
      "--require-calibrated",
      "RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEPS.bat",
      "RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_VISUALS.bat",
      "build_original_v1_workspace_sweep_motion_reviews.py",
      "collect_original_v1_workspace_sweep_evidence.py",
      "collect_original_v1_post_repair_evidence.py",
    ]
    positions=[text.index(x) for x in order]
    if positions!=sorted(positions): raise ValueError("post-repair bundle command order differs")
    if 'if not "%CONTACT_SWEEPS%"==""' not in text:
        raise ValueError("contact sweep execution must remain conditional")
    if 'if not "%REQUIRED_SWEEPS%"==""' not in text:
        raise ValueError("generic sweep execution must remain conditional")
    if 'set "CALIBRATION=%~5"' not in text:
        raise ValueError("calibration record argument missing")
    return {"required_tokens":len(required),"status":"PASS"}

def main():
    try:
        out=validate(BATCH.read_text(encoding="utf-8"))
        print("POST-REPAIR BUNDLE SOURCE: PASS"); print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError) as exc:
        print("STOP - "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
