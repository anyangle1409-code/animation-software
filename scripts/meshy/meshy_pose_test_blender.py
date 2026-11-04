"""Deformation tests for the Meshy appearance mesh bound to the canonical skeleton (bind_meshy_blender.py output).

Poses (rigid world-space rotations of canonical bone subtrees; bone lengths never change):
  stand          arms down (humerus 8 deg abduction), elbows 10 deg
  press_bottom   humerus 55 deg elevation, 40 deg forward, elbow 70 deg (included), clavicle +8 deg
  press_mid      humerus 105 / 30, elbow 115, clavicle +15
  press_top      humerus 170 / 15, elbow 175, clavicle +25 (girdle rhythm)
  curl           humerus hanging, elbow 40 deg included (140 deg flexion), forearm in front
  squat          hip flexion 100 deg, knee flexion 110 deg, ankle dorsiflexion 25 deg, trunk lean 35 deg, arms forward 80 deg
Per pose: self-intersecting triangle pairs (non-adjacent), edge stretch / compression percentiles in the moving
region, signed volume change, min arm-trunk gap, renders front / side / back (Workbench clay, ortho).

usage: python3.13 meshy_pose_test_blender.py -- <meshy_bound.blend> <out dir> [poses comma list]
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
SRC, OUT = Path(a[0]), Path(a[1]); OUT.mkdir(parents=True, exist_ok=True)
ONLY = a[2].split(",") if len(a) > 2 else None
bpy.ops.wm.open_mainfile(filepath=str(SRC))
rig = bpy.data.objects["MESHY_RIG"]; body = bpy.data.objects["MESHY_BODY"]
pb = rig.pose.bones; MW = rig.matrix_world; W2A = MW.to_3x3().inverted(); wp = lambda v: MW @ v
import os  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shoulder_pose_lib import apply_correctives  # noqa: E402
CORR = os.environ.get("CORRECTIVES", "1") != "0"     # drive CORR_SH_* keys by humerus elevation when the mesh has them


def subtree(root):
    return [root] + [c.name for c in pb[root].children_recursive]


def rot_rigid(names, piv_w, axis_w, deg):
    piv = W2A @ (Vector(piv_w) - MW.translation); R = Matrix.Rotation(math.radians(deg), 4, (W2A @ Vector(axis_w)).normalized())
    D = Matrix.Translation(piv) @ R @ Matrix.Translation(-piv); mats = {n: pb[n].matrix.copy() for n in names}
    for n in names:
        pb[n].matrix = D @ mats[n]; bpy.context.view_layer.update()


def aim(root, bone, target_w):
    b = pb[bone]; cur = (wp(b.tail) - wp(b.head)).normalized(); tgt = Vector(target_w).normalized(); ax = cur.cross(tgt)
    if ax.length > 1e-7:
        rot_rigid(subtree(root), wp(b.head), ax, math.degrees(cur.angle(tgt)))


def arm_pose(sd, elev, fwd, elbow, clav):
    lat = 1.0 if wp(pb[f"upperarm_{sd}"].head).x > 0 else -1.0
    if clav:
        rot_rigid(subtree(f"clavicle_{sd}"), wp(pb[f"clavicle_{sd}"].head), Vector((0, -lat, 0)), clav)
    e, p_ = math.radians(elev), math.radians(fwd)
    aim(f"upperarm_{sd}", f"upperarm_{sd}", Vector((lat * math.sin(e) * math.cos(p_), -math.sin(e) * math.sin(p_), -math.cos(e))))
    u = (wp(pb[f"upperarm_{sd}"].tail) - wp(pb[f"upperarm_{sd}"].head)).normalized()
    ref = Vector((0, 0, 1)) if elev > 30 else Vector((0, -1, 0))   # forearm towards the ceiling (press) / forwards (curl)
    w = ref - u * ref.dot(u); w = w.normalized() if w.length > 1e-4 else Vector((0, -1, 0))
    fl = math.radians(180 - elbow); fdir = u * math.cos(fl) + w * math.sin(fl)
    aim(f"forearm_{sd}", f"forearm_{sd}", fdir)
    hd = pb[f"hand_{sd}"]; aim(f"hand_{sd}", f"hand_{sd}", fdir)


def squat():
    for sd in ("l", "r"):
        lat = 1.0 if wp(pb[f"thigh_{sd}"].head).x > 0 else -1.0
        rot_rigid(subtree(f"thigh_{sd}"), wp(pb[f"thigh_{sd}"].head), Vector((1, 0, 0)), -100)   # knee forwards (-y), up
        rot_rigid(subtree(f"shin_{sd}"), wp(pb[f"shin_{sd}"].head), Vector((1, 0, 0)), 110)
        rot_rigid(subtree(f"foot_{sd}"), wp(pb[f"foot_{sd}"].head), Vector((1, 0, 0)), -(110 - 100) + 0)
    # the feet must stay flat: rotate the whole body so the shin is inclined forwards by the dorsiflexion angle
    rot_rigid(subtree("spine_01"), wp(pb["spine_01"].head), Vector((1, 0, 0)), 35)    # trunk leans forwards
    for sd in ("l", "r"):
        arm_pose(sd, 80, 85, 170, 0)


RAW = {"stand": lambda: [arm_pose(s, 8, 10, 170, 0) for s in ("l", "r")],
       "press_bottom": lambda: [arm_pose(s, 55, 40, 70, 8) for s in ("l", "r")],
       "press_mid": lambda: [arm_pose(s, 105, 30, 115, 15) for s in ("l", "r")],
       "press_top": lambda: [arm_pose(s, 170, 15, 175, 25) for s in ("l", "r")],
       "curl": lambda: [arm_pose(s, 5, 5, 40, 0) for s in ("l", "r")],
       "squat": squat}
rest = {n: pb[n].matrix_basis.copy() for n in pb.keys()}


def evaluated():
    dg = bpy.context.evaluated_depsgraph_get(); m = bpy.data.meshes.new_from_object(body.evaluated_get(dg), depsgraph=dg)
    V = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
    m.calc_loop_triangles(); T = np.empty(len(m.loop_triangles) * 3, np.int32); m.loop_triangles.foreach_get("vertices", T)
    E = np.empty(len(m.edges) * 2, np.int32); m.edges.foreach_get("vertices", E)
    bpy.data.meshes.remove(m); mw = np.array(body.matrix_world)
    return V @ mw[:3, :3].T + mw[:3, 3], T.reshape(-1, 3), E.reshape(-1, 2)


def self_hits(V, T):
    bvh = BVHTree.FromPolygons([tuple(p) for p in V], [tuple(t) for t in T], all_triangles=True)
    pairs = bvh.overlap(bvh); n = 0; locs = []
    Ts = [set(t) for t in T]
    for i, j in pairs:
        if i < j and not (Ts[i] & Ts[j]):
            n += 1; locs.append(V[T[i]].mean(0))
    return n, np.array(locs)


def volume(V, T):
    a_, b_, c_ = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]; return float(np.einsum("ij,ij->i", a_, np.cross(b_, c_)).sum() / 6)


GN = {g.index: g.name for g in body.vertex_groups}
Wg = {}
for v in body.data.vertices:
    for g in v.groups:
        Wg.setdefault(GN[g.group], {})[v.index] = g.weight
V0, T0, E0 = evaluated(); SH_Z = float(wp(pb["upperarm_l"].head).z) - 0.05; L0 = np.linalg.norm(V0[E0[:, 0]] - V0[E0[:, 1]], axis=1); vol0 = volume(V0, T0)
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading
sh.light = "STUDIO"; sh.color_type = "SINGLE"; sh.single_color = (0.78, 0.64, 0.55); sh.show_cavity = False
sh.background_type = "VIEWPORT"; sh.background_color = (0.16, 0.16, 0.17)
cd = bpy.data.cameras.new("PT"); cd.type = "ORTHO"; cam = bpy.data.objects.new("PT", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 800, 1100
rig.hide_render = True
REP = {}
for name, fn in RAW.items():
    if ONLY and name not in ONLY:
        continue
    for n, m in rest.items():
        pb[n].matrix_basis = m
    bpy.context.view_layer.update(); fn(); bpy.context.view_layer.update()
    corr = apply_correctives(rig, body) if CORR else {}
    V, T, E = evaluated()
    if name == "squat":                                           # feet back on the floor
        dz = V[:, 2].min(); rig.location.z -= dz; bpy.context.view_layer.update(); V, T, E = evaluated()
    L = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1); r = L / np.maximum(L0, 1e-7)
    moving = np.linalg.norm(V - V0, axis=1) > 0.01; em = moving[E[:, 0]] | moving[E[:, 1]]
    n_hit, locs = self_hits(V, T)
    reg = {}
    if n_hit:
        z0 = V[:, 2].min(); H = V[:, 2].max() - z0
        for lab, cond in (("head_neck", lambda p: (p[:, 2] - z0) / H > 0.83), ("shoulder_axilla", lambda p: ((p[:, 2] - z0) / H > 0.62) & ((p[:, 2] - z0) / H <= 0.83)),
                          ("hip_groin", lambda p: ((p[:, 2] - z0) / H > 0.35) & ((p[:, 2] - z0) / H <= 0.62)), ("legs_feet", lambda p: (p[:, 2] - z0) / H <= 0.35)):
            reg[lab] = int(cond(locs).sum())
    REP[name] = {"correctives": corr, "self_intersections": n_hit, "self_intersections_by_height_band": reg,
                 "edge_stretch_p99": round(float(np.percentile(r[em], 99)), 3) if em.any() else None,
                 "edge_stretch_max": round(float(r[em].max()), 2) if em.any() else None,
                 "edge_compress_p1": round(float(np.percentile(r[em], 1)), 3) if em.any() else None,
                 "volume_change_pct": round((volume(V, T) / vol0 - 1) * 100, 2)}
    z0 = V[:, 2].min(); H = V[:, 2].max() - z0
    for view, dv in (("front", (0, -1, 0)), ("side", (-1, 0, 0)), ("back", (0, 1, 0))):
        dvec = Vector(dv); centre = Vector((0, 0, z0 + 0.5 * H)); cam.location = centre + dvec * 6
        cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (-dvec).to_track_quat("-Z", "Y"); cd.ortho_scale = 2.35
        sc.render.filepath = str(OUT / f"{name}_{view}.png"); bpy.ops.render.render(write_still=True)
    if name.startswith("press") or name in ("stand", "curl"):
        for view, dv in (("front", (0, -1, 0)), ("back", (0, 1, 0)), ("side", (-1, 0, 0))):
            dvec = Vector(dv); centre = Vector((0, 0, SH_Z)); cam.location = centre + dvec * 6
            cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (-dvec).to_track_quat("-Z", "Y"); cd.ortho_scale = 0.75
            sc.render.filepath = str(OUT / f"{name}_{view}_shoulder.png"); bpy.ops.render.render(write_still=True)
    rig.location.z = 0.0
    print("POSE", name, json.dumps(REP[name]), flush=True)
(OUT / "pose_report.json").write_text(json.dumps(REP, indent=1)); print("POSES done", flush=True)
