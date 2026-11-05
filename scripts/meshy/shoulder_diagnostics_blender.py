"""Shoulder / armpit diagnostics through arm elevation 0-170 deg on a bound retopology file (MESHY_RIG / MESHY_BODY).

Purpose: tell WHY each shoulder problem happens (topology, weights, joint placement / motion, or missing corrective
deformation), not to hide it. Read-only on the input; writes JSON + renders only.

Zones (per side, defined on the REST mesh relative to the rest shoulder joint GH, in metres):
  deltoid      cap over the joint: within 0.14 of GH, not below GH.z - 0.09, lateral of GH.x - 0.035
  front_fold   pectoral -> arm (anterior axillary fold): GH.x - 0.11 .. GH.x + 0.05, y < GH.y - 0.025, z GH.z-0.19 .. GH.z-0.02
  back_fold    latissimus / teres -> arm (posterior axillary fold): same, y > GH.y + 0.025
  armpit       axilla floor between the folds: GH.x - 0.10 .. GH.x + 0.03, |y - GH.y| <= 0.025, z GH.z-0.21 .. GH.z-0.04
  clavicle_trap  above / medial: GH.x - 0.17 .. GH.x - 0.02, z > GH.z - 0.02, within 0.20 of GH
  scapula      back medial: GH.x - 0.17 .. GH.x - 0.02, y > GH.y + 0.02, z GH.z-0.22 .. GH.z
Per zone and elevation: self-intersecting triangle pairs, folded faces (normal against its vertices' mean normal),
crease sharpness (dihedral angle p99, count of edges sharper than 60 deg), edge stretch p95 / max, compression p5
(pinching), and for the deltoid the enclosed volume about the posed joint (ratio to rest).

Motion modes:
  lib     the current test motion (shoulder_pose_lib.arm_pose: humerus aimed, clavicle +25 deg at 170, scapula fixed to it)
  rhythm  anatomical scapulohumeral rhythm: clavicle elevation 0.15 x elevation and retraction 0.10 x elevation about
          the sternoclavicular joint; scapular upward rotation about the acromioclavicular joint so the total scapular
          upward rotation is elevation / 3 (about 2:1 glenohumeral : scapulothoracic); then the humerus is aimed to the
          target elevation. Bone lengths never change.

usage: python3.13 shoulder_diagnostics_blender.py -- <bound .blend> <out dir> <mode lib|rhythm> [elevations]
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
SRC, OUT, MODE = Path(a[0]), Path(a[1]), a[2]
ELEV = [int(x) for x in a[3].split(",")] if len(a) > 3 else [0, 45, 90, 105, 135, 170]
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SRC), load_ui=False)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shoulder_pose_lib import arm_pose, rest_capture, rest_restore, rot_rigid, subtree, aim  # noqa: E402
rig = bpy.data.objects["MESHY_RIG"]; body = bpy.data.objects["MESHY_BODY"]; pb = rig.pose.bones; wp = lambda v: rig.matrix_world @ v
FWD = 30


def pose_rhythm(sd, el):
    lat = 1.0 if wp(pb[f"upperarm_{sd}"].head).x > 0 else -1.0
    clav_el, clav_ret = 0.15 * el, 0.10 * el; scap_up = el / 3.0 - clav_el
    sc_ = wp(pb[f"clavicle_{sd}"].head)
    rot_rigid(rig, subtree(rig, f"clavicle_{sd}"), sc_, Vector((0, -lat, 0)), clav_el)          # elevation
    rot_rigid(rig, subtree(rig, f"clavicle_{sd}"), sc_, Vector((0, 0, lat)), clav_ret)          # retraction (lateral end back)
    ac = wp(pb[f"clavicle_{sd}"].tail)
    n_sp = Vector((math.sin(math.radians(FWD)) * lat, -math.cos(math.radians(FWD)), 0.0))       # scapular-plane normal (forwards-out)
    rot_rigid(rig, subtree(rig, f"scapula_{sd}"), ac, n_sp * lat, scap_up)          # upward rotation (glenoid up)
    e, p_ = math.radians(el), math.radians(FWD)
    aim(rig, f"upperarm_{sd}", f"upperarm_{sd}", Vector((lat * math.sin(e) * math.cos(p_), -math.sin(e) * math.sin(p_), -math.cos(e))))
    u = (wp(pb[f"upperarm_{sd}"].tail) - wp(pb[f"upperarm_{sd}"].head)).normalized()
    aim(rig, f"forearm_{sd}", f"forearm_{sd}", u); aim(rig, f"hand_{sd}", f"hand_{sd}", u)
    return {"clavicle_elev": round(clav_el, 1), "clavicle_retr": round(clav_ret, 1), "scapula_upward_extra": round(scap_up, 1)}


def evaluated():
    dg = bpy.context.evaluated_depsgraph_get(); m = bpy.data.meshes.new_from_object(body.evaluated_get(dg), depsgraph=dg)
    V = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
    m.calc_loop_triangles(); T = np.empty(len(m.loop_triangles) * 3, np.int32); m.loop_triangles.foreach_get("vertices", T)
    E = np.empty(len(m.edges) * 2, np.int32); m.edges.foreach_get("vertices", E)
    P = np.empty(len(m.polygons) * 4, np.int32); m.polygons.foreach_get("vertices", P)
    bpy.data.meshes.remove(m); return V, T.reshape(-1, 3), E.reshape(-1, 2), P.reshape(-1, 4)


def normals(V, F):
    if F.shape[1] == 4:
        n = np.cross(V[F[:, 2]] - V[F[:, 0]], V[F[:, 3]] - V[F[:, 1]])
    else:
        n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    return n / np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-12)


rest = rest_capture(rig); V0, T0, E0, P0 = evaluated()
GH0 = {sd: np.array(wp(pb[f"upperarm_{sd}"].head)) for sd in ("l", "r")}
# edge -> two quads (for dihedral angles)
from collections import defaultdict  # noqa: E402
ef = defaultdict(list)
for fi, q in enumerate(P0):
    for k in range(4):
        e = tuple(sorted((q[k], q[(k + 1) % 4]))); ef[e].append(fi)
EP = np.array([e for e, f in ef.items() if len(f) == 2]); EF = np.array([ef[tuple(e)] for e in EP])


def zones(sd):
    g = GH0[sd]; s = 1 if sd == "r" else -1; X = (V0[:, 0] - g[0]) * s; Y = V0[:, 1] - g[1]; Z = V0[:, 2] - g[2]
    D = np.linalg.norm(V0 - g, axis=1); side = V0[:, 0] * s > 0.03
    return {"deltoid": side & (D < 0.14) & (Z > -0.09) & (X > -0.035),
            "front_fold": side & (X > -0.11) & (X < 0.05) & (Y < -0.025) & (Z > -0.19) & (Z < -0.02),
            "back_fold": side & (X > -0.11) & (X < 0.05) & (Y > 0.025) & (Z > -0.19) & (Z < -0.02),
            "armpit": side & (X > -0.10) & (X < 0.03) & (np.abs(Y) <= 0.025) & (Z > -0.21) & (Z < -0.04),
            "clavicle_trap": side & (X > -0.17) & (X < -0.02) & (Z > -0.02) & (D < 0.20),
            "scapula": side & (X > -0.17) & (X < -0.02) & (Y > 0.02) & (Z > -0.22) & (Z < 0.0)}


ZN = {sd: zones(sd) for sd in ("l", "r")}
L0 = np.linalg.norm(V0[E0[:, 0]] - V0[E0[:, 1]], axis=1)


def dihedral(V):
    N = normals(V, P0); c = np.clip(np.einsum("ij,ij->i", N[EF[:, 0]], N[EF[:, 1]]), -1, 1); return np.degrees(np.arccos(c))


def deltoid_volume(V, sd, gh):
    m = ZN[sd]["deltoid"]; tri = T0[m[T0].all(1)]
    a_, b_, c_ = V[tri[:, 0]] - gh, V[tri[:, 1]] - gh, V[tri[:, 2]] - gh
    return abs(float(np.einsum("ij,ij->i", a_, np.cross(b_, c_)).sum() / 6))


DIH0 = dihedral(V0); VOL0 = {sd: deltoid_volume(V0, sd, GH0[sd]) for sd in ("l", "r")}
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading
sh.light = "STUDIO"; sh.color_type = "SINGLE"; sh.single_color = (0.78, 0.64, 0.55); sh.show_cavity = True; sh.cavity_type = "WORLD"
sh.background_type = "VIEWPORT"; sh.background_color = (0.16, 0.16, 0.17)
cd = bpy.data.cameras.new("SD"); cd.type = "ORTHO"; cam = bpy.data.objects.new("SD", cd); sc.collection.objects.link(cam); sc.camera = cam
for o in sc.objects:
    o.hide_render = o is not body


def shot(n, d, c, s, res=(700, 700)):
    d = Vector(d).normalized(); cam.location = Vector(c) + d * 5; cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y"); cd.ortho_scale = s
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.filepath = str(OUT / f"{n}.png"); bpy.ops.render.render(write_still=True)


REP = {"mode": MODE, "rest": {}}
for sd in ("r", "l"):
    REP["rest"][sd] = {z: {"vertices": int(m.sum()), "dihedral_p99": round(float(np.percentile(DIH0[m[EP].all(1)], 99)), 1),
                           "edges_sharper_60": int((DIH0[m[EP].all(1)] > 60).sum())} for z, m in ZN[sd].items()}
for el in ELEV:
    rest_restore(rig, rest); motion = {}
    if el:
        for sd in ("l", "r"):
            if MODE == "rhythm":
                motion[sd] = pose_rhythm(sd, el)
            else:
                arm_pose(rig, sd, el, FWD, 175, 25.0 * el / 170.0)
    bpy.context.view_layer.update(); V, T, E, P = evaluated()
    bvh = BVHTree.FromPolygons([tuple(p) for p in V], [tuple(t) for t in T], all_triangles=True); Ts = [set(t) for t in T]
    hit_tri = np.zeros(len(T), bool)
    for i, j in bvh.overlap(bvh):
        if i < j and not (Ts[i] & Ts[j]):
            hit_tri[i] = hit_tri[j] = True
    NT = normals(V, T); VN = np.zeros_like(V)
    for k in range(3):
        np.add.at(VN, T[:, k], NT)
    VN /= np.maximum(np.linalg.norm(VN, axis=1)[:, None], 1e-12); fold_tri = np.einsum("ij,ij->i", NT, VN[T].mean(1)) < 0
    DIH = dihedral(V); r = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1) / np.maximum(L0, 1e-9)
    res = {"motion": motion}
    for sd in ("r", "l"):
        gh = np.array(wp(pb[f"upperarm_{sd}"].head)); zr = {}
        for z, m in ZN[sd].items():
            tm = m[T0].any(1); em = m[E0].all(1); dm = m[EP].all(1)
            zr[z] = {"intersections": int(hit_tri[tm].sum()), "folded": int(fold_tri[tm].sum()),
                     "dihedral_p99": round(float(np.percentile(DIH[dm], 99)), 1), "edges_sharper_60": int((DIH[dm] > 60).sum()),
                     "new_sharp_edges": int(((DIH[dm] > 60) & (DIH0[dm] <= 60)).sum()),
                     "stretch_p95": round(float(np.percentile(r[em], 95)), 2), "stretch_max": round(float(r[em].max()), 2),
                     "compress_p5": round(float(np.percentile(r[em], 5)), 2)}
        zr["deltoid"]["volume_ratio"] = round(deltoid_volume(V, sd, gh) / VOL0[sd], 3)
        zr["gh_moved_mm"] = round(float(np.linalg.norm(gh - GH0[sd])) * 1000, 1)
        res[sd] = zr
    REP[el] = res
    c = (0.0, 0.03, float(GH0["r"][2]) - 0.05)
    for view, dv in (("front", (0, -1, 0)), ("back", (0, 1, 0)), ("side", (1, 0, 0))):
        shot(f"{MODE}_{el:03d}_{view}", dv, c, 0.95 if view != "side" else 0.8)
    cr = tuple(GH0["r"] + np.array([0.0, 0.0, -0.06]))
    shot(f"{MODE}_{el:03d}_armpit", (0.75, -0.25, -0.6), cr, 0.42)
    print("DIAG", el, json.dumps(res["r"]), flush=True)
rest_restore(rig, rest)
(OUT / f"shoulder_diagnostics_{MODE}.json").write_text(json.dumps(REP, indent=1)); print("DIAG done")
