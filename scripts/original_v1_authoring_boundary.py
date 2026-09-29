"""Reusable first-party authoring-boundary checks for ORIGINAL v1 O2 Blender work."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
BLEND = ROOT / "ORIGINAL_V1_WORK" / "HomeGymPT_Male_ORIGINAL_v1.blend"
TAINT_RECORD = ROOT / "ORIGINAL_V1_WORK" / "AUTHORING_TAINT.json"

ASSET_ID = "HomeGymPT_Male_ORIGINAL_v1"
BODY_OBJECT = "HGPT_ORIGINAL_V1_CLEAN_SCAFFOLD"
BODY_MESH = "HGPT_ORIGINAL_V1_CLEAN_SCAFFOLD_MESH"
HISTORICAL_RIG = "HGPT_CLEAN_HISTORICAL_REFERENCE_RIG"
HISTORICAL_ARMATURE = "HGPT_CLEAN_HISTORICAL_REFERENCE_ARMATURE"
V4_RIG = "HGPT_CANONICAL_V4_ORIGINAL"
SCAFFOLD_MATERIAL = "HGPT_ORIGINAL_SCAFFOLD_MAT"

EXPECTED_OBJECTS = {
    BODY_OBJECT: "MESH",
    HISTORICAL_RIG: "ARMATURE",
    V4_RIG: "ARMATURE",
}
EXPECTED_COLLECTIONS = {
    "ORIGINAL_BODY",
    "ORIGINAL_CLOTHING",
    "ORIGINAL_RIG",
    "ANATOMY_GUIDES",
    "VALIDATION_HELPERS",
}
EXPECTED_MESHES = {BODY_MESH}
EXPECTED_ARMATURES = {HISTORICAL_ARMATURE, V4_RIG}
EXPECTED_MATERIALS = {SCAFFOLD_MATERIAL}
IGNORED_IMAGES = {"Render Result", "Viewer Node"}

_LINKABLE_COLLECTIONS = (
    "objects", "meshes", "armatures", "curves", "materials", "node_groups",
    "collections", "images", "actions", "cameras", "lights", "lattices",
    "metaballs", "texts",
)
_EXTERNAL_DATA_COLLECTIONS = (
    "movieclips", "sounds", "cache_files", "volumes", "pointclouds",
    "grease_pencils",
)


def _names(collection_name: str) -> set[str]:
    collection = getattr(bpy.data, collection_name, None)
    return set() if collection is None else {block.name for block in collection}


def _add(blockers: list[dict[str, str]], kind: str, detail: str) -> None:
    entry = {"kind": kind, "detail": detail}
    if entry not in blockers:
        blockers.append(entry)


def inspect_boundary(require_guarded: bool = False) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    scene = bpy.context.scene

    expected_path = BLEND.resolve()
    actual_path = Path(bpy.data.filepath).resolve() if bpy.data.filepath else None
    if actual_path != expected_path:
        _add(blockers, "blend_path", f"{actual_path} != {expected_path}")

    if not bool(scene.get("hgpt_clean_room")):
        _add(blockers, "scene", "Scene is not marked hgpt_clean_room=true.")
    if scene.get("hgpt_asset_id") != ASSET_ID:
        _add(blockers, "scene", f"hgpt_asset_id is {scene.get('hgpt_asset_id')!r}, expected {ASSET_ID}.")
    if bool(scene.get("hgpt_legacy_geometry_imported")):
        _add(blockers, "scene", "Scene metadata says legacy geometry was imported.")
    if bool(scene.get("hgpt_authoring_tainted")):
        _add(blockers, "authoring_tainted", str(
            scene.get("hgpt_authoring_taint_reason") or "Guarded authoring session was tainted."
        ))
    if require_guarded and not bool(scene.get("hgpt_guarded_authoring")):
        _add(blockers, "guard", "Checkpoint was not saved from the guarded O2 authoring launcher.")

    # O2 is stock-Blender-only. Enabled add-ons create an untracked code path
    # capable of generating or transferring production geometry.
    for addon in bpy.context.preferences.addons:
        _add(blockers, "enabled_addon", addon.module)

    for library in bpy.data.libraries:
        if library.filepath:
            _add(blockers, "linked_library", library.filepath)

    for collection_name in _LINKABLE_COLLECTIONS:
        collection = getattr(bpy.data, collection_name, None)
        if collection is None:
            continue
        for block in collection:
            library = getattr(block, "library", None)
            if library is not None:
                _add(
                    blockers,
                    "linked_datablock",
                    f"{collection_name}/{block.name} from {getattr(library, 'filepath', '')}",
                )
            if getattr(block, "override_library", None) is not None:
                _add(blockers, "library_override", f"{collection_name}/{block.name}")

    object_names = _names("objects")
    expected_object_names = set(EXPECTED_OBJECTS)
    for name in sorted(object_names - expected_object_names):
        _add(blockers, "unexpected_object", name)
    for name in sorted(expected_object_names - object_names):
        _add(blockers, "missing_object", name)
    for name, expected_type in EXPECTED_OBJECTS.items():
        obj = bpy.data.objects.get(name)
        if obj is not None and obj.type != expected_type:
            _add(blockers, "object_type", f"{name}: {obj.type} != {expected_type}")

    collection_names = _names("collections")
    for name in sorted(collection_names - EXPECTED_COLLECTIONS):
        _add(blockers, "unexpected_collection", name)
    for name in sorted(EXPECTED_COLLECTIONS - collection_names):
        _add(blockers, "missing_collection", name)

    for name in sorted(_names("meshes") - EXPECTED_MESHES):
        _add(blockers, "unexpected_mesh_datablock", name)
    for name in sorted(EXPECTED_MESHES - _names("meshes")):
        _add(blockers, "missing_mesh_datablock", name)
    for name in sorted(_names("armatures") - EXPECTED_ARMATURES):
        _add(blockers, "unexpected_armature_datablock", name)
    for name in sorted(EXPECTED_ARMATURES - _names("armatures")):
        _add(blockers, "missing_armature_datablock", name)
    for name in sorted(_names("materials") - EXPECTED_MATERIALS):
        _add(blockers, "unexpected_material", name)
    for name in sorted(EXPECTED_MATERIALS - _names("materials")):
        _add(blockers, "missing_material", name)

    for image in bpy.data.images:
        if image.name not in IGNORED_IMAGES:
            _add(
                blockers,
                "image",
                f"{image.name}: source={getattr(image, 'source', '')}, filepath={getattr(image, 'filepath', '')}",
            )

    for collection_name in _EXTERNAL_DATA_COLLECTIONS:
        collection = getattr(bpy.data, collection_name, None)
        if collection is not None:
            for block in collection:
                _add(blockers, "external_datablock", f"{collection_name}/{block.name}")

    for action in bpy.data.actions:
        _add(blockers, "action", action.name)

    body = bpy.data.objects.get(BODY_OBJECT)
    if body is not None and body.type == "MESH":
        if body.data.name != BODY_MESH:
            _add(blockers, "body_mesh", f"{body.data.name} != {BODY_MESH}")
        if not bool(body.get("hgpt_clean_scaffold")):
            _add(blockers, "body_metadata", "Body lost hgpt_clean_scaffold=true.")
        if bool(body.get("hgpt_third_party_geometry_imported")):
            _add(blockers, "body_metadata", "Body metadata says third-party geometry was imported.")
        if body.parent is not None:
            _add(blockers, "body_parent", f"Body is parented to {body.parent.name}; O2 body must be unbound.")
        for modifier in body.modifiers:
            _add(blockers, "body_modifier", f"{modifier.name}/{modifier.type}")
        for constraint in body.constraints:
            _add(blockers, "body_constraint", f"{constraint.name}/{constraint.type}")
        if body.vertex_groups:
            _add(blockers, "body_vertex_groups", f"{len(body.vertex_groups)} group(s) remain at O2.")
        if body.data.uv_layers:
            _add(blockers, "body_uv", f"{len(body.data.uv_layers)} UV layer(s) exist at O2.")
        if body.data.shape_keys is not None:
            _add(blockers, "body_shape_keys", "Shape keys exist at O2.")
        if body.animation_data is not None:
            _add(blockers, "body_animation", "Body has animation data at O2.")
        material_names = {material.name for material in body.data.materials if material is not None}
        if material_names != EXPECTED_MATERIALS:
            _add(blockers, "body_materials", f"{sorted(material_names)} != {sorted(EXPECTED_MATERIALS)}")

    historical = bpy.data.objects.get(HISTORICAL_RIG)
    if historical is not None and historical.type == "ARMATURE":
        if not bool(historical.get("hgpt_reference_only")):
            _add(blockers, "historical_rig", "Historical rig is not reference-only.")
        if not historical.hide_viewport or not historical.hide_render:
            _add(blockers, "historical_rig", "Historical rig must remain hidden in O2.")
        if historical.parent is not None:
            _add(blockers, "historical_rig", f"Historical rig is parented to {historical.parent.name}.")
        if historical.modifiers or historical.constraints or historical.animation_data is not None:
            _add(blockers, "historical_rig", "Historical rig has modifiers, constraints, or animation data.")

    rig = bpy.data.objects.get(V4_RIG)
    if rig is not None and rig.type == "ARMATURE":
        if not bool(rig.get("hgpt_unbound_o2_target")):
            _add(blockers, "v4_rig", "v4 rig is not marked hgpt_unbound_o2_target=true.")
        if rig.parent is not None:
            _add(blockers, "v4_rig", f"v4 rig is parented to {rig.parent.name}.")
        if rig.modifiers or rig.constraints or rig.animation_data is not None:
            _add(blockers, "v4_rig", "v4 rig must remain unbound and unanimated at O2.")
        if rig.pose:
            for bone in rig.pose.bones:
                for constraint in bone.constraints:
                    _add(blockers, "v4_pose_constraint", f"{bone.name}/{constraint.name}/{constraint.type}")

    for material in bpy.data.materials:
        if material.use_nodes and material.node_tree:
            for node in material.node_tree.nodes:
                if node.type == "TEX_IMAGE":
                    _add(blockers, "image_texture_node", f"{material.name}/{node.name}")

    for obj in bpy.data.objects:
        if obj.name != BODY_OBJECT:
            for constraint in obj.constraints:
                _add(blockers, "object_constraint", f"{obj.name}/{constraint.name}/{constraint.type}")

    return blockers


def write_taint(blockers: list[dict[str, str]], source: str) -> dict:
    scene = bpy.context.scene
    record = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "blend": bpy.data.filepath,
        "blockers": blockers,
    }
    scene["hgpt_authoring_tainted"] = True
    scene["hgpt_authoring_taint_reason"] = json.dumps(blockers, separators=(",", ":"))[:4000]
    TAINT_RECORD.parent.mkdir(parents=True, exist_ok=True)
    TAINT_RECORD.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record
