"""Review renders of a body_v2 blend in raised-arm poses (upper body, front / back / side), r57 drives active and the
R121 candidate drives on or off (V2_POSE_R121=0 switches the candidate keys off).  Read-only on the blend.

usage: python3.13 render_pose_blender.py -- <body.blend> <r57src> <out dir> [pose ...]   (poses: abduct_<deg>, flex_<deg>, squat_<depth %>)
"""
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
SRC, ROOT, OUT = Path(args[0]), Path(args[1]), Path(args[2])
POSES = args[3:] or ["abduct_150", "flex_150"]
OUT.mkdir(parents=True, exist_ok=True)
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts/anatomy_fit"), str(Path(__file__).resolve().parent)]
bpy.ops.wm.open_mainfile(filepath=str(SRC))
import build_original_movement_benchmarks_blender as bench  # noqa: E402
import original_v1_review_candidate_drives as drives  # noqa: E402
import r121_drives  # noqa: E402

body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
sc = bpy.context.scene
for ob in sc.objects:
    if ob.type in ("MESH", "CURVE") and ob is not body:
        ob.hide_render = True
USE = os.environ.get("V2_POSE_R121", "1") == "1"
tag = os.environ.get("V2_POSE_TAG", "keys" if USE else "nokeys")


bench._reset(rig)
REST_HEADS = {s_: rig.pose.bones[f"foot_{s_}"].head.copy() for s_ in ("l", "r")}


def pose(name):
    kind, ang = name.rsplit("_", 1); ang = float(ang)
    if kind == "squat":                                         # the movement benchmark's squat at depth ang %
        bench.pose_squat(rig, ang / 100.0, REST_HEADS)
    else:
        bench._reset(rig)
    for sd, sg in (("r", -1.0), ("l", 1.0)) if kind != "squat" else ():
        pb = rig.pose.bones[f"upperarm_{sd}"]; pb.rotation_mode = "XYZ"
        if kind == "abduct":
            pb.rotation_euler = (0.0, 0.0, math.radians(sg * ang))
        else:
            ys = []
            for sx in (1.0, -1.0):
                pb.rotation_euler = (math.radians(sx * ang), 0.0, 0.0); bpy.context.view_layer.update(); ys.append((pb.tail.y, sx))
            pb.rotation_euler = (math.radians(min(ys)[1] * ang), 0.0, 0.0)
    bpy.context.view_layer.update(); drives.drive(rig, body)
    if USE:
        r121_drives.drive(rig, body)
    else:
        for kb in body.data.shape_keys.key_blocks:
            if kb.name.startswith(("R121_ARM_", "R121_FLEX_", "R121_HIP_")):
                kb.value = 0.0
    bpy.context.view_layer.update()


cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam)
sc.camera = cam; cd.ortho_scale = 1.0
mat = bpy.data.materials.new("REVIEW_ONLY"); mat.diffuse_color = (.72, .55, .45, 1)
body.data.materials.clear(); body.data.materials.append(mat)
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
sc.display.shading.show_cavity = True; sc.render.resolution_x = 1000; sc.render.resolution_y = 1000
sc.render.film_transparent = False
for name in POSES:
    pose(name)
    centre = Vector((0.0, 0.05, 0.62 if name.startswith("squat") else 1.42))
    for view, dv in {"front": (0, -1, 0), "back": (0, 1, 0), "side": (1, 0, 0), "back34": (0.7, 0.7, 0.3)}.items():
        d = Vector(dv).normalized(); cam.location = centre + d * 4; cam.rotation_mode = "QUATERNION"
        cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
        sc.render.filepath = str(OUT / f"pose_{name}_{view}_{tag}.png"); bpy.ops.render.render(write_still=True)
bench._reset(rig)
print("POSE_RENDERS done", flush=True)
