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
#                                                            hinge: benchmark deadlift at ANGLES / 100, APPENDED to the
#                                                            hip family (deeper hip flexion than the squat reaches); keys
#                                                            are named by their measured hip angle
FAMILY = {"abd": (r121_drives.PREFIX, r121_drives.PROP), "flex": (r121_drives.FLEX_PREFIX, r121_drives.FLEX_PROP),
          "squat": (r121_drives.HIP_PREFIX, r121_drives.HIP_PROP), "hinge": (r121_drives.HIP_PREFIX, r121_drives.HIP_PROP),
          "elbow": (r121_drives.ELBOW_PREFIX, r121_drives.ELBOW_PROP),
          "knee": (r121_drives.KNEE_PREFIX, r121_drives.KNEE_PROP),
          "combo": (r121_drives.COMBO_PREFIX, r121_drives.COMBO_PROP)}[MODE]
HINGE = {"elbow": ("upperarm", "forearm", float(os.environ.get("V2_R121_HINGE_REACH", "0.16"))),
         "knee": ("thigh", "shin", float(os.environ.get("V2_R121_HINGE_REACH", "0.18"))),   # upper bone, lower bone, reach (m)
         # hip (hinge mode, V2_R121_HIP_CONTACT=1): the trunk side is the pelvis / spine-weighted skin, its axis runs from
         # the hip joint up to the posed spine_02; abdomen and thigh meet on the bisecting plane
         **({"hinge": (("pelvis", "spine", "hip_crease"), "thigh", float(os.environ.get("V2_R121_HINGE_REACH", "0.26")))}
            if os.environ.get("V2_R121_HIP_CONTACT") == "1" else {})}
if os.environ.get("V2_R121_ARMKEY_REPLACE") == "1":         # re-author: drop this family's keys and drive data first
    for kb in [k for k in me.shape_keys.key_blocks if k.name.startswith(FAMILY[0])]:
        body.shape_key_remove(kb)
    for s_ in ("l", "r"):
        if f"{FAMILY[1]}_{s_}" in rig:
            del rig[f"{FAMILY[1]}_{s_}"]
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
ARMGIRDLE = os.environ.get("V2_R121_ARMKEY_GIRDLE", "0") == "1"   # author abd / flex keys with the candidate girdle
if MODE in HINGE:                                           # the limb within reach of each hinge; hands / feet held
    ub_, lb_, reach = HINGE[MODE]
    wu, wf = (gsum(*ub_) if isinstance(ub_, tuple) else gsum(ub_)), gsum(lb_)
    near = np.zeros(n, bool)
    for s_ in ("l", "r"):
        e_ = np.array(rig.data.bones[f"{lb_}_{s_}"].head_local)
        near |= np.linalg.norm(R0 - e_, axis=1) < reach
    UPPER = near & ((wu + wf) > 0.3) & ~HOLD
    CONTACT = (UPPER & (wu >= wf), UPPER & (wf > wu))      # proximal side / distal side of the hinge
if MODE == "combo":                                         # press rack: the arm and the elbow region
    near = np.zeros(n, bool)
    for s_ in ("l", "r"):
        e_ = np.array(rig.data.bones[f"forearm_{s_}"].head_local)
        near |= np.linalg.norm(R0 - e_, axis=1) < 0.18
    UPPER = near & ((gsum("upperarm") + gsum("forearm")) > 0.3) & ~HOLD
    import build_functional_shoulder_correction_blender as correction
    import functional_shoulder_correction as corr
    RA = {}
    for side_, name_ in correction.HUMERI:
        b_ = rig.data.bones[name_]
        RA[name_] = corr.humeral_axial_angle_deg(tuple(b_.tail_local - b_.head_local), tuple(b_.matrix_local.col[0].xyz), 40.0, side_)
    COMBO_ELBOW = float(os.environ.get("V2_R121_COMBO_ELBOW", "90"))
if MODE == "knee":
    bench._reset(rig)
    REST_HEADS = {s_: rig.pose.bones[f"foot_{s_}"].head.copy() for s_ in ("l", "r")}
if MODE in ("squat", "hinge"):                             # hips, glutes, groin, lower back - not the knees
    fz = (R0[:, 2] - z0) / H
    arm_g = {i for i, g in enumerate(GN) if any(k in g for k in ("upperarm", "forearm"))}
    ARMV = np.array([sum(g.weight for g in v.groups if g.group in arm_g) > 0.3 for v in me.vertices])
    UPPER = (fz > 0.38) & (fz < 0.66) & ~HOLD & ~ARMV          # the hanging arms stay as they are
    bench._reset(rig)
    REST_HEADS = {s_: rig.pose.bones[f"foot_{s_}"].head.copy() for s_ in ("l", "r")}


def pose(ang):
    if MODE == "combo":                                    # press rack: girdle + humerus (press plane) + elbow
        import shoulder_girdle_candidate as girdle
        girdle.apply_press_pose(rig, float(ang), RA)
        for sd in ("r", "l"):
            fb = rig.pose.bones[f"forearm_{sd}"]; fb.rotation_mode = "XYZ"; fb.rotation_euler = (math.radians(-COMBO_ELBOW), 0.0, 0.0)
        bpy.context.view_layer.update(); drives.drive(rig, body); r121_drives.drive(rig, body); bpy.context.view_layer.update()
        return
    if MODE == "elbow":                                    # standing carriage, both elbows flexed
        bench._reset(rig)
        for sd, sg in (("r", -1.0), ("l", 1.0)):
            pb = rig.pose.bones[f"upperarm_{sd}"]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (0.0, 0.0, math.radians(sg * 16.0))
            fb = rig.pose.bones[f"forearm_{sd}"]; fb.rotation_mode = "XYZ"; fb.rotation_euler = (math.radians(-ang), 0.0, 0.0)
        bpy.context.view_layer.update(); drives.drive(rig, body); r121_drives.drive(rig, body); bpy.context.view_layer.update()
        return
    if MODE == "hinge":
        bench.pose_deadlift(rig, ang / 100.0, REST_HEADS)
        bpy.context.view_layer.update(); drives.drive(rig, body); r121_drives.drive(rig, body); bpy.context.view_layer.update()
        return
    if MODE in ("squat", "knee"):
        bench.pose_squat(rig, ang / 100.0, REST_HEADS)
        bpy.context.view_layer.update(); drives.drive(rig, body); r121_drives.drive(rig, body); bpy.context.view_layer.update()
        return
    if ARMGIRDLE:                                           # coupled girdle + humerus in the frontal / sagittal plane
        import shoulder_girdle_candidate as girdle
        girdle.apply_arm_pose(rig, float(ang), 0.0 if MODE == "abd" else 90.0)
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


BULGE = float(os.environ.get("V2_R121_CONTACT_BULGE", "0"))   # sideways bulge per unit flattening depth
SOFT = float(os.environ.get("V2_R121_CONTACT_SOFT", "0"))     # width (m) of the rounded lip band beside the contact face
FOOT = float(os.environ.get("V2_R121_CONTACT_FOOTPRINT", "0"))  # >0: flatten only inside the other side's footprint (tol m)
FOOT_SLAB = float(os.environ.get("V2_R121_CONTACT_FOOTPRINT_SLAB", "0.004"))  # footprint = other side's skin this near the plane


def contact(T, margin=0.0008):
    """hinge contact: the plane through the flexion axis that bisects the joint angle is where the two sides' inner
    skin meets.  Skin of either side that has crossed it, on the inner side of the angle, is flattened onto it (each
    side keeps a small margin on its own side); the flattening is then spread a few rings so the contact face is
    smooth.  In place on T; returns the number of flattened vertices per side."""
    out = {}
    D = np.zeros_like(T)
    for s_ in ("r", "l"):
        ubn, lbn = HINGE[MODE][:2]
        side = np.sign(R0[:, 0]) == (1.0 if rig.data.bones[f"{lbn}_{s_}"].head_local.x > 0 else -1.0)
        fb = rig.pose.bones[f"{lbn}_{s_}"]
        e = np.array(fb.head)
        if isinstance(ubn, tuple):                             # hip: hinge axis from the joint up the trunk
            u = np.array(rig.pose.bones["spine_02"].head) - e; u /= np.linalg.norm(u)
        else:
            ub = rig.pose.bones[f"{ubn}_{s_}"]
            u = np.array((ub.head - ub.tail).normalized())     # elbow -> shoulder
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
        if FOOT > 0 and cu.any() and cf.any():                 # mutual footprint: each side is flattened only where
            from scipy.spatial import cKDTree                  # the other side actually reaches the plane, so the
            hx_ = np.array(fb.x_axis.normalized())             # wider biceps is not cut flat beyond the forearm
            uv = np.c_[r @ hx_, r @ b]
            near_u = up_side & inner & (h < margin + FOOT_SLAB)
            near_f = fo_side & inner & (h > -margin - FOOT_SLAB)
            du, _ = cKDTree(uv[near_f]).query(uv[cu])
            df, _ = cKDTree(uv[near_u]).query(uv[cf])
            cu[np.flatnonzero(cu)[du > FOOT]] = False
            cf[np.flatnonzero(cf)[df > FOOT]] = False
        D[cu] += np.outer(margin - h[cu], nb)
        D[cf] += np.outer(-margin - h[cf], nb)
        if SOFT > 0:                                           # rounded lips: skin within SOFT of the plane is drawn
            for sm, sg in ((up_side, 1.0), (fo_side, -1.0)):   # towards it, tangent at the plane -> a tight crease
                g = sg * h - margin                            # distance outside the contact face (on its own side)
                lip = sm & inner & (g > 0) & (g < SOFT)
                t = g[lip] / SOFT
                D[lip] += np.outer(-sg * g[lip] * (1.0 - t) ** 2, nb)
        if BULGE > 0:                                          # displaced tissue bulges out at the contact's edges
            hx = np.array(fb.x_axis.normalized())              # hinge (flexion) axis
            ex_ = r @ hx                                       # signed distance from the limb's mid-plane
            half = max(float(np.percentile(np.abs(ex_[cu | cf]), 95)), 1e-3) if (cu | cf).any() else 1.0
            for cm, hh in ((cu, h), (cf, h)):
                depth = np.abs(hh[cm]) + margin
                k = BULGE * depth * np.clip(np.abs(ex_[cm]) / half, 0, 1) ** 2
                D[cm] += np.outer(k * np.sign(ex_[cm]), hx)
        out[s_] = int(cu.sum() + cf.sum())
    w = (np.linalg.norm(D, axis=1) > 0).astype(float)
    for _ in range(4):                                         # spread so the contact face stays smooth
        D = np.where(w[:, None] > 0, D, mean(D) * UPPER[:, None])
        w = np.maximum(w, ((A @ w) * Dinv > 0) * UPPER)
    T += D
    return out


CMODE = os.environ.get("V2_R121_CONTACT_MODE", "plane")    # plane: contact() above; mutual / plane_restore: below
TRI = np.array([(p.vertices[0], p.vertices[k], p.vertices[k + 1]) for p in me.polygons for k in range(1, len(p.vertices) - 1)])


def contact_mutual(T, margin=0.0008, iters=int(os.environ.get("V2_R121_CONTACT_ITERS", "6")),
                   rest_sep=float(os.environ.get("V2_R121_CONTACT_REST_SEP", "0.025"))):
    """hinge contact without a plane: skin of either side that lies INSIDE the other side's skin (signed by the normal
    of the nearest face of the other side) moves out by half the depth plus a margin, along that normal, so the two
    meet on a curved interface and nothing outside the overlap is touched (the plane version flattens each side onto
    the bisecting plane, which cuts the wider biceps flat beyond the forearm and leaves a straight crease edge).  Pairs
    closer than rest_sep at REST are the continuous skin across the crease, not contact, and are ignored.  Iterated,
    then spread a few rings as in contact().  In place on T; returns the number of moved vertices per side."""
    from mathutils import Vector as V_
    from mathutils.bvhtree import BVHTree
    out = {}
    D = np.zeros_like(T)
    for s_ in ("r", "l"):
        lbn = HINGE[MODE][1]
        side = np.sign(R0[:, 0]) == (1.0 if rig.data.bones[f"{lbn}_{s_}"].head_local.x > 0 else -1.0)
        sides = (CONTACT[0] & side, CONTACT[1] & side)
        tris = [TRI[sm[TRI].all(1)] for sm in sides]
        moved = np.zeros(n, bool)
        for _ in range(iters):
            P_ = T + D
            step = np.zeros_like(T)
            for a_, b_ in ((0, 1), (1, 0)):                 # vertices of side a against the surface of side b
                tb = tris[b_]
                if not len(tb) or not sides[a_].any():
                    continue
                bvh = BVHTree.FromPolygons([V_(p) for p in P_], tb.tolist(), all_triangles=True)
                for i in np.flatnonzero(sides[a_]):
                    hit = bvh.find_nearest(V_(P_[i]), 0.04)
                    if hit[0] is None:
                        continue
                    nrm = np.array(hit[1]); dep = float(np.dot(P_[i] - np.array(hit[0]), nrm))
                    if dep >= margin or (hit[3] > 1e-4 and dep > -0.7 * hit[3]):
                        continue                            # outside, or off the patch edge (offset not along the normal)
                    f_ = tb[hit[2]]
                    if np.linalg.norm(R0[f_] - R0[i], axis=1).min() < rest_sep:
                        continue                            # the same skin across the crease
                    step[i] = nrm * (0.5 * (margin - dep))
                    moved[i] = True
            if not np.abs(step).any():
                break
            D += step
        out[s_] = int(moved.sum())
    w = (np.linalg.norm(D, axis=1) > 0).astype(float)
    for _ in range(4):                                         # spread so the contact face stays smooth
        D = np.where(w[:, None] > 0, D, mean(D) * UPPER[:, None])
        w = np.maximum(w, ((A @ w) * Dinv > 0) * UPPER)
    T += D
    return out


POSTGUARD = {}


def post_guard(T):
    """after the unfold / de-crumple relaxation (which shrinks the restored, rounded proximal skin back towards the
    distal limb - measured at 140 deg): proximal vertices of any proximal triangle that overlaps the distal limb, and
    one ring, take their contact-flattened position again.  With V2_R121_POSTGUARD_ROUNDS > 1 the border of the
    snapped skin is then blended (4 rings, snapped vertices held) and checked again (snapping alone left seams: curl
    folds 7 -> 80 at 140 deg).  In place on T; returns the overlap counts per round."""
    hist = []
    if not POSTGUARD:
        return hist
    tp, td, prox, flat = POSTGUARD["tp"], POSTGUARD["td"], POSTGUARD["prox"], POSTGUARD["flat"]
    done = np.zeros(n, bool)
    rounds = int(os.environ.get("V2_R121_POSTGUARD_ROUNDS", "1"))
    for r_ in range(rounds):
        hist.append(_post_snap(T, tp, td, prox, flat, done))
        if (r_ > 0 and hist[-1][0] == 0) or not done.any() or r_ == rounds - 1:
            break                                           # clean after blending / nothing snapped / last round
        band = done.astype(float)                           # blend the border of the snapped skin (snapped vertices
        for _k in range(4):                                 # held), then check again
            band = np.maximum(band, ((A @ band) * Dinv > 0).astype(float))
        band = (band > 0) & ~done & UPPER
        for _k in range(20):
            T[band] += 0.5 * (mean(T)[band] - T[band])
    return hist


def _post_snap(T, tp, td, prox, flat, done):
    from mathutils import Vector as V_
    from mathutils.bvhtree import BVHTree
    hist = []
    for _ in range(8):
        ba = BVHTree.FromPolygons([V_(p) for p in T], tp.tolist(), all_triangles=True)
        bb = BVHTree.FromPolygons([V_(p) for p in T], td.tolist(), all_triangles=True)
        ov = np.array(ba.overlap(bb), dtype=np.int64).reshape(-1, 2)
        hist.append(int(len(ov)))
        if not len(ov):
            break
        bad = np.zeros(n, bool); bad[tp[ov[:, 0]].ravel()] = True
        bad = (bad | ((A @ bad.astype(float)) > 0)) & prox & ~done
        if not bad.any():
            break
        T[bad] = flat[bad]; done |= bad
    return hist


def contact_plane_restore(T, margin=0.0008, rest_sep=float(os.environ.get("V2_R121_CONTACT_REST_SEP", "0.025"))):
    """plane contact (robust where the limbs overlap deeply), then every proximal-side vertex it moved goes back towards where it was
    by the largest fraction (1, 3/4, 1/2, 1/4) that keeps it outside the other side's (contacted) skin - so the flat
    face shrinks to where the other limb really touches, and the biceps stays round beyond the forearm.  The restore
    fractions are eroded over two rings (never raised), so restored and contacted skin blend.  In place on T."""
    from mathutils import Vector as V_
    from mathutils.bvhtree import BVHTree
    T0 = T.copy()
    out = contact(T)
    moved = np.linalg.norm(T - T0, axis=1) > 1e-7
    t = np.zeros(n)
    distal = gsum(*(("forearm", "hand", "thumb", "index", "middle", "ring", "pinky", "metacarpal") if MODE == "elbow"
                    else ("shin", "foot", "toe", "ball"))) > 0.5
    for s_ in ("r", "l"):
        lbn = HINGE[MODE][1]
        side = np.sign(R0[:, 0]) == (1.0 if rig.data.bones[f"{lbn}_{s_}"].head_local.x > 0 else -1.0)
        sides = (CONTACT[0] & side, distal & side)          # obstacle: the WHOLE distal limb (at 140 deg the wrist
        tris = [TRI[sm[TRI].all(1)] for sm in sides]        # reaches the upper biceps, beyond the contact reach)
        for a_, b_ in ((0, 1),):                           # the proximal side only: restoring both sides against
            tb = tris[b_]                                   # each other's flattened state let them overlap again
            if not len(tb):                                 # (measured); the narrower distal side stays covered
                continue
            bvh = BVHTree.FromPolygons([V_(p) for p in T], tb.tolist(), all_triangles=True)
            for i in np.flatnonzero(sides[a_] & moved):
                for f_ in (1.0, 0.75, 0.5, 0.25):
                    x = T[i] + f_ * (T0[i] - T[i])
                    hit = bvh.find_nearest(V_(x), 0.04)
                    if hit[0] is not None:
                        dep = float(np.dot(x - np.array(hit[0]), np.array(hit[1])))
                        tri_ = tb[hit[2]]
                        if (dep < margin and np.linalg.norm(R0[tri_] - R0[i], axis=1).min() >= rest_sep
                                and not (hit[3] > 1e-4 and dep > -0.7 * hit[3])):
                            continue                        # still inside the other side: try a smaller fraction
                    t[i] = f_
                    break
    for _ in range(2):                                         # erode: restored skin next to contact skin blends
        tt = np.where(moved, t, 1.0)                           # (skin the contact never moved counts as restored)
        t = np.where(moved, np.minimum(t, (A @ tt) * Dinv), t)
    # triangle guard: a vertex test misses triangles that join restored and flattened skin and cut through the side
    # wall of the distal limb (measured at 140 deg: upper biceps through the wrist end of the forearm).  Proximal
    # vertices of any proximal triangle that overlaps the distal limb (and one ring) go back to fully flattened.
    prox_all = np.zeros(n, bool); dist_all = np.zeros(n, bool)
    for s_ in ("r", "l"):
        lbn = HINGE[MODE][1]
        side = np.sign(R0[:, 0]) == (1.0 if rig.data.bones[f"{lbn}_{s_}"].head_local.x > 0 else -1.0)
        prox_all |= CONTACT[0] & side; dist_all |= distal & side
    tp = TRI[prox_all[TRI].any(1) & ~dist_all[TRI].any(1)]; td = TRI[dist_all[TRI].all(1)]
    guard = []
    for _ in range(6):
        X_ = T + t[:, None] * (T0 - T)
        ba = BVHTree.FromPolygons([V_(p) for p in X_], tp.tolist(), all_triangles=True)
        bb = BVHTree.FromPolygons([V_(p) for p in X_], td.tolist(), all_triangles=True)
        ov = np.array(ba.overlap(bb), dtype=np.int64).reshape(-1, 2)
        guard.append(int(len(ov)))
        if not len(ov):
            break
        bad = np.zeros(n, bool); bad[tp[ov[:, 0]].ravel()] = True
        bad = (bad | ((A @ bad.astype(float)) > 0)) & moved & prox_all
        if not (t[bad] > 0).any():
            break
        t[bad] = 0.0
    POSTGUARD.update(flat=T.copy(), tp=tp, td=td, prox=prox_all & moved)   # for post_guard() after the relaxation
    T += t[:, None] * (T0 - T)
    return {"contact": out, "moved": int(moved.sum()), "triangle_guard_overlaps": guard, "restored_full": int(((t > 0.99) & moved).sum()),
            "restored_part": int(((t > 0) & (t <= 0.99) & moved).sum()), "kept": int(((t == 0) & moved).sum())}


def set_key(kb, d):
    kb.data.foreach_set("co", (R0 + d).ravel()); me.update()


keys = me.shape_keys.key_blocks
tmp = body.shape_key_add(name="R121_TMP", from_mix=False); tmp.value = 0.0
if MODE == "flex" and min(ANGLES) <= r121_drives.START:   # a low forward key needs the family's own, lower start
    rig[r121_drives.FLEX_START_PROP] = float(os.environ.get("V2_R121_FLEX_START", "0"))   # set before authoring
REP = {"mode": MODE, "angles_deg": ANGLES, "keys": {}}
made = {}
if MODE == "hinge":                                        # append to the existing hip family
    made = {s_: list(rig.get(f"{FAMILY[1]}_{s_}", [])) for s_ in ("l", "r")}
    above = float(os.environ.get("V2_R121_HINGE_DROP_ABOVE", "1e9"))   # re-author: drop appended keys past this angle
    for s_ in ("l", "r"):
        names_ = sorted((kb.name for kb in me.shape_keys.key_blocks if kb.name.startswith(f"{FAMILY[0]}{s_}_")),
                        key=lambda n_: int(n_.rsplit("_", 1)[1]))
        keep = [i for i, a_ in enumerate(made[s_]) if a_ <= above]
        for i, nm in enumerate(names_):
            if i not in keep:
                body.shape_key_remove(me.shape_keys.key_blocks[nm])
        made[s_] = [made[s_][i] for i in keep]
        rig[f"{FAMILY[1]}_{s_}"] = made[s_]
for ang in ANGLES:
    pose(ang)
    measure = {"squat": r121_drives.hip_flex_deg, "hinge": r121_drives.hip_flex_deg, "elbow": r121_drives.elbow_flex_deg,
               "knee": r121_drives.knee_flex_deg}.get(MODE, drives.elevation_deg)
    elev = {s: round(float(measure(rig, s)), 2) for s in ("l", "r")}
    P = evaluated()
    T = P.copy(); hist = []
    contact_hist = ({"mutual": contact_mutual, "plane_restore": contact_plane_restore}.get(CMODE, contact)(T)
                    if CONTACT is not None else None)
    # relax: unfold rounds, then a light Laplacian over the folded area (posed space).  V2_R121_ARMKEY_UNFOLD_DEG < 90
    # also flattens broad creases (the shape-preserving de-crumple below keeps them), e.g. the lower-back fold the
    # skinning makes at the squat bottom
    UT = math.cos(math.radians(float(os.environ.get("V2_R121_ARMKEY_UNFOLD_DEG", "90"))))   # unfold edges past this
    for rnd in range(int(os.environ.get("V2_R121_ARMKEY_ROUNDS", "8"))):
        m, nf = folds(T, UT); hist.append(nf)
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
    postguard_hist = post_guard(T) if (CMODE == "plane_restore" and CONTACT is not None) else None
    # skin slide (optional): tangential relaxation - vertices move only within the surface, which keeps the shape and
    # evens out the stretch the skinning concentrates (armpit / lat skin at full elevation)
    SL = int(os.environ.get("V2_R121_ARMKEY_SLIDE", "0"))
    if SL > 0:
        ws = UPPER.astype(float)
        for _ in range(SL):
            a_, b_, c_ = T[FA[:, 0]], T[FA[:, 1]], T[FA[:, 2]]
            fn_ = np.cross(b_ - a_, c_ - a_)
            vn = np.zeros_like(T)
            for k_ in range(3):
                np.add.at(vn, FA[:, k_], fn_)
            vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-15)
            L_ = mean(T) - T
            L_ -= np.einsum("ij,ij->i", L_, vn)[:, None] * vn
            T = T + 0.5 * ws[:, None] * L_
    # stretch relief (optional): tangential springs towards the REST edge lengths - unlike the Laplacian slide above,
    # this evens out edge length, not vertex spacing, so the stretch the skinning piles into the armpit at the lockout
    # is shared with the surrounding skin; vertices move only within the surface (shape kept)
    SR = int(os.environ.get("V2_R121_ARMKEY_STRETCH", "0"))
    if SR > 0:
        L0 = np.linalg.norm(R0[E[:, 0]] - R0[E[:, 1]], axis=1)
        ws = UPPER.astype(float)
        for _ in range(SR):
            a_, b_, c_ = T[FA[:, 0]], T[FA[:, 1]], T[FA[:, 2]]
            fn_ = np.cross(b_ - a_, c_ - a_)
            vn = np.zeros_like(T)
            for k_ in range(3):
                np.add.at(vn, FA[:, k_], fn_)
            vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-15)
            ev = T[E[:, 1]] - T[E[:, 0]]; el = np.maximum(np.linalg.norm(ev, axis=1), 1e-12)
            f = ((el - L0) / el)[:, None] * ev                 # pulls the two ends together when stretched
            F = np.zeros_like(T)
            np.add.at(F, E[:, 0], f); np.add.at(F, E[:, 1], -f)
            F *= Dinv[:, None]
            F -= np.einsum("ij,ij->i", F, vn)[:, None] * vn
            T = T + 0.4 * ws[:, None] * F
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
        kname = f"{FAMILY[0]}{s}" if MODE == "combo" else f"{FAMILY[0]}{s}_{int(round(elev[s])) if MODE == 'hinge' else ang}"
        kb = body.shape_key_add(name=kname, from_mix=False); kb.value = 0.0
        set_key(kb, Dk * side[:, None])
        made.setdefault(s, []).append(elev[s] if MODE != "combo" else
                                      [float(drives.elevation_deg(rig, s)), float(r121_drives.elbow_flex_deg(rig, s))])
    REP["keys"][str(ang)] = {"elevation_deg": elev, "folds_gt90_before": int(folds(P, 0.0)[1]), "unfold_history": hist, "contact_history": contact_hist, "post_guard_overlaps": postguard_hist, "crumple_gt35_history": crum,
                             "folds_gt90_with_key": nk, "max_offset_mm": round(float(np.linalg.norm(Dk, axis=1).max() * 1000), 2),
                             "vertices": int(len(sel)), "fit_residual_max_mm": round(resid, 3)}
    print("ARMKEY", ang, json.dumps(REP["keys"][str(ang)]), flush=True)
body.shape_key_remove(tmp)
if MODE == "hinge":
    # each appended key was authored with the family's earlier keys at their OLD hat values (the last one fully on
    # beyond its angle); once appended, those earlier keys fade out towards the new angle.  Fold what they lose at the
    # new key's angle into the new key, so the family reproduces the authored pose exactly.
    for s in ("l", "r"):
        names = sorted((kb.name for kb in me.shape_keys.key_blocks if kb.name.startswith(f"{FAMILY[0]}{s}_")),
                       key=lambda n_: int(n_.rsplit("_", 1)[1]))
        old_pts = (r121_drives.HIP_START,) + tuple(rig.get(f"{FAMILY[1]}_{s}", []))
        new_pts = (r121_drives.HIP_START,) + tuple(made[s])
        n_old = len(old_pts) - 1
        for k_new in range(n_old, len(made[s])):
            a_new = made[s][k_new]
            before = dict(r121_drives._hats(names[:n_old], old_pts[:n_old + 1], a_new))
            after = dict(r121_drives._hats(names, new_pts, a_new))
            kn = me.shape_keys.key_blocks[names[k_new]]
            c = np.empty(n * 3); kn.data.foreach_get("co", c); c = c.reshape(-1, 3)
            for nm, v0 in before.items():
                dv = v0 - after.get(nm, 0.0)
                if abs(dv) > 1e-6:
                    o = np.empty(n * 3); me.shape_keys.key_blocks[nm].data.foreach_get("co", o)
                    c += dv * (o.reshape(-1, 3) - R0)
            kn.data.foreach_set("co", c.ravel())
            REP.setdefault("folded_in", {})[names[k_new]] = {nm: round(v0 - after.get(nm, 0.0), 3) for nm, v0 in before.items()}
for s in ("l", "r"):
    rig[f"{FAMILY[1]}_{s}"] = made[s][0] if MODE == "combo" else made[s]
bench._reset(rig)
for kb in me.shape_keys.key_blocks:
    if kb.name.startswith(("R121_ARM_", "R121_FLEX_", "R121_HIP_", "R121_ELBOW_", "R121_KNEE_", "R121_COMBO_", "R121_REST_")):
        kb.value = 0.0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "body_v2_r121_arms.blend"), copy=True)
(OUT / f"r121_arm_correctives_{MODE}_report.json").write_text(json.dumps(REP, indent=1))
print("R121_ARMKEYS done", flush=True)
