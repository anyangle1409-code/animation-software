"""Full-body standing review renders (read-only on the inputs): current body vs the approved source, and the natural
standing pose, under ordinary lighting, plus anatomical diagnostic views.

Sets (all orthographic, whole figure head to feet, same cameras for every model in a set):
  A  'rest'   - source and current body in the shared bind pose (the source has no rig, so this is the only pose in
                which they can be compared like for like): front, back, left, right, three-quarter; smooth shading,
                neutral skin material, three-point studio lighting (key, fill, rim; no cavity or curvature tricks).
  B  'stand'  - current body in a natural standing pose: arms relaxed at the sides (8 deg from vertical, 10 deg
                forwards, elbows softly bent 15 deg, anatomical hinge), legs and head as bound: front, back, left,
                right, three-quarter front-left / front-right, three-quarter back; smooth shading, same lighting.
  C  'diag'   - the natural standing pose: flat shading with wireframe overlay (topology and faceting), and a
                deviation map at rest (signed distance of the current surface from the source, blue = inside /
                red = outside, +-3 mm full scale; green = on the surface) front and back.

usage: python3.13 standing_review_blender.py -- <bound .blend> <retopo checkpoint with source proxy> <out dir> [res]
"""
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, SRCBLEND, OUT = Path(a[0]), Path(a[1]), Path(a[2]); RES = int(a[3]) if len(a) > 3 else 1400
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(Path(__file__).resolve().parent))
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
from shoulder_pose_lib import arm_pose  # noqa: E402
with bpy.data.libraries.load(str(SRCBLEND), link=False) as (src, dst):
    dst.objects = ["HGPT_SOURCE_PROXY_Mesh_0"]
sc = bpy.context.scene; srcob = dst.objects[0]; sc.collection.objects.link(srcob)
rig = bpy.data.objects["MESHY_RIG"]; body = bpy.data.objects["MESHY_BODY"]
for o in sc.objects:
    if o.type == "MESH" and o not in (body, srcob):
        o.hide_render = True
skin = bpy.data.materials.new("skin"); skin.use_nodes = True; bs = skin.node_tree.nodes["Principled BSDF"]
bs.inputs["Base Color"].default_value = (0.66, 0.50, 0.41, 1); bs.inputs["Roughness"].default_value = 0.6
for o in (body, srcob):
    o.data.materials.clear(); o.data.materials.append(skin)
eng = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
EEVEE = "BLENDER_EEVEE" if "BLENDER_EEVEE" in eng else "BLENDER_EEVEE_NEXT"
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.20, 0.21, 0.23, 1); w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.5
for nm, rot, en in (("key", (55, 0, 30), 3.2), ("fill", (70, 0, -55), 1.1), ("rim", (60, 0, 180), 1.8)):
    ld = bpy.data.lights.new(nm, "SUN"); ld.energy = en; ld.angle = math.radians(8)
    lo = bpy.data.objects.new(nm, ld); lo.rotation_euler = tuple(math.radians(x) for x in rot); sc.collection.objects.link(lo)
sc.view_settings.view_transform = "Standard"
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
VIEWS = {"front": (0, -1, 0), "back": (0, 1, 0), "left": (-1, 0, 0), "right": (1, 0, 0), "q34_fl": (-0.7, -0.7, 0.05),
         "q34_fr": (0.7, -0.7, 0.05), "q34_back": (0.7, 0.7, 0.05)}


def shoot(path, view, scale=2.02, centre=0.93, aspect=0.55):
    d = Vector(VIEWS[view]).normalized(); cam.location = Vector((0, 0, centre)) + d * 6
    cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y"); cd.ortho_scale = scale
    sc.render.resolution_y = RES; sc.render.resolution_x = int(RES * aspect); sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def smooth(ob, on):
    ob.data.polygons.foreach_set("use_smooth", [on] * len(ob.data.polygons)); ob.data.update()


def show(*obs):
    for o in (body, srcob):
        o.hide_render = o not in obs


def rest():
    for p in rig.pose.bones:
        p.matrix_basis.identity()
    bpy.context.view_layer.update()


sc.render.engine = EEVEE
# A: rest pose, source vs current (the A-pose needs a wider frame)
rest(); smooth(body, True); smooth(srcob, True)
for who, ob in (("source", srcob), ("current", body)):
    show(ob)
    for v in ("front", "back", "left", "right", "q34_fl"):
        shoot(OUT / f"A_rest_{v}_{who}.png", v, aspect=0.75 if v in ("front", "back", "q34_fl") else 0.55)
# B: natural standing pose, current body
rest()
for sd in ("l", "r"):
    arm_pose(rig, sd, 8, 10, 165, 0, hinge=True)
bpy.context.view_layer.update(); show(body)
for v in VIEWS:
    shoot(OUT / f"B_stand_{v}.png", v)
# C: diagnostics - flat shading + wireframe in the standing pose
smooth(body, False)
wire = body.copy(); wire.data = body.data; sc.collection.objects.link(wire)
wm = wire.modifiers.new("W", "WIREFRAME"); wm.thickness = 0.0006; wm.use_replace = True
dark = bpy.data.materials.new("wire"); dark.use_nodes = True; dark.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.05, 0.05, 0.06, 1)
wire.material_slots[0].link = "OBJECT"; wire.material_slots[0].material = dark; wire.hide_render = False
for v in ("front", "back", "right"):
    shoot(OUT / f"C_flatwire_{v}.png", v)
wire.hide_render = True; smooth(body, True)
# C: deviation map at rest (vertex colour, workbench flat lighting so the colour is read as data)
rest(); me = body.data
sb = BVHTree.FromPolygons([v.co.copy() for v in srcob.data.vertices], [tuple(p.vertices) for p in srcob.data.polygons])
ca = me.color_attributes.new("dev", "FLOAT_COLOR", "POINT"); dev = np.zeros(len(me.vertices))
for v in me.vertices:
    loc, n, _, _ = sb.find_nearest(body.matrix_world @ v.co); dev[v.index] = (body.matrix_world @ v.co - loc).dot(n)
for i, d in enumerate(dev):
    t = max(-1.0, min(1.0, d / 0.003))
    ca.data[i].color = (0.15 + 0.85 * max(t, 0), 0.75 * (1 - abs(t)) + 0.15, 0.15 + 0.85 * max(-t, 0), 1)
me.color_attributes.active_color = ca
sc.render.engine = "BLENDER_WORKBENCH"; shd = sc.display.shading; shd.light = "FLAT"; shd.color_type = "VERTEX"
shd.background_type = "VIEWPORT"; shd.background_color = (0.9, 0.9, 0.9); show(body)
for v in ("front", "back"):
    shoot(OUT / f"C_deviation_{v}.png", v, aspect=0.75)
abs_mm = np.abs(dev) * 1000
(OUT / "deviation_stats.txt").write_text("vertices %d  |dev| mean %.2f mm  p95 %.2f mm  max %.2f mm  >2mm %d  >5mm %d\n" % (
    len(dev), abs_mm.mean(), np.percentile(abs_mm, 95), abs_mm.max(), int((abs_mm > 2).sum()), int((abs_mm > 5).sum())))
print("REVIEW done")
