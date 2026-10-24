"""R121 candidate: arm-raise correctives authored on the rebuilt surface (CANDIDATE - the r57 drives are not changed).

The R120 rebuild carried the old shoulder correctives across by transfer, and raising the arm folds the rebuilt arm root
(r121_motion_check_blender.py: ~3,300 edges > 90 deg in the arm-root band at 150 deg abduction, ~2.4x V14).  Recipe
(as R30): for each key angle, pose both arms with every existing drive active, relax the posed upper body where it folds
(local unfold by averaging + a light Laplacian; hands and feet held), and take the correction back to rest space through
each vertex's measured deformation matrix (three unit test keys - exact for linear blend skinning plus additive keys),
refined by two fixed-point passes.  Stored as shape keys R121_ARM_<s>_<deg> (sideways raise), hats on the humerothoracic
elevation that drive_s1 uses; V2_R121_ARMKEY_MODE=flex then authors R121_FLEX_<s>_<deg> in a forward raise as the residual
on top of them, weighted by the plane of elevation (r121_drives.drive, call after the r57 drives.drive).

usage: python3.13 r121_arm_correctives_blender.py -- <body_v2_r121.blend> <r57src> <out dir>
"""
import json
import math
import os
import sys
from pathlib import Path

import bpy
import bmesh  # noqa: E402  (after bpy)
import numpy as np
from scipy.sparse import csr_matrix

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
SRC, ROOT, OUT = Path(args[0]), Path(args[1]), Path(args[2])
OUT.mkdir(parents=True, exist_ok=True)
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts/anatomy_fit"), str(HERE)]
bpy.ops.wm.open_mainfile(filepath=str(SRC))
import build_original_movement_benchmarks_blender as bench  # noqa: E402
import original_v1_review_candidate_drives as drives  # noqa: E402
import r121_drives  # noqa: E402

ANGLES = [int(a) for a in os.environ.get("V2_R121_ARMKEY_ANGLES", "60,90,120,150").split(",")]
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
me = body.data
n = len(me.vertices)
dg = bpy.context.evaluated_depsgraph_get()
R0 = np.empty(n * 3); me.vertices.foreach_get("co", R0); R0 = R0.reshape(-1, 3)
z0 = float(R0[:, 2].min()); H = float(R0[:, 2].max()) - z0
GN = [g.name for g in body.vertex_groups]
hold_g = {i for i, g in enumerate(GN) if any(k in g for k in ("hand", "thumb", "index", "middle", "ring", "pinky",
                                                            "metacarpal", "foot", "toe", "ball"))}
HOLD = np.zeros(n, bool)
for v in me.vertices:
    HOLD[v.index] = sum(g.weight for g in v.groups if g.group in hold_g) > 0.3
UPPER = ((R0[:, 2] - z0) / H > 0.62) & ~HOLD                  # the corrections stay on the upper body
E = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
A = csr_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n))
Dinv = 1.0 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)
mean = lambda X: (A @ X) * Dinv[:, None]
FA = np.array([p.vertices[:3] for p in me.polygons])          # first three corners: face normal direction
# edge -> its two faces, for the fold test in numpy
ek = {}
for fi, p in enumerate(me.polygons):
    for e_ in p.edge_keys:
        ek.setdefault(e_, []).append(fi)
EF = np.array([(k[0], k[1], f[0], f[1]) for k, f in ek.items() if len(f) == 2])


def folds(P, th=0.0):
    """vertices of edges whose two faces differ by more than acos(th)"""
    a, b, c = P[FA[:, 0]], P[FA[:, 1]], P[FA[:, 2]]
    fn = np.cross(b - a, c - a); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-15)
    d = np.einsum("ij,ij->i", fn[EF[:, 2]], fn[EF[:, 3]])
    bad = EF[d < th]
    m = np.zeros(n, bool); m[bad[:, 0]] = True; m[bad[:, 1]] = True
    return m & UPPER, int((d < th).sum())


def evaluated():
    bpy.context.view_layer.update()
    ev = body.evaluated_get(dg); m_ = ev.to_mesh()
    P = np.empty(n * 3); m_.vertices.foreach_get("co", P); ev.to_mesh_clear()
    return P.reshape(-1, 3)


MODE = os.environ.get("V2_R121_ARMKEY_MODE", "abd")        # abd: sideways raise; flex: forward raise (on top of abd keys)
#                                                            squat: benchmark squat at depth ANGLES / 100 (hip family)
FAMILY = {"abd": (r121_drives.PREFIX, r121_drives.PROP), "flex": (r121_drives.FLEX_PREFIX, r121_drives.FLEX_PROP),
          "squat": (r121_drives.HIP_PREFIX, r121_drives.HIP_PROP),
          "elbow": (r121_drives.ELBOW_PREFIX, r121_drives.ELBOW_PROP)}[MODE]
WGT = {}
for v in me.vertices:
    for g in v.groups:
        WGT.setdefault(GN[g.group], np.zeros(n))[v.index] = g.weight


def gsum(*keys):
    out = np.zeros(n)
    for name, w_ in WGT.items():
        if any(k in name for k in keys):
            out += w_
    return out


CONTACT = None
if MODE == "elbow":                                        # the arm within 16 cm of each elbow; hands held
    wu, wf = gsum("upperarm"), gsum("forearm")
    near = np.zeros(n, bool)
    for s_ in ("l", "r"):
        e_ = np.array(rig.data.bones[f"forearm_{s_}"].head_local)
        near |= np.linalg.norm(R0 - e_, axis=1) < 0.16
    UPPER = near & ((wu + wf) > 0.3) & ~HOLD
    CONTACT = (UPPER & (wu >= wf), UPPER & (wf > wu))      # upper-arm side / forearm side of the elbow
if MODE == "squat":                                        # hips, glutes, groin, lower back - not the knees
    fz = (R0[:, 2] - z0) / H
    arm_g = {i for i, g in enumerate(GN) if any(k in g for k in ("upperarm", "forearm"))}
    ARMV = np.array([sum(g.weight for g in v.groups if g.group in arm_g) > 0.3 for v in me.vertices])
    UPPER = (fz > 0.38) & (fz < 0.66) & ~HOLD & ~ARMV          # the hanging arms stay as they are
    bench._reset(rig)
    REST_HEADS = {s_: rig.pose.bones[f"foot_{s_}"].head.copy() for s_ in ("l", "r")}


def pose(ang):
    if MODE == "elbow":                                    # standing carriage, both elbows flexed
        bench._reset(rig)
        for sd, sg in (("r", -1.0), ("l", 1.0)):
            pb = rig.pose.bones[f"upperarm_{sd}"]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (0.0, 0.0, math.radians(sg * 16.0))
            fb = rig.pose.bones[f"forearm_{sd}"]; fb.rotation_mode = "XYZ"; fb.rotation_euler = (math.radians(-ang), 0.0, 0.0)
        bpy.context.view_layer.update(); drives.drive(rig, body); r121_drives.drive(rig, body); bpy.context.view_layer.update()
        return
    if MODE == "squat":
        bench.pose_squat(rig, ang / 100.0, REST_HEADS)
        bpy.context.view_layer.update(); drives.drive(rig, body); r121_drives.drive(rig, body); bpy.context.view_layer.update()
        return
    bench._reset(rig)
    for sd, sg in (("r", -1.0), ("l", 1.0)):
        pb = rig.pose.bones[f"upperarm_{sd}"]; pb.rotation_mode = "XYZ"
        if MODE == "abd":
            pb.rotation_euler = (0.0, 0.0, math.radians(sg * ang))
        else:                                                   # the local-X sign that moves the elbow forward (-y)
            ys = []
            for sx in (1.0, -1.0):
                pb.rotation_euler = (math.radians(sx * ang), 0.0, 0.0); bpy.context.view_layer.update(); ys.append((pb.tail.y, sx))
            pb.rotation_euler = (math.radians(min(ys)[1] * ang), 0.0, 0.0)
    bpy.context.view_layer.update(); drives.drive(rig, body); r121_drives.drive(rig, body); bpy.context.view_layer.update()


POLYS = [p.vertices[:] for p in me.polygons]


def contact(T, margin=0.0008):
    """hinge contact: the plane through the flexion axis that bisects the joint angle is where the two sides' inner
    skin meets.  Skin of either side that has crossed it, on the inner side of the angle, is flattened onto it (each
    side keeps a small margin on its own side); the flattening is then spread a few rings so the contact face is
    smooth.  In place on T; returns the number of flattened vertices per side."""
    out = {}
    D = np.zeros_like(T)
    for s_ in ("r", "l"):
        side = np.sign(R0[:, 0]) == (1.0 if rig.data.bones[f"upperarm_{s_}"].head_local.x > 0 else -1.0)
        ub, fb = rig.pose.bones[f"upperarm_{s_}"], rig.pose.bones[f"forearm_{s_}"]
        e = np.array(fb.head)
        u = np.array((ub.head - ub.tail).normalized())         # elbow -> shoulder
        f = np.array((fb.tail - fb.head).normalized())         # elbow -> wrist
        if np.dot(u, f) < -0.95:                               # nearly straight: no inner angle
            out[s_] = 0; continue
        b = u + f; b /= np.linalg.norm(b)                      # into the inner angle
        nb = u - f; nb /= np.linalg.norm(nb)                   # plane normal, towards the upper-arm side
        up_side, fo_side = CONTACT[0] & side, CONTACT[1] & side
        r = T - e
        inner = r @ b > 0.0
        h = r @ nb
        cu = up_side & inner & (h < margin)                    # upper-arm skin on the forearm side
        cf = fo_side & inner & (h > -margin)                   # forearm skin on the upper-arm side
        D[cu] += np.outer(margin - h[cu], nb)
        D[cf] += np.outer(-margin - h[cf], nb)
        out[s_] = int(cu.sum() + cf.sum())
    w = (np.linalg.norm(D, axis=1) > 0).astype(float)
    for _ in range(4):                                         # spread so the contact face stays smooth
        D = np.where(w[:, None] > 0, D, mean(D) * UPPER[:, None])
        w = np.maximum(w, ((A @ w) * Dinv > 0) * UPPER)
    T += D
    return out


def set_key(kb, d):
    kb.data.foreach_set("co", (R0 + d).ravel()); me.update()


keys = me.shape_keys.key_blocks
tmp = body.shape_key_add(name="R121_TMP", from_mix=False); tmp.value = 0.0
REP = {"mode": MODE, "angles_deg": ANGLES, "keys": {}}
made = {}
for ang in ANGLES:
    pose(ang)
    measure = {"squat": r121_drives.hip_flex_deg, "elbow": r121_drives.elbow_flex_deg}.get(MODE, drives.elevation_deg)
    elev = {s: round(float(measure(rig, s)), 2) for s in ("l", "r")}
    P = evaluated()
    T = P.copy(); hist = []
    contact_hist = contact(T) if CONTACT is not None else None
    # relax: unfold rounds, then a light Laplacian over the folded area (posed space)
    for rnd in range(int(os.environ.get("V2_R121_ARMKEY_ROUNDS", "8"))):
        m, nf = folds(T); hist.append(nf)
        if nf == 0:
            break
        w = m.astype(float)
        for _ in range(4):
            w = np.maximum(w, ((A @ w) * Dinv > 0).astype(float))
        w *= UPPER
        for _ in range(30):
            T = T + 0.6 * w[:, None] * (mean(T) - T)
    CT = math.cos(math.radians(float(os.environ.get("V2_R121_ARMKEY_CRUMPLE_DEG", "35"))))
    # de-crumple: edges past ~35 deg (below the fold test) read as crumpled skin - HC (shrink-free) over them, dilated
    crum = []
    for rnd in range(int(os.environ.get("V2_R121_ARMKEY_CRUMPLE", "0"))):
        m, nc = folds(T, CT); crum.append(nc)
        w = m.astype(float)
        for _ in range(3):
            w = np.maximum(w, 0.7 * (A @ w) * Dinv)
        w = np.clip(1.5 * w, 0, 1) * UPPER
        O = T.copy(); Q = T.copy()
        for _ in range(20):
            Pm = Q + w[:, None] * (mean(Q) - Q)
            B = Pm - O
            Q = Pm - w[:, None] * (0.6 * B + 0.4 * mean(B))
        T = Q
    crum.append(folds(T, CT)[1])
    m90, n90 = folds(T, 0.0)
    hist.append(n90)
    # deformation matrices: posed response to unit rest offsets through a temporary key (1 mm)
    tmp.value = 1.0
    M = np.zeros((n, 3, 3))
    for j in range(3):
        d = np.zeros((n, 3)); d[:, j] = 1e-3; set_key(tmp, d)
        M[:, :, j] = (evaluated() - P) / 1e-3
    set_key(tmp, np.zeros((n, 3)))
    sel = np.nonzero(np.linalg.norm(T - P, axis=1) > 1e-6)[0]
    Dk = np.zeros((n, 3))
    Dk[sel] = np.linalg.solve(M[sel], (T - P)[sel][:, :, None])[:, :, 0]
    for it in range(2):                                        # fixed-point refinement on the true deformation
        set_key(tmp, Dk); r_ = T - evaluated()
        Dk[sel] += np.linalg.solve(M[sel], r_[sel][:, :, None])[:, :, 0]
    set_key(tmp, Dk); Pk = evaluated(); _, nk = folds(Pk, 0.0)
    resid = float(np.linalg.norm(T - Pk, axis=1).max() * 1000)
    tmp.value = 0.0; set_key(tmp, np.zeros((n, 3)))
    for s, sg in (("r", 1.0), ("l", -1.0)):
        side = (np.sign(R0[:, 0]) == sg)
        kb = body.shape_key_add(name=f"{FAMILY[0]}{s}_{ang}", from_mix=False); kb.value = 0.0
        set_key(kb, Dk * side[:, None])
        made.setdefault(s, []).append(elev[s])
    REP["keys"][str(ang)] = {"elevation_deg": elev, "folds_gt90_before": int(folds(P, 0.0)[1]), "unfold_history": hist, "contact_history": contact_hist, "crumple_gt35_history": crum,
                             "folds_gt90_with_key": nk, "max_offset_mm": round(float(np.linalg.norm(Dk, axis=1).max() * 1000), 2),
                             "vertices": int(len(sel)), "fit_residual_max_mm": round(resid, 3)}
    print("ARMKEY", ang, json.dumps(REP["keys"][str(ang)]), flush=True)
body.shape_key_remove(tmp)
for s in ("l", "r"):
    rig[f"{FAMILY[1]}_{s}"] = made[s]
bench._reset(rig)
for kb in me.shape_keys.key_blocks:
    if kb.name.startswith(("R121_ARM_", "R121_FLEX_", "R121_HIP_", "R121_ELBOW_")):
        kb.value = 0.0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "body_v2_r121_arms.blend"), copy=True)
(OUT / f"r121_arm_correctives_{MODE}_report.json").write_text(json.dumps(REP, indent=1))
print("R121_ARMKEYS done", flush=True)
