import sys, os
sys.path.insert(0, "/home/user/p5/scripts"); sys.path.insert(0, "/home/user/p5/scripts/anatomy_fit")
import bpy
import original_v1_review_candidate_drives as drives
from mathutils import Vector, Matrix
blend, out = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=blend)
_b = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
for _m in _b.modifiers:
    if _m.type == "ARMATURE" and _m.object and _m.object.name == "HGPT_BIND_RIG_A":
        _m.object = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
import build_functional_shoulder_correction_blender as correction
import build_original_movement_benchmarks_blender as bench
import original_v1_press_extension as px
res = correction.build_corrected_scene(); body, rig = res["body"], res["runtime"]
drives.setup(res); px.install(); bench._reset(rig)
brig = bpy.data.objects.get("HGPT_BIND_RIG_A")
if brig:
    for m in body.modifiers:
        if m.type == "ARMATURE": m.object = brig
    def sync():
        for pb in sorted(brig.pose.bones, key=lambda b: len(b.parent_recursive)):
            src = rig.pose.bones.get(pb.name)
            if src is not None: pb.matrix = src.matrix.copy()
            bpy.context.view_layer.update()
    od = drives.drive
    drives.drive = lambda r, b: (od(r, b), sync())
scene = bpy.context.scene
for o in scene.objects:
    if o.type in ("MESH", "CURVE") and o is not body: o.hide_render = True
m = bpy.data.materials.new("S"); m.diffuse_color = (0.72, 0.55, 0.45, 1); body.data.materials.clear(); body.data.materials.append(m)
scene.render.engine = "BLENDER_WORKBENCH"; sh = scene.display.shading
sh.light, sh.color_type, sh.show_cavity = "STUDIO", "MATERIAL", True
scene.render.film_transparent = True; scene.render.resolution_x = scene.render.resolution_y = 600
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = float(os.environ.get("ORTHO", 0.75))
cam = bpy.data.objects.new("C", cd); scene.collection.objects.link(cam); scene.camera = cam
for tag, t in (("down", None), ("lock", 1.0)):
    bench._reset(rig)
    if t is not None: px.pose_press_full(res, t)
    drives.drive(rig, body)
    if not os.environ.get("KEYS"):
        for kb in body.data.shape_keys.key_blocks[1:]: kb.value = 0.0
    bpy.context.view_layer.update()
    gh = rig.matrix_world @ rig.pose.bones["upperarm_r"].head
    for view, d in (("back", (0, 1, 0.1)), ("three_quarter", (0.7, 0.7, 0.1)), ("side", (1, 0, 0.05)), ("front", (0, -1, 0.05))):
        d = Vector(d).normalized(); tgt = Vector((0.0, 0, gh.z - 0.08))
        cam.location = tgt + d * 4.0; cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
        scene.render.filepath = f"{out}/{tag}_{view}.png"; bpy.ops.render.render(write_still=True)
