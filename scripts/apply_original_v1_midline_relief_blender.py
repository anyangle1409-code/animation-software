"""Apply the declared Phase 3E midline relief to a NEW numbered O4 candidate.

blender --background --factory-startup <source O4_bind candidate.blend> --python-exit-code 1 ^
  --python scripts/apply_original_v1_midline_relief_blender.py -- <mask.json> <new candidate.blend>

Recomputes the displacement from the declaration (core ids + parameters) with scripts/original_v1_midline_relief.py and REFUSES
unless the derived mask equals the declared one. Only declared vertex positions change; weights/topology/rig untouched.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import original_v1_midline_relief as mr  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:]
mask_path, new_path = Path(args[0]), Path(args[1])
if new_path.exists():
    raise SystemExit(f"Refusing to overwrite {new_path}")
scene = bpy.context.scene
if not scene.get("hgpt_not_production") or scene.get("hgpt_candidate") != "O4_bind":
    raise SystemExit("O4_bind candidate files only.")
src_path = Path(bpy.data.filepath)
src_sha = hashlib.sha256(src_path.read_bytes()).hexdigest()
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
if len(rig.data.bones) != 63:
    raise SystemExit("Expected the frozen 63-bone v4 rig.")
me = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"].data
declared = json.loads(mask_path.read_text(encoding="utf-8"))
if not declared.get("declared_before_edit"):
    raise SystemExit("mask file is not a pre-edit declaration")
par = declared["parameters"]
rest = np.array([v.co[:] for v in me.vertices])
me.calc_loop_triangles()
tris = np.array([t.vertices[:] for t in me.loop_triangles])
n_before, f_before = len(me.vertices), len(me.polygons)
mask, disp, rep = mr.plan(rest, tris, declared["core_vertex_ids"], par["depth_mm"] / 1000, par["half_width_mm"] / 1000, par["taper_mm"] / 1000)
if mask != sorted(declared["allowed_vertex_ids"]):
    raise SystemExit("derived mask differs from the declared mask: refusing to edit")
for i, dv in disp.items():
    me.vertices[i].co = (rest[i] + dv).tolist()
me.update()
after = np.array([v.co[:] for v in me.vertices])
changed = np.nonzero(np.abs(after - rest).max(axis=1) > 1e-9)[0]
if set(int(i) for i in changed) != set(mask):
    raise SystemExit("edited vertex set differs from the declared mask")
if len(me.vertices) != n_before or len(me.polygons) != f_before:
    raise SystemExit("topology changed")
scene["hgpt_candidate_revision"] = new_path.stem
scene["hgpt_candidate_parent_sha256"] = src_sha
scene["hgpt_geometry_revision"] = "midline_relief_v1"
bpy.ops.wm.save_as_mainfile(filepath=str(new_path), copy=True)
mag = np.linalg.norm(after[changed] - rest[changed], axis=1) * 1000.0
rec = {"generated_utc": datetime.now(timezone.utc).isoformat(),
       "stage": "O4 candidate first-party local geometry edit: midline relief (not production)",
       "source_candidate": src_path.name, "source_sha256": src_sha, "candidate": new_path.name,
       "candidate_sha256": hashlib.sha256(new_path.read_bytes()).hexdigest(),
       "declared_mask": mask_path.name, "declared_mask_sha256": hashlib.sha256(mask_path.read_bytes()).hexdigest(),
       "parameters": par, "vertices_moved": int(len(changed)), "max_displacement_mm": round(float(mag.max()), 4),
       "mean_displacement_mm": round(float(mag.mean()), 4), "planned": rep, "weights_changed": False,
       "topology_changed": False, "rig_bones": len(rig.data.bones)}
new_path.with_suffix(".json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
print("MIDLINE RELIEF", json.dumps({k: rec[k] for k in ("candidate", "candidate_sha256", "vertices_moved", "max_displacement_mm")}))
