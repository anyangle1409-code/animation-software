#!/usr/bin/env python3
"""Read-only Home Gym PT character checkpoint audit for Blender 5.2.x.

Run:
  blender -b /path/to/checkpoint.blend \
    --python scripts/preflight/v1_character_readonly_audit.py -- \
    --output /path/to/report.json

This script creates a JSON report only. It never saves or changes the .blend.
For separate parent/locked-body fingerprint comparison, run on F23d and F83a
and compare body geometry hashes from their JSON output.
"""
import argparse
import hashlib
import json
import os
import struct
import sys
from datetime import datetime, timezone

import bpy

CENTER = ("root", "pelvis", "spine_01", "spine_02", "spine_03", "neck", "head")
SIDE = (
    "clavicle", "scapula", "upperarm", "forearm", "hand",
    "thumb_01", "thumb_02", "thumb_03",
    "metacarpal_index", "index_01", "index_02", "index_03",
    "metacarpal_middle", "middle_01", "middle_02", "middle_03",
    "metacarpal_ring", "ring_01", "ring_02", "ring_03",
    "metacarpal_pinky", "pinky_01", "pinky_02", "pinky_03",
    "thigh", "shin", "foot", "toe",
)
CONTRACT = set(CENTER) | {f"{n}_{s}" for n in SIDE for s in ("l", "r")}
assert len(CONTRACT) == 63


def digest_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def round_vec(vec):
    return [round(float(v), 7) for v in vec]


def mesh_fingerprint(mesh):
    """Hash rest positions plus polygon indices; no topology or deformation edits."""
    h = hashlib.sha256()
    h.update(struct.pack("<QQQ", len(mesh.vertices), len(mesh.edges), len(mesh.polygons)))
    for vertex in mesh.vertices:
        h.update(struct.pack("<3d", *map(float, vertex.co)))
    for face in mesh.polygons:
        h.update(struct.pack("<I", len(face.vertices)))
        for vi in face.vertices:
            h.update(struct.pack("<I", int(vi)))
    return h.hexdigest()


def mesh_info(obj):
    mesh = obj.data
    group_names = {g.index: g.name for g in obj.vertex_groups}
    deform_names = {
        b.name for mod in obj.modifiers if mod.type == "ARMATURE" and mod.object
        for b in mod.object.data.bones if b.use_deform
    }
    n_unweighted = n_not_normalized = n_overweighted = 0
    n_unmapped = 0
    max_total = 0.0
    for vertex in mesh.vertices:
        total = sum(float(a.weight) for a in vertex.groups
                    if group_names.get(a.group) in deform_names)
        if total < 1e-7:
            n_unweighted += 1
        elif abs(total - 1.0) > 1e-3:
            n_not_normalized += 1
            if total > 1.001:
                n_overweighted += 1
        max_total = max(max_total, total)
        if any(group_names.get(a.group) is None for a in vertex.groups):
            n_unmapped += 1

    chest_group = obj.vertex_groups.get("CHEST_REBUILD_REGION")
    chest_count = 0
    if chest_group:
        chest_count = sum(
            any(g.group == chest_group.index for g in v.groups)
            for v in mesh.vertices
        )
    return {
        "name": obj.name, "mesh_name": mesh.name,
        "vertex_count": len(mesh.vertices), "edge_count": len(mesh.edges),
        "polygon_count": len(mesh.polygons),
        "geometry_sha256": mesh_fingerprint(mesh),
        "vertex_groups_count": len(obj.vertex_groups),
        "shape_keys": [k.name for k in mesh.shape_keys.key_blocks] if mesh.shape_keys else [],
        "materials": [m.name if m else None for m in mesh.materials],
        "modifier_types": [m.type for m in obj.modifiers],
        "armatures": [m.object.name for m in obj.modifiers if m.type == "ARMATURE" and m.object],
        "working_chest_region_vertices": chest_count if chest_group else None,
        "deform_weight_unassigned_vertices": n_unweighted if deform_names else None,
        "deform_weight_not_unit_vertices": n_not_normalized if deform_names else None,
        "deform_weight_over_one_vertices": n_overweighted if deform_names else None,
        "max_deform_weight_sum": round(max_total, 5) if deform_names else None,
        "unmapped_vertex_group_indices": n_unmapped,
        "location": round_vec(obj.location),
        "scale": round_vec(obj.scale),
    }


def rig_info(obj):
    bones = obj.data.bones
    names = {b.name for b in bones}
    return {
        "name": obj.name,
        "bone_count": len(bones),
        "deform_bone_count": sum(bool(b.use_deform) for b in bones),
        "contract_63_complete": CONTRACT <= names,
        "missing_control_bones": sorted(CONTRACT - names),
        "extra_bones": sorted(names - CONTRACT),
        "bones": {
            b.name: {
                "parent": b.parent.name if b.parent else None,
                "deforms": bool(b.use_deform),
                "head_local": round_vec(b.head_local),
                "tail_local": round_vec(b.tail_local),
                "roll_radians": round(float(b.roll), 7),
            }
            for b in bones
        },
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True, help="A new report.json, not the .blend")
    args = p.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    source = bpy.data.filepath
    if not source or not os.path.isfile(source):
        raise RuntimeError("Open an existing checkpoint .blend before running this audit")
    if os.path.abspath(args.output) == os.path.abspath(source):
        raise RuntimeError("Output must not overwrite source Blender file")

    report = {
        "tool": "HGPT v1 read-only checkpoint audit",
        "tool_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_path": source,
        "source_size_bytes": os.path.getsize(source),
        "source_sha256": digest_file(source),
        "blender_version": bpy.app.version_string,
        "scene_unit_scale": bpy.context.scene.unit_settings.scale_length,
        "mesh_objects": [],
        "rigs": [],
        "packed_image_status": [],
        "object_names": [o.name for o in bpy.data.objects],
        "text_blocks": [t.name for t in bpy.data.texts],
        "warnings": [],
    }
    for obj in bpy.data.objects:
        if obj.type == "ARMATURE":
            report["rigs"].append(rig_info(obj))
        elif obj.type == "MESH":
            report["mesh_objects"].append(mesh_info(obj))
    for img in bpy.data.images:
        packed = bool(img.packed_file) or bool(getattr(img, "packed_files", ()))
        report["packed_image_status"].append({
            "name": img.name, "packed": packed,
            "source": img.source, "filepath": img.filepath,
        })
        if img.source == "FILE" and not packed and not img.filepath.startswith("//"):
            report["warnings"].append(f"Unpacked image with external path: {img.name}")
    for obj in report["mesh_objects"]:
        if obj["deform_weight_unassigned_vertices"] not in (None, 0):
            report["warnings"].append(f"{obj['name']}: vertices with no deform weights")
        if obj["deform_weight_not_unit_vertices"] not in (None, 0):
            report["warnings"].append(f"{obj['name']}: non-unit deform weight sums (inspect before export)")
    for rig in report["rigs"]:
        if rig["missing_control_bones"]:
            report["warnings"].append(
                f"{rig['name']}: canonical naming differs; requires mapping/contract review"
            )
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as dest:
        json.dump(report, dest, indent=2, sort_keys=True)
    print("READONLY_AUDIT", args.output, report["source_sha256"])
    print("RIGS", [(r["name"], r["bone_count"], r["contract_63_complete"]) for r in report["rigs"]])
    print("WARNINGS", len(report["warnings"]))


if __name__ == "__main__":
    main()
