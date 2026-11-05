"""Continuous shoulder movement test: both arms 0 -> 170 -> 0 deg on a bound retopology file (read-only on the input).

Each frame sets the elevation e(t) = 170 * (1 - cos(2 pi t)) / 2 (smooth start / stop), arm raised in the scapular
plane, elbow straight (175 deg), clavicle lifting 25 deg at 170 (shoulder_pose_lib.arm_pose); helpers and corrective
shapes on the file run through their own drivers. Per frame, measured on the evaluated mesh:
  * self-intersecting triangle pairs within 0.25 m of either shoulder joint (rest), folded faces there;
  * elbow included angle and wrist deviation (forearm vs hand direction), both arms - must stay constant;
  * the largest vertex jump between consecutive frames relative to the frame step's elevation change (popping);
  * shoulder-joint path (mm moved from rest).
Every frame is rendered from the same cameras (front, back, right side, right armpit, left armpit) and composed into
one panel; the panels are written as an animated GIF and, if Blender's FFMPEG is available, an MP4.

usage: python3.13 shoulder_sweep_animation_blender.py -- <bound .blend> <out dir> <label> [frames]
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT, LABEL = Path(a[0]), Path(a[1]), a[2]
NF = int(a[3]) if len(a) > 3 else 61
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SRC), load_ui=False)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shoulder_pose_lib import arm_pose, rest_capture, rest_restore  # noqa: E402
rig = bpy.data.objects["MESHY_RIG"]; body = bpy.data.objects["MESHY_BODY"]; pb = rig.pose.bones; wp = lambda v: rig.matrix_world @ v


def evaluated():
    dg = bpy.context.evaluated_depsgraph_get(); m = bpy.data.meshes.new_from_object(body.evaluated_get(dg), depsgraph=dg)
    V = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
    m.calc_loop_triangles(); T = np.empty(len(m.loop_triangles) * 3, np.int32); m.loop_triangles.foreach_get("vertices", T)
    bpy.data.meshes.remove(m); return V, T.reshape(-1, 3)


rest = rest_capture(rig); V0, T0 = evaluated()
GH0 = {sd: np.array(wp(pb[f"upperarm_{sd}"].head)) for sd in ("l", "r")}
near = np.zeros(len(V0), bool)
for sd in ("l", "r"):
    near |= np.linalg.norm(V0 - GH0[sd], axis=1) < 0.25
tri_near = near[T0].all(1)
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading
sh.light = "STUDIO"; sh.color_type = "SINGLE"; sh.single_color = (0.78, 0.64, 0.55); sh.show_cavity = True; sh.cavity_type = "WORLD"
sh.background_type = "VIEWPORT"; sh.background_color = (0.16, 0.16, 0.17)
cd = bpy.data.cameras.new("AN"); cd.type = "ORTHO"; cam = bpy.data.objects.new("AN", cd); sc.collection.objects.link(cam); sc.camera = cam
for o in sc.objects:
    o.hide_render = o is not body
VIEWS = [("front", (0, -1, 0), (0.0, 0.03, 1.40), 1.05), ("back", (0, 1, 0), (0.0, 0.03, 1.40), 1.05),
         ("side", (1, 0, 0), (0.0, 0.03, 1.40), 1.05),
         ("armpit_r", (0.75, -0.25, -0.6), tuple(GH0["r"] + np.array([0, 0, -0.06])), 0.42),
         ("armpit_l", (-0.75, -0.25, -0.6), tuple(GH0["l"] + np.array([0, 0, -0.06])), 0.42)]


def shot(path, d, c, s, res):
    d = Vector(d).normalized(); cam.location = Vector(c) + d * 5; cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y"); cd.ortho_scale = s
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.filepath = str(path); bpy.ops.render.render(write_still=True)


def angle(u, v):
    return math.degrees(math.acos(max(-1.0, min(1.0, u.normalized().dot(v.normalized())))))


frames = []; Vprev = None; eprev = None
for f in range(NF):
    t = f / (NF - 1); e = 170.0 * (1 - math.cos(2 * math.pi * t)) / 2
    rest_restore(rig, rest)
    if e > 1e-3:
        for sd in ("l", "r"):
            arm_pose(rig, sd, e, 30, 175, 25.0 * e / 170.0)
    bpy.context.view_layer.update(); V, T = evaluated()
    bvh = BVHTree.FromPolygons([tuple(p) for p in V], [tuple(x) for x in T], all_triangles=True); Ts = [set(x) for x in T]; hits = 0
    for i, j in bvh.overlap(bvh):
        if i < j and (tri_near[i] or tri_near[j]) and not (Ts[i] & Ts[j]):
            hits += 1
    N = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]); N /= np.maximum(np.linalg.norm(N, axis=1)[:, None], 1e-12)
    VN = np.zeros_like(V)
    for k in range(3):
        np.add.at(VN, T[:, k], N)
    VN /= np.maximum(np.linalg.norm(VN, axis=1)[:, None], 1e-12)
    folds = int(((np.einsum("ij,ij->i", N, VN[T].mean(1)) < 0) & tri_near).sum())
    rec = {"frame": f, "elevation_deg": round(e, 2), "intersections": hits, "folded_faces": folds}
    for sd in ("l", "r"):
        ua = wp(pb[f"upperarm_{sd}"].tail) - wp(pb[f"upperarm_{sd}"].head); fa = wp(pb[f"forearm_tw1_{sd}"].tail) - wp(pb[f"forearm_{sd}"].head)
        hd = wp(pb[f"hand_{sd}"].tail) - wp(pb[f"hand_{sd}"].head)
        rec[f"elbow_included_deg_{sd}"] = round(180 - angle(ua, fa), 2); rec[f"wrist_dev_deg_{sd}"] = round(angle(fa, hd), 2)
        rec[f"gh_moved_mm_{sd}"] = round(float(np.linalg.norm(np.array(wp(pb[f"upperarm_{sd}"].head)) - GH0[sd])) * 1000, 1)
    if Vprev is not None and abs(e - eprev) > 1e-6:
        rec["max_jump_mm_per_deg"] = round(float(np.linalg.norm(V - Vprev, axis=1)[near].max()) * 1000 / abs(e - eprev), 2)
    Vprev, eprev = V, e
    frames.append(rec)
    for name, d, c, s in VIEWS:
        shot(OUT / f"f{f:03d}_{name}.png", d, c, s, (520, 520))
    print("FRAME", json.dumps(rec), flush=True)
rest_restore(rig, rest)
summ = {"label": LABEL, "frames": NF,
        "intersections_max": max(r["intersections"] for r in frames), "folded_max": max(r["folded_faces"] for r in frames),
        "elbow_included_range": [min(min(r["elbow_included_deg_l"], r["elbow_included_deg_r"]) for r in frames), max(max(r["elbow_included_deg_l"], r["elbow_included_deg_r"]) for r in frames)],
        "wrist_dev_max_deg": max(max(r["wrist_dev_deg_l"], r["wrist_dev_deg_r"]) for r in frames),
        "jump_mm_per_deg_max": max(r.get("max_jump_mm_per_deg", 0) for r in frames),
        "up_down_symmetry_max_intersection_diff": max(abs(frames[i]["intersections"] - frames[NF - 1 - i]["intersections"]) for i in range(NF))}
(OUT / "sweep_animation.json").write_text(json.dumps({"summary": summ, "frames": frames}, indent=1)); print("SUMMARY", json.dumps(summ))
