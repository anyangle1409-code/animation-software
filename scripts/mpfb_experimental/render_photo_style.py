"""Photo-style review render (Cycles): skin-toned principled material, soft studio key + rim lights, grey backdrop like
the owner's reference sheets.  REVIEW ONLY - judges shape under realistic light; nothing here is a production material.
usage: python3.13 render_photo_style.py -- <defined .blend> <out dir> [views comma list] [samples]"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(a[0]), Path(a[1]); OUT.mkdir(parents=True, exist_ok=True)
VIEWS = (a[2] if len(a) > 2 else "front,front34,side,back34,back").split(",")
SAMPLES = int(a[3]) if len(a) > 3 else 48
bpy.ops.wm.open_mainfile(filepath=str(SRC))
sc = bpy.context.scene
body = bpy.data.objects.get("MPFB_DEFINED_REVIEW") or max((o for o in sc.objects if o.type == "MESH" and "FLOOR" not in o.name),
                                                          key=lambda o: len(o.data.vertices))
for o in sc.objects:
    if o.type == "MESH" and o is not body:
        o.hide_render = True
sc.render.engine = "CYCLES"; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
try:
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
except Exception:
    pass
sc.cycles.device = "CPU"; sc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
sc.render.resolution_x, sc.render.resolution_y = 720, 1280
m = bpy.data.materials.new("SKIN_REVIEW_ONLY"); m.use_nodes = True
bsdf = m.node_tree.nodes.get("Principled BSDF")
import os as _os
bsdf.inputs["Base Color"].default_value = tuple(float(v) for v in _os.environ.get("PHOTO_SKIN", "0.36,0.19,0.11").split(",")) + (1,)
bsdf.inputs["Roughness"].default_value = 0.5
nt = m.node_tree                                   # fine skin texture: procedural noise bump (render only)
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 900.0; nz.inputs["Detail"].default_value = 6.0
bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.06; bp.inputs["Distance"].default_value = 0.0004
nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
for nm, v in (("Subsurface Weight", 0.12), ("Subsurface Scale", 0.01), ("Specular IOR Level", 0.45)):
    if nm in bsdf.inputs:
        bsdf.inputs[nm].default_value = v
body.data.materials.clear(); body.data.materials.append(m)
for o in bpy.data.objects:
    if o.type == "MESH" and o is not body:
        o.hide_render = True
# grey backdrop
if sc.world is None:
    sc.world = bpy.data.worlds.new("W")
sc.world.use_nodes = True; bg = sc.world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.11, 0.11, 0.115, 1); bg.inputs["Strength"].default_value = 0.4
import numpy as np  # noqa: E402
dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); me = ev.to_mesh()
V = np.array([body.matrix_world @ v.co for v in me.vertices]); ev.to_mesh_clear()
z0, z1 = V[:, 2].min(), V[:, 2].max(); H = z1 - z0
fm = bpy.data.meshes.new("BACKDROP"); s = 16.0
fm.from_pydata([(-s, -s, z0), (s, -s, z0), (s, s, z0), (-s, s, z0), (-s, s, z0 + 4), (s, s, z0 + 4)], [], [(0, 1, 2, 3), (3, 2, 5, 4)])
fo = bpy.data.objects.new("BACKDROP", fm); sc.collection.objects.link(fo)
fmat = bpy.data.materials.new("BACKDROP"); fmat.use_nodes = True
fmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.09, 0.09, 0.095, 1)
fmat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
fm.materials.append(fmat)


def area(name, loc, energy, size, target):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = energy; ld.size = size
    lo = bpy.data.objects.new(name, ld); sc.collection.objects.link(lo); lo.location = loc
    lo.rotation_mode = "QUATERNION"; lo.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y")
    return lo


cz = z0 + 0.6 * H
cd = bpy.data.cameras.new("PC"); import os; cd.lens = float(os.environ.get("PHOTO_LENS", "70")); cam = bpy.data.objects.new("PC", cd); sc.collection.objects.link(cam); sc.camera = cam
DIRS = {"front": (0, -1), "front34": (0.7071, -0.7071), "side": (1, 0), "back34": (0.7071, 0.7071), "back": (0, 1),
        "side_l": (-1, 0), "front34_l": (-0.7071, -0.7071), "back34_l": (-0.7071, 0.7071)}   # _l: the left side, as the owner's reference sheet
for v in VIEWS:
    dx, dy = DIRS[v]
    for o in [o for o in sc.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o, do_unlink=True)
    fwd = Vector((dx, dy, 0)); side = Vector((-dy, dx, 0))
    fo.rotation_euler = (0.0, 0.0, math.atan2(dx, -dy))       # the wall always behind the figure, facing the camera
    area("KEY", tuple(Vector((0, 0, cz + 1.2)) + fwd * 2.4 + side * 2.6), 260, 1.2, (0, 0, cz))
    area("FILL", tuple(Vector((0, 0, cz)) + fwd * 3.5 - side * 2.5), 45, 3.0, (0, 0, cz))
    area("RIM_L", tuple(Vector((0, 0, cz + 0.6)) - fwd * 2.5 + side * 2.0), 180, 1.0, (0, 0, cz))
    area("RIM_R", tuple(Vector((0, 0, cz + 0.6)) - fwd * 2.5 - side * 2.0), 180, 1.0, (0, 0, cz))
    dist = H * float(os.environ.get("PHOTO_DIST", "3.0"))
    cam.location = Vector((0, 0, z0 + 0.55 * H)) + fwd * dist
    cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (Vector((0, 0, z0 + 0.52 * H)) - cam.location).to_track_quat("-Z", "Y")
    sc.render.filepath = str(OUT / f"photo_{v}.png"); bpy.ops.render.render(write_still=True)
print("PHOTO done", flush=True)
