"""Build a private Blender timeline over pinned, multi-group NLM CT slices.

The generated scene is an inspection viewer only. Image-plane positions are
scanner coordinates rotated solely for viewing; no Home Gym PT registration,
anatomical labels, segmentation, or canonical geometry is created.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


def _hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _one_file(directories, name, label):
    matches = [Path(directory) / name for directory in directories
               if (Path(directory) / name).is_file()]
    if len(matches) != 1:
        raise ValueError(f"{label} must resolve to exactly one private file: {name}")
    return matches[0].resolve()


def _vector(value):
    return Vector((float(value[0]), float(value[1]), float(value[2])))


def _scanner_to_view(point_ras_mm):
    """Use the established display-only proper rotation; never a rig transform."""
    return Vector((-point_ras_mm[0], -point_ras_mm[1], point_ras_mm[2])) / 1000.0


def _action_curves(action):
    """Read curves from legacy actions and Blender 4.4+ layered actions."""
    if hasattr(action, "layers") and action.layers:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    yield from bag.fcurves
    else:
        yield from action.fcurves


def _set_constant_interpolation(obj):
    if not obj.animation_data or not obj.animation_data.action:
        return
    for curve in _action_curves(obj.animation_data.action):
        for key in curve.keyframe_points:
            key.interpolation = "CONSTANT"


def _key_visibility(obj, frame, frame_count):
    for path in ("hide_viewport", "hide_render"):
        if frame > 1:
            setattr(obj, path, True)
            obj.keyframe_insert(data_path=path, frame=frame - 1)
        setattr(obj, path, False)
        obj.keyframe_insert(data_path=path, frame=frame)
        if frame < frame_count:
            setattr(obj, path, True)
            obj.keyframe_insert(data_path=path, frame=frame + 1)
    _set_constant_interpolation(obj)


def _material_for_image(name, filepath):
    image = bpy.data.images.load(str(filepath), check_existing=False)
    image.filepath = str(filepath)
    image.filepath_raw = str(filepath)
    material = bpy.data.materials.new(f"DISPLAY_ONLY__{name}")
    if material.node_tree is None:
        material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Closest"
    emission = nodes.new("ShaderNodeEmission")
    output = nodes.new("ShaderNodeOutputMaterial")
    material.node_tree.links.new(texture.outputs["Color"], emission.inputs["Color"])
    material.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    material.diffuse_color = (0.65, 0.65, 0.65, 1.0)
    return material, image


def _make_plane(name, geometry, image_material, record):
    top_left = _scanner_to_view(geometry["plane_TL_RAS_mm"])
    top_right = _scanner_to_view(geometry["plane_TR_RAS_mm"])
    bottom_right = _scanner_to_view(geometry["plane_BR_RAS_mm"])
    bottom_left = top_left + bottom_right - top_right
    vertices = [top_left, top_right, bottom_right, bottom_left]
    mesh = bpy.data.meshes.new(f"{name}__DISPLAY_PLANE")
    mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="SOURCE_PIXEL_UV")
    uv_by_vertex = {0: (0.0, 1.0), 1: (1.0, 1.0),
                    2: (1.0, 0.0), 3: (0.0, 0.0)}
    for loop in mesh.polygons[0].loop_indices:
        vertex_index = mesh.loops[loop].vertex_index
        uv_layer.data[loop].uv = uv_by_vertex[vertex_index]
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(image_material)
    obj["source_id"] = record["source_id"]
    obj["source_png_sha256"] = record["source_png_sha256"]
    obj["source_header_sha256"] = record["source_header_sha256"]
    obj["source_group_index"] = record["group_index"]
    obj["timeline_frame"] = record["frame"]
    obj["scanner_centre_RAS_mm"] = record["scanner_centre_RAS_mm"]
    obj["scanner_S_mm"] = record["scanner_S_mm"]
    obj["display_only_scanner_rotation_not_HGPT_registration"] = True
    obj["source_skeleton_governs_geometry"] = True
    obj["anatomical_label_assigned"] = False
    obj["segmentation_performed"] = False
    obj["canonical_promotion_allowed"] = False
    return obj, (top_left, top_right, bottom_right, bottom_left)


def _camera_pose(corners):
    top_left, top_right, bottom_right, bottom_left = corners
    x_axis = (top_right - top_left).normalized()
    y_axis = (top_left - bottom_left).normalized()
    z_axis = x_axis.cross(y_axis).normalized()
    right = (top_right - top_left).length
    down = (bottom_right - top_right).length
    rotation = Matrix((x_axis, y_axis, z_axis)).transposed().to_quaternion()
    centre = (top_left + top_right + bottom_right + bottom_left) / 4.0
    return centre + z_axis, rotation, max(right, down) * 1.04


def _clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for current in list(bpy.data.collections):
        if current != bpy.context.scene.collection:
            bpy.data.collections.remove(current)


def _add_group_timeline_markers(scene, frame_plan):
    """Expose acquisition starts without flattening group membership."""
    markers = []
    for group in frame_plan["groups"]:
        markers.append(scene.timeline_markers.new(
            f"SOURCE_GROUP_{group['group_index']:02d}_START",
            frame=group["frame_start"],
        ))
    return markers


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--ct-dir", type=Path, action="append", required=True)
    parser.add_argument("--header-dir", type=Path, action="append", required=True)
    parser.add_argument("--display-dir", type=Path, required=True)
    parser.add_argument("--out-blend", type=Path, required=True)
    parser.add_argument("--out-report", type=Path, required=True)
    parser.add_argument("--window-low", type=int, default=950)
    parser.add_argument("--window-high", type=int, default=1900)
    args = parser.parse_args(argv)
    if len(args.ct_dir) != len(args.header_dir):
        parser.error("each CT directory requires a matching header directory")
    if args.window_high <= args.window_low:
        parser.error("display window high must be greater than low")

    repo_root = args.repo_root.resolve()
    sys.path.insert(0, str(repo_root / "scripts" / "anatomy_fit"))
    import ct_pelvis_window_geometry as window
    import nlm_ct_blender_sequence as frame_planner
    import nlm_ct_scanner_geometry_header as header_parser
    import pelvic_ct_series_manifest as bundle_validator

    bundle_path = args.bundle.resolve()
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle_evidence = bundle_validator.validate_series_bundle(bundle)
    frame_plan = frame_planner.build_frame_plan(bundle)
    private_dirs = [*args.ct_dir, *args.header_dir, args.display_dir,
                    args.out_blend.parent, args.out_report.parent]
    for directory in private_dirs:
        window.assert_private_location(directory, repo_root=repo_root)
    display_dir = args.display_dir.resolve()
    if display_dir.is_symlink():
        raise ValueError("private display directory must not be a symlink")
    display_dir.mkdir(parents=True, exist_ok=True)
    if not display_dir.is_dir():
        raise ValueError("private display directory path is not a directory")
    out_blend = window.assert_private_location(args.out_blend, repo_root=repo_root)
    out_report = window.assert_private_location(args.out_report, repo_root=repo_root)
    if out_blend.exists() or out_report.exists():
        raise FileExistsError("private Blender output paths must be new")

    validated = []
    for record in frame_plan["frames"]:
        source_id = record["source_id"]
        png_path = _one_file(args.ct_dir, f"{source_id}.png", "source PNG")
        header_path = _one_file(args.header_dir, f"{source_id}.txt", "scanner header")
        png_hash = _hash(png_path)
        header_hash = _hash(header_path)
        if png_hash != record["source_png_sha256"]:
            raise ValueError(f"source PNG hash mismatch for {source_id}")
        if header_hash != record["source_header_sha256"]:
            raise ValueError(f"scanner header hash mismatch for {source_id}")

        geometry = header_parser.scanner_geometry_from_text(header_path.read_bytes())
        centre = geometry["reported_plane_centre_RAS_mm"]
        for actual, declared in zip(centre, record["scanner_centre_RAS_mm"]):
            if abs(actual - declared) > 0.01:
                raise ValueError(f"scanner centre differs from pinned series row: {source_id}")
        if (geometry["pixel_spacing_mm"] != record["pixel_spacing_mm"] or
                geometry["slice_thickness_mm"] != record["slice_thickness_mm"] or
                geometry["image_dimensions"] != record["scanner_grid"]):
            raise ValueError(f"scanner image grid differs from pinned series row: {source_id}")
        width, height, values = window.decode_png_gray16(png_path.read_bytes())
        if [width, height] != record["scanner_grid"]:
            raise ValueError(f"source image grid differs from pinned series row: {source_id}")
        display_path = display_dir / f"{source_id}_stored-window-display8.png"
        display_bytes = window.encode_png_gray8(
            width, height, window.window_to_8bit(values, args.window_low, args.window_high)
        )
        display_hash = frame_planner.write_private_display_copy(
            display_path, display_bytes
        )
        geometry["header_HU_addend"] = geometry["stored_pixel_value_addend_for_HU"]
        record.update({
            "source_png_path": str(png_path),
            "source_header_path": str(header_path),
            "display_path": str(display_path.resolve()),
            "display_sha256": display_hash,
            "display_bytes": len(display_bytes),
            "geometry": geometry,
        })
        validated.append(record)

    expected_display_names = {Path(row["display_path"]).name for row in validated}
    actual_display_names = {path.name for path in display_dir.iterdir()}
    if actual_display_names != expected_display_names:
        raise ValueError("private display directory contains missing or unrelated files")

    _clear_scene()
    scene = bpy.context.scene
    scene.name = "PRIVATE_SOURCE_ORDERED_CT_REVIEW"
    scene["viewer_kind"] = "SOURCE_ORDERED_CT_DISPLAY_ONLY"
    scene["source_series_group_count"] = len(frame_plan["groups"])
    scene["source_group_boundary_frames"] = frame_plan["group_boundary_frames"]
    scene["source_skeleton_governs_geometry"] = True
    scene["scanner_to_HGPT_transform_applied"] = False
    scene["anatomical_coverage_verified"] = False
    scene["segmentation_performed"] = False
    scene["canonical_promotion_allowed"] = False
    scene["fixed_stored_value_display_low"] = args.window_low
    scene["fixed_stored_value_display_high"] = args.window_high
    scene["display_window_is_tissue_or_bone_classifier"] = False
    scene.frame_start = 1
    scene.frame_end = frame_plan["total_frames"]

    root_collection = bpy.data.collections.new("CT_REVIEW__NOT_REGISTERED_TO_SKELETON")
    scene.collection.children.link(root_collection)
    groups = {}
    for group in frame_plan["groups"]:
        collection = bpy.data.collections.new(
            f"SOURCE_GROUP_{group['group_index']:02d}__BOUNDARY_PRESERVED"
        )
        root_collection.children.link(collection)
        groups[group["group_index"]] = collection

    camera_data = bpy.data.cameras.new("CT_SOURCE_PLANE_CAMERA")
    camera_data.type = "ORTHO"
    camera = bpy.data.objects.new("CT_SOURCE_PLANE_CAMERA", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera["scanner_to_HGPT_transform_applied"] = False

    image_records = []
    for record in validated:
        name = (f"FRAME_{record['frame']:03d}__GROUP_{record['group_index']:02d}__"
                f"{record['source_id']}")
        material, image = _material_for_image(name, Path(record["display_path"]))
        obj, corners = _make_plane(name, record["geometry"], material, record)
        groups[record["group_index"]].objects.link(obj)
        _key_visibility(obj, record["frame"], frame_plan["total_frames"])
        camera_location, camera_rotation, ortho_scale = _camera_pose(corners)
        camera.location = camera_location
        camera.rotation_mode = "QUATERNION"
        camera.rotation_quaternion = camera_rotation
        camera.data.ortho_scale = ortho_scale
        camera.keyframe_insert(data_path="location", frame=record["frame"])
        camera.keyframe_insert(data_path="rotation_quaternion", frame=record["frame"])
        camera.data.keyframe_insert(data_path="ortho_scale", frame=record["frame"])
        image_records.append({
            "source_id": record["source_id"],
            "timeline_frame": record["frame"],
            "group_index": record["group_index"],
            "scanner_S_mm": record["scanner_S_mm"],
            "source_png_sha256": record["source_png_sha256"],
            "source_header_sha256": record["source_header_sha256"],
            "display_sha256": record["display_sha256"],
            "image_packed": image.packed_file is not None,
        })
    _set_constant_interpolation(camera)
    if camera.data.animation_data and camera.data.animation_data.action:
        for curve in _action_curves(camera.data.animation_data.action):
            for key in curve.keyframe_points:
                key.interpolation = "CONSTANT"

    _add_group_timeline_markers(scene, frame_plan)
    caution = bpy.data.texts.new("READ_FIRST__CT_REVIEW_LIMITS")
    caution.write(
        "PRIVATE SOURCE-ORDERED CT DISPLAY ONLY.\n"
        "Use the timeline to view one pinned source slice at a time.\n"
        "The two scanner-defined acquisition groups remain separate.\n"
        f"Display uses a fixed stored-value window [{args.window_low}, {args.window_high}].\n"
        "This display window is not a segmentation threshold or tissue classifier.\n"
        "No anatomical labels, segmentation, skeleton overlay, or HGPT transform.\n"
        "Keep all source images, display copies, and this Blender file private.\n"
    )

    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.display.shading.light = "FLAT"
    scene.display.shading.color_type = "TEXTURE"
    scene.display.shading.show_shadows = False
    scene.display.shading.show_cavity = False
    scene.view_settings.view_transform = "Standard"
    scene.render.filepath = str(out_blend.with_suffix(".frame-####.png"))
    scene.frame_set(1)
    out_blend.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out_blend))

    # Render only the first frame and the preserved boundary frame, not an animation.
    preview_paths = []
    preview_frames = sorted({1, *frame_plan["group_boundary_frames"]})
    for frame in preview_frames:
        scene.frame_set(frame)
        scene.render.filepath = str(out_blend.with_name(
            f"{out_blend.stem}.frame-{frame:03d}.png"
        ))
        bpy.ops.render.render(write_still=True)
        preview_paths.append({"frame": frame, "path": scene.render.filepath,
                              "sha256": _hash(scene.render.filepath)})

    report = {
        "schema_version": 1,
        "kind": "PRIVATE_NLM_CT_SOURCE_ORDERED_BLENDER_REVIEW_VIEWER",
        "blender_version": bpy.app.version_string,
        "bundle_sha256": _hash(bundle_path),
        "bundle_evidence": bundle_evidence,
        "frame_plan": {key: value for key, value in frame_plan.items()
                       if key != "frames"},
        "source_frame_count": len(image_records),
        "source_frames": image_records,
        "fixed_display_window_stored_values": [args.window_low, args.window_high],
        "display_window_is_anatomical_classifier": False,
        "source_images_packed": any(row["image_packed"] for row in image_records),
        "scanner_to_HGPT_transform_applied": False,
        "source_skeleton_geometry_modified": False,
        "anatomical_labels_assigned": False,
        "anatomical_coverage_verified": False,
        "segmentation_performed": False,
        "canonical_promotion_allowed": False,
        "source_skeleton_governs_geometry": True,
        "private_outputs_must_remain_untracked": True,
        "previews": preview_paths,
        "blend_sha256": _hash(out_blend),
    }
    with out_report.open("x", encoding="utf-8") as target:
        json.dump(report, target, indent=2)
        target.write("\n")
    print(json.dumps({
        "status": "PRIVATE_SOURCE_ORDERED_REVIEW_ONLY",
        "blender_version": bpy.app.version_string,
        "source_frames": len(image_records),
        "groups": frame_plan["groups"],
        "group_boundary_frames": frame_plan["group_boundary_frames"],
        "boundary_overlap_mm": bundle_evidence["boundary_evidence"],
        "source_images_packed": report["source_images_packed"],
        "segmentation_performed": report["segmentation_performed"],
        "canonical_promotion_allowed": report["canonical_promotion_allowed"],
        "blend_sha256": report["blend_sha256"],
        "preview_sha256": [item["sha256"] for item in preview_paths],
    }, indent=2))


if __name__ == "__main__":
    main()
