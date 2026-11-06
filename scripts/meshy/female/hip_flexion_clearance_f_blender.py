"""FEMALE shorts / groin clearance at limited hip flexion (read-only; never saves). A structural check only - not
movement development: both thighs flexed in the sagittal plane about the hip joints and the knees bent, no pelvis tilt,
no correctives, the current weights. Poses (hip flexion, knee flexion): standing reference, (45, 60), (90, 90) -
a squat-depth thigh angle.

Measured per pose:
  * skin outside the shorts: body vertices whose nearest shorts point (fabric base surface, no Solidify) is within
    12 mm, normal-aligned, and the skin is on the outer side (penetration);
  * shorts floating: shorts vertices' distance to the skin (p95 / max, mm) and the count farther than 10 mm;
  * groin self-intersections: body faces in the pelvis / upper-thigh box intersecting other body faces (pairs that
    share no vertex);
  * renders: clay side, front-below.

usage: python3.13 hip_flexion_clearance_f_blender.py -- <candidate .blend> <out dir> <report .json>
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2]); OUT.mkdir(parents=True, exist_ok=True)
POSES = [(0, 0), (45, 60), (90, 90)]
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
sc = bpy.context.scene; rig = bpy.data.objects["HGPT_FEMALE_RIG"]; rig.data.pose_position = "POSE"
body, bra, shorts = (bpy.data.objects[n] for n in ("HGPT_Female_Body", "HGPT_Female_Bra", "HGPT_Female_Shorts"))
P0 = np.array([v.co[:] for v in body.data.vertices]); FACES = [tuple(p.vertices) for p in body.data.polygons]
box = (np.abs(P0[:, 0]) < 0.22) & (P0[:, 2] > 0.55) & (P0[:, 2] < 0.98)
GF = [k for k, f in enumerate(FACES) if box[list(f)].all()]
rep = {"in": IN.name, "structural_only": True, "poses": {}}


def evaluated(o, solid_off=False):
    mods = [m for m in o.modifiers if m.type == "SOLIDIFY"] if solid_off else []
    for m in mods:
        m.show_viewport = False
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); me = oe.to_mesh()
    V = [v.co.copy() for v in me.vertices]; F = [tuple(p.vertices) for p in me.polygons]; oe.to_mesh_clear()
    for m in mods:
        m.show_viewport = True
    return V, F


def rot_about(pb, R):
    M = pb.matrix.copy(); h = M.translation.copy(); pb.matrix = Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ M
    bpy.context.view_layer.update()


def set_pose(hip, knee):
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    for s in ("l", "r"):
        rot_about(rig.pose.bones[f"thigh_{s}"], Matrix.Rotation(math.radians(-hip), 4, "X"))   # knee forward (-y)
        rot_about(rig.pose.bones[f"shin_{s}"], Matrix.Rotation(math.radians(knee), 4, "X"))   # foot back


sh = sc.display.shading; sc.render.engine = "BLENDER_WORKBENCH"; sh.light = "STUDIO"; sh.color_type = "OBJECT"
body.color = (0.80, 0.68, 0.60, 1); bra.color = shorts.color = (0.30, 0.30, 0.33, 1)
for o in sc.objects:
    o.hide_render = o not in (body, bra, shorts)
for o in (body, bra, shorts):
    for p in o.data.polygons:
        p.use_smooth = True
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x = sc.render.resolution_y = 700


def shot(name, view, centre, scale):
    d = Vector(view).normalized(); cam.location = Vector(centre) + d * 4; cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y"); cd.ortho_scale = scale; cd.clip_end = 10
    sc.render.filepath = str(OUT / f"{name}.png"); bpy.ops.render.render(write_still=True)


for hip, knee in POSES:
    set_pose(hip, knee); BV, _ = evaluated(body); SV, SF = evaluated(shorts, True)
    st = BVHTree.FromPolygons(SV, SF); bt = BVHTree.FromPolygons(BV, FACES)
    out = 0
    for i in np.where(box)[0]:
        c = BV[i]; h = st.find_nearest(c, 0.012)
        if h[0] is None:
            continue
        d = c - h[0]; s_ = d.dot(h[1])
        out += (d - h[1] * s_).length < 0.0015 and s_ > 0
    off = np.array([bt.find_nearest(v)[3] for v in SV]) * 1000
    gt = BVHTree.FromPolygons(BV, [FACES[k] for k in GF])
    pairs = [(x, y) for x, y in gt.overlap(gt) if x < y and not set(FACES[GF[x]]) & set(FACES[GF[y]])]
    key = f"hip{hip}_knee{knee}"
    rep["poses"][key] = {"skin_outside_shorts": int(out), "shorts_off_skin_mm": {"p95": round(float(np.percentile(off, 95)), 2), "max": round(float(off.max()), 2)},
                         "shorts_vertices_over_10mm": int((off > 10).sum()), "groin_self_intersections": len(pairs)}
    print("HIPFLEX", key, json.dumps(rep["poses"][key]))
    zc = 0.80 - 0.1 * hip / 90
    shot(f"{key}_side", (1, 0, 0), (0, -0.1 * hip / 90, zc), 0.75)
    shot(f"{key}_front_below", (0, -1, -0.6), (0, -0.12 * hip / 90, zc), 0.6)
REP.write_text(json.dumps(rep, indent=1)); print("DONE")
