"""FEMALE chest / shorts review renders for one candidate (read-only; never saves). Workbench, studio light, clay,
smooth shading, natural standing pose, the same cameras for every candidate (before / after comparisons).

  chest_bra_{front,q34,side}, chest_body_{front,q34,side}, sternum_{bra,body}   (enlarged chest views)
  shorts_{front,back,side,under}            body + shorts
  shorts_only_{front,under}, body_only_{front,under}
  diag_{front,under,chest}                  the body coloured by its clearance under the garments: green >= 1 mm under
                                            the fabric's outer face, yellow 0-1 mm, RED = skin outside the fabric
                                            (penetration); grey = not under a garment

usage: python3.13 review_chest_shorts_f_blender.py -- <candidate .blend> <out dir> <prefix>
"""
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, PFX = Path(a[0]), Path(a[1]), a[2]; OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
sc = bpy.context.scene; rig = bpy.data.objects["HGPT_FEMALE_RIG"]; rig.data.pose_position = "POSE"; bpy.context.view_layer.update()
body, bra, shorts = (bpy.data.objects[n] for n in ("HGPT_Female_Body", "HGPT_Female_Bra", "HGPT_Female_Shorts"))
for o in (body, bra, shorts):
    for p in o.data.polygons:
        p.use_smooth = True
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "OBJECT"
body.color = (0.80, 0.68, 0.60, 1); bra.color = shorts.color = (0.30, 0.30, 0.33, 1)
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x = sc.render.resolution_y = 900


def shot(name, objs, view, centre, scale):
    for o in sc.objects:
        o.hide_render = o not in objs
    d = Vector(view).normalized(); cam.location = Vector(centre) + d * 4; cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y"); cd.ortho_scale = scale; cd.clip_end = 10
    sc.render.filepath = str(OUT / f"{PFX}_{name}.png"); bpy.ops.render.render(write_still=True)


C = (0, -0.05, 1.2)
for nm, objs in (("chest_bra", (body, bra, shorts)), ("chest_body", (body,))):
    shot(f"{nm}_front", objs, (0, -1, 0.05), C, 0.36)
    shot(f"{nm}_q34", objs, (0.6, -0.8, 0.05), C, 0.36)
    shot(f"{nm}_side", objs, (1, 0, 0.05), C, 0.36)
shot("sternum_bra", (body, bra), (0, -1, 0.15), (0, -0.08, 1.2), 0.18)
shot("sternum_body", (body,), (0, -1, 0.15), (0, -0.08, 1.2), 0.18)
G = (0, -0.01, 0.80)
shot("shorts_front", (body, shorts), (0, -1, 0), G, 0.36)
shot("shorts_back", (body, shorts), (0, 1, 0), G, 0.36)
shot("shorts_side", (body, shorts), (1, 0, 0), G, 0.36)
shot("shorts_under", (body, shorts), (0, -0.5, -1), (0, 0, 0.78), 0.30)
shot("shorts_only_front", (shorts,), (0, -1, 0), G, 0.36)
shot("shorts_only_under", (shorts,), (0, -0.5, -1), (0, 0, 0.78), 0.30)
shot("body_only_front", (body,), (0, -1, 0), G, 0.36)
shot("body_only_under", (body,), (0, -0.5, -1), (0, 0, 0.78), 0.30)
# clearance diagnostic (posed): signed distance of each skin vertex to the garment outer surface along the garment normal
dg = bpy.context.evaluated_depsgraph_get(); be = body.evaluated_get(dg); bm_ = be.to_mesh(); BV = [v.co.copy() for v in bm_.vertices]; be.to_mesh_clear()
TB = []
for o in (bra, shorts):
    m = [x for x in o.modifiers if x.type == "SOLIDIFY"]
    for x in m:
        x.show_viewport = False
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); gm = oe.to_mesh()
    TB.append(BVHTree.FromPolygons([v.co.copy() for v in gm.vertices], [tuple(p.vertices) for p in gm.polygons])); oe.to_mesh_clear()
    for x in m:
        x.show_viewport = True
ca = body.data.color_attributes.new("CLEAR", "FLOAT_COLOR", "POINT"); red = 0
for i, c in enumerate(BV):
    col = (0.62, 0.62, 0.62, 1)
    for t in TB:
        h = t.find_nearest(c, 0.012)
        if h[0] is None:
            continue
        d = c - h[0]; s_ = d.dot(h[1])
        if (d - h[1] * s_).length > 0.0015:
            continue
        col = (0.85, 0.1, 0.1, 1) if s_ > 0 else ((0.95, 0.85, 0.1, 1) if s_ > -0.001 else (0.2, 0.7, 0.25, 1))
        red += s_ > 0
    ca.data[i].color = col
body.data.color_attributes.active_color = ca; sh.color_type = "VERTEX"
shot("diag_front", (body,), (0, -1, 0), (0, -0.02, 0.98), 0.75)
shot("diag_under", (body,), (0, -0.5, -1), (0, 0, 0.78), 0.30)
shot("diag_chest", (body,), (0, -1, 0.05), C, 0.36)
print("REVIEW", PFX, "skin_outside_fabric_vertices", red)
