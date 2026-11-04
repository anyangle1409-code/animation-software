"""Shoulder-press deformation test for an MPFB / MakeHuman-based candidate (game_engine rig), review renders only.

Poses (scapular-plane press, both arms):
  * bottom - bar at the clavicles: humerus ~80 deg elevation, 25 deg forward of the frontal plane, elbow 95 deg, forearm
    vertical, clavicle elevated 8 deg;
  * mid    - humerus 120 deg, elbow 140 deg, clavicle 15 deg;
  * lockout - humerus 172 deg, elbow 175 deg, clavicle 25 deg (shoulder-girdle rhythm: the clavicle / scapula rise
    with the arm instead of the humerus rotating alone).
Each pose is evaluated (subdivision level 1), rendered front / side / back in clay (Workbench, ortho), and measured:
self-intersection-free check is not available for MPFB here, so the report lists armpit / shoulder stretch: the
largest edge-length ratio vs the stand pose in the shoulder region, and the minimum distance between the upper-arm and
trunk skin.

usage: python3.13 press_test_blender.py -- <mpfb_candidate.blend> <out dir>
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector
from scipy.spatial import cKDTree

a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(a[0]), Path(a[1]); OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SRC))
rig = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
body = max((o for o in bpy.data.objects if o.type == "MESH" and "FLOOR" not in o.name), key=lambda o: len(o.data.vertices))
for o in bpy.data.objects:
    if o.type == "MESH" and o is not body and "FLOOR" not in o.name:
        o.hide_render = True
pb = rig.pose.bones; MW = rig.matrix_world; W2A = MW.to_3x3().inverted()
sub = body.modifiers.get("SUBDIV_REVIEW") or body.modifiers.new("SUBDIV_REVIEW", "SUBSURF"); sub.levels = sub.render_levels = 1
wp = lambda v: MW @ v


def swing_to(b, target_w):
    target = (W2A @ target_w).normalized(); cur = (b.tail - b.head).normalized(); piv = b.head.copy()
    b.matrix = Matrix.Translation(piv) @ cur.rotation_difference(target).to_matrix().to_4x4() @ Matrix.Translation(-piv) @ b.matrix
    bpy.context.view_layer.update()


def mesh_state():
    dg = bpy.context.evaluated_depsgraph_get(); m = bpy.data.meshes.new_from_object(body.evaluated_get(dg), depsgraph=dg)
    V = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
    E = np.empty(len(m.edges) * 2, np.int32); m.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
    GN = {g.index: g.name for g in body.vertex_groups}; arm = np.zeros(len(V)); sh = np.zeros(len(V))
    for v in m.vertices:
        for g in v.groups:
            nm = GN.get(g.group, "")
            if "upperarm" in nm:
                arm[v.index] += g.weight
            if any(k in nm for k in ("upperarm", "clavicle", "spine_03")):
                sh[v.index] += g.weight
    bpy.data.meshes.remove(m)
    mw = np.array(body.matrix_world)
    return V @ mw[:3, :3].T + mw[:3, 3], E, arm, sh


rest = {n: pb[n].matrix_basis.copy() for n in pb.keys()}          # local transforms: order-independent restore
V0, E0, arm0, sh0 = mesh_state(); L0 = np.linalg.norm(V0[E0[:, 0]] - V0[E0[:, 1]], axis=1)
POSES = {"bottom": (55, 40, 70, 8), "mid": (105, 30, 115, 15), "lockout": (170, 15, 175, 25)}
ARMK = ("upperarm", "lowerarm", "hand", "thumb", "index", "middle", "ring", "pinky")


def chain(sd, keys):
    names = [n for n in pb.keys() if n.endswith("_" + sd) and any(k in n for k in keys)]
    depth = lambda n: len(pb[n].parent_recursive)
    return sorted(names, key=depth)


def rotate_rigid(names, piv_w, axis_w, ang):
    """rotate a set of pose bones rigidly about a world pivot / axis (parents first)"""
    piv = W2A @ (piv_w - MW.translation); R = Matrix.Rotation(ang, 4, (W2A @ axis_w).normalized())
    D = Matrix.Translation(piv) @ R @ Matrix.Translation(-piv)
    mats = {n: pb[n].matrix.copy() for n in names}
    for n in names:
        pb[n].matrix = D @ mats[n]; bpy.context.view_layer.update()


def aim_rigid(names, bone, target_w):
    b = pb[bone]; cur = (wp(b.tail) - wp(b.head)).normalized(); tgt = target_w.normalized()
    ax = cur.cross(tgt)
    if ax.length < 1e-6:
        return
    rotate_rigid(names, wp(b.head), ax, cur.angle(tgt))
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; shd = sc.display.shading
shd.light = "STUDIO"; shd.color_type = "SINGLE"; shd.single_color = (0.78, 0.62, 0.52); shd.show_cavity = False
shd.background_type = "VIEWPORT"; shd.background_color = (0.16, 0.16, 0.17)
cd = bpy.data.cameras.new("PT"); cd.type = "ORTHO"; cam = bpy.data.objects.new("PT", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 900, 1100
rep = {}
for pname, (elev, fwd, elbow, clav) in POSES.items():
    for n, m in rest.items():
        pb[n].matrix_basis = m
    bpy.context.view_layer.update()
    for sd in ("l", "r"):
        lat = 1.0 if wp(pb[f"upperarm_{sd}"].head).x > 0 else -1.0
        cl = pb.get(f"clavicle_{sd}")
        if cl is not None:                                   # girdle elevation about the sternoclavicular joint
            piv = cl.head.copy(); axw = Vector((0, 1, 0)) * (-lat)
            R = Matrix.Rotation(math.radians(clav), 4, (W2A @ axw).normalized())
            cl.matrix = Matrix.Translation(piv) @ R @ Matrix.Translation(-piv) @ cl.matrix; bpy.context.view_layer.update()
        e, p_ = math.radians(elev), math.radians(fwd)
        ua = pb[f"upperarm_{sd}"]
        aim_rigid(chain(sd, ARMK), f"upperarm_{sd}", Vector((lat * math.sin(e) * math.cos(p_), -math.sin(e) * math.sin(p_), -math.cos(e))))
        u = (wp(ua.tail) - wp(ua.head)).normalized()
        # forearm: in the plane of the humerus and the vertical, at `elbow` deg included angle -> towards the ceiling
        up = Vector((0, 0, 1)); w = (up - u * up.dot(u))
        w = w.normalized() if w.length > 1e-4 else Vector((0, -1, 0))
        flex = math.radians(180 - elbow)
        fdir = (u * math.cos(flex) + w * math.sin(flex)).normalized()
        aim_rigid(chain(sd, ARMK[1:]), f"lowerarm_{sd}", fdir)
        aim_rigid(chain(sd, ARMK[2:]), f"hand_{sd}", fdir)
    V, E, arm, sh = mesh_state(); L = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1)
    shm = (sh[E[:, 0]] > 0.2) & (sh[E[:, 1]] > 0.2)
    ratio = L / np.maximum(L0, 1e-6)
    a_ = arm > 0.6; t_ = (arm < 0.05) & (V[:, 2] > np.percentile(V[:, 2], 55))
    gap = float(cKDTree(V[t_]).query(V[a_])[0].min()) if a_.any() and t_.any() else None
    rep[pname] = {"humerus_elev_deg": elev, "elbow_deg": elbow, "clavicle_elev_deg": clav,
                  "shoulder_edge_stretch_max": round(float(ratio[shm].max()), 2),
                  "shoulder_edge_stretch_p99": round(float(np.percentile(ratio[shm], 99)), 2),
                  "shoulder_edge_compress_min": round(float(ratio[shm].min()), 2),
                  "arm_trunk_min_gap_mm": round(gap * 1000, 1) if gap is not None else None}
    z0 = V[:, 2].min(); H = V[:, 2].max() - z0
    for view, dv in (("front", (0, -1, 0)), ("side", (-1, 0, 0)), ("back", (0, 1, 0))):
        dvec = Vector(dv); centre = Vector((0, 0, z0 + 0.72 * H)); cam.location = centre + dvec * 5
        cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (-dvec).to_track_quat("-Z", "Y"); cd.ortho_scale = 1.65
        sc.render.filepath = str(OUT / f"press_{pname}_{view}.png"); bpy.ops.render.render(write_still=True)
    print("PRESS", pname, json.dumps(rep[pname]), flush=True)
(OUT / "press_report.json").write_text(json.dumps(rep, indent=1))
print("PRESS done", flush=True)
