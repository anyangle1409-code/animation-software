"""Phase 3 shoulder test: raise both arms through 0 / 45 / 90 / 105 / 135 / 170 deg on the bound retopology.

Arms are raised in the scapular plane (30 deg forwards of the coronal plane), elbows straight (175 deg), with the
clavicle lifting in proportion (25 deg at 170, the press rhythm of meshy_pose_test_blender.py). Per elevation, in the
shoulder region (vertices within REG_R of either shoulder joint at rest):
  * self-intersecting triangle pairs (non-adjacent) - surface passing through itself (armpit collapse, deltoid / chest
    or rear-deltoid folds);
  * folded faces - faces whose normal points against the average normal of their own vertices (local folding /
    crumpling);
  * edge stretch p99 / max and compression p1 (skin stretch / bunching);
  * renders: front, back, side and armpit-from-below close-ups.

usage: python3.13 retopo_shoulder_sweep_blender.py -- <bound .blend (MESHY_RIG / MESHY_BODY)> <out dir> [elevations]
"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(a[0]), Path(a[1]); OUT.mkdir(parents=True, exist_ok=True)
ELEV = [int(x) for x in a[2].split(",")] if len(a) > 2 else [0, 45, 90, 105, 135, 170]
bpy.ops.wm.open_mainfile(filepath=str(SRC), load_ui=False)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shoulder_pose_lib import arm_pose, rest_capture, rest_restore  # noqa: E402
rig = bpy.data.objects["MESHY_RIG"]; body = bpy.data.objects["MESHY_BODY"]
REG_R = 0.20; FWD = 30


def evaluated():
    dg = bpy.context.evaluated_depsgraph_get(); m = bpy.data.meshes.new_from_object(body.evaluated_get(dg), depsgraph=dg)
    V = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
    m.calc_loop_triangles(); T = np.empty(len(m.loop_triangles) * 3, np.int32); m.loop_triangles.foreach_get("vertices", T)
    E = np.empty(len(m.edges) * 2, np.int32); m.edges.foreach_get("vertices", E)
    bpy.data.meshes.remove(m); return V, T.reshape(-1, 3), E.reshape(-1, 2)


def tri_normals(V, T):
    n = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]); return n / np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-12)


rest = rest_capture(rig); V0, T0, E0 = evaluated(); N0 = tri_normals(V0, T0); L0 = np.linalg.norm(V0[E0[:, 0]] - V0[E0[:, 1]], axis=1)
GH = {sd: np.array(rig.matrix_world @ rig.pose.bones[f"upperarm_{sd}"].head) for sd in ("l", "r")}
near = np.zeros(len(V0), bool); side = np.where(V0[:, 0] > 0, "r", "l")
for sd in ("l", "r"):
    near |= np.linalg.norm(V0 - GH[sd], axis=1) < REG_R
tri_near = near[T0].all(1); edge_near = near[E0].all(1)
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading
sh.light = "STUDIO"; sh.color_type = "SINGLE"; sh.single_color = (0.78, 0.64, 0.55); sh.show_cavity = True; sh.cavity_type = "WORLD"
sh.background_type = "VIEWPORT"; sh.background_color = (0.16, 0.16, 0.17)
cd = bpy.data.cameras.new("SW"); cd.type = "ORTHO"; cam = bpy.data.objects.new("SW", cd); sc.collection.objects.link(cam); sc.camera = cam
rig.hide_render = True
for o in sc.objects:
    if o not in (body, cam):
        o.hide_render = True


def shot(n, d, c, s, res=(800, 800)):
    d = Vector(d).normalized(); cam.location = Vector(c) + d * 5; cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y"); cd.ortho_scale = s
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.filepath = str(OUT / f"{n}.png"); bpy.ops.render.render(write_still=True)


REP = {}
for el in ELEV:
    rest_restore(rig, rest)
    if el:
        for sd in ("l", "r"):
            arm_pose(rig, sd, el, FWD, 175, 25.0 * el / 170.0)
    bpy.context.view_layer.update(); V, T, E = evaluated()
    # self-intersections in the shoulder region
    bvh = BVHTree.FromPolygons([tuple(p) for p in V], [tuple(t) for t in T], all_triangles=True); Ts = [set(t) for t in T]; hits = 0
    for i, j in bvh.overlap(bvh):
        if i < j and (tri_near[i] or tri_near[j]) and not (Ts[i] & Ts[j]):
            hits += 1
    N = tri_normals(V, T)
    # a robust fold measure: faces whose normal disagrees with the average normal of their neighbourhood by > 90 deg
    VN = np.zeros_like(V); np.add.at(VN, T[:, 0], N); np.add.at(VN, T[:, 1], N); np.add.at(VN, T[:, 2], N)
    VN /= np.maximum(np.linalg.norm(VN, axis=1)[:, None], 1e-12)
    folds = int(((np.einsum("ij,ij->i", N, VN[T].mean(1)) < 0.0) & tri_near).sum())
    L = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1); r = (L / np.maximum(L0, 1e-9))[edge_near]
    REP[el] = {"self_intersections_shoulder": hits, "folded_faces_shoulder": folds,
               "edge_stretch_p99": round(float(np.percentile(r, 99)), 3), "edge_stretch_max": round(float(r.max()), 2),
               "edge_compress_p1": round(float(np.percentile(r, 1)), 3)}
    c = (GH["r"] + np.array([0.02, 0, -0.04])).tolist()
    shot(f"elev_{el:03d}_front", (0.25, -1, 0), c, 0.55); shot(f"elev_{el:03d}_back", (0.25, 1, 0), c, 0.55)
    shot(f"elev_{el:03d}_side", (1, -0.1, 0), c, 0.55); shot(f"elev_{el:03d}_armpit", (0.7, -0.35, -0.6), c, 0.45)
    print("SWEEP", el, json.dumps(REP[el]), flush=True)
rest_restore(rig, rest)
(OUT / "shoulder_sweep.json").write_text(json.dumps(REP, indent=1)); print("SWEEP done")
