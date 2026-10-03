"""Skin-on close-up renders of a stress pose, optionally with the skeleton proxy overlaid (never saves the .blend).

blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
  --python scripts/render_original_v1_pose_closeup_blender.py -- <out_dir> <pose> <focus_bone> <ortho_scale> <tag> [--skeleton] [--pose-script <path>] [--fraction f]

Reuses the exact pose constructors of scripts/pose_test_original_v1_o4_candidate_blender.py (executed up to its metrics
section), shows the BARE body (dressed mask and shorts hidden so barefoot/skin mechanics are visible), and writes
<pose>__<tag>_<view>.png for front / side / three_quarter views centred on the head of <focus_bone>. With --skeleton a simple
project-generated bone/joint proxy is drawn over the skin (diagnostic only, not production geometry).
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(args) < 5:
    raise SystemExit("Usage: ... -- <out_dir> <pose> <focus_bone> <ortho_scale> <tag> [--skeleton]")
OUT = Path(args[0]).resolve()
POSE, FOCUS, SCALE, TAG = args[1], args[2], float(args[3]), args[4]
SKEL = "--skeleton" in args
POSE_SCRIPT_ARG = next((args[i + 1] for i, a in enumerate(args) if a == "--pose-script"), None)
OUT.mkdir(parents=True, exist_ok=True)

pose_script = Path(POSE_SCRIPT_ARG).resolve() if POSE_SCRIPT_ARG else Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py")
src = pose_script.read_text(encoding="utf-8")
src_defs = src[:src.index("# ---------------------------------------------------------------- metrics")]
saved = sys.argv
sys.argv = ["blender", "--", tempfile.mkdtemp(), ""]
ns = {"__name__": "pose_defs", "__file__": pose_script.name}
exec(compile(src_defs, "pose_test_defs", "exec"), ns)
sys.argv = saved
rig, body = ns["rig"], ns["body"]
mask = body.modifiers.get("HGPT_DRESSED_MASK")
if mask is not None:
    mask.show_viewport = False
    mask.show_render = False
for o in bpy.context.scene.objects:
    if o.type == "MESH" and o is not body:
        o.hide_render = True
        o.hide_viewport = True

ns["reset"]()
rig.location = (0, 0, 0)
ns["HANDLE"].clear()
ns["POSES"][POSE]()
ns["upd"]()

FRACTION = next((float(args[i + 1]) for i, a in enumerate(args) if a == "--fraction"), None)
if FRACTION is not None:
    # Replay the pose continuously from rest (0) to the final pose (1) with the same swing/twist interpolation as the
    # arc audit, so intermediate elevation states (e.g. the corrective's blend zone) can be inspected visually.
    import math
    from mathutils import Matrix, Quaternion
    final = {p.name: (p.matrix_basis.to_quaternion(), p.matrix_basis.to_translation()) for p in rig.pose.bones}
    for p in rig.pose.bones:
        q, t = final[p.name]
        v = Vector((q.x, q.y, q.z))
        proj = Vector((0, 1, 0)) * v.dot(Vector((0, 1, 0)))
        tw = Quaternion((q.w, proj.x, proj.y, proj.z))
        if tw.magnitude < 1e-12:
            tw = Quaternion((1, 0, 0, 0))
        tw.normalize()
        sw = q @ tw.inverted()
        ang = (2.0 * math.atan2(tw.y, tw.w) + math.pi) % (2.0 * math.pi) - math.pi
        qf = Quaternion((1, 0, 0, 0)).slerp(sw, FRACTION) @ Quaternion((0.0, 1.0, 0.0), FRACTION * ang)
        p.matrix_basis = Matrix.Translation(t * FRACTION) @ qf.to_matrix().to_4x4()
    ns["upd"]()

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "SINGLE"
scene.display.shading.single_color = (0.78, 0.66, 0.58)
scene.display.shading.show_cavity = True
scene.render.resolution_x = scene.render.resolution_y = 900
scene.render.image_settings.file_format = "PNG"
stage = bpy.data.collections.new("HGPT_CLOSEUP_STAGE_TMP")
scene.collection.children.link(stage)

floor_mat = bpy.data.materials.new("HGPT_CLOSEUP_FLOOR_TMP")
floor_mat.diffuse_color = (0.25, 0.25, 0.25, 1.0)
bpy.ops.mesh.primitive_plane_add(size=4.0, location=(0, 0, 0))
floor = bpy.context.object
for c in list(floor.users_collection):
    c.objects.unlink(floor)
stage.objects.link(floor)
floor.data.materials.append(floor_mat)

if SKEL:
    bone_mat = bpy.data.materials.new("HGPT_CLOSEUP_BONE_TMP")
    bone_mat.diffuse_color = (0.1, 0.35, 0.9, 1.0)
    mw = rig.matrix_world
    for p in rig.pose.bones:
        if not p.bone.use_deform:
            continue
        a, b = mw @ p.head, mw @ p.tail
        d = b - a
        if d.length < 1e-7:
            continue
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.0025, depth=d.length, location=(a + b) * 0.5)
        o = bpy.context.object
        for c in list(o.users_collection):
            c.objects.unlink(o)
        stage.objects.link(o)
        o.data.materials.append(bone_mat)
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
        o.show_in_front = True

cam_data = bpy.data.cameras.new("HGPT_CLOSEUP_CAM_TMP")
cam_data.type = "ORTHO"
cam_data.ortho_scale = SCALE
cam = bpy.data.objects.new("HGPT_CLOSEUP_CAM_TMP", cam_data)
stage.objects.link(cam)
scene.camera = cam
target = rig.matrix_world @ rig.pose.bones[FOCUS].head
VIEWS = {"front": Vector((0, -4, 0.0)), "side": Vector((4, 0, 0.0)), "three_quarter": Vector((3, -3, 1.0)), "top": Vector((0, -0.01, 4))}
written = []
for view, off in VIEWS.items():
    cam.location = target + off
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    path = OUT / f"{POSE}__{TAG}_{view}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    written.append(path.name)
print("CLOSEUP", POSE, FOCUS, written)
