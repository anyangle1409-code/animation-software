"""Apply the declared Phase 3C thumb-pad clearance edit to a NEW numbered O4 candidate.

blender --background --factory-startup <source O4_bind candidate.blend> --python-exit-code 1 ^
  --python scripts/apply_original_v1_thumb_pad_clearance_blender.py -- <mask.json> <survey.json> <new candidate.blend>

mask.json is the declaration written (and committed) BEFORE the edit by scripts/declare_original_v1_thumb_pad_mask.py;
survey.json is the read-only survey of the SAME source candidate. The displacement is recomputed with the shared module
scripts/original_v1_thumb_pad.py and the run REFUSES unless the derived mask equals the declared one exactly. Only the
positions of the declared thumb-region vertices change: no weights, topology, UVs, materials, shape keys, rig, poses or
handle frame. Refuses to overwrite; writes <new>.json with hashes and displacement statistics.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import original_v1_thumb_pad as tp  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:]
mask_path, survey_path, new_path = Path(args[0]), Path(args[1]), Path(args[2])
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
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
me = body.data

declared = json.loads(mask_path.read_text(encoding="utf-8"))
survey = json.loads(survey_path.read_text(encoding="utf-8"))
if survey["candidate"] != src_path.name:
    raise SystemExit(f"survey is of {survey['candidate']}, not of {src_path.name}")
if not declared.get("declared_before_edit"):
    raise SystemExit("mask file is not a pre-edit declaration")
par = declared["parameters"]
names = json.loads(scene["hgpt_region_names"])
region = np.array([d.value for d in me.attributes["hgpt_region"].data])
rest = np.array([v.co[:] for v in me.vertices])
n_before, f_before = len(me.vertices), len(me.polygons)
thumb_ids = np.nonzero(region == names.index("thumb"))[0]
side_of = lambda i: "l" if rest[i, 0] < 0 else "r"
mask, disp, report = tp.plan(survey, rest, thumb_ids, side_of, par["margin_mm"] / 1000.0, par["falloff_mm"] / 1000.0)
if mask != sorted(declared["allowed_vertex_ids"]):
    raise SystemExit("derived mask differs from the declared mask: refusing to edit")
after = tp.clearance_after(survey, rest, disp, side_of)
inside = {i for s in "lr" for i in tp.inside_vertices(survey, s, [j for j in thumb_ids if side_of(j) == s])}
worst_mm = min(after[i] for i in inside) * 1000.0
if worst_mm < par["margin_mm"] - 1e-3:
    raise SystemExit(f"clearance check failed: worst formerly-inside vertex clears by only {worst_mm:.3f} mm")
moved = 0
for i, dv in disp.items():
    me.vertices[i].co = (rest[i] + dv).tolist()
    moved += 1
me.update()
rest_after = np.array([v.co[:] for v in me.vertices])
changed = np.nonzero(np.abs(rest_after - rest).max(axis=1) > 1e-9)[0]
if set(int(i) for i in changed) != set(mask):
    raise SystemExit("edited vertex set differs from the declared mask")
if len(me.vertices) != n_before or len(me.polygons) != f_before:
    raise SystemExit("topology changed")

scene["hgpt_candidate_revision"] = new_path.stem
scene["hgpt_candidate_parent_sha256"] = src_sha
scene["hgpt_geometry_revision"] = "thumb_pad_clearance_v1"
bpy.ops.wm.save_as_mainfile(filepath=str(new_path), copy=True)
mag = np.linalg.norm(rest_after[changed] - rest[changed], axis=1) * 1000.0
rec = {"generated_utc": datetime.now(timezone.utc).isoformat(),
       "stage": "O4 candidate first-party local geometry edit: thumb-pad clearance (not production)",
       "source_candidate": src_path.name, "source_sha256": src_sha,
       "candidate": new_path.name, "candidate_sha256": hashlib.sha256(new_path.read_bytes()).hexdigest(),
       "declared_mask": mask_path.name, "declared_mask_sha256": hashlib.sha256(mask_path.read_bytes()).hexdigest(),
       "declared_ids_sha256": declared["allowed_vertex_ids_sha256"], "survey": survey_path.name,
       "survey_sha256": hashlib.sha256(survey_path.read_bytes()).hexdigest(), "parameters": par,
       "vertices_moved": int(len(changed)), "max_displacement_mm": round(float(mag.max()), 4),
       "mean_displacement_mm": round(float(mag.mean()), 4), "planned": report,
       "min_clearance_after_mm_of_formerly_inside_vertices": round(worst_mm, 4),
       "vertices_before": n_before, "vertices_after": len(me.vertices), "faces_before": f_before, "faces_after": len(me.polygons),
       "weights_changed": False, "topology_changed": False, "rig_bones": len(rig.data.bones),
       "inputs": "this candidate's own ORIGINAL v1 mesh and the project's own handle frame only"}
new_path.with_suffix(".json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
print("THUMB PAD", json.dumps({k: rec[k] for k in ("candidate", "candidate_sha256", "vertices_moved", "max_displacement_mm",
                                                    "min_clearance_after_mm_of_formerly_inside_vertices")}))
