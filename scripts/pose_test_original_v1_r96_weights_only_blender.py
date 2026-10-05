"""Run the authoritative pose metrics with every corrective disabled in memory.

This wrapper never saves. It removes the three shoulder corrective configs and
mutes every non-Basis body shape key before executing the frozen pose test.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy


SCRIPT = Path(__file__).resolve()
POSE_SCRIPT = SCRIPT.with_name("pose_test_original_v1_o4_candidate_blender.py")
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not args:
    raise SystemExit("output directory is required")
out = Path(args[0]).resolve()
scene = bpy.context.scene
body = bpy.data.objects.get("HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE")
if body is None:
    raise SystemExit("frozen ORIGINAL-v1 candidate body is missing")

disabled_properties = []
for name in ("hgpt_shoulder_corrective", "hgpt_flexion_corrective", "hgpt_scapular_corrective"):
    if name in scene:
        del scene[name]
        disabled_properties.append(name)
disabled_keys = []
shape_keys = body.data.shape_keys
if shape_keys is not None:
    for key in shape_keys.key_blocks:
        if key == shape_keys.reference_key:
            continue
        key.value = 0.0
        key.mute = True
        disabled_keys.append(key.name)
bpy.context.view_layer.update()

mode = args[2] if len(args) > 2 else "--metrics-only"
if mode not in ("--metrics-only", "--milestone", "--render"):
    raise SystemExit("mode must be --metrics-only, --milestone or --render")
pose_args = [str(out), args[1] if len(args) > 1 else ""]
if mode != "--render":
    pose_args.append(mode)
saved_argv = sys.argv
sys.argv = ["blender", "--", *pose_args]
namespace = {"__name__": "__main__", "__file__": str(POSE_SCRIPT)}
try:
    source = POSE_SCRIPT.read_text(encoding="utf-8")
    exec(compile(source, str(POSE_SCRIPT), "exec"), namespace)
finally:
    sys.argv = saved_argv

candidate = Path(bpy.data.filepath)
record = {
    "schema_version": 1,
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "weights_only_gate": True,
    "candidate": candidate.name,
    "candidate_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
    "disabled_scene_properties": disabled_properties,
    "disabled_shape_keys": disabled_keys,
    "capture_mode": mode.removeprefix("--"),
    "pose_report_sha256": hashlib.sha256((out / "pose_test_report.json").read_bytes()).hexdigest(),
    "saved_blend": False,
    "production_approved": False,
}
(out / "weights_only_gate_manifest.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print("R96 WEIGHTS-ONLY GATE", json.dumps(record, sort_keys=True))
