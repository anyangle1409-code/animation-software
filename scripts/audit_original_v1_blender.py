"""Audit the ORIGINAL v1 clean-room Blender workspace.

Run with Blender:
  blender --background ORIGINAL_V1_WORK/HomeGymPT_Male_ORIGINAL_v1.blend \
    --python scripts/audit_original_v1_blender.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports"
REPORT = REPORT_DIR / "original_v1_blender_audit.json"

FORBIDDEN = (
    "BASELINE_v5",
    "BASELINE_v6",
    "BASELINE_v7",
    "BASELINE_v8",
    "CORNER_FINAL",
    "V13e",
    "V14e",
    "V15",
    "MakeHuman",
    "makehuman",
    "Meshy",
)

blockers: list[dict] = []
warnings: list[dict] = []


def block(kind: str, detail: str):
    blockers.append({"kind": kind, "detail": detail})


scene = bpy.context.scene

if not bool(scene.get("hgpt_clean_room")):
    block("scene", "Scene is not marked hgpt_clean_room=true.")

if bool(scene.get("hgpt_legacy_geometry_imported")):
    block("scene", "Scene metadata says legacy geometry was imported.")

# Linked external Blend libraries would make the asset depend on another file.
for library in bpy.data.libraries:
    if library.filepath:
        block("linked_library", library.filepath)

# No external images/textures are allowed at the clean scaffold stage.
for image in bpy.data.images:
    if image.name in {"Render Result", "Viewer Node"}:
        continue
    source = getattr(image, "source", "")
    filepath = getattr(image, "filepath", "")
    block("image", f"{image.name}: source={source}, filepath={filepath}")

for material in bpy.data.materials:
    if not material.use_nodes or not material.node_tree:
        continue
    for node in material.node_tree.nodes:
        if node.type == "TEX_IMAGE":
            block("image_texture_node", f"{material.name}/{node.name}")

# Reject obvious legacy/third-party lineage identifiers in actual scene data.
data_names = []
data_names += [obj.name for obj in bpy.data.objects]
data_names += [mesh.name for mesh in bpy.data.meshes]
data_names += [arm.name for arm in bpy.data.armatures]
data_names += [mat.name for mat in bpy.data.materials]

for name in data_names:
    for token in FORBIDDEN:
        if token.lower() in name.lower():
            block("forbidden_name", f"{name} contains {token}")

body = bpy.data.objects.get("HGPT_ORIGINAL_V1_CLEAN_SCAFFOLD")
rig = bpy.data.objects.get("HGPT_CLEAN_HISTORICAL_REFERENCE_RIG")

if body is None:
    block("scaffold", "HGPT_ORIGINAL_V1_CLEAN_SCAFFOLD is missing.")
elif body.type != "MESH":
    block("scaffold", f"Scaffold object type is {body.type}, expected MESH.")
else:
    vertices = len(body.data.vertices)
    triangles = sum(max(0, len(poly.vertices) - 2) for poly in body.data.polygons)
    if vertices != 3890:
        block("scaffold_vertices", f"{vertices} != expected 3890")
    if triangles != 7280:
        block("scaffold_triangles", f"{triangles} != expected 7280")
    if not bool(body.get("hgpt_clean_scaffold")):
        block("scaffold_metadata", "Body is not marked hgpt_clean_scaffold=true.")
    if bool(body.get("hgpt_third_party_geometry_imported")):
        block("scaffold_metadata", "Body metadata says third-party geometry was imported.")
    if bool(body.get("hgpt_production_ready")):
        warnings.append({
            "kind": "production_ready",
            "detail": "Clean scaffold is marked production ready; it should remain false until the final asset gates pass.",
        })

if rig is None:
    block("reference_rig", "HGPT_CLEAN_HISTORICAL_REFERENCE_RIG is missing.")
elif rig.type != "ARMATURE":
    block("reference_rig", f"Reference rig type is {rig.type}, expected ARMATURE.")
else:
    bones = len(rig.data.bones)
    if bones != 53:
        block("reference_rig_bones", f"{bones} != expected 53")
    if not bool(rig.get("hgpt_reference_only")):
        block("reference_rig_metadata", "Historical rig is not marked hgpt_reference_only=true.")

# Clean stage should not carry actions/animations copied in from elsewhere.
if len(bpy.data.actions) != 0:
    block("actions", f"{len(bpy.data.actions)} action(s) exist in clean scaffold workspace.")

result = {
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "blend": bpy.data.filepath,
    "pass": len(blockers) == 0,
    "blocker_count": len(blockers),
    "warning_count": len(warnings),
    "blockers": blockers,
    "warnings": warnings,
    "counts": {
        "objects": len(bpy.data.objects),
        "meshes": len(bpy.data.meshes),
        "armatures": len(bpy.data.armatures),
        "materials": len(bpy.data.materials),
        "images": len(bpy.data.images),
        "actions": len(bpy.data.actions),
    },
}

REPORT_DIR.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
sys.exit(0 if result["pass"] else 1)
