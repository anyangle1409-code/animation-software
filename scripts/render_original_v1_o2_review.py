"""Render O2 review views from a DISPOSABLE copy of the ORIGINAL v1 Blend.

Usage (never on the production Blend; the script refuses it):
  blender --background --factory-startup <copy.blend> --python scripts/render_original_v1_o2_review.py -- \
      <out_dir> <label> <view,view,...> [--xray] [--regen] [--no-bones]

--regen loads the current project-authored generator output into the copy
first (preview only). Adds a camera, bone sticks for the v4 rig and renders
with Workbench. Never saves.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = (ROOT / "ORIGINAL_V1_WORK" / "HomeGymPT_Male_ORIGINAL_v1.blend").resolve()
if Path(bpy.data.filepath).resolve() == PRODUCTION:
    raise SystemExit("Refusing to render from the production Blend; render a disposable copy.")

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
flags = {a for a in args if a.startswith("--")}
pos = [a for a in args if not a.startswith("--")]
out_dir = Path(pos[0]) if pos else ROOT / "reports" / "o2_review"
label = pos[1] if len(pos) > 1 else "review"
views = pos[2].split(",") if len(pos) > 2 else ["front", "side", "three_quarter", "back"]
out_dir.mkdir(parents=True, exist_ok=True)

scene = bpy.context.scene
body = bpy.data.objects["HGPT_ORIGINAL_V1_CLEAN_SCAFFOLD"]
rig = bpy.data.objects.get("HGPT_CANONICAL_V4_ORIGINAL")

if "--regen" in flags:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import original_v1_o2_body as gen
    result = gen.build()
    mesh = body.data
    mesh.clear_geometry()
    mesh.from_pydata([tuple(p) for p in result["vertices"]], [], [tuple(f) for f in result["faces"]])
    mesh.update()
    body.modifiers.clear()
    body.vertex_groups.clear()
    body.parent = None
    body.matrix_world.identity()
    for poly in mesh.polygons:
        poly.use_smooth = True

if "--wire" in flags:
    # Topology review: a dark wireframe shell over the surface (copy only).
    wire = body.copy()
    wire.data = body.data.copy()
    scene.collection.objects.link(wire)
    mod = wire.modifiers.new("REVIEW_WIRE", "WIREFRAME")
    mod.thickness = 0.0007
    mod.use_replace = True
    wire_mat = bpy.data.materials.new("REVIEW_WIRE_MAT")
    wire_mat.diffuse_color = (0.08, 0.08, 0.09, 1.0)
    wire.data.materials.clear()
    wire.data.materials.append(wire_mat)

# Bone sticks so joint centres are visible against the surface.
if rig is not None and "--no-bones" not in flags:
    stick_mat = bpy.data.materials.new("REVIEW_BONE")
    stick_mat.diffuse_color = (0.9, 0.15, 0.1, 1.0)
    for bone in rig.data.bones:
        head = rig.matrix_world @ bone.head_local
        tail = rig.matrix_world @ bone.tail_local
        length = (tail - head).length
        if length < 1e-6:
            continue
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.0025, depth=length, location=(head + tail) / 2)
        stick = bpy.context.active_object
        stick.rotation_mode = "QUATERNION"
        stick.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(tail - head)
        stick.data.materials.append(stick_mat)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=0.005, location=head)
        bpy.context.active_object.data.materials.append(stick_mat)

scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_xray = "--xray" in flags
scene.display.shading.xray_alpha = 0.55
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "WORLD"
scene.render.resolution_x = 900
scene.render.resolution_y = 1400
scene.world = scene.world or bpy.data.worlds.new("REVIEW_WORLD")

if body.data.materials and body.data.materials[0] is not None:
    body.data.materials[0].diffuse_color = (0.78, 0.66, 0.58, 1.0)

cam_data = bpy.data.cameras.new("REVIEW_CAM")
cam_data.type = "ORTHO"
cam = bpy.data.objects.new("REVIEW_CAM", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

# name: (azimuth deg; 0 = looking at the character's front, 90 = its left (-X) side),
#        elevation deg, target (x, y, z), ortho scale, aspect (w, h)
LX = -0.216
VIEWS = {
    "front": (0, 0, (0, 0, 0.91), 2.04, (900, 1400)),
    "three_quarter": (35, 0, (0, 0, 0.91), 2.04, (900, 1400)),
    "side": (90, 0, (0, 0, 0.91), 2.04, (900, 1400)),
    "back": (180, 0, (0, 0, 0.91), 2.04, (900, 1400)),
    "torso_front": (0, 0, (0, 0, 1.25), 0.85, (1100, 1100)),
    "torso_side": (90, 0, (0, 0, 1.25), 0.85, (1100, 1100)),
    "torso_back": (180, 0, (0, 0, 1.25), 0.85, (1100, 1100)),
    "torso_34": (35, 10, (0, 0, 1.25), 0.85, (1100, 1100)),
    "shoulder_front": (0, 0, (LX, 0.03, 1.40), 0.40, (1000, 1000)),
    "shoulder_34": (50, 15, (LX, 0.03, 1.40), 0.40, (1000, 1000)),
    "shoulder_back": (180, 0, (LX, 0.03, 1.40), 0.40, (1000, 1000)),
    "shoulder_top": (0, 80, (LX * 0.6, 0.0, 1.50), 0.55, (1000, 1000)),
    "hand_lateral": (90, 0, (LX, 0.02, 0.84), 0.24, (1000, 1000)),
    "hand_medial": (-90, 0, (LX, 0.02, 0.84), 0.24, (1000, 1000)),
    "hand_front": (0, 0, (LX, 0.02, 0.84), 0.24, (1000, 1000)),
    "hand_34": (40, -20, (LX, 0.02, 0.84), 0.24, (1000, 1000)),
    "foot_side": (90, 0, (-0.092, -0.1, 0.07), 0.40, (1100, 800)),
    "foot_top": (0, 89, (-0.092, -0.1, 0.07), 0.40, (1000, 1000)),
    "foot_front": (0, 5, (-0.092, -0.1, 0.07), 0.40, (1100, 800)),
    "foot_medial": (-90, 0, (-0.092, -0.1, 0.07), 0.40, (1100, 800)),
    "head_front": (0, 0, (0, 0, 1.69), 0.36, (1000, 1000)),
    "head_side": (90, 0, (0, 0, 1.69), 0.36, (1000, 1000)),
    "head_34": (35, 5, (0, 0, 1.69), 0.36, (1000, 1000)),
    "hips_front": (0, 0, (0, 0, 0.88), 0.62, (1100, 1100)),
    "hips_back": (180, 0, (0, 0, 0.88), 0.62, (1100, 1100)),
    "hips_side": (90, 0, (0, 0, 0.88), 0.62, (1100, 1100)),
    "knee_front": (0, 0, (-0.092, 0, 0.50), 0.40, (1000, 1000)),
    "knee_side": (90, 0, (-0.092, 0, 0.50), 0.40, (1000, 1000)),
    "arm_side": (90, 0, (LX, 0, 1.15), 0.60, (900, 1300)),
    "arm_front": (0, 0, (LX, 0, 1.15), 0.60, (900, 1300)),
}

for view in views:
    az, el, target, scale, (w, h) = VIEWS[view]
    scene.render.resolution_x, scene.render.resolution_y = w, h
    cam_data.ortho_scale = scale
    a, e = math.radians(az), math.radians(el)
    # character forward is -Y; azimuth 90 looks at its left side (-X)
    direction = Vector((-math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    cam.location = Vector(target) + direction * 6.0
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = (-direction).to_track_quat("-Z", "Y")
    scene.render.filepath = str(out_dir / f"{label}_{view}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", scene.render.filepath)
