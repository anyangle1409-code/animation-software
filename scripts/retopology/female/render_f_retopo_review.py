"""FEMALE review renders (her heights and close-up centres) for the Home Gym PT manual retopology WIP (read-only on the input .blend; never saves it).

The source surface (geometry proxy or the real linked Meshy source) is shown in clay; the evaluated WIP body
(mirror + projection modifiers applied in the evaluated copy only) is drawn as a teal wire cage on top, with its
faces in a translucent tint so open areas read clearly.  Views: front, back, side (left), three-quarter, and
close-ups: face, back shoulder, armpit (front-lateral), side neck.

usage: python3.13 render_f_retopo_review.py -- <wip .blend> <out dir> [prefix] [source object name] [body object name]
"""
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
WIP, OUT = Path(a[0]), Path(a[1]); PFX = a[2] if len(a) > 2 else "wip"
SRC_NAME = a[3] if len(a) > 3 else "HGPT_FEMALE_SOURCE_Mesh_0"
BODY_NAME = a[4] if len(a) > 4 else "HGPT_Female_Shell"
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(WIP), load_ui=False)
sc = bpy.context.scene
src = bpy.data.objects[SRC_NAME]; body = bpy.data.objects[BODY_NAME]
for o in sc.objects:                       # only the source surface and the WIP are rendered
    o.hide_render = o not in (src, body)
src.hide_render = False; src.hide_viewport = False
dg = bpy.context.evaluated_depsgraph_get()
ev = bpy.data.meshes.new_from_object(body.evaluated_get(dg), depsgraph=dg)
cage = bpy.data.objects.new("REVIEW_CAGE", ev); sc.collection.objects.link(cage); cage.matrix_world = body.matrix_world
body.hide_render = True
# wire overlay: a wireframe-modified copy, pushed 1.5 mm outwards
wire = bpy.data.objects.new("REVIEW_WIRE", ev.copy()); sc.collection.objects.link(wire); wire.matrix_world = body.matrix_world
wm = wire.modifiers.new("W", "WIREFRAME"); wm.thickness = float(os.environ.get("REVIEW_WIRE_MM", "1.6")) * 0.001; wm.offset = 1.0; wm.use_replace = True; wm.use_even_offset = False
dsp = wire.modifiers.new("D", "DISPLACE"); dsp.strength = 0.0015; dsp.mid_level = 0.0
mats = {}
for nm, col in (("clay", (0.70, 0.67, 0.63, 1)), ("wire", (0.02, 0.55, 0.58, 1)), ("tint", (0.30, 0.72, 0.74, 1))):
    m = bpy.data.materials.new(nm); m.diffuse_color = col; mats[nm] = m
for ob, m in ((src, "clay"), (wire, "wire"), (cage, "tint")):
    ob.data.materials.clear(); ob.data.materials.append(mats[m])
sh = sc.display.shading; sc.render.engine = "BLENDER_WORKBENCH"
sh.light = "STUDIO"; sh.color_type = "MATERIAL"; sh.show_cavity = True; sh.cavity_type = "WORLD"
sh.background_type = "VIEWPORT"; sh.background_color = (0.82, 0.82, 0.83)
sh.show_xray = False
cage.show_in_front = False
# the translucent tint: workbench has no per-object alpha in render, so offset the cage 0.6 mm and leave it opaque
dc = cage.modifiers.new("D", "DISPLACE"); dc.strength = 0.0006; dc.mid_level = 0.0
cd = bpy.data.cameras.new("RV"); cd.type = "ORTHO"; cam = bpy.data.objects.new("RV", cd); sc.collection.objects.link(cam); sc.camera = cam


def shot(name, direction, centre, scale, res=(900, 1200)):
    d = Vector(direction).normalized(); cam.location = Vector(centre) + d * 6
    cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y"); cd.ortho_scale = scale
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = str(OUT / f"{PFX}_{name}.png"); bpy.ops.render.render(write_still=True)


H = 1.68
shot("front", (0, -1, 0), (0, 0, H / 2), 1.90)
shot("back", (0, 1, 0), (0, 0, H / 2), 1.90)
shot("side", (1, 0, 0), (0, 0, H / 2), 1.90)
shot("three_quarter", (0.7, -0.7, 0.1), (0, 0, H / 2), 1.90)
shot("head_side", (1, 0, 0), (0, 0.01, 1.52), 0.32, (900, 900))
shot("head_back34", (0.6, 0.8, 0.15), (0.03, 0.03, 1.52), 0.32, (900, 900))
shot("head_front", (0, -1, 0), (0, 0, 1.52), 0.32, (900, 900))
shot("back_shoulder", (0.35, 1, 0.25), (0.12, 0.03, 1.30), 0.50, (900, 900))
shot("armpit", (1, -0.6, -0.15), (0.15, 0.0, 1.24), 0.45, (900, 900))
shot("chest", (0.25, -1, 0.05), (0.05, -0.05, 1.18), 0.45, (900, 900))
shot("pelvis_back", (0.2, 1, 0), (0.0, 0.05, 0.92), 0.50, (900, 900))
if os.environ.get("REVIEW_FACE"):                   # her face: front, three-quarter, side, eye, mouth / nose
    shot("face_front", (0, -1, 0), (-0.0005, 0, 1.50), 0.20, (1000, 1000))
    shot("face_34", (0.6, -0.8, 0.05), (0.0, -0.04, 1.50), 0.20, (1000, 1000))
    shot("face_side", (1, 0, 0), (0, -0.05, 1.50), 0.20, (1000, 1000))
    shot("eye_r", (0.15, -1, 0), (0.029, 0, 1.515), 0.07, (1000, 700))
    shot("mouth_nose", (0, -1, 0), (-0.0005, 0, 1.465), 0.08, (1000, 1000))
if os.environ.get("REVIEW_EARS"):
    shot("ear_r", (1, 0, 0), (0.07, 0.005, 1.505), 0.10, (900, 900))
    shot("ear_l", (-1, 0, 0), (-0.07, 0.005, 1.505), 0.10, (900, 900))
    shot("ear_back", (0.6, 0.8, 0.0), (0.06, 0.02, 1.505), 0.14, (900, 900))
if os.environ.get("REVIEW_HANDS"):
    shot("hand_r_out", (1, 0, 0), (0.44, -0.03, 0.79), 0.20, (900, 900))
    shot("hand_r_front", (0, -1, 0), (0.44, -0.03, 0.79), 0.20, (900, 900))
    shot("hand_r_back", (0, 1, 0), (0.44, -0.03, 0.79), 0.20, (900, 900))
    shot("hand_l_out", (-1, 0, 0), (-0.44, -0.03, 0.79), 0.20, (900, 900))
    shot("hand_l_front", (0, -1, 0), (-0.44, -0.03, 0.79), 0.20, (900, 900))
    shot("foot_r", (0.4, -0.8, 0.45), (0.20, -0.07, 0.04), 0.20, (900, 900))
    shot("foot_r_top", (0, -0.3, 1), (0.20, -0.07, 0.04), 0.20, (900, 900))
print("RENDERED", PFX, OUT)
