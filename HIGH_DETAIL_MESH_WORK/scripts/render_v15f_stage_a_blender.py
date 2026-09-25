"""Render matched V13e vs V15f Stage-A ring/pinky proof directly from Blend files.

Renders ring_L, ring_R, pinky_L, pinky_R from two identical close-up views each.
Camera focus/scale for every digit is derived from V13e and reused for V15f.
"""
from __future__ import annotations

import bpy
import json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v13e_fingertip_retopology.blend"
CAND = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15f_deep_hand_rebuild.blend"
OUT = ROOT / "renders_v15f_stage_a"
META = ROOT / "reports" / "v15f_stage_a_visual_proof.json"
BODY = "Mike_Freeman"

DIGITS = (
    ("ring", "L"),
    ("ring", "R"),
    ("pinky", "L"),
    ("pinky", "R"),
)
VIEWS = {
    "yneg": Vector((0.0, -1.0, 0.18)),
    "oblique": Vector((0.72, -0.72, 0.32)),
}

def owned_world(body, digit, side):
    gids = {
        group.index
        for group in body.vertex_groups
        if f"DEF-f_{digit}." in group.name and group.name.endswith("." + side)
    }
    if not gids:
        raise RuntimeError(f"Could not find {digit}_{side} deform groups.")
    points = []
    for vertex in body.data.vertices:
        weight = sum(g.weight for g in vertex.groups if g.group in gids)
        if weight > 0.65:
            points.append(body.matrix_world @ vertex.co)
    if not points:
        raise RuntimeError(f"No {digit}_{side} owned vertices found.")
    return points

def bounds(points):
    lo = Vector((
        min(p.x for p in points),
        min(p.y for p in points),
        min(p.z for p in points),
    ))
    hi = Vector((
        max(p.x for p in points),
        max(p.y for p in points),
        max(p.z for p in points),
    ))
    return (lo + hi) * 0.5, hi - lo

def setup_scene(body):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 760
    scene.render.resolution_y = 760
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (0.12, 0.12, 0.12)
    scene.view_settings.view_transform = "Standard"
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.studiolight_rotate_z = 0.4
    shading.color_type = "SINGLE"
    shading.single_color = (0.62, 0.62, 0.62)
    shading.show_shadows = False
    shading.show_cavity = True
    shading.cavity_type = "BOTH"
    shading.curvature_ridge_factor = 1.5
    shading.curvature_valley_factor = 1.0
    shading.show_specular_highlight = False
    shading.background_type = "WORLD"
    for obj in scene.objects:
        obj.hide_render = obj != body
    camera_data = bpy.data.cameras.new("V15f Stage-A proof camera")
    camera = bpy.data.objects.new("V15f Stage-A proof camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = "ORTHO"
    return scene, camera

def derive_baseline_cameras():
    bpy.ops.wm.open_mainfile(filepath=str(BASE))
    body = bpy.data.objects[BODY]
    cameras = {}
    for digit, side in DIGITS:
        points = owned_world(body, digit, side)
        focus, extent = bounds(points)
        cameras[f"{digit}_{side}"] = {
            "focus": focus,
            "scale": max(0.105, max(extent.x, extent.y, extent.z) * 1.65),
            "owned_vertices": len(points),
        }
    return cameras

def render_file(path, label, cameras):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body = bpy.data.objects[BODY]
    scene, camera = setup_scene(body)
    OUT.mkdir(parents=True, exist_ok=True)
    result = {}
    for digit, side in DIGITS:
        key = f"{digit}_{side}"
        current = owned_world(body, digit, side)
        focus = cameras[key]["focus"]
        scale = cameras[key]["scale"]
        images = {}
        for view, raw in VIEWS.items():
            direction = raw.copy()
            # Mirror X component for right-hand oblique so both sides get an
            # equivalent outside/three-quarter presentation.
            if side == "R":
                direction.x *= -1
            direction.normalize()
            camera.location = focus + direction * 0.45
            camera.rotation_euler = (focus - camera.location).to_track_quat("-Z", "Y").to_euler()
            camera.data.ortho_scale = scale
            target = OUT / f"{label}_{key}_{view}.png"
            scene.render.filepath = str(target)
            bpy.ops.render.render(write_still=True)
            images[view] = target.name
        result[key] = {
            "owned_vertices": len(current),
            "images": images,
        }
    return result

if not BASE.is_file():
    raise SystemExit(f"Missing V13e Blend: {BASE}")
if not CAND.is_file():
    raise SystemExit(f"Missing V15f Blend: {CAND}")

cameras = derive_baseline_cameras()
baseline = render_file(BASE, "V13e", cameras)
candidate = render_file(CAND, "V15f", cameras)

payload = {
    "baseline": baseline,
    "candidate": candidate,
    "cameras": {
        key: {
            "focus": [float(x) for x in item["focus"]],
            "ortho_scale": float(item["scale"]),
            "baseline_owned_vertices": item["owned_vertices"],
        }
        for key, item in cameras.items()
    },
    "views": {k: [float(x) for x in v] for k, v in VIEWS.items()},
    "purpose": "Stage-A ring/pinky visual proof before index/middle",
    "promotion": "none",
}
META.parent.mkdir(parents=True, exist_ok=True)
META.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("V15F_STAGE_A_VISUAL_META", META, flush=True)
