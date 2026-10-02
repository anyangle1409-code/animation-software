"""Render temporary skeleton-only review images for ORIGINAL v1.

Usage:
  blender --background --factory-startup <candidate.blend> \
    --python scripts/render_original_v1_skeleton_review_blender.py -- \
    <out_dir> [pose,pose,...]

Read-only with respect to the .blend: creates temporary render geometry and never
saves. Reuses the exact Phase 3 pose constructors, hides body/shorts, creates a
simple project-generated bone/joint proxy from the posed armature, and renders
front/side/three-quarter evidence.

This is a diagnostic proxy, not anatomical production geometry.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import tempfile
from pathlib import Path

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = Path(args[0]).resolve() if args else None
if OUT is None:
    raise SystemExit("Usage: ... -- <out_dir> [pose,pose,...]")
ONLY = set(args[1].split(",")) if len(args) > 1 and args[1] else None
FOCUS = args[2] if len(args) > 2 and args[2] else None          # optional close-up on this bone's head
SCALE = float(args[3]) if len(args) > 3 else 2.3
TAG = args[4] if len(args) > 4 else ""
OUT.mkdir(parents=True, exist_ok=True)

pose_script = Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py")
src = pose_script.read_text(encoding="utf-8")
src_defs = src[:src.index("# ---------------------------------------------------------------- metrics")]
tmp = tempfile.mkdtemp()
saved_argv = sys.argv
sys.argv = ["blender", "--", tmp, ""]
ns = {"__name__": "pose_defs", "__file__": pose_script.name}
exec(compile(src_defs, "pose_test_defs", "exec"), ns)
sys.argv = saved_argv

rig = ns["rig"]
_mask = ns["body"].modifiers.get("HGPT_DRESSED_MASK")   # the pose script's closing search expects the undressed body
if _mask is not None:
    _mask.show_viewport = False
    _mask.show_render = False
POSES = ns["POSES"]
reset = ns["reset"]
upd = ns["upd"]

source_path = Path(bpy.data.filepath).resolve()
source_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()

# Hide all production meshes for skeleton-only evidence.
for o in bpy.context.scene.objects:
    if o.type == "MESH":
        o.hide_render = True

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_cavity = True
scene.display.shading.show_shadows = True
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"

# Temporary collection.
coll = bpy.data.collections.new("HGPT_SKELETON_REVIEW_TMP")
scene.collection.children.link(coll)
stage = bpy.data.collections.new("HGPT_SKELETON_REVIEW_STAGE_TMP")   # floor + camera: never cleared between poses
scene.collection.children.link(stage)

bone_mat = bpy.data.materials.new("HGPT_SKELETON_BONE_MAT_TMP")
bone_mat.diffuse_color = (0.72, 0.72, 0.72, 1.0)
joint_mat = bpy.data.materials.new("HGPT_SKELETON_JOINT_MAT_TMP")
joint_mat.diffuse_color = (0.92, 0.92, 0.92, 1.0)


def link_only(obj, target=None):
    # primitive ops link into active scene collection; move to our temp collection
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    (target or coll).objects.link(obj)


def sphere_at(p, radius=0.010):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=radius, location=p)
    o = bpy.context.object
    link_only(o)
    o.data.materials.append(joint_mat)
    return o


def cylinder_between(a, b, radius=0.005):
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    if L < 1e-7:
        return None
    mid = (a + b) * 0.5
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=radius, depth=L, location=mid)
    o = bpy.context.object
    link_only(o)
    o.data.materials.append(bone_mat)
    # Cylinder local Z -> bone direction.
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return o


def clear_proxy():
    for o in list(coll.objects):
        bpy.data.objects.remove(o, do_unlink=True)


def build_proxy():
    # Pose-bone heads/tails are armature-space; transform to world.
    mw = rig.matrix_world
    seen_joints = []
    for p in rig.pose.bones:
        if not p.bone.use_deform and p.name not in {"root", "pelvis"}:
            continue
        h = mw @ p.head
        t = mw @ p.tail
        # Thinner helper appearance for fingers/toes.
        small = any(k in p.name for k in ("index_", "middle_", "ring_", "pinky_", "thumb_", "toe_"))
        radius = 0.0032 if small else 0.0055
        cylinder_between(h, t, radius)
        seen_joints.append(h)
        if not p.children:
            seen_joints.append(t)

    # Deduplicate approximate joint positions.
    unique = {}
    for p in seen_joints:
        k = tuple(round(float(x), 4) for x in p)
        unique[k] = p
    for p in unique.values():
        sphere_at(p, 0.006 if len(unique) > 50 else 0.008)


# Floor for orientation.
floor_mat = bpy.data.materials.new("HGPT_SKELETON_FLOOR_MAT_TMP")
floor_mat.diffuse_color = (0.25, 0.25, 0.25, 1.0)
bpy.ops.mesh.primitive_plane_add(size=4.0, location=(0, 0, 0))
floor = bpy.context.object
link_only(floor, stage)
floor.data.materials.append(floor_mat)

cam_data = bpy.data.cameras.new("HGPT_SKELETON_REVIEW_CAM_TMP")
cam_data.type = "ORTHO"
cam = bpy.data.objects.new("HGPT_SKELETON_REVIEW_CAM_TMP", cam_data)
stage.objects.link(cam)
scene.camera = cam


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


VIEWS = {
    "front": Vector((0.0, -4.0, 1.0)),
    "side": Vector((4.0, 0.0, 1.0)),
    "three_quarter": Vector((3.0, -3.0, 1.2)),
}

manifest = {
    "schema_version": 1,
    "source_candidate": source_path.name,
    "source_candidate_sha256": source_sha,
    "pose_definition_script": pose_script.name,
    "pose_definition_script_sha256": hashlib.sha256(pose_script.read_bytes()).hexdigest(),
    "purpose": "skeleton-only diagnostic review; temporary project-generated proxy; not production geometry",
    "captures": [],
}

for pose_name, fn in POSES.items():
    if ONLY and pose_name not in ONLY:
        continue
    reset()
    rig.location = (0, 0, 0)
    rig.rotation_euler = (0, 0, 0)
    upd()
    ns["HANDLE"].clear()
    fn()
    upd()

    clear_proxy()
    build_proxy()

    # Approximate target from root/pelvis world-space position.
    pelvis = rig.matrix_world @ rig.pose.bones["pelvis"].head
    target = Vector((pelvis.x, pelvis.y, max(0.8, pelvis.z)))
    if FOCUS:
        target = rig.matrix_world @ rig.pose.bones[FOCUS].head
    cam_data.ortho_scale = SCALE

    for view, offset in VIEWS.items():
        # Keep camera distance but centre around current subject.
        cam.location = target + offset
        look_at(cam, target)
        path = OUT / f"{pose_name}__skeleton{TAG}_{view}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        manifest["captures"].append({
            "pose": pose_name,
            "view": view,
            "focus": FOCUS,
            "path": path.name,
        })

(OUT / f"skeleton_review_manifest{TAG}.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print("SKELETON REVIEW", len(manifest["captures"]), "captures ->", OUT)
