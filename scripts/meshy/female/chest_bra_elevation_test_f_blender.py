"""FEMALE chest / sports-bra structural test at arm elevations 0, 45, 90, 135, 170 deg (read-only; never saves).

Limited test before Female V1 is frozen (no movement development): both upper arms are raised in the coronal plane
(abduction) about the shoulder joint to the given angle between the humerus and the downward vertical. Glenohumeral
only: scapulohumeral rhythm is OFF in the first-party exercise system (docs/CANONICAL_SKELETON_FREEZE.md), so this is
what the shared clips would do to her today. Measured per elevation:
  * BREAST tissue (body vertices under the bra cups: front chest, y < -0.04, 1.08 < z < 1.32, |x| < 0.15): edge
    stretch (posed / rest length: p95, max) over the whole box and over the CORE (within 60 mm of the front-most
    point: the breast itself, without the lateral border towards the axilla), displacement of the breast centroids in the sternum frame (spine_03), and
    the share of their skin weight on arm / girdle bones (upperarm, clavicle, scapula: static, from the bind);
  * BRA: skin outside the fabric (a body vertex with the bra under it along its normal and nothing over it), bra
    vertices floating > 6 mm off the skin (band, cups, straps separately), band slip (band vertices' displacement
    relative to the nearest skin point, tangential);
  * CHEST self-intersections of the body (face pairs, 1.0 < z < 1.45);
  * renders: clay front / side / back per elevation (body + bra + shorts).

usage: python3.13 chest_bra_elevation_test_f_blender.py -- <candidate .blend> <out dir> <report .json>
"""
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh  # noqa: E402
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2]); OUT.mkdir(parents=True, exist_ok=True)
ELEV = (0, 45, 90, 135, 170)
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
sc = bpy.context.scene
rig = bpy.data.objects["HGPT_FEMALE_RIG"]; body = bpy.data.objects["HGPT_Female_Body"]; bra = bpy.data.objects["HGPT_Female_Bra"]
shorts = bpy.data.objects["HGPT_Female_Shorts"]
rig.data.pose_position = "POSE"
for pb in rig.pose.bones:
    pb.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
me = body.data; P0 = np.array([v.co[:] for v in me.vertices])
breast = np.where((P0[:, 1] < -0.04) & (P0[:, 2] > 1.08) & (P0[:, 2] < 1.32) & (np.abs(P0[:, 0]) < 0.15))[0]
bset = set(breast.tolist())
E = np.array([[e.vertices[0], e.vertices[1]] for e in me.edges if e.vertices[0] in bset and e.vertices[1] in bset])
L0 = np.linalg.norm(P0[E[:, 0]] - P0[E[:, 1]], axis=1)
# breast CORE: within 60 mm of each side's front-most point (the gland and its envelope; the lateral border towards
# the axilla is excluded - its skin must stretch when the arm rises)
core = np.zeros(len(P0), bool)
for sg in (1, -1):
    ids = breast[np.sign(P0[breast, 0]) == sg]; ap = P0[ids[np.argmin(P0[ids, 1])]]
    core[ids[np.linalg.norm(P0[ids] - ap, axis=1) < 0.06]] = True
EC = np.array([e for e in E if core[e[0]] and core[e[1]]]); LC0 = np.linalg.norm(P0[EC[:, 0]] - P0[EC[:, 1]], axis=1)
vg = {g.index: g.name for g in body.vertex_groups}
arm_share = []
for i in breast:
    gs = me.vertices[i].groups; t = sum(g.weight for g in gs) or 1
    arm_share.append(sum(g.weight for g in gs if vg[g.group].startswith(("upperarm", "clavicle", "scapula"))) / t)
arm_share = np.array(arm_share)
rep = {"in": IN.name, "breast_vertices": int(len(breast)),
       "breast_weight_share_arm_girdle": {"mean": round(float(arm_share.mean()), 3), "p95": round(float(np.percentile(arm_share, 95)), 3),
                                          "max": round(float(arm_share.max()), 3), "vertices_over_0.2": int((arm_share > 0.2).sum())},
       "glenohumeral_only": True, "elevations": {}}
side_of = {}
for s in ("l", "r"):
    side_of[s] = np.sign((rig.matrix_world @ rig.data.bones[f"upperarm_{s}"].head_local).x)
bra_me = bra.data; BR0 = np.array([v.co[:] for v in bra_me.vertices])
band = BR0[:, 2] < 1.13; strap = BR0[:, 2] > 1.30; cup = ~band & ~strap


def evaluated(o):
    dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); m = oe.to_mesh()
    V = np.array([v.co[:] for v in m.vertices]); N_ = np.array([v.normal[:] for v in m.vertices]); F = [tuple(p.vertices) for p in m.polygons]
    oe.to_mesh_clear(); return V, N_, F


def set_elevation(deg):
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    for s in ("l", "r"):
        pb = rig.pose.bones[f"upperarm_{s}"]; M = pb.bone.matrix_local.copy(); h = M.translation.copy()
        d0 = (pb.bone.tail_local - pb.bone.head_local).normalized(); down = Vector((0, 0, -1))
        a0 = math.degrees(d0.angle(down)); dx = Vector((side_of[s], 0, 0))
        axis = down.cross(dx).normalized()               # rotates the arm up and out in the coronal plane
        if axis.length < 1e-6:
            continue
        R = Matrix.Rotation(math.radians(deg - a0), 4, axis)
        pb.matrix = Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ M
        bpy.context.view_layer.update()


# renders (workbench clay)
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "SINGLE"; sh.single_color = (0.78, 0.68, 0.62)
for o in sc.objects:
    o.hide_render = o not in (body, bra, shorts)
for o in (body, bra, shorts):
    for p in o.data.polygons:
        p.use_smooth = True
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 600, 600


def shot(name, view, centre, scale):
    d = Vector(view).normalized(); cam.location = Vector(centre) + d * 4; cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y"); cd.ortho_scale = scale; cd.clip_end = 10
    sc.render.filepath = str(OUT / f"{name}.png"); bpy.ops.render.render(write_still=True)


sp = rig.pose.bones["spine_03"]
for deg in ELEV:
    set_elevation(deg)
    V, N_, F = evaluated(body); BV, BN, BF = evaluated(bra)
    r = {}
    L = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1) / np.maximum(L0, 1e-9)
    LC = np.linalg.norm(V[EC[:, 0]] - V[EC[:, 1]], axis=1) / np.maximum(LC0, 1e-9)
    r["breast_core_edge_stretch"] = {"p95": round(float(np.percentile(LC, 95)), 3), "max": round(float(LC.max()), 3), "p5": round(float(np.percentile(LC, 5)), 3)}
    r["breast_edge_stretch"] = {"p95": round(float(np.percentile(L, 95)), 3), "max": round(float(L.max()), 3), "p5": round(float(np.percentile(L, 5)), 3)}
    Ms = (rig.matrix_world @ sp.matrix).inverted(); Ms0 = (rig.matrix_world @ sp.bone.matrix_local).inverted()
    for s, sg in (("left", 1), ("right", -1)):
        ids = breast[np.sign(P0[breast, 0]) == sg]
        c = Ms @ Vector(V[ids].mean(0)); c0 = Ms0 @ Vector(P0[ids].mean(0))
        r[f"breast_{s}_centroid_shift_in_sternum_frame_mm"] = round((c - c0).length * 1000, 1)
    tb = BVHTree.FromPolygons([Vector(p) for p in V], F); tg = BVHTree.FromPolygons([Vector(p) for p in BV], BF)
    out_ = 0
    for i in breast.tolist() + [j for j in range(len(V)) if 1.05 < V[j, 2] < 1.45 and j not in bset][::3]:
        c = Vector(V[i]); n = Vector(N_[i])
        h = tg.ray_cast(c + n * 0.0001, -n, 0.012)
        if h[0] is not None and tg.ray_cast(c + n * 0.0001, n, 0.012)[0] is None:
            out_ += 1
    r["skin_outside_bra_vertices"] = out_
    dist = np.array([tb.find_nearest(Vector(p))[3] for p in BV[:len(BR0)]]) * 1000      # the outer (original) shell; Solidify adds the inner copy after it
    for nm, m in (("band", band), ("cups", cup), ("straps", strap)):
        r[f"bra_{nm}_off_skin_mm"] = {"p95": round(float(np.percentile(dist[m], 95)), 2), "max": round(float(dist[m].max()), 2),
                                      "floating_over_6mm": int((dist[m] > 6).sum())}
    bm = bmesh.new()
    for p in V:
        bm.verts.new(p)
    bm.verts.ensure_lookup_table()
    for f in F:
        try:
            bm.faces.new([bm.verts[i] for i in f])
        except ValueError:
            pass
    bm.faces.ensure_lookup_table(); t = BVHTree.FromBMesh(bm); k = 0
    for i, j in t.overlap(t):
        if i < j and not (set(bm.faces[i].verts) & set(bm.faces[j].verts)):
            if 1.0 < bm.faces[i].calc_center_median().z < 1.45 + (0.3 if deg > 90 else 0):
                k += 1
    bm.free(); r["chest_self_intersections"] = k
    rep["elevations"][str(deg)] = r
    zc = 1.2 if deg < 135 else 1.3
    shot(f"elev{deg:03d}_front", (0, -1, 0.05), (0, 0, zc), 0.95 if deg >= 90 else 0.8)
    shot(f"elev{deg:03d}_side", (1, -0.15, 0.05), (0, 0, zc), 0.95 if deg >= 90 else 0.8)
    shot(f"elev{deg:03d}_back", (0, 1, 0.05), (0, 0, zc), 0.95 if deg >= 90 else 0.8)
    shot(f"elev{deg:03d}_chest", (0.35, -1, 0.1), (0.0, -0.05, 1.2), 0.42)
REP.write_text(json.dumps(rep, indent=1)); print("CHEST", json.dumps(rep))
