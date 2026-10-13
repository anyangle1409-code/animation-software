"""Guarded authored shoulder coupling on the original male runtime rig.

This is diagnostic pose evidence only.  It does not fit anatomical axes,
solve scapulothoracic contact, or establish human/clinical motion validity.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import build_functional_original_attachment_blender as attachment
import functional_original_coupled_motion as motion


DEFORMATION_SAMPLE_INDICES = ()
POSE_VIEWS = {
    "front": (0.0, -4.0, 0.0),
    "side": (4.0, 0.0, 0.0),
    "rear": (0.0, 4.0, 0.0),
}


def _rotation(x=0.0, y=0.0, z=0.0):
    return (Matrix.Rotation(math.radians(z), 4, "Z") @
            Matrix.Rotation(math.radians(y), 4, "Y") @
            Matrix.Rotation(math.radians(x), 4, "X"))


def clavicle_basis(profile, side_sign):
    """Map named channels onto the rig's local +Y clavicle shaft frame."""
    return _rotation(
        x=side_sign * profile["clavicle_elevation_deg"],
        y=side_sign * profile["clavicle_posterior_rotation_deg"],
        z=side_sign * profile["clavicle_retraction_deg"],
    )


def _choose_deformation_samples(body):
    wanted = {"upperarm_r", "upperarm_l", "clavicle_r", "clavicle_l",
              "scapula_r", "scapula_l"}
    group_indices = {group.index for group in body.vertex_groups if group.name in wanted}
    weighted = []
    for vertex in body.data.vertices:
        score = sum(element.weight for element in vertex.groups
                    if element.group in group_indices)
        if score > 0.0:
            weighted.append((score, vertex.index))
    weighted.sort(reverse=True)
    if not weighted:
        raise RuntimeError("original body has no shoulder/upperarm deformation weights")
    return tuple(index for _, index in weighted[: min(12, len(weighted))])


def build_coupled_scene():
    global DEFORMATION_SAMPLE_INDICES
    result = attachment.build_attachment_scene()
    DEFORMATION_SAMPLE_INDICES = _choose_deformation_samples(result["body"])
    bpy.context.scene["functional_coupled_motion_approved"] = False
    bpy.context.scene["functional_coupled_motion_scope"] = (
        "project-authored directional hypothesis; no human-motion acceptance"
    )
    apply_coupled_pose(result, 0)
    return result


def _reset_runtime(runtime):
    for bone in runtime.pose.bones:
        bone.matrix_basis.identity()
    bpy.context.view_layer.update()


def apply_coupled_pose(result, ht_elevation_deg):
    # Validate before mutating the loaded source scene.
    profile = motion.pose_profile(ht_elevation_deg)
    runtime = result["runtime"]
    _reset_runtime(runtime)

    for suffix in ("r", "l"):
        clavicle = runtime.pose.bones[f"clavicle_{suffix}"]
        scapula = runtime.pose.bones[f"scapula_{suffix}"]
        side_sign = 1.0 if suffix == "r" else -1.0
        clavicle.matrix_basis = clavicle_basis(profile, side_sign)
        scapula.matrix_basis = _rotation(
            x=profile["scapula_posterior_tilt_deg"],
            y=side_sign * profile["scapula_internal_rotation_deg"],
            z=side_sign * profile["scapula_upward_rotation_deg"],
        )
    bpy.context.view_layer.update()

    elevation = math.radians(profile["ht_elevation_deg"])
    plane = math.radians(profile["plane_deg"])
    for _, sign, runtime_name in (("left", 1.0, "upperarm_r"),
                                  ("right", -1.0, "upperarm_l")):
        bone = runtime.pose.bones[runtime_name]
        pivot = bone.head.copy()
        current = (bone.tail - bone.head).normalized()
        target = Vector((sign * math.sin(elevation) * math.cos(plane),
                         -math.sin(elevation) * math.sin(plane),
                         -math.cos(elevation)))
        correction = current.rotation_difference(target).to_matrix().to_4x4()
        bone.matrix = (Matrix.Translation(pivot) @ correction @
                       Matrix.Translation(-pivot) @ bone.matrix)
    bpy.context.view_layer.update()
    return profile


def evaluated_centroid(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    points = [evaluated.matrix_world @ vertex.co for vertex in evaluated.data.vertices]
    return sum(points, Vector()) / len(points)


def _bounds(points):
    return (tuple(min(point[i] for point in points) for i in range(3)),
            tuple(max(point[i] for point in points) for i in range(3)))


def render_coupled_evidence(output_directory):
    output = Path(output_directory).resolve()
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    result = build_coupled_scene()
    scene = bpy.context.scene
    body = result["body"]
    guides = list(result["objects"].values())
    for obj in scene.objects:
        if obj.type == "MESH" and obj is not body and obj not in guides:
            obj.hide_render = True
            obj.hide_viewport = True
    body.data.materials.clear()
    body.data.materials.append(attachment._material(
        "HGPT_COUPLED_SKIN_TMP", (0.64, 0.44, 0.36)))
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
    camera_data = bpy.data.cameras.new("HGPT_COUPLED_REVIEW_CAMERA_TMP")
    camera_data.type = "ORTHO"
    camera = bpy.data.objects.new("HGPT_COUPLED_REVIEW_CAMERA_TMP", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera

    metrics = []
    written = []
    rest_sample = None
    for angle in (0, 90, 160):
        profile = apply_coupled_pose(result, angle)
        sample = []
        evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        for index in DEFORMATION_SAMPLE_INDICES:
            sample.append(evaluated.matrix_world @ evaluated.data.vertices[index].co)
        if rest_sample is None:
            rest_sample = [point.copy() for point in sample]
        metrics.append({
            **profile,
            "max_sampled_skin_displacement_m": max(
                (a - b).length for a, b in zip(sample, rest_sample)),
            "sample_indices": list(DEFORMATION_SAMPLE_INDICES),
        })
        if angle == 0:
            continue  # PR109 already contains the unchanged neutral evidence.
        points = attachment._world_points(body)
        points.extend(point for guide in guides for point in attachment._world_points(guide))
        lo, hi = _bounds(points)
        target_tuple, scale = attachment.bridge.frame_from_bounds(lo, hi, padding=1.16)
        target = Vector(target_tuple)
        camera_data.ortho_scale = scale
        for view, offset in POSE_VIEWS.items():
            camera.location = target + Vector(offset)
            camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
            path = output / f"ht{angle:03d}__full_{view}.png"
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            written.append(path)

    source = Path(bpy.data.filepath).resolve()
    manifest = {
        "candidate": "PROVISIONAL_FUNCTIONAL_ORIGINAL_COUPLED_MOTION_v1",
        "source_blend": source.name,
        "source_blend_sha256": attachment._sha256(source),
        "source_record": str(attachment.RECORD.relative_to(ROOT)).replace("\\", "/"),
        "source_record_sha256": attachment._sha256(attachment.RECORD),
        "rendered_angles_deg": [90, 160],
        "measured_angles_deg": [0, 90, 160],
        "views": POSE_VIEWS,
        "metrics": metrics,
        "neutral_render_omitted": True,
        "anatomy_approved": False,
        "human_motion_accepted": False,
        "deformation_approved": False,
        "production_approved": False,
        "known_limits": [
            "authored directional coupling, not a fitted cohort trajectory",
            "absolute humeral shaft direction lacks fitted anatomical axial rotation",
            "no scapulothoracic contact solver or fitted blade-on-thorax placement",
            "sampled skin displacement is diagnostic, not deformation acceptance",
        ],
        "files_sha256": {path.name: attachment._sha256(path) for path in written},
    }
    manifest_path = output / "functional_original_coupled_motion_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("FUNCTIONAL_ORIGINAL_COUPLED_EVIDENCE", json.dumps({
        "output": str(output), "images": len(written),
        "source_blend_sha256": manifest["source_blend_sha256"],
    }))
    return manifest


if __name__ == "__main__":
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if arguments:
        render_coupled_evidence(attachment.output_argument(arguments))
    else:
        result = build_coupled_scene()
        for angle in (0, 90, 160):
            print("FUNCTIONAL_ORIGINAL_COUPLED_MOTION", apply_coupled_pose(result, angle))
