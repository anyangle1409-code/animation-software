"""Read-only detailed body/garment scene audit for ORIGINAL-v1 Phase 7.

Captures modifier properties, shape keys/drivers, normal state, vertex groups,
attributes and linked material/image references. Never saves or changes the scene.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path
import subprocess
import sys

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from original_v1_garment_evidence import capture, NAMES
from original_v1_production_control import digest, ensure_finite

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(args) != 1:
    raise SystemExit("STOP — usage: blender ... --python scripts/capture_original_v1_garment_scene_blender.py -- <fresh-output.json>")
out = Path(args[0])
if out.exists():
    raise SystemExit("STOP — output already exists")


def id_ref(value):
    if value is None:
        return None
    if isinstance(value, bpy.types.ID):
        return {
            "id_type": value.bl_rna.identifier,
            "name": value.name,
            "library": value.library.filepath if value.library else None,
        }
    return None


def encode(value):
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite RNA value")
        return value
    ref = id_ref(value)
    if ref is not None:
        return ref
    if isinstance(value, set):
        return sorted(str(x) for x in value)
    if hasattr(value, "to_list"):
        data = value.to_list()
        return data
    if isinstance(value, (tuple, list)):
        return [encode(x) for x in value]
    # bpy_prop_array and similar numeric arrays.
    try:
        values = list(value)
        if all(isinstance(x, (bool, int, float, str)) for x in values):
            return [encode(x) for x in values]
    except (TypeError, ValueError):
        pass
    raise TypeError(type(value).__name__)


def modifier_receipt(mod):
    properties = {}
    unsupported = []
    for prop in mod.bl_rna.properties:
        name = prop.identifier
        if name in ("rna_type", "name"):
            continue
        try:
            properties[name] = encode(getattr(mod, name))
        except (AttributeError, TypeError, ValueError) as exc:
            unsupported.append({"property": name, "type": type(getattr(mod, name, None)).__name__, "reason": str(exc)})
    return {
        "name": mod.name,
        "type": mod.type,
        "properties": properties,
        "unsupported_properties": unsupported,
    }


def shape_key_receipt(obj):
    keys = obj.data.shape_keys
    if keys is None:
        return {"present": False, "key_blocks": [], "drivers": []}
    blocks = []
    for key in keys.key_blocks:
        blocks.append({
            "name": key.name,
            "value": float(key.value),
            "slider_min": float(key.slider_min),
            "slider_max": float(key.slider_max),
            "mute": bool(key.mute),
            "relative_key": key.relative_key.name if key.relative_key else None,
            "vertex_count": len(key.data),
        })
    drivers = []
    ad = keys.animation_data
    if ad and ad.drivers:
        for fc in ad.drivers:
            drivers.append({
                "data_path": fc.data_path,
                "array_index": fc.array_index,
                "driver_type": fc.driver.type,
                "expression": fc.driver.expression,
                "variables": [
                    {
                        "name": var.name,
                        "type": var.type,
                        "targets": [
                            {
                                "id": id_ref(t.id),
                                "data_path": t.data_path,
                                "bone_target": getattr(t, "bone_target", ""),
                                "transform_type": getattr(t, "transform_type", ""),
                                "transform_space": getattr(t, "transform_space", ""),
                            }
                            for t in var.targets
                        ],
                    }
                    for var in fc.driver.variables
                ],
            })
    return {"present": True, "key_blocks": blocks, "drivers": drivers}


def material_receipts(obj):
    rows = []
    images = {}
    for slot in obj.material_slots:
        material = slot.material
        if material is None:
            rows.append({"slot": slot.name, "material": None})
            continue
        row = {
            "slot": slot.name,
            "material": material.name,
            "library": material.library.filepath if material.library else None,
            "use_nodes": bool(material.use_nodes),
        }
        rows.append(row)
        if material.use_nodes and material.node_tree:
            for node in material.node_tree.nodes:
                if node.type == "TEX_IMAGE" and getattr(node, "image", None) is not None:
                    image = node.image
                    images[image.name] = {
                        "name": image.name,
                        "library": image.library.filepath if image.library else None,
                        "filepath": image.filepath,
                        "packed": image.packed_file is not None,
                        "source": image.source,
                    }
    return rows, [images[k] for k in sorted(images)]


def object_receipt(obj):
    materials, images = material_receipts(obj)
    attrs = []
    for attr in obj.data.attributes:
        attrs.append({"name": attr.name, "domain": attr.domain, "data_type": attr.data_type})
    uv = [{"name": layer.name, "active": bool(layer.active), "active_render": bool(layer.active_render)} for layer in obj.data.uv_layers]
    return {
        "name": obj.name,
        "object_library": obj.library.filepath if obj.library else None,
        "data_name": obj.data.name,
        "data_library": obj.data.library.filepath if obj.data.library else None,
        "vertex_count": len(obj.data.vertices),
        "edge_count": len(obj.data.edges),
        "face_count": len(obj.data.polygons),
        "loop_count": len(obj.data.loops),
        "vertex_groups": sorted(g.name for g in obj.vertex_groups),
        "attributes": sorted(attrs, key=lambda x: (x["domain"], x["name"])),
        "uv_layers": uv,
        "has_custom_normals": getattr(obj.data, "has_custom_normals", "UNAVAILABLE_IN_THIS_BLENDER_API"),
        "modifiers": [modifier_receipt(m) for m in obj.modifiers],
        "shape_keys": shape_key_receipt(obj),
        "materials": materials,
        "images": images,
        "armature": obj.find_armature().name if obj.find_armature() else None,
    }


try:
    body_raw = capture(bpy, "body")
    garment_raw = capture(bpy, "garment")
    if body_raw["candidate_sha256"] != garment_raw["candidate_sha256"]:
        raise ValueError("body/garment candidate identity differs")
    body = bpy.data.objects.get(NAMES["body"])
    garment = bpy.data.objects.get(NAMES["garment"])
    rig = bpy.data.objects.get("HGPT_CANONICAL_V4_ORIGINAL")
    if body is None or garment is None or rig is None:
        raise ValueError("required ORIGINAL-v1 body/garment/rig objects missing")
    result = {
        "schema_version": 1,
        "status": "EVIDENCE_ONLY",
        "phase_complete": False,
        "production_approved": False,
        "candidate_sha256": body_raw["candidate_sha256"],
        "source_candidate": body_raw["source_candidate"],
        "rig_id": "hgpt_canonical_v4_original",
        "blender_version": bpy.app.version_string,
        "body": object_receipt(body),
        "garment": object_receipt(garment),
        "rig": {
            "name": rig.name,
            "library": rig.library.filepath if rig.library else None,
            "bone_count": len(rig.data.bones),
            "deform_bone_count": sum(1 for b in rig.data.bones if b.use_deform),
            "bones": sorted(
                [{"name": b.name, "parent": b.parent.name if b.parent else None} for b in rig.data.bones],
                key=lambda row: row["name"],
            ),
            "lock_revision": "rev2_forearm_twist_only",
            "rig_structure_sha256": "aca64584e42890d27c3a59ee0d7e618fec58791546df9b81299d9746185bf197",
        },
        "scene_linked_libraries": sorted(lib.filepath for lib in bpy.data.libraries),
        "source_candidate_manifest": body_raw["source_candidate_manifest"],
        "capture_script": {
            "path": "scripts/capture_original_v1_garment_scene_blender.py",
            "sha256": digest(ROOT / "scripts/capture_original_v1_garment_scene_blender.py"),
        },
        "source_git_commit": subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        "capture_command": list(sys.argv),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "limits": [
            "Scene state evidence only; independent authorship still requires explicit operation history.",
            "Material/image references are inventoried but Phase 8 owns final material provenance/appearance.",
            "Modifier RNA properties that cannot be serialized are reported explicitly rather than ignored.",
            "No dressed deformation/contact PASS is inferred.",
        ],
    }
    ensure_finite(result)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(result, indent=2) + "\n")
    print("PHASE 7 GARMENT SCENE EVIDENCE WRITTEN — EVIDENCE_ONLY")
except (OSError, ValueError, KeyError, TypeError, ArithmeticError, subprocess.SubprocessError) as exc:
    raise SystemExit("STOP — " + str(exc))
