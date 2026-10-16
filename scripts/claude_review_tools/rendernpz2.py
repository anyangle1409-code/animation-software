import sys, os
sys.path.insert(0, "/home/user/p5/scripts"); sys.path.insert(0, "/home/user/p5/scripts/anatomy_fit")
import bpy, numpy as np
from mathutils import Vector
import original_v1_review_candidate_drives as drives
blend, out = sys.argv[-2], sys.argv[-1]
items = [x.split("=") for x in os.environ["ITEMS"].split(",")]     # tag=npzpath:key  or tag=posed
bpy.ops.wm.open_mainfile(filepath=blend)
if os.environ.get("LOCK_HT"): bpy.context.scene["hgpt_press_lockout_ht"] = float(os.environ["LOCK_HT"])
import build_functional_shoulder_correction_blender as correction
import build_original_movement_benchmarks_blender as bench
import build_original_sculpt_corrective_blender as s4
import original_v1_press_extension as px
res = correction.build_corrected_scene(); body, rig = res["body"], res["runtime"]
for kb in body.data.shape_keys.key_blocks[1:]: kb.value = 0.0
drives.setup(res); px.install(); bench._reset(rig); V0, F = bench._evaluated(body)
ht = int(os.environ.get("HT", 172))
s4.press_pose(res, ht); drives.drive(rig, body)
V, _ = bench._evaluated(body); P = np.array([tuple(v) for v in V])
c = rig.pose.bones["upperarm_l"].head.copy(); cr = rig.pose.bones["upperarm_r"].head.copy(); mid = (c + cr) / 2
scene = bpy.context.scene
for o in scene.objects:
    if o.type in ("MESH", "CURVE"): o.hide_render = True
m = bpy.data.materials.new("S"); m.diffuse_color = (0.64, 0.46, 0.38, 1)
scene.render.engine = "BLENDER_WORKBENCH"; sh = scene.display.shading
sh.light, sh.color_type, sh.show_cavity = "STUDIO", "MATERIAL", True
scene.render.resolution_x = scene.render.resolution_y = 600
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = float(os.environ.get("ORTHO", 0.75))
cam = bpy.data.objects.new("C", cd); scene.collection.objects.link(cam); scene.camera = cam
os.makedirs(out, exist_ok=True)
for tag, src in items:
    if src == "posed": Q = P
    else:
        path, key = src.split(":"); Q = np.load(path)[key]
    me = bpy.data.meshes.new(tag); me.from_pydata([tuple(x) for x in Q], [], [tuple(f) for f in F]); me.update()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(tag, me); scene.collection.objects.link(ob); me.materials.append(m)
    for view, d, tgt in (("back", (0, 1, 0.05), mid + Vector((0, 0, 0.05))), ("threeq", (0.7, 0.7, 0.05), cr + Vector((0, 0, 0.08)))):
        cam.location = tgt + Vector(d).normalized() * 3
        cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = f"{out}/{tag}_{view}.png"; bpy.ops.render.render(write_still=True)
    ob.hide_render = True
