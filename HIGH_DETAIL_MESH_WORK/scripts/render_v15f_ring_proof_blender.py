"""Render a fast matched V13e vs V15f left-ring proof directly from Blend files.

No export, pose generation or source tests are required. This is a bind-pose
surface proof used immediately after AUDIT_V15F_RING_PROOF.bat.

Four identical orthographic cameras are derived from the V13e ring_L owned
surface and then reused unchanged for V15f.
"""
from __future__ import annotations

import bpy
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v13e_fingertip_retopology.blend"
CAND = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15f_deep_hand_rebuild.blend"
OUT = ROOT / "renders_v15f_ring_proof"
META = ROOT / "reports" / "v15f_ring_visual_proof.json"
BODY = "Mike_Freeman"

VIEWS = {
    "yneg": Vector((0.0, -1.0, 0.18)),
    "ypos": Vector((0.0, 1.0, 0.18)),
    "xpos": Vector((1.0, 0.0, 0.12)),
    "oblique": Vector((0.72, -0.72, 0.32)),
}

def ring_owned_world(body):
    gids = {
        group.index
        for group in body.vertex_groups
        if "DEF-f_ring." in group.name and group.name.endswith(".L")
    }
    if not gids:
        raise RuntimeError("Could not find left-ring deform groups.")
    points = []
    indices = []
    for vertex in body.data.vertices:
        weight = sum(g.weight for g in vertex.groups if g.group in gids)
        if weight > 0.65:
            points.append(body.matrix_world @ vertex.co)
            indices.append(vertex.index)
    if not points:
        raise RuntimeError("No ring_L owned vertices found.")
    return points, indices

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
    center = (lo + hi) * 0.5
    extent = hi - lo
    return center, extent

def setup_scene(body):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
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

    # Hide everything except the body mesh. The camera is very close to the
    # hand; removing unrelated meshes keeps the proof clean and deterministic.
    for obj in bpy.context.scene.objects:
        obj.hide_render = obj != body

    camera_data = bpy.data.cameras.new("V15f ring proof camera")
    camera = bpy.data.objects.new("V15f ring proof camera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = "ORTHO"
    return scene, camera

def render_file(path, label, focus, scale):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body = bpy.data.objects.get(BODY)
    if body is None:
        raise RuntimeError(f"{path.name}: missing {BODY}")
    points, indices = ring_owned_world(body)
    scene, camera = setup_scene(body)

    OUT.mkdir(parents=True, exist_ok=True)
    images = {}
    for name, raw_direction in VIEWS.items():
        direction = raw_direction.normalized()
        camera.location = focus + direction * 0.45
        camera.rotation_euler = (focus - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera.data.ortho_scale = scale
        target = OUT / f"{label}_ring_L_{name}.png"
        scene.render.filepath = str(target)
        bpy.ops.render.render(write_still=True)
        images[name] = target.name
        print("V15F_RING_RENDER", label, name, target, flush=True)

    current_center, current_extent = bounds(points)
    return {
        "blend": path.name,
        "owned_vertices": len(indices),
        "ring_center": [float(x) for x in current_center],
        "ring_extent": [float(x) for x in current_extent],
        "images": images,
    }

if not BASE.is_file():
    raise SystemExit(f"Missing V13e baseline Blend: {BASE}")
if not CAND.is_file():
    raise SystemExit(f"Missing V15f candidate Blend: {CAND}")

# Derive all cameras from the baseline only.
bpy.ops.wm.open_mainfile(filepath=str(BASE))
base_body = bpy.data.objects[BODY]
base_points, _ = ring_owned_world(base_body)
focus, extent = bounds(base_points)
# Include the full digit plus a little neighboring hand context. Keep a floor so
# tiny extent differences do not create unstable framing.
scale = max(0.11, max(extent.x, extent.y, extent.z) * 1.65)

baseline = render_file(BASE, "V13e", focus, scale)
candidate = render_file(CAND, "V15f", focus, scale)

META.parent.mkdir(parents=True, exist_ok=True)
payload = {
    "baseline": baseline,
    "candidate": candidate,
    "camera_focus_from_v13e": [float(x) for x in focus],
    "ortho_scale": float(scale),
    "views": {name: [float(x) for x in direction] for name, direction in VIEWS.items()},
    "purpose": "fast bind-pose ring_L topology proof before propagation",
    "promotion": "none",
}
META.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("V15F_RING_VISUAL_META", META, flush=True)
