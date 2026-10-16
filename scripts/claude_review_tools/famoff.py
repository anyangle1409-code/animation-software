# press pose t, drive, then switch off shape-key families listed in OFF (";"-separated prefixes); render the back crop
import sys, os
sys.path.insert(0, "/home/user/p5/scripts"); sys.path.insert(0, "/home/user/p5/scripts/anatomy_fit")
import bpy
import original_v1_review_candidate_drives as drives
from mathutils import Vector
blend, out = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=blend)
import build_functional_shoulder_correction_blender as correction
import build_original_movement_benchmarks_blender as bench
import original_v1_press_extension as px
res = correction.build_corrected_scene(); body, rig = res["body"], res["runtime"]
drives.setup(res); px.install(); bench._reset(rig)
scene = bpy.context.scene
for o in scene.objects:
    if o.type in ("MESH", "CURVE") and o is not body: o.hide_render = True
m = bpy.data.materials.new("S"); m.diffuse_color = (0.72, 0.55, 0.45, 1); body.data.materials.clear(); body.data.materials.append(m)
scene.render.engine = "BLENDER_WORKBENCH"; sh = scene.display.shading
sh.light, sh.color_type, sh.show_cavity = "STUDIO", "MATERIAL", True
scene.render.film_transparent = True; scene.render.resolution_x = scene.render.resolution_y = 500
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = 0.55
cam = bpy.data.objects.new("C", cd); scene.collection.objects.link(cam); scene.camera = cam
t = float(os.environ.get("T", 0.6))
for tag in os.environ["SETS"].split("|"):
    name, off = tag.split("=") if "=" in tag else (tag, "")
    px.pose_press_full(res, t); drives.drive(rig, body)
    for kb in body.data.shape_keys.key_blocks[1:]:
        if off and kb.name.startswith(tuple(off.split(";"))): kb.value = 0.0
    bpy.context.view_layer.update()
    gh = rig.matrix_world @ rig.pose.bones["upperarm_" + os.environ.get("SIDE", "l")].head
    d = Vector(tuple(float(x) for x in os.environ.get("VIEW", "0,1,0.1").split(","))).normalized(); tgt = Vector((gh.x + (0.08 if os.environ.get("SIDE", "l") == "r" else -0.08), 0, gh.z + 0.05))
    cam.location = tgt + d * 4.0; cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
    scene.render.filepath = f"{out}/{name}.png"; bpy.ops.render.render(write_still=True)
