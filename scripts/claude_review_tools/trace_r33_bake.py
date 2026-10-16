"""Read-only R33 bake-stage trace; reconstruct keys in memory, never save a blend."""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/anatomy_fit"))
os.environ["S7_LOCKOUT_HT"] = "166"
import bpy
import numpy as np
import build_original_review_candidate_r17_blender as r17
import build_original_bake_corrective_blender as bake
import build_original_movement_benchmarks_blender as bench
import build_original_sculpt_corrective_blender as sculpt
import original_v1_review_candidate_drives as drives
import original_v1_shoulder_r4 as r4

CAND = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates/claude_review_r33_20261016"
OUT = Path("/tmp/r33-diagnostics/bake-stages.json")
KEYS = (120.0, 145.0, 156.0, 166.0)
targets_file = CAND / "stages/r33_targets.npz"
with np.load(targets_file) as z:
    targets = {str(ht): z[str(ht)].copy() for ht in KEYS}
res = r17._setup(CAND / "stages/B5_base.blend")
body, rig = res["body"], res["runtime"]
rig["hgpt_s7_angles_start"] = 95.0
trace = {}

def snapshot(tag):
    rows = {}
    for ht in KEYS:
        bench._reset(rig)
        for kb in body.data.shape_keys.key_blocks[1:]:
            kb.value = 0.0
        sculpt.press_pose(res, ht)
        drives.drive(rig, body)
        vertices, _ = bench._evaluated(body)
        posed = np.array([tuple(v) for v in vertices])
        err = np.linalg.norm(posed - targets[str(ht)], axis=1) * 1000
        rows[str(ht)] = {
            "max_mm": float(err.max()),
            "p99_mm": float(np.percentile(err, 99)),
            "over_5mm": int((err > 5).sum()),
            "v18633_mm": float(err[18633]),
            "top_vertices": [
                {"index": int(i), "error_mm": float(err[i])}
                for i in np.argsort(-err)[:12]
            ],
        }
    bench._reset(rig)
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    trace[tag] = rows
    print("BAKE_STAGE", tag, json.dumps(rows), flush=True)

original_smooth = bake.smooth_guard
original_final = sculpt._guard

def traced_smooth(*args, **kwargs):
    snapshot("before_path_guards")
    value = original_smooth(*args, **kwargs)
    snapshot("after_smooth_guard")
    return value

def traced_final(*args, **kwargs):
    value = original_final(*args, **kwargs)
    snapshot("after_final_guard")
    return value

def benchmark_press(t):
    hook = r4._S.get("extend")
    r4._S["extend"] = None
    try:
        bench.pose_press(res, t, __import__("build_functional_shoulder_correction_blender"))
    finally:
        r4._S["extend"] = hook

bake.smooth_guard = traced_smooth
sculpt._guard = traced_final
try:
    log = bake.build(res, targets, prefix="HGPT_S7_DELT_", keys_ht=KEYS,
                     angles_prop="hgpt_s7_angles",
                     extra_guard_paths=[("benchmark_press", benchmark_press)])
finally:
    bake.smooth_guard = original_smooth
    sculpt._guard = original_final
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"status": "DIAGNOSTIC_ONLY_NO_BLEND_SAVED",
                           "stages": trace, "build_log": log}, indent=2) + "\n")
print("TRACE_COMPLETE", str(OUT), flush=True)
