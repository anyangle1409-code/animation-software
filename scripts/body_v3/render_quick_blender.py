"""Quick review renders (Workbench, matcap-like studio light) of a body_v3 blend: front, 3/4, side, back + upper-body.
usage: python3.13 render_quick_blender.py -- <blend> <out.png composite> [height px]"""
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); OUTP = Path(a[1]); HP = int(a[2]) if len(a) > 2 else 900
sc = bpy.context.scene; ob = max((o for o in sc.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices))
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading
sh.light = "STUDIO"; sh.color_type = "SINGLE"; sh.single_color = (0.80, 0.62, 0.50); sh.show_specular_highlight = False
sh.show_cavity = False; sh.background_type = "VIEWPORT"; sh.background_color = (0.16, 0.16, 0.17)
sc.render.film_transparent = False
cd = bpy.data.cameras.new("Q"); cd.type = "ORTHO"; cam = bpy.data.objects.new("Q", cd); sc.collection.objects.link(cam); sc.camera = cam
z = np.array([(ob.matrix_world @ v.co).z for v in ob.data.vertices]); z0, H = z.min(), z.max() - z.min()
tiles = []
for name, d, hc, s, w in (("front", (0, -1, 0), 0.5, 1.08, 0.45), ("front34", (0.7071, -0.7071, 0), 0.5, 1.08, 0.45),
                          ("side", (1, 0, 0), 0.5, 1.08, 0.45), ("back", (0, 1, 0), 0.5, 1.08, 0.45),
                          ("front_up", (0, -1, 0), 0.78, 0.42, 0.62), ("back_up", (0, 1, 0), 0.78, 0.42, 0.62)):
    dv = Vector(d); dv.normalize(); c = Vector((0, 0, z0 + hc * H)); cam.location = c + dv * 4
    cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (-dv).to_track_quat("-Z", "Y"); cd.ortho_scale = s * H
    sc.render.resolution_y = HP; sc.render.resolution_x = int(HP * w)
    fp = str(OUTP.parent / f"_q_{name}.png"); sc.render.filepath = fp; bpy.ops.render.render(write_still=True); tiles.append(fp)
img = [bpy.data.images.load(f) for f in tiles]
W = sum(i.size[0] for i in img); Hh = max(i.size[1] for i in img)
buf = np.zeros((Hh, W, 4), np.float32); x = 0
for i in img:
    p = np.array(i.pixels[:], np.float32).reshape(i.size[1], i.size[0], 4); buf[:i.size[1], x:x + i.size[0]] = p; x += i.size[0]
out = bpy.data.images.new("C", W, Hh); out.pixels = buf.ravel(); out.filepath_raw = str(OUTP); out.file_format = "PNG"; out.save()
print("QUICK", OUTP)
