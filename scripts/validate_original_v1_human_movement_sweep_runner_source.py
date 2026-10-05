#!/usr/bin/env python3
"""Static source audit for the generic ORIGINAL-v1 Blender sweep runner."""
from __future__ import annotations
import ast,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RUNNER=ROOT/"scripts/audit_original_v1_human_movement_sweeps_blender.py"
SPEC=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_SPEC.json"

FORBIDDEN_SOURCE=(
    "bpy.ops.wm.save",
    "bpy.ops.wm.save_as_mainfile",
    "bpy.ops.wm.save_mainfile",
    ".save_mainfile(",
    ".save_as_mainfile(",
)

def read_json(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def validate_source(text,spec):
    try:
        ast.parse(text)
    except SyntaxError as exc:
        raise ValueError(f"runner syntax invalid: {exc}") from exc
    for token in FORBIDDEN_SOURCE:
        if token in text:
            raise ValueError(f"runner contains forbidden save operation token: {token}")
    required_literals=[
      "READ_ONLY_GENERIC_HUMAN_MOVEMENT_SWEEP_AUDIT",
      "EXPERIMENTAL_UNCALIBRATED",
      "source_saved_or_modified",
      "candidate_sha256",
      "sweep_execution_spec_sha256",
      "movement_plan_sha256",
      "pose_definition_sha256",
      "flexion_driver_sha256",
      "weights_only_surface",
      "corrective_contribution",
      "joint_state",
      "# ---------------------------------------------------------------- metrics",
    ]
    for token in required_literals:
        if token not in text: raise ValueError(f"runner contract token missing: {token}")
    sweeps=list((spec.get("sweeps") or {}).keys())
    for sid in sweeps:
        if f'name=="{sid}"' not in text:
            raise ValueError(f"runner dispatcher missing sweep adapter: {sid}")
    if "pose_test_original_v1_o4_candidate_blender.py" not in text:
        raise ValueError("frozen pose-definition source not referenced")
    if "src[:src.index(marker)]" not in text:
        raise ValueError("runner must execute only frozen pose-definition/helper section")
    if 'result["sweeps"][name]' not in text:
        raise ValueError("per-sweep result binding missing")
    return {"sweeps":len(sweeps),"syntax":"PASS","read_only_source_contract":"PASS"}

def main():
    try:
        text=RUNNER.read_text(encoding="utf-8"); spec=read_json(SPEC)
        out=validate_source(text,spec)
        print("HUMAN MOVEMENT SWEEP RUNNER SOURCE: PASS")
        print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
