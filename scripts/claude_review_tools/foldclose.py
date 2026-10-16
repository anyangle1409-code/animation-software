"""Lockout stretch/compression + sharp-fold map on a candidate (right side), with heat-map renders."""
import sys, os, math, json
sys.path.insert(0, "/home/user/p5/scripts"); sys.path.insert(0, "/home/user/p5/scripts/anatomy_fit")
import bpy, numpy as np
import original_v1_review_candidate_drives as drives
from mathutils import Vector
blend, out = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=blend)
import build_functional_shoulder_correction_blender as correction
import build_original_movement_benchmarks_blender as bench
import original_v1_press_extension as px
res = correction.build_corrected_scene(); body, rig = res["body"], res["runtime"]
drives.setup(res); px.install(); bench._reset(rig)
V0, F = bench._evaluated(body); R = np.array([tuple(v) for v in V0])
px.pose_press_full(res, float(os.environ.get("T", 1.0))); drives.drive(rig, body)
V, _ = bench._evaluated(body); P = np.array([tuple(v) for v in V])
nv = len(R)
def farea(X, f):
    a = 0.0
    for i in range(1, len(f) - 1): a += np.linalg.norm(np.cross(X[f[i]] - X[f[0]], X[f[i + 1]] - X[f[0]])) / 2
    return a
ar0 = np.array([farea(R, f) for f in F]); ar = np.array([farea(P, f) for f in F])
vr = np.zeros(nv); vc = np.zeros(nv)
for k, f in enumerate(F):
    for v in f: vr[v] += ar[k]; vc[v] += ar0[k]
ratio = vr / np.maximum(vc, 1e-12)             # >1 stretched, <1 compressed
# sharp folds: dihedral between adjacent face normals, posed vs rest
me = body.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
ef = {}
for k, f in enumerate(F):
    for i in range(len(f)):
        e = tuple(sorted((f[i], f[(i + 1) % len(f)]))); ef.setdefault(e, []).append(k)
def nrm(X, f):
    n = np.cross(X[f[1]] - X[f[0]], X[f[2]] - X[f[0]]); l = np.linalg.norm(n); return n / l if l > 1e-15 else n
gh = np.array(tuple(rig.matrix_world @ rig.pose.bones["upperarm_r"].head))
gh0 = np.array(tuple(rig.data.bones["upperarm_r"].head_local))
region = np.linalg.norm(R - gh0, axis=1) < 0.20
fold = np.zeros(nv)
sharp = 0
for e, fs in ef.items():
    if len(fs) != 2 or not (region[e[0]] and R[e[0], 0] > 0): continue
    d0 = math.degrees(math.acos(max(-1, min(1, float(np.dot(nrm(R, F[fs[0]]), nrm(R, F[fs[1]])))))))
    d1 = math.degrees(math.acos(max(-1, min(1, float(np.dot(nrm(P, F[fs[0]]), nrm(P, F[fs[1]])))))))
    if d1 > 30 and d1 - d0 > 15:
        sharp += 1
        for v in e: fold[v] = 1
reg = region & (R[:, 0] > 0)
summary = {"t": float(os.environ.get("T", 1.0)), "region_vertices": int(reg.sum()),
           "stretched_gt_1_5": int((ratio[reg] > 1.5).sum()), "compressed_lt_0_6": int((ratio[reg] < 0.6).sum()),
           "sharp_fold_edges_gt30": sharp}
print("MAP", json.dumps(summary))
# where are the sharp folds (right side) relative to the posed joint?
fv = np.where(fold > 0)[0]
if len(fv):
    rel = P[fv] - gh
    print("FOLDPOS n", len(fv), "mean cm", np.round(rel.mean(0) * 100, 1), "z range cm", np.round([rel[:, 2].min() * 100, rel[:, 2].max() * 100], 1))
    cells = {}
    for p, v in zip(np.round(rel / 0.03).astype(int), fv):
        cells.setdefault(tuple(p), []).append(v)
    for k, vs in sorted(cells.items(), key=lambda x: -len(x[1]))[:8]:
        c = (P[vs] - gh).mean(0) * 100
        print("FOLDCELL", len(vs), "x(out+) %.1f y(back+) %.1f z(up+) %.1f cm" % tuple(c))
json.dump(summary, open(f"{out}/map.json", "w"))
col = body.data.color_attributes.new("M", "FLOAT_COLOR", "POINT")
for i in range(nv):
    r = ratio[i]
    if fold[i]: c = (1.0, 0.95, 0.1)
    elif os.environ.get("FOLDONLY"): c = (0.72, 0.55, 0.45)
    elif r > 1: t = min(1, (r - 1) / 1.0); c = (0.75 + 0.25 * t, 0.7 * (1 - t) + 0.15 * t, 0.65 * (1 - t) + 0.1 * t)
    else: t = min(1, (1 - r) / 0.6); c = (0.75 * (1 - t) + 0.1 * t, 0.7 * (1 - t) + 0.35 * t, 0.65 * (1 - t) + 1.0 * t)
    col.data[i].color = (*c, 1)
body.data.color_attributes.active_color = col
scene = bpy.context.scene
for o in scene.objects:
    if o.type in ("MESH", "CURVE") and o is not body: o.hide_render = True
scene.render.engine = "BLENDER_WORKBENCH"; sh = scene.display.shading
sh.light, sh.color_type, sh.show_cavity = "STUDIO", "VERTEX", True
scene.render.film_transparent = True; scene.render.resolution_x = scene.render.resolution_y = 600
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = 0.62
cam = bpy.data.objects.new("C", cd); scene.collection.objects.link(cam); scene.camera = cam
for view, d in (("tq_close", (0.7, 0.7, 0.1)), ("tq_close_plain", (0.7, 0.7, 0.1)), ("back", (0.15, 1, 0.1)), ("side", (1, 0, 0.05))):
    if view == "tq_close_plain":
        for i in range(nv): col.data[i].color = (0.72, 0.55, 0.45, 1)
    elif view == "back":
        pass
    d = Vector(d).normalized(); tgt = Vector(tuple(gh)) + Vector((-0.04, 0.0, 0.0))
    cam.location = tgt + d * 4.0; cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
    scene.render.filepath = f"{out}/{view}.png"; bpy.ops.render.render(write_still=True)
