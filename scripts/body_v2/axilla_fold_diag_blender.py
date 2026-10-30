"""Diagnostic (read-only): the armpit folds at the press lockout - how deep, where, and which layer makes them.

The lockout close-ups show a pinched notch where the posterior armpit fold (latissimus / teres major skin) meets the
upper arm, and a pointed cone in front of it, where the owner's reference photos show a smooth, rounded fold and an
open armpit hollow.  This measures the crease depth per vertex - the offset of each vertex from a smoothed copy of the
surface, along the normal (negative = sunk into a crease, positive = a ridge / cone) - in the rest-space zones of
lockout_stretch_diag_blender.py, at rest and at the lockout with the key families switched on / off (all keys, without
the R121 keys, plain skinning), and renders close-ups of the left armpit coloured by crease depth (blue = crease,
red = ridge, white = flat).  Nothing is saved.

The rig's _l side lives at -x and its _r side at +x (docs/ARCHITECTURE.md, "Handedness"); the stats are labelled by
the rig side.  AXFOLD_POSE=abd / flex measures the sideways / forward raise (shoulder_girdle_candidate.apply_arm_pose)
at ht_deg instead of the press; AXFOLD_LAYERS picks the key layers (default all,no_r121,lbs_only).

usage: python3.13 axilla_fold_diag_blender.py -- <body.blend> <r57src> <out_dir> [ht_deg]
"""
import json
import os
import sys

import bpy
import numpy as np
from mathutils import Vector
from scipy.sparse import csr_matrix

a = sys.argv[sys.argv.index("--") + 1:]; SRC, ROOT, OUT = a[0], a[1], a[2]
HT = float(a[3]) if len(a) > 3 else 160.0
os.makedirs(OUT, exist_ok=True)
sys.path[:0] = [ROOT + "/scripts", ROOT + "/scripts/anatomy_fit", os.path.dirname(os.path.abspath(__file__))]
bpy.ops.wm.open_mainfile(filepath=SRC)
import build_original_movement_benchmarks_blender as bench  # noqa: E402
import original_v1_review_candidate_drives as drives  # noqa: E402
import r121_drives  # noqa: E402
import build_functional_shoulder_correction_blender as correction  # noqa: E402
import functional_shoulder_correction as corr  # noqa: E402
import shoulder_girdle_candidate as girdle  # noqa: E402

body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
me = body.data; n = len(me.vertices)
AX = {}
for side, name in correction.HUMERI:
    b = rig.data.bones[name]
    AX[name] = corr.humeral_axial_angle_deg(tuple(b.tail_local - b.head_local), tuple(b.matrix_local.col[0].xyz), 40.0, side)
E = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
R = np.empty(n * 3); me.vertices.foreach_get("co", R); R = R.reshape(-1, 3)
TRI = np.array([(p.vertices[0], p.vertices[k], p.vertices[k + 1]) for p in me.polygons for k in range(1, len(p.vertices) - 1)])
Adj = csr_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n))
Dinv = 1.0 / np.maximum(np.asarray(Adj.sum(1)).ravel(), 1)
POSE = os.environ.get("AXFOLD_POSE", "press")
LAYERS = os.environ.get("AXFOLD_LAYERS", "all,no_r121,lbs_only").split(",")
SMOOTH = int(os.environ.get("AXFOLD_SMOOTH", "60"))         # Laplacian rounds for the reference surface (~2-3 cm scale)
z0 = float(R[:, 2].min()); H = float(R[:, 2].max()) - z0


def zone(P):
    """rest-space zone of points (symmetric in x) - as lockout_stretch_diag_blender.zone"""
    x, y, z = np.abs(P[:, 0]), P[:, 1], (P[:, 2] - z0) / H
    out = np.full(len(P), "other", dtype=object)
    out[(z > 0.62) & (x < 0.10)] = "torso_mid"
    out[(z > 0.66) & (z < 0.80) & (x >= 0.10) & (x < 0.19) & (y < -0.02)] = "chest_side_pec"
    out[(z > 0.66) & (z < 0.80) & (x >= 0.10) & (x < 0.19) & (y > 0.04)] = "back_side_lat"
    out[(z > 0.66) & (z < 0.80) & (x >= 0.10) & (x < 0.19) & (y >= -0.02) & (y <= 0.04)] = "axilla_floor"
    out[(z > 0.80) & (x >= 0.06) & (x < 0.17)] = "trapezius_neck"
    out[(z > 0.74) & (x >= 0.17)] = "deltoid_cap"
    out[(z > 0.62) & (z <= 0.74) & (x >= 0.19)] = "upper_arm"
    return out


VZ = zone(R)
GN = [g.name for g in body.vertex_groups]
TW = np.zeros(n); AW = np.zeros(n)                          # torso-side / arm-side weight: the junction skin has both
for v in me.vertices:
    for g in v.groups:
        nm = GN[g.group]
        if any(k in nm for k in ("muscle_lat", "spine", "scapula")):
            TW[v.index] += g.weight
        elif any(k in nm for k in ("upperarm", "shoulder_cap")):
            AW[v.index] += g.weight
JUNC = np.minimum(TW, AW) > 0.1
ZONES = ("back_side_lat", "axilla_floor", "chest_side_pec", "upper_arm", "deltoid_cap")


def normals(P):
    fn = np.cross(P[TRI[:, 1]] - P[TRI[:, 0]], P[TRI[:, 2]] - P[TRI[:, 0]])
    vn = np.zeros_like(P)
    for k in range(3):
        np.add.at(vn, TRI[:, k], fn)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-15)


def crease(P):
    """signed offset (m) of each vertex from a Laplacian-smoothed copy, along the normal: <0 crease, >0 ridge"""
    Q = P.copy()
    for _ in range(SMOOTH):
        Q = 0.5 * Q + 0.5 * (Adj @ Q) * Dinv[:, None]
    return np.einsum("ij,ij->i", P - Q, normals(P))


def ev():
    dg = bpy.context.evaluated_depsgraph_get(); e = body.evaluated_get(dg); m = e.to_mesh()
    P = np.empty(n * 3); m.vertices.foreach_get("co", P); e.to_mesh_clear(); return P.reshape(-1, 3)


def pose(r121=True, legacy=True, lock=True):
    bench._reset(rig)
    for kb in me.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    if lock and POSE in ("abd", "flex"):
        girdle.apply_arm_pose(rig, HT, 0.0 if POSE == "abd" else 90.0)
    elif lock:
        girdle.apply_press_pose(rig, HT, AX)
        for s in ("l", "r"):
            pb = rig.pose.bones[f"forearm_{s}"]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    if legacy:
        drives.drive(rig, body)
    if r121:
        r121_drives.drive(rig, body)
    bpy.context.view_layer.update()


def stats(c):
    out = {}
    for z in ZONES:
        for s, sg in (("l", -1), ("r", 1)):
            m = (VZ == z) & (np.sign(R[:, 0]) == sg)
            if not m.any():
                continue
            v = c[m] * 1000
            out[f"{z}_{s}"] = {"min_mm": round(float(v.min()), 2), "p1_mm": round(float(np.percentile(v, 1)), 2),
                               "p99_mm": round(float(np.percentile(v, 99)), 2), "max_mm": round(float(v.max()), 2),
                               "n_crease_gt3mm": int((v < -3).sum()), "n_ridge_gt3mm": int((v > 3).sum())}
    return out


sc = bpy.context.scene
for ob in sc.objects:
    if ob.type in ("MESH", "CURVE") and ob is not body:
        ob.hide_render = True
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam)
sc.camera = cam; cd.ortho_scale = 0.42
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "VERTEX"
sc.render.resolution_x = 560; sc.render.resolution_y = 560
attr = me.color_attributes.get("HGPT_CREASE") or me.color_attributes.new("HGPT_CREASE", "FLOAT_COLOR", "POINT")
me.color_attributes.active_color = attr
rep = {"pose": POSE, "ht_deg": HT, "girdle_frame": os.environ.get("V2_GIRDLE_FRAME", "plane35"), "smooth_rounds": SMOOTH,
       "sign": "crease depth = vertex offset from a smoothed surface along the normal; <0 crease, >0 ridge / cone"}
for tag, r121, leg, lock in [("rest", True, True, False)] + [t for t in (
        ("lock_all", True, True, True), ("lock_no_r121", False, True, True), ("lock_lbs_only", False, False, True))
        if t[0][5:] in LAYERS]:
    pose(r121, leg, lock); P = ev(); c = crease(P)
    rep[tag] = stats(c)
    if not lock:
        C_REST = c
    else:                                                    # pose-made relief at the arm / torso junction
        ex = (c - C_REST) * 1000
        for s, sg in (("l", -1), ("r", 1)):
            m = JUNC & (np.sign(R[:, 0]) == sg)
            k = np.nonzero(m)[0][np.argmax(ex[m])]
            rep[tag][f"junction_{s}"] = {"vertices": int(m.sum()), "pose_ridge_max_mm": round(float(ex[k]), 2),
                                         "at_rest_xyz": np.round(R[k], 3).tolist(),
                                         "n_pose_ridge_gt1.5mm": int((ex[m] > 1.5).sum()),
                                         "n_pose_ridge_gt3mm": int((ex[m] > 3).sum()),
                                         "n_pose_crease_gt3mm": int((ex[m] < -3).sum()),
                                         "pose_crease_min_mm": round(float(ex[m].min()), 2)}
    if lock:
        m = np.isin(VZ, ZONES) & (R[:, 0] > 0)
        i = np.argmin(np.where(m, c, 1)); j = np.argmax(np.where(m, c, -1))
        rep[tag]["deepest_crease_r"] = {"mm": round(float(c[i]) * 1000, 2), "zone": str(VZ[i]),
                                        "rest_xyz": np.round(R[i], 3).tolist(), "posed_xyz": np.round(P[i], 3).tolist()}
        rep[tag]["highest_ridge_r"] = {"mm": round(float(c[j]) * 1000, 2), "zone": str(VZ[j]),
                                       "rest_xyz": np.round(R[j], 3).tolist(), "posed_xyz": np.round(P[j], 3).tolist()}
    print("CREASE", tag, json.dumps(rep[tag]), flush=True)
    t = np.clip(c / 0.006, -1, 1)                              # +-6 mm full colour
    col = np.ones((n, 4))
    col[:, 0] = np.where(t < 0, 1 + t, 1.0); col[:, 1] = 1 - np.abs(t); col[:, 2] = np.where(t > 0, 1 - t, 1.0)
    attr.data.foreach_set("color", col.ravel())
    if lock and tag in ("lock_all", "lock_lbs_only"):
        ctr = Vector((0.16, 0.0, 1.40))
        for view, dv in {"back": (0.55, 0.83, 0), "side": (1, 0, 0), "front": (0.55, -0.83, 0)}.items():
            d = Vector(dv).normalized(); cam.location = ctr + d * 3; cam.rotation_mode = "QUATERNION"
            cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
            sc.render.filepath = f"{OUT}/{POSE}{int(HT)}_{tag}_{view}.png"; bpy.ops.render.render(write_still=True)
json.dump(rep, open(f"{OUT}/axilla_fold_diag_{POSE}{int(HT)}.json", "w"), indent=1)
print("DIAG done", flush=True)
