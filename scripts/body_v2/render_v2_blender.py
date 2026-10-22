"""Standing renders of a finished body .blend (the set-up of the builder's R103/R114 skin renders and of legs_v2):
V2_full_stand_{front,back,side,front34}.png (workbench, transparent), V2_skin_stand_{front,side,front34,back}.png,
V2_skin_{legs,feet}_{front,side,back,front34}.png.

usage: blender python render_v2_blender.py -- <body.blend> <r57src root> <out dir>
"""
import math
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
SRC, ROOT, OUT = Path(args[0]).resolve(), Path(args[1]).resolve(), Path(args[2])
OUT.mkdir(parents=True, exist_ok=True)
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts/anatomy_fit")]
bpy.ops.wm.open_mainfile(filepath=str(SRC))
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
me = body.data
V1 = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", V1); V1 = V1.reshape(-1, 3)
z0 = float(V1[:, 2].min()); H = float(V1[:, 2].max()) - z0

# ------------------------------------------------------------------ standing renders (same set-up as the builder)
if True:
    import build_original_movement_benchmarks_blender as bench
    import original_v1_review_candidate_drives as drives
    sc = bpy.context.scene
    for ob in sc.objects:
        if ob.type in ("MESH", "CURVE") and ob is not body:
            ob.hide_render = True
    abd, elb = (float(x) for x in os.environ.get("V2_STAND", "16:6").split(":"))
    bench._reset(rig)
    for sd, sg in (("r", -1.0), ("l", 1.0)):
        pb = rig.pose.bones[f"upperarm_{sd}"]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (0.0, 0.0, math.radians(sg * abd))
        fb_ = rig.pose.bones[f"forearm_{sd}"]; fb_.rotation_mode = "XYZ"; fb_.rotation_euler = (math.radians(-elb), 0.0, 0.0)
    bpy.context.view_layer.update(); drives.drive(rig, body); bpy.context.view_layer.update()
    lo, hi = V1.min(0), V1.max(0); mid = Vector(((lo + hi) / 2).tolist())
    cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
    cd.ortho_scale = float(hi[2] - lo[2]) * 1.08
    sc.render.film_transparent = True
    mat = bpy.data.materials.new("REVIEW_ONLY"); mat.diffuse_color = (.72, .55, .45, 1)
    body.data.materials.clear(); body.data.materials.append(mat)
    sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
    sc.display.shading.show_cavity = True; sc.render.resolution_x = 900; sc.render.resolution_y = 1500
    VIEWS = {"front": (0, -1, 0), "back": (0, 1, 0), "side": (1, 0, 0), "front34": (0.7, -0.7, 0)}

    def aim(centre, dv):
        dvec = Vector(dv).normalized(); cam.location = centre + dvec * 4; cam.rotation_mode = "QUATERNION"
        cam.rotation_quaternion = (-dvec).to_track_quat("-Z", "Y")
    for view, dv in VIEWS.items():
        aim(mid, dv); sc.render.filepath = str(OUT / f"V2_full_stand_{view}.png"); bpy.ops.render.render(write_still=True)
    # skin (as R103 / R114)
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = int(os.environ.get("V2_SKIN_SAMPLES", "48"))
    try:
        sc.cycles.use_denoising = True
    except Exception:
        pass
    sm = bpy.data.materials.new("REVIEW_SKIN"); sm.use_nodes = True
    bsdf = sm.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.62, 0.40, 0.30, 1); bsdf.inputs["Roughness"].default_value = float(os.environ.get("V2_SKIN_ROUGH", "0.62"))
    for nm, val in (("Subsurface Weight", 0.2), ("Subsurface Scale", 0.012), ("Specular IOR Level", 0.28)):
        if nm in bsdf.inputs:
            bsdf.inputs[nm].default_value = val
    body.data.materials.clear(); body.data.materials.append(sm)
    if sc.world is None:
        sc.world = bpy.data.worlds.new("W")
    sc.world.use_nodes = True; sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.055, 1)
    sc.render.film_transparent = False
    try:
        sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "None"
    except Exception:
        pass
    lights = []
    for nm, loc, energy, size in (("KEY", (-1.6, -2.6, 2.6), 70, 1.6), ("FILL", (2.2, -2.0, 1.4), 18, 2.5), ("RIM", (1.2, 2.6, 2.4), 45, 1.2)):
        ld = bpy.data.lights.new(nm, "AREA"); ld.energy = energy; ld.size = size
        lo_ = bpy.data.objects.new(nm, ld); sc.collection.objects.link(lo_); lo_.location = loc
        lo_.rotation_mode = "QUATERNION"; lo_.rotation_quaternion = (mid - Vector(loc)).to_track_quat("-Z", "Y"); lights.append(lo_)

    def key_at(loc):
        lights[0].location = loc; lights[0].rotation_quaternion = (mid - lights[0].location).to_track_quat("-Z", "Y")
    _sk = float(os.environ.get("V2_SKIN_SCALE", "2"))
    sc.render.resolution_x = int(900 * _sk); sc.render.resolution_y = int(1500 * _sk)
    for view, dv in {"front": (0, -1, 0), "side": (1, 0, 0), "front34": (0.7, -0.7, 0), "back": (0, 1, 0)}.items():
        key_at({"side": (2.6, -1.6, 2.6), "back": (-2.5, 1.5, 2.6)}.get(view, (-1.6, -2.6, 2.6)))
        aim(mid, dv); sc.render.filepath = str(OUT / f"V2_skin_stand_{view}.png"); bpy.ops.render.render(write_still=True)
    # leg and foot close-ups
    sc.render.resolution_x = 1000; sc.render.resolution_y = 1400
    for name, zf, scale in (("legs", 0.25, 0.56), ("feet", 0.05, 0.20)):
        cd.ortho_scale = scale * H; c_ = Vector((0.0, float(mid.y), z0 + zf * H))
        if name == "feet":
            sc.render.resolution_y = 1000
        for view, dv in {"front": (0, -1, 0), "side": (1, 0, 0), "back": (0, 1, 0), "front34": (0.7, -0.7, 0)}.items():
            key_at({"side": (2.6, -1.6, 2.6), "back": (-2.5, 1.5, 2.6)}.get(view, (-1.6, -2.6, 2.6)))
            aim(c_, dv); sc.render.filepath = str(OUT / f"V2_skin_{name}_{view}.png"); bpy.ops.render.render(write_still=True)
    bench._reset(rig)
    print("LEGS_V2_RENDERED", flush=True)
