"""Attach provisional authored anatomy guides to the original runtime rig.

The guides are constructed in the 206-bone anatomical rest frame.  A rigid
one-weight Armature attachment applies mapped 67-bone pose deltas without
moving anatomical joint centres or changing the original body's driver.
Nothing here saves the source blend or grants anatomy/motion approval.
"""

from __future__ import annotations

import json
import hashlib
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import original_v1_functional_fullbody as bridge
from functional_original_attachment import (
    ATTACHMENT_MAPPING,
    EVIDENCE_VIEWS,
    fit_segment_similarity,
    validate_attachment_inventory,
)
from functional_shoulder_shapes import blade_mesh, clavicle_points, scapula_bowl_mesh
from functional_thorax_shapes import rib_points


COLLECTION_NAME = "HGPT_FUNCTIONAL_ANATOMY_ATTACHMENT_TMP"
RECORD = ROOT / "ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json"


def _remove_previous():
    collection = bpy.data.collections.get(COLLECTION_NAME)
    if collection is None:
        return
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(collection)


def _material(name, colour):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.diffuse_color = (*colour, 1.0)
    return material


def _link_only(obj, collection):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)


def _tube(name, points, radius, material, collection):
    curve = bpy.data.curves.new(name + "_curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    curve.use_fill_caps = True
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for vertex, coordinate in zip(spline.points, points):
        vertex.co = (*coordinate, 1.0)
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    # The source blend opens with production objects selected.  Conversion
    # must be strictly scoped to this temporary curve or Blender may apply the
    # original body's modifiers while converting the entire selection.
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    obj.select_set(False)
    return obj


def _mesh(name, vertices, faces, material, collection):
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    mesh.materials.append(material)
    return obj


def _attach(obj, runtime, anatomical_name, label):
    runtime_name = ATTACHMENT_MAPPING[anatomical_name]
    group = obj.vertex_groups.new(name=runtime_name)
    group.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
    modifier = obj.modifiers.new("provisional_runtime_pose_delta", "ARMATURE")
    modifier.object = runtime
    modifier.use_vertex_groups = True
    obj["runtime_control"] = runtime_name
    obj["anatomical_source_bone"] = anatomical_name
    obj["attachment_kind"] = "rest anatomical guide plus mapped runtime pose delta"
    obj["guide_label"] = label
    obj["anatomy_approved"] = False
    obj["motion_approved"] = False
    obj["production_approved"] = False


def _source_segment(anatomy, name):
    bone = anatomy.data.bones[name]
    return tuple(bone.head_local), tuple(bone.tail_local)


def build_attachment_scene():
    anatomy = bpy.data.objects.get("HGPT_ANATOMICAL_MASTER")
    runtime = bpy.data.objects.get("HGPT_CANONICAL_V4_ORIGINAL")
    body = bpy.data.objects.get("HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE")
    if anatomy is None or runtime is None or body is None:
        raise RuntimeError("actual source anatomy, runtime rig and original body are required")
    bridge_result = bridge.validate_blender_bridge(anatomy, runtime, body)
    if bridge_result["errors"]:
        raise RuntimeError("original bridge guard failed: " + "; ".join(bridge_result["errors"]))

    selected_anatomy = {name for name in ATTACHMENT_MAPPING if anatomy.data.bones.get(name)}
    selected_runtime = {name for name in set(ATTACHMENT_MAPPING.values()) if runtime.data.bones.get(name)}
    contract = validate_attachment_inventory(selected_anatomy, selected_runtime)
    if contract["errors"]:
        raise RuntimeError("attachment inventory failed: " + "; ".join(contract["errors"]))

    record = json.loads(RECORD.read_text(encoding="utf-8"))
    _remove_previous()
    collection = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(collection)
    materials = {
        "clavicle": _material("HGPT_ATTACHMENT_CLAVICLE_TMP", (0.95, 0.70, 0.20)),
        "scapula": _material("HGPT_ATTACHMENT_SCAPULA_TMP", (0.15, 0.65, 0.85)),
        "thorax": _material("HGPT_ATTACHMENT_THORAX_TMP", (0.65, 0.78, 0.52)),
    }
    objects = {}

    for side in ("left", "right"):
        clavicle_name = f"anat_clavicle_{side}"
        source_head, source_tail = _source_segment(anatomy, clavicle_name)
        clavicle = _tube(
            f"HGPT_authored_clavicle_{side}_TMP",
            clavicle_points(source_head, source_tail),
            0.006,
            materials["clavicle"],
            collection,
        )
        _attach(clavicle, runtime, clavicle_name, "project-authored S curve")
        clavicle["source_head"] = source_head
        clavicle["source_tail"] = source_tail
        clavicle["curve_kind"] = "project-authored S curve"
        objects[f"clavicle_{side}"] = clavicle

        record_landmarks = [tuple(value / 1000.0 for value in point)
                            for point in record["candidate"]["scapula_landmarks_world_mm"][side]]
        perimeter = [record_landmarks[index - 1]
                     for index in (3, 4, 5, 6, 7, 8, 9, 12, 13, 15, 18, 1, 2)]
        record_bone = record["bones"][f"scapula_{side}"]
        anatomy_name = f"anat_scapula_{side}"
        target_head, target_tail = _source_segment(anatomy, anatomy_name)
        fitted_perimeter = fit_segment_similarity(
            perimeter,
            record_bone["head_m"],
            record_bone["tail_m"],
            target_head,
            target_tail,
        )
        vertices, faces = scapula_bowl_mesh(fitted_perimeter, 0.008)
        scapula = _mesh(
            f"HGPT_authored_scapula_bowl_{side}_TMP",
            vertices,
            faces,
            materials["scapula"],
            collection,
        )
        _attach(scapula, runtime, anatomy_name, "authored 8mm costal-fossa bowl")
        scapula["fit_source"] = "c004 authored perimeter similarity-fitted to a003 anatomical scapula segment"
        scapula["authored_costal_recession_m"] = 0.008
        objects[f"scapula_{side}"] = scapula

    for number in range(1, 13):
        bow = 0.09 + 0.06 * max(0.0, 1.0 - abs(number - 7) / 6.0)
        for side in ("left", "right"):
            anatomy_name = f"anat_rib_{number:02d}_{side}"
            head, tail = _source_segment(anatomy, anatomy_name)
            rib = _tube(
                f"HGPT_authored_rib_{number:02d}_{side}_TMP",
                rib_points(head, tail, side, bow),
                0.004,
                materials["thorax"],
                collection,
            )
            _attach(rib, runtime, anatomy_name, "authored rib bow on a003 endpoints")
            rib["authored_bow_m"] = bow
            objects[f"rib_{number:02d}_{side}"] = rib

    sternum_head, sternum_tail = _source_segment(anatomy, "anat_sternum")
    head, tail = Vector(sternum_head), Vector(sternum_tail)
    perimeter = [head + Vector((-0.025, 0, 0)), head + Vector((0.025, 0, 0)),
                 tail + Vector((0.012, 0, 0)), tail + Vector((-0.012, 0, 0))]
    vertices, faces = blade_mesh([tuple(point) for point in perimeter])
    sternum = _mesh("HGPT_authored_sternum_TMP", vertices, faces,
                    materials["thorax"], collection)
    _attach(sternum, runtime, "anat_sternum", "authored sternum plate on a003 endpoints")
    objects["sternum"] = sternum

    bpy.context.scene["functional_attachment_status"] = "PROVISIONAL_NOT_ANATOMY_OR_MOTION_APPROVED"
    return {
        "anatomy": anatomy,
        "runtime": runtime,
        "body": body,
        "objects": objects,
        "contract": contract,
        "bridge": bridge_result,
    }


def _world_points(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return [evaluated.matrix_world @ vertex.co for vertex in evaluated.data.vertices]


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_attachment_evidence(output_directory):
    output = Path(output_directory).resolve()
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    result = build_attachment_scene()
    scene = bpy.context.scene
    body = result["body"]
    guides = list(result["objects"].values())

    for obj in scene.objects:
        if obj.type == "MESH" and obj is not body and obj not in guides:
            obj.hide_render = True
            obj.hide_viewport = True
    skin = _material("HGPT_ATTACHMENT_SKIN_TMP", (0.64, 0.44, 0.36))
    body.data.materials.clear()
    body.data.materials.append(skin)

    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_cavity = True
    scene.display.shading.show_shadows = True
    scene.display.shading.show_xray = True
    scene.display.shading.xray_alpha = 0.28
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"

    camera_data = bpy.data.cameras.new("HGPT_ATTACHMENT_REVIEW_CAMERA_TMP")
    camera_data.type = "ORTHO"
    camera = bpy.data.objects.new("HGPT_ATTACHMENT_REVIEW_CAMERA_TMP", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera

    full_points = _world_points(body)
    guide_points = [point for guide in guides for point in _world_points(guide)]
    full_lo = tuple(min(point[index] for point in full_points + guide_points) for index in range(3))
    full_hi = tuple(max(point[index] for point in full_points + guide_points) for index in range(3))
    full_target, full_scale = bridge.frame_from_bounds(full_lo, full_hi, padding=1.16)
    shoulder_lo = tuple(min(point[index] for point in guide_points) for index in range(3))
    shoulder_hi = tuple(max(point[index] for point in guide_points) for index in range(3))
    shoulder_target, shoulder_scale = bridge.frame_from_bounds(shoulder_lo, shoulder_hi, padding=1.22)

    written = []
    for name, view in EVIDENCE_VIEWS.items():
        target = Vector(full_target if view["scope"] == "full_body" else shoulder_target)
        camera_data.ortho_scale = full_scale if view["scope"] == "full_body" else shoulder_scale
        camera.location = target + Vector(view["offset"])
        camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        path = output / f"neutral__{name}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        written.append(path)

    source = Path(bpy.data.filepath).resolve()
    manifest = {
        "candidate": "PROVISIONAL_FUNCTIONAL_ORIGINAL_ATTACHMENT_v1",
        "source_blend": source.name,
        "source_blend_sha256": _sha256(source),
        "source_record": str(RECORD.relative_to(ROOT)).replace("\\", "/"),
        "source_record_sha256": _sha256(RECORD),
        "objects": len(result["objects"]),
        "contract": result["contract"],
        "views": EVIDENCE_VIEWS,
        "anatomy_approved": False,
        "motion_approved": False,
        "deformation_approved": False,
        "production_approved": False,
        "known_limits": [
            "a003 anatomical joint centres retained; c004 scapula perimeter similarity-fitted only",
            "67-bone controls supply pose deltas; no 206-bone inverse-bind or one-to-one retarget",
            "all ribs and sternum collapse to rigid spine_02 attachment; no breathing or contact solver",
            "8mm scapula recession and S-curve bows are authored assumptions, not specimen measurements",
            "neutral evidence only; coupled motion and skin deformation comparison remain open",
        ],
        "files_sha256": {path.name: _sha256(path) for path in written},
    }
    manifest_path = output / "functional_original_attachment_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("FUNCTIONAL_ATTACHMENT_EVIDENCE", json.dumps({
        "output": str(output),
        "images": len(written),
        "source_blend_sha256": manifest["source_blend_sha256"],
    }))
    return manifest


if __name__ == "__main__":
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if arguments:
        render_attachment_evidence(arguments[0])
    else:
        result = build_attachment_scene()
        print("FUNCTIONAL_ATTACHMENT", json.dumps({
            "objects": len(result["objects"]),
            "contract": result["contract"],
            "source_record": str(RECORD.relative_to(ROOT)),
        }))
