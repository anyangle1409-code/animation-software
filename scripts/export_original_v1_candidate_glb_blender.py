"""Export the O4/O7 CANDIDATE as review GLBs (dressed + bare). Never saves the Blend.

blender --background --factory-startup ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE.blend \
        --python scripts/export_original_v1_candidate_glb_blender.py

Uses Blender's bundled glTF exporter as a development tool (enabled only for
this candidate export session). Output: rest-pose skinned GLBs for runtime
review; they are candidates, not production assets.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import addon_utils
import bpy

scene = bpy.context.scene
if not scene.get("hgpt_not_production"):
    raise SystemExit("Candidate files only.")
addon_utils.enable("io_scene_gltf2", default_set=False)
out = Path(bpy.data.filepath).parent
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
body = next(o for o in bpy.data.objects if o.type == "MESH" and o.find_armature() == rig and "SHORTS" not in o.name)
shorts = bpy.data.objects.get("HGPT_ORIGINAL_V1_SHORTS_CANDIDATE")
mask = body.modifiers.get("HGPT_DRESSED_MASK")
for o in bpy.data.objects:
    o.select_set(False)
bpy.data.objects["HGPT_CLEAN_HISTORICAL_REFERENCE_RIG"].hide_set(True)

results = {}
for variant in ("dressed", "bare"):
    dressed = variant == "dressed"
    if mask:
        mask.show_viewport = mask.show_render = dressed
    rig.select_set(True)
    body.select_set(True)
    if shorts:
        shorts.hide_set(not dressed)
        shorts.select_set(dressed)
    path = out / f"HomeGymPT_Male_ORIGINAL_v1_CANDIDATE_{variant.upper()}.glb"
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True,
                              export_apply=True, export_skins=True, export_animations=False,
                              export_yup=True, export_texcoords=False, export_materials="EXPORT")
    results[variant] = {"file": path.name, "bytes": path.stat().st_size,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    for o in bpy.data.objects:
        o.select_set(False)

record = {"generated_utc": datetime.now(timezone.utc).isoformat(), "stage": "candidate review export (not production)",
          "rig": "hgpt_canonical_v4_original", "exports": results}
(out / "CANDIDATE_GLB_EXPORT.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print("GLB", json.dumps(record))
