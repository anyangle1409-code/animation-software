#!/usr/bin/env python3
"""Static source audit for generic human movement sweep visual renderer."""
from __future__ import annotations
import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/capture_original_v1_human_movement_sweep_visual_blender.py"
CAM=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CAMERA_PLAN.json"
PLAN=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PLAN.json"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def validate_source(text,cam,plan):
    try: ast.parse(text)
    except SyntaxError as exc: raise ValueError(f"visual renderer syntax invalid: {exc}") from exc
    for token in ("bpy.ops.wm.save","save_as_mainfile","save_mainfile"):
        if token in text: raise ValueError("visual renderer contains save operation")
    required=("HUMAN_MOVEMENT_SWEEP_VISUAL_CAPTURE","candidate_after","camera_matrix_world","runner_script_sha256","generic_handle_visible","floor_visible")
    for token in required:
        if token not in text: raise ValueError(f"visual renderer contract token missing: {token}")
    expected={x for row in plan["sweeps"].values() for x in row["cameras"]}
    if set(cam["cameras"])!=expected: raise ValueError("camera plan coverage differs")
    return {"cameras":len(expected),"status":"PASS"}
def main():
    try:
        out=validate_source(SCRIPT.read_text(encoding="utf-8"),read(CAM),read(PLAN))
        print("HUMAN SWEEP VISUAL RENDERER SOURCE: PASS"); print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP - "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
