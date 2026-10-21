# render Work's benchmark straight-arm shoulder press at chosen frames (close-ups of the right armpit)
from pathlib import Path
import sys, json, os
import bpy, numpy as np
from mathutils import Vector
ROOT = Path("/home/user/r57src"); sys.path[:0] = ["/home/user/animation-software/scripts/shoulder_r61", str(ROOT/'scripts'), str(ROOT/'scripts/anatomy_fit')]
os.environ['S7_LOCKOUT_HT'] = '166'
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
from claude_r61_native import install
dense_path, tag, out = sys.argv[-3:]
OUT = Path(out); OUT.mkdir(exist_ok=True)
zd = np.load(dense_path); delta = (zd["dense"] if "dense" in zd.files else zd["dense_delta"]).astype(float)
parent = ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017'
bpy.ops.wm.open_mainfile(filepath=str(parent/'HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend'))
st = {"i": 0}
def setup(res):
    install(res, delta); drives.setup(res)
    sc = bpy.context.scene; body = res["body"]
    for ob in sc.objects:
        if ob.type in ("MESH", "CURVE") and ob is not body: ob.hide_render = True
    mat = bpy.data.materials.new("REVIEW_ONLY"); mat.diffuse_color = (.72, .55, .45, 1)
    body.data.materials.clear(); body.data.materials.append(mat)
    sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"; sc.display.shading.show_cavity = True
    sc.render.resolution_x = sc.render.resolution_y = 700
    cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
    st["cam"] = cam; st["cd"] = cd
def post(res):
    drives.drive(res['runtime'], res['body'])
    t = st["i"] / (bench.FRAMES - 1); st["i"] += 1
    if round(t, 3) not in (0.75, 1.0): return
    rig = res["runtime"]; W = rig.matrix_world; ua = W @ rig.pose.bones["upperarm_r"].head
    for view, (dv, scale) in {"rear": ((0.15, 1, 0.1), 0.32), "side": ((1, 0.15, 0.0), 0.32), "below_side": ((0.8, 0.1, -0.6), 0.32), "front34": ((0.7, -0.7, 0.1), 0.32)}.items():
        d = Vector(dv).normalized(); st["cd"].ortho_scale = scale
        st["cam"].location = ua + Vector((0, 0, -0.04)) + d * 3; st["cam"].rotation_mode = "QUATERNION"; st["cam"].rotation_quaternion = (-d).to_track_quat("-Z", "Y")
        bpy.context.scene.render.filepath = str(OUT / f"{tag}_bench_t{t:.3f}_{view}.png"); bpy.ops.render.render(write_still=True)
bench.run(setup=setup, post_pose=post, only=["shoulder_press"])
print("BR_DONE", flush=True)
