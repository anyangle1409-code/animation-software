"""FEMALE standing-model review renders (read-only on the input .blend; never saves it).

Cycles (CPU), three-point area lighting (key, fill, rim) + soft grey world, orthographic cameras; the same cameras,
lights and pose for every model compared in a set. Smooth shading; no wireframe, cavity or curvature tricks in the
review sets. Shading modes: "clay" (neutral skin / fabric / hair clay colours, no textures) and "tex" (her colour baked
from the source albedo onto the new meshes; the source uses its own albedo).

Sets (argument 3):
  rest     source vs new model in the shared A-pose (the source has no rig): front, back, left, right, 3/4 front, 3/4 rear
  stand    new model in the natural standing pose: the same six views
  close    close-ups in the natural pose: face (front, 3/4), hands, feet, pelvis (front, back), shoulders (front, back)
  nude     the body without the removable bra / shorts (clay only): front, back, side, 3/4
  wire     topology diagnostics (Workbench, flat shading + wire): front, back, face, hand, foot

usage: python3.13 render_f_standing_review.py -- <final .blend> <out dir> <set> [clay|tex|both] [res]
"""
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, SET = Path(a[0]), Path(a[1]), a[2]; MODES = {"both": ("clay", "tex")}.get(a[3] if len(a) > 3 else "both", (a[3],) if len(a) > 3 else ("clay", "tex"))
RES = int(a[4]) if len(a) > 4 else 1100
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
sc = bpy.context.scene
OB = {n: bpy.data.objects.get(n) for n in ("HGPT_Female_Body", "HGPT_Female_Bra", "HGPT_Female_Shorts", "HGPT_Female_Ponytail",
                                            "HGPT_FEMALE_SOURCE_Mesh_0", "HGPT_FEMALE_RIG")}
SRC_TEX = bpy.data.objects.get("HGPT_FEMALE_SOURCE_TEXTURED")       # the original source with its albedo (if linked in)
NEW = [OB[n] for n in ("HGPT_Female_Body", "HGPT_Female_Bra", "HGPT_Female_Shorts", "HGPT_Female_Ponytail") if OB[n]]
for o in sc.objects:
    o.hide_render = True
for o in NEW:
    for p in o.data.polygons:
        p.use_smooth = True
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = int(os.environ.get("SAMPLES", "48"))
try:
    sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
except Exception:
    sc.cycles.use_denoising = False
sc.view_settings.view_transform = "AgX" if "AgX" in [i.name for i in type(sc.view_settings).bl_rna.properties["view_transform"].enum_items] else "Filmic"
sc.render.film_transparent = False
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.32, 0.33, 0.35, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.6


def clay(name, col, rough=0.55, sss=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = col; b.inputs["Roughness"].default_value = rough
    if sss and "Subsurface Weight" in b.inputs:
        b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Radius"].default_value = (0.008, 0.004, 0.0025)
    return m


CLAY = {"HGPT_Female_Body": clay("skin_clay", (0.72, 0.56, 0.47, 1), 0.5, 0.15), "HGPT_Female_Bra": clay("fabric_clay", (0.10, 0.10, 0.11, 1), 0.8),
        "HGPT_Female_Shorts": clay("fabric_clay2", (0.10, 0.10, 0.11, 1), 0.8), "HGPT_Female_Ponytail": clay("hair_clay", (0.16, 0.10, 0.07, 1), 0.45),
        "HGPT_FEMALE_SOURCE_Mesh_0": clay("src_clay", (0.72, 0.56, 0.47, 1), 0.5, 0.15)}
TEXMAT = {o.name: (o.data.materials[0] if len(o.data.materials) else None) for o in NEW}


def set_mode(mode, objs):
    for o in objs:
        if mode == "clay" or TEXMAT.get(o.name) is None:
            m = CLAY.get(o.name)
        else:
            m = TEXMAT[o.name]
        if m is not None and o.type == "MESH":
            o.data.materials.clear(); o.data.materials.append(m)


# lights (fixed in world space for every view: the key light follows the camera's side so faces read; set per view)
def light(name, t, energy, size, loc):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = energy; ld.size = size; lo = bpy.data.objects.new(name, ld); sc.collection.objects.link(lo)
    lo.location = loc; d = (Vector((0, 0, 0.95)) - Vector(loc)).normalized(); lo.rotation_mode = "QUATERNION"; lo.rotation_quaternion = d.to_track_quat("-Z", "Y")
    return lo


cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
LIGHTS = []


def place_lights(view_dir):
    for lo in LIGHTS:
        bpy.data.objects.remove(lo)
    LIGHTS.clear(); d = Vector(view_dir).normalized(); side = d.cross(Vector((0, 0, 1))).normalized()
    LIGHTS.append(light("key", 0, 900, 1.6, tuple(Vector((0, 0, 1.3)) + (d * 2.6 + side * 1.8 + Vector((0, 0, 1.2))))))
    LIGHTS.append(light("fill", 0, 300, 2.5, tuple(Vector((0, 0, 1.0)) + (d * 3.0 - side * 2.4))))
    LIGHTS.append(light("rim", 0, 600, 1.2, tuple(Vector((0, 0, 1.4)) + (-d * 2.6 + side * 0.6 + Vector((0, 0, 1.0))))))


def shot(name, view, centre, scale, res=(RES, int(RES * 1.6))):
    d = Vector(view).normalized(); cam.location = Vector(centre) + d * 6; cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y"); cd.ortho_scale = scale; cd.clip_end = 20
    sc.render.resolution_x, sc.render.resolution_y = res; place_lights(view)
    sc.render.filepath = str(OUT / f"{name}.png"); bpy.ops.render.render(write_still=True)


H = 1.68; C = (0, 0, H / 2 + 0.01)
VIEWS = [("front", (0, -1, 0)), ("back", (0, 1, 0)), ("left", (-1, 0, 0)), ("right", (1, 0, 0)),
         ("q34_front", (0.7, -0.7, 0.05)), ("q34_rear", (-0.7, 0.7, 0.05))]
rig = OB["HGPT_FEMALE_RIG"]


def pose(on):
    if rig is not None:
        rig.data.pose_position = "POSE" if on else "REST"; bpy.context.view_layer.update()


if SET == "rest":
    pose(False)
    for mode in MODES:
        for who, objs in (("source", [SRC_TEX if (mode == "tex" and SRC_TEX) else OB["HGPT_FEMALE_SOURCE_Mesh_0"]]), ("new", NEW)):
            for o in sc.objects:
                o.hide_render = o not in objs
            if who == "source" and mode == "clay":
                set_mode("clay", objs)
            elif who == "new":
                set_mode(mode, objs)
            for vn, vd in VIEWS:
                shot(f"rest_{mode}_{who}_{vn}", vd, C, 1.95)
elif SET in ("stand", "close"):
    pose(True)
    for o in sc.objects:
        o.hide_render = o not in NEW
    for mode in MODES:
        set_mode(mode, NEW)
        if SET == "stand":
            for vn, vd in VIEWS:
                shot(f"stand_{mode}_{vn}", vd, C, 1.95)
        else:
            sq = (RES, RES)
            shot(f"close_{mode}_face_front", (0, -1, 0.02), (0, -0.02, 1.52), 0.24, sq)
            shot(f"close_{mode}_face_q34", (0.6, -0.8, 0.05), (0.01, -0.02, 1.52), 0.24, sq)
            shot(f"close_{mode}_face_side", (1, 0, 0.02), (0.0, 0.0, 1.52), 0.28, sq)
            shot(f"close_{mode}_shoulders_front", (0, -1, 0.1), (0, 0, 1.25), 0.55, sq)
            shot(f"close_{mode}_shoulders_back", (0, 1, 0.1), (0, 0, 1.25), 0.55, sq)
            shot(f"close_{mode}_pelvis_front", (0, -1, 0), (0, 0, 0.86), 0.50, sq)
            shot(f"close_{mode}_pelvis_back", (0, 1, 0), (0, 0, 0.86), 0.50, sq)
            for s_, sg in (("r", 1), ("l", -1)):
                hb = rig.pose.bones.get(f"hand_{s_}") if rig else None
                hc = (rig.matrix_world @ hb.head) if hb else Vector((sg * 0.25, -0.02, 0.80))
                hc = hc + Vector((0, -0.01, -0.07))
                shot(f"close_{mode}_hand_{s_}_out", (sg, -0.25, 0.05), hc, 0.22, sq)
                shot(f"close_{mode}_hand_{s_}_front", (0, -1, 0.05), hc, 0.22, sq)
                shot(f"close_{mode}_foot_{s_}", (sg * 0.45, -0.8, 0.45), (sg * 0.13, -0.05, 0.05), 0.26, sq)
elif SET == "nude":
    pose(True)
    objs = [OB["HGPT_Female_Body"], OB["HGPT_Female_Ponytail"]]
    for o in sc.objects:
        o.hide_render = o not in objs
    set_mode("clay", objs)
    for vn, vd in VIEWS[:5]:
        shot(f"nude_clay_{vn}", vd, C, 1.95)
    shot("nude_clay_torso_front", (0, -1, 0), (0, 0, 1.08), 0.62, (RES, RES))
    shot("nude_clay_torso_back", (0, 1, 0), (0, 0, 1.08), 0.62, (RES, RES))
elif SET == "wire":
    pose(False)
    sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "SINGLE"
    sh.single_color = (0.75, 0.66, 0.6); sh.show_object_outline = False
    for o in NEW:
        for p in o.data.polygons:
            p.use_smooth = False
    wires = []
    for o in NEW:
        wo = bpy.data.objects.new(o.name + "_W", o.data.copy()); sc.collection.objects.link(wo); wo.matrix_world = o.matrix_world
        wm = wo.modifiers.new("W", "WIREFRAME"); wm.thickness = 0.0006; wm.use_replace = True; wm.offset = 1.0
        mt = bpy.data.materials.new("wire"); mt.diffuse_color = (0.05, 0.25, 0.3, 1); wo.data.materials.clear(); wo.data.materials.append(mt)
        wires.append(wo)
    sh.color_type = "MATERIAL"
    for o in NEW:
        mt = bpy.data.materials.new("flat"); mt.diffuse_color = (0.78, 0.7, 0.64, 1); o.data.materials.clear(); o.data.materials.append(mt)
    for o in sc.objects:
        o.hide_render = o not in NEW + wires
    for vn, vd in VIEWS[:2]:
        shot(f"wire_{vn}", vd, C, 1.95)
    shot("wire_face", (0.3, -1, 0.02), (0, -0.02, 1.52), 0.24, (RES, RES))
    shot("wire_hand_r", (1, -0.25, 0.05), (0.43, -0.04, 0.78), 0.22, (RES, RES))
    shot("wire_foot_r", (0.45, -0.8, 0.45), (0.2, -0.07, 0.05), 0.24, (RES, RES))
    shot("wire_shoulder_r", (0.8, -0.6, 0.1), (0.15, 0, 1.25), 0.40, (RES, RES))
print("RENDERED", SET, OUT)
