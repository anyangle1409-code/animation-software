"""Initialize the Home Gym PT Male ORIGINAL v1 clean-room Blender workspace.

Run with Blender, not normal Python:
  blender --background --factory-startup --python scripts/init_original_v1_blender.py

This script intentionally creates no body geometry and imports no legacy asset.
It establishes a traceable blank starting file and clean-room collections only.
"""
from __future__ import annotations

import json
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "ORIGINAL_V1_WORK"
BLEND = OUT_DIR / "HomeGymPT_Male_ORIGINAL_v1.blend"
PROVENANCE = OUT_DIR / "ORIGINAL_V1_PROVENANCE.json"


def git_value(*args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).strip()
    except Exception:
        return None


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# Factory-startup should be blank except defaults. Remove every object and
# datablock that could accidentally become the seed of the production asset.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

for meshes in (bpy.data.meshes, bpy.data.armatures, bpy.data.curves):
    for block in list(meshes):
        meshes.remove(block)

scene = bpy.context.scene
scene.name = "HGPT_ORIGINAL_V1"
scene["hgpt_clean_room"] = True
scene["hgpt_asset_id"] = "HomeGymPT_Male_ORIGINAL_v1"
scene["hgpt_legacy_geometry_imported"] = False
scene["hgpt_starting_geometry"] = "blank"
scene["hgpt_created_utc"] = datetime.now(timezone.utc).isoformat()
scene["hgpt_source_branch"] = git_value("branch", "--show-current") or "unknown"
scene["hgpt_source_head"] = git_value("rev-parse", "HEAD") or "unknown"

# Remove all non-master collections left by startup, then create only project
# clean-room work areas.
master = scene.collection
for collection in list(bpy.data.collections):
    if collection != master:
        bpy.data.collections.remove(collection)

for name in (
    "ORIGINAL_BODY",
    "ORIGINAL_CLOTHING",
    "ORIGINAL_RIG",
    "ANATOMY_GUIDES",
    "VALIDATION_HELPERS",
):
    collection = bpy.data.collections.new(name)
    master.children.link(collection)

# Use metric units so every authored dimension is explicit and reviewable.
scene.unit_settings.system = "METRIC"
scene.unit_settings.length_unit = "METERS"
scene.unit_settings.scale_length = 1.0

OUT_DIR.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))

record = {
    "asset_id": "HomeGymPT_Male_ORIGINAL_v1",
    "created_utc": scene["hgpt_created_utc"],
    "clean_room": True,
    "starting_geometry": "blank",
    "legacy_geometry_imported": False,
    "source_branch": scene["hgpt_source_branch"],
    "source_head": scene["hgpt_source_head"],
    "blend_path": str(BLEND.relative_to(ROOT)).replace("\\", "/"),
    "blend_sha256": sha256(BLEND),
    "blender_version": bpy.app.version_string,
    "collections": [
        "ORIGINAL_BODY",
        "ORIGINAL_CLOTHING",
        "ORIGINAL_RIG",
        "ANATOMY_GUIDES",
        "VALIDATION_HELPERS",
    ],
    "prohibited_sources": [
        "V5/V6/V7/V8 imported character lineage",
        "CORNER_FINAL",
        "V9-V15 character candidates",
        "MakeHuman anatomical body arrays",
        "legacy skin weights/UVs/materials/source rig transforms",
    ],
}
PROVENANCE.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record, indent=2))
