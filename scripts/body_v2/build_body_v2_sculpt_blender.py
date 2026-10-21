"""Body v2: muscle definition on the ORIGINAL_v1 R41 body (Claude, 21 Oct 2026).  Review candidate only.

Owner (21 Oct), after full-body renders of the current model: "I think the muscles need better definition so I will send
you an example to follow", then a 7-view reference set (front, back, side, both three-quarters, arms raised front/back,
close-ups of back / shoulder / armpit) of a lean athletic male - "Start now please".

Same mesh (21600 vertices, same topology), same skeleton and skin weights: only the rest surface changes.  Every muscle
is a smooth normal-direction swelling anchored to the skeleton:
  * limb muscles: along the bone (head -> tail, a bump over [t0, t1] peaking at tp), on the side the muscle faces
    (angle between the vertex normal, projected off the bone axis, and the muscle's facing direction, half-width hw);
    masked by that bone's skin weight so it never pushes neighbouring parts;
  * torso muscles: ellipsoids (centre, radii) facing a direction, masked off the arms.
Right side authored, left side mirrored (exact bilateral symmetry).  The summed field is relaxed on the surface so
bellies blend into each other and the separations between them stay as soft grooves.

  blender python: build_body_v2_sculpt_blender.py -- <R57 root> <out dir> [gain]
Writes <out>/body_v2_offsets.npz (rest-space offsets, float32) and <out>/body_v2_report.json; with R76_RENDER=1 also
standing renders (front / front34 / side / back34 / back) as <out>/V2_full_standing_<view>.png.
"""
import json
import math
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
ROOT = Path(args[0]).resolve(); OUT = Path(args[1]); OUT.mkdir(parents=True, exist_ok=True)
GAIN = float(args[2]) if len(args) > 2 else 1.0
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts/anatomy_fit")]
import build_original_review_candidate_r17_blender as r17

res = r17._setup(ROOT / "ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend")
body, rig = res["body"], res["runtime"]
me = body.data
nv = len(me.vertices)
rest = np.array([v.co[:] for v in me.vertices])
nrm = np.array([v.normal[:] for v in me.vertices])
faces = np.array([p.vertices[:] for p in me.polygons])
gidx = {g.name: g.index for g in body.vertex_groups}
W = {}
for v in me.vertices:
    for g in v.groups:
        W.setdefault(g.group, np.zeros(nv))[v.index] = g.weight


def gw(*names):
    out = np.zeros(nv)
    for n in names:
        if n in gidx and gidx[n] in W:
            out += W[gidx[n]]
    return np.clip(out, 0, 1)


def ss(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def bone(name):
    b = rig.data.bones[name]; return np.array(b.head_local), np.array(b.tail_local)


# ---- muscle specification (right side; rest coordinates: +x lateral right, -y front, +y back, +z up; metres, mm) ----
LIMB = [  # bone, t0, tp, t1, facing, half-width deg, amp mm, mask groups
    ("upperarm", 0.12, 0.58, 0.90, (0, -1, 0), 75, 11.0, ("upperarm",)),         # biceps
    ("upperarm", 0.04, 0.35, 0.82, (0.3, 1, 0), 80, 11.0, ("upperarm",)),        # triceps (long + lateral heads)
    ("upperarm", 0.45, 0.75, 0.98, (1, -0.4, 0), 55, 4.0, ("upperarm",)),        # brachialis, lateral
    ("upperarm", 0.00, 0.50, 1.00, (1, 0, 0), 180, 2.5, ("upperarm",)),          # overall arm thickness
    ("forearm", 0.00, 0.22, 0.65, (1, -0.3, 0), 70, 7.0, ("forearm", "forearm_tw0", "forearm_tw1")),   # brachioradialis / extensors
    ("forearm", 0.00, 0.25, 0.62, (-0.6, -0.8, 0), 70, 6.0, ("forearm", "forearm_tw0", "forearm_tw1")),  # flexors
    ("forearm", 0.00, 0.30, 0.80, (1, 0, 0), 180, 2.0, ("forearm", "forearm_tw0", "forearm_tw1")),
    ("thigh", 0.30, 0.62, 0.97, (0, -1, 0), 60, 8.0, ("thigh",)),                # rectus femoris (R76d: mid-thigh)
    ("thigh", 0.25, 0.60, 0.95, (1, -0.4, 0), 55, 8.0, ("thigh",)),              # vastus lateralis (R76c: lower, no hip bulge)
    ("thigh", 0.55, 0.85, 1.00, (-0.7, -0.7, 0), 45, 9.0, ("thigh",)),           # vastus medialis (teardrop)
    ("thigh", 0.22, 0.50, 0.88, (0, 1, 0), 70, 8.0, ("thigh",)),                 # hamstrings
    ("thigh", 0.20, 0.40, 0.70, (-1, 0, 0), 60, 2.0, ("thigh",)),                # adductors
    ("thigh", 0.20, 0.60, 1.00, (1, 0, 0), 180, 2.0, ("thigh",)),
    ("shin", 0.06, 0.26, 0.62, (-0.45, 1, 0), 55, 9.0, ("shin",)),               # gastrocnemius medial head (R76f: not sticking out)
    ("shin", 0.06, 0.24, 0.55, (0.5, 1, 0), 50, 7.0, ("shin",)),                 # gastrocnemius lateral head
    ("shin", 0.10, 0.35, 0.70, (0.6, -0.8, 0), 45, 4.0, ("shin",)),              # tibialis anterior
    ("shin", 0.00, 0.40, 0.85, (1, 0, 0), 180, 2.0, ("shin",)),
]
BLOB = [  # centre, radii (x,y,z), facing, min facing dot, amp mm, mask ("torso" = off the arms, "arm" = upper arm/shoulder)
    ((0.262, 0.030, 1.420), (0.055, 0.075, 0.085), (1, 0, 0.35), -0.3, 10.0, "shoulder"),   # deltoid (lateral; R76h: shoulders already 0.332 H vs reference 0.300)
    ((0.240, -0.035, 1.415), (0.045, 0.045, 0.075), (0.5, -1, 0.2), -0.1, 7.0, "shoulder"),  # anterior deltoid
    ((0.240, 0.095, 1.415), (0.045, 0.045, 0.075), (0.5, 1, 0.2), -0.1, 7.0, "shoulder"),    # posterior deltoid
    ((0.095, -0.112, 1.365), (0.095, 0.060, 0.075), (0, -1, 0.15), 0.25, 13.0, "torso"),     # pectoralis major
    ((0.160, -0.080, 1.395), (0.050, 0.050, 0.055), (0.6, -1, 0.1), 0.1, 6.0, "torso"),      # pec into the armpit
    ((0.150, 0.075, 1.320), (0.055, 0.085, 0.120), (1, 0.7, 0), 0.0, 12.0, "torso"),         # latissimus (V taper, high under the armpit)
    ((0.130, -0.055, 1.150), (0.055, 0.060, 0.090), (1, -0.6, 0), 0.0, 5.0, "torso"),        # serratus / obliques
    ((0.120, -0.040, 1.010), (0.050, 0.060, 0.070), (1, -0.5, 0), 0.0, 4.0, "torso"),        # external oblique, lower
    ((0.085, 0.060, 1.530), (0.075, 0.065, 0.055), (0.3, 0.5, 0.8), 0.0, 10.0, "torso"),     # upper trapezius
    ((0.090, 0.145, 1.405), (0.075, 0.045, 0.085), (0.2, 1, 0), 0.2, 6.0, "torso"),          # middle trapezius / rhomboid
    ((0.140, 0.135, 1.380), (0.055, 0.050, 0.060), (0.6, 1, 0), 0.2, 7.0, "torso"),          # infraspinatus / teres
    ((0.035, 0.125, 1.140), (0.026, 0.050, 0.170), (0, 1, 0), 0.3, 7.0, "torso"),            # erector spinae column
    ((0.080, 0.120, 0.880), (0.080, 0.075, 0.095), (0.2, 1, -0.1), 0.2, 5.0, "torso"),       # gluteus maximus (R76e: owner - not sticking out)
    ((0.120, 0.070, 0.950), (0.045, 0.050, 0.050), (1, 0.6, 0), 0.0, 3.0, "torso"),          # gluteus medius
]


def masks():
    arm = gw("upperarm_r", "forearm_r", "forearm_tw0_r", "forearm_tw1_r", "hand_r", "upperarm_l", "forearm_l",
             "forearm_tw0_l", "forearm_tw1_l", "hand_l")
    leg = gw("thigh_r", "shin_r", "foot_r", "thigh_l", "shin_l", "foot_l")
    head = gw("head")
    return arm, leg, head


ARM, LEG, HEAD = masks()


UNION_P = float(os.environ.get("V2_UNION_P", "3"))      # soft-max exponent: bellies meeting leave a groove (1 = plain sum)


def field(P, N, side):
    """right-side field evaluated on (possibly mirrored) positions/normals; masks use the given side's groups.
    Returns base (all-round thickness) + soft union of the bellies: (sum c_k^p)^(1/p)."""
    base = np.zeros(len(P)); bell = np.zeros(len(P))
    for bn, t0, tp, t1, face, hw, amp, grp in LIMB:
        h, t = bone(f"{bn}_r")
        ax = t - h; L = np.linalg.norm(ax); ax = ax / L
        u = (P - h) @ ax / L
        lo = ss((u - t0) / max(tp - t0, 1e-6)); hi = ss((t1 - u) / max(t1 - tp, 1e-6))
        along = np.where(u < tp, lo, hi) * ((u > t0) & (u < t1))
        f = np.array(face, float); f = f - (f @ ax) * ax; f /= np.linalg.norm(f)
        nperp = N - np.outer(N @ ax, ax); nperp /= np.maximum(np.linalg.norm(nperp, axis=1, keepdims=True), 1e-9)
        c = nperp @ f; ch = math.cos(math.radians(min(hw, 179.9)))
        ang = np.ones(len(P)) if hw >= 180 else ss((c - ch) / (1 - ch))
        m = gw(*[f"{g}_{side}" for g in grp])
        c = amp * along * ang * m
        if hw >= 180:
            base += c
        else:
            bell += c ** UNION_P
    for cen, rad, face, mind, amp, kind in BLOB:
        q = (P - np.array(cen)) / np.array(rad)
        r = np.linalg.norm(q, axis=1)
        prof = ss(1 - r) ** 0.8
        f = np.array(face, float); f /= np.linalg.norm(f)
        fd = ss(((N @ f) - mind) / (1 - mind))
        if kind == "torso":
            m = (1 - ARM) * (1 - HEAD)
        else:                                                         # shoulder: cap + top of the upper arm
            m = 1 - HEAD
        bell += (amp * prof * fd * m) ** UNION_P
    return (base + bell ** (1.0 / UNION_P)) / 1000.0


dr = field(rest, nrm, "r")
SPINE_MM = float(os.environ.get("V2_SPINE_MM", "4"))          # groove down the back between the erectors (both sides share it)
Pm = rest * np.array([-1, 1, 1]); Nm = nrm * np.array([-1, 1, 1])
dl = field(Pm, Nm, "l")
side_r = rest[:, 0] >= 0
amt = np.where(side_r, dr, dl) * GAIN
amt[np.abs(rest[:, 0]) < 1e-6] = 0.5 * (dr + dl)[np.abs(rest[:, 0]) < 1e-6] * GAIN
amt *= (1 - HEAD)
spine = ss(1 - np.abs(rest[:, 0]) / 0.022) * ss((rest[:, 2] - 0.98) / 0.06) * ss((1.45 - rest[:, 2]) / 0.06) * ss(nrm[:, 1] / 0.5) * (1 - ARM)
amt -= SPINE_MM / 1000.0 * spine * GAIN / 2.0
# R76e (owner: "Can we check the spine shape ... very harsh. Is there no muscle at lower back?"): measured side profile of
# the back midline - the lumbar hollow sits 60-70 mm in from the glute-to-upper-back line (V1 already; v2 glutes made it
# look harsher).  The erector spinae fill most of it in a fit man: absolute fill (mm, not scaled by the gain) peaking at
# the deepest point (rest z 1.12), wide enough to cover both erector columns, fading at the glutes and the shoulder blades.
LUMBAR_MM = float(os.environ.get("V2_LUMBAR_MM", "34"))
zc, zw = 1.115, 0.16
lum = ss(1 - np.abs(rest[:, 2] - zc) / zw) * ss(1 - np.abs(rest[:, 0]) / 0.13) * ss(nrm[:, 1] / 0.4) * (1 - ARM) * (rest[:, 1] > 0)
amt += LUMBAR_MM / 1000.0 * lum
# relax the amount on the surface so bellies blend (8 passes of neighbour averaging)
nb = [[] for _ in range(nv)]
for f in faces:
    for i in range(len(f)):
        nb[f[i]] += [f[(i + 1) % len(f)], f[i - 1]]
nb = [np.unique(n) for n in nb]
rows = np.repeat(np.arange(nv), [len(n) for n in nb]); cols = np.concatenate(nb); deg = np.array([len(n) for n in nb], float)


def avg(x):
    acc = np.zeros_like(x); np.add.at(acc, rows, x[cols]); return acc / deg


for _ in range(int(os.environ.get("V2_RELAX", "4"))):
    amt = 0.5 * amt + 0.5 * avg(amt)
off = nrm * amt[:, None]
# R76h (owner: "the torso ... seems very slim and the photos I sent are a bit wider"): measured as fractions of height on
# the front view - waist (torso only) 0.156 vs reference 0.187, chest 0.179 vs 0.20.  Widen the ribcage / waist sides
# (lateral-facing torso skin, rest z 0.95..1.45), most at the waist, but never closer than 4 mm to the hanging arm.
WAIST_MM = float(os.environ.get("V2_WAIST_MM", "24")); CHEST_MM = float(os.environ.get("V2_CHEST_MM", "16"))
from scipy.spatial import cKDTree as _T
z_ = rest[:, 2]
prof_w = np.interp(z_, [0.92, 1.00, 1.10, 1.22, 1.34, 1.44, 1.50], [0, WAIST_MM * 0.6, WAIST_MM, WAIST_MM * 0.9, CHEST_MM, CHEST_MM * 0.6, 0]) / 1000.0
lat_face = ss((np.abs(nrm[:, 0]) - 0.25) / 0.5)
tors = (1 - ARM) * (1 - HEAD) * (1 - LEG)
push = prof_w * lat_face * tors
armpts = (rest + off)[ARM > 0.5]
cand = push > 1e-5
newpos = rest + off + nrm * push[:, None]
gap, _ = _T(armpts).query(rest[cand] + off[cand])                      # current clearance to the arm skin
push[cand] = np.minimum(push[cand], np.maximum(gap - 0.004, 0.0))
for _ in range(6):
    push = 0.5 * push + 0.5 * avg(push)
off = off + nrm * push[:, None]
# R76i: clearance between the arms (incl. hands) and the body.  The muscle volume made the inner upper arm press into the
# lats / armpit (~400 overlapping triangle pairs) and the hands into the front of the thighs (~70).  Wherever a vertex
# of one part ends up closer to the other part than min(its rest clearance, 4 mm), shrink the new volume of both sides
# there, and repeat.
CLEAR = float(os.environ.get("V2_CLEAR_MM", "4")) / 1000.0
A_ = ARM > 0.5; B_ = ~A_
ta0 = _T(rest[B_]); tb0 = _T(rest[A_])
d0A, _ = ta0.query(rest[A_]); d0B, _ = tb0.query(rest[B_])
needA = np.minimum(d0A, CLEAR); needB = np.minimum(d0B, CLEAR)
scale = np.ones(nv); clr_iters = 0
for it in range(25):
    P_ = rest + off * scale[:, None]
    dA, _ = _T(P_[B_]).query(P_[A_]); dB, _ = _T(P_[A_]).query(P_[B_])
    badA = dA < needA - 1e-4; badB = dB < needB - 1e-4
    if not badA.any() and not badB.any():
        break
    sA = np.ones(A_.sum()); sA[badA] = 0.7; sB = np.ones(B_.sum()); sB[badB] = 0.7
    shrink = np.ones(nv); shrink[A_] = sA; shrink[B_] = sB
    for _ in range(3):
        shrink = np.minimum(shrink, 0.5 * shrink + 0.5 * avg(shrink))
    scale *= shrink; clr_iters = it + 1
off = off * scale[:, None]
# then the exact test: triangles of the new rest surface that overlap (not sharing a vertex).  Shrink the new volume on
# their vertices and a small neighbourhood, until none are left (the V1 rest surface has none).
from mathutils.bvhtree import BVHTree as _BVH
_fs = [set(f) for f in faces]; _ft = [tuple(f) for f in faces]
ov_log = []
for it in range(40):
    P_ = rest + off
    tr = _BVH.FromPolygons([Vector(v) for v in P_], _ft, all_triangles=True)
    pr = [(a_, b_) for a_, b_ in tr.overlap(tr) if a_ < b_ and not (_fs[a_] & _fs[b_])]
    ov_log.append(len(pr))
    if not pr:
        break
    hit = np.zeros(nv); hit[np.unique(faces[np.array(pr).ravel()].ravel())] = 1.0
    for _ in range(2):
        hit = np.maximum(hit, avg(hit))
    off = off * (1.0 - 0.35 * np.clip(hit * 2, 0, 1))[:, None]
WIDTH_REPORT = {"overlap_iterations": ov_log, "clearance_iterations": clr_iters, "min_scale": round(float(scale.min()), 3), "waist_mm": WAIST_MM, "chest_mm": CHEST_MM, "max_side_push_mm": round(float(push.max() * 1000), 2)}
np.savez_compressed(OUT / "body_v2_offsets.npz", offsets=off.astype(np.float32))
mir = {}
rep = {"gain": GAIN, "width": WIDTH_REPORT, "lumbar_mm": LUMBAR_MM, "spine_mm": SPINE_MM, "union_p": UNION_P, "relax": int(os.environ.get("V2_RELAX", "4")), "max_mm": round(float(amt.max() * 1000), 2), "mean_mm_nonzero": round(float(amt[amt > 1e-4].mean() * 1000), 2),
       "vertices_moved_gt_1mm": int((amt > 1e-3).sum())}
# symmetry check: mirror pairs by nearest neighbour
from scipy.spatial import cKDTree
tree = cKDTree(rest); dd, j = tree.query(rest * np.array([-1, 1, 1]))
ok = dd < 1e-5
rep["symmetry_max_mm"] = round(float(np.abs(amt[ok] - amt[j[ok]]).max() * 1000), 4)
# self-intersections of the rest surface (pairs of non-adjacent triangles that overlap), before and after
from mathutils.bvhtree import BVHTree


def _pairs(P):
    tree = BVHTree.FromPolygons([Vector(v) for v in P], [tuple(f) for f in faces], all_triangles=True)
    fs = [set(f) for f in faces]
    return sum(1 for a_, b_ in tree.overlap(tree) if a_ < b_ and not (fs[a_] & fs[b_]))


rep["rest_self_intersections"] = {"v1": _pairs(rest), "v2": _pairs(rest + off)}
(OUT / "body_v2_report.json").write_text(json.dumps(rep, indent=1))
print("V2_SCULPT", json.dumps(rep), flush=True)

if os.environ.get("R76_RENDER") == "1":
    key = body.shape_key_add(name="V2_BODY_SCULPT", from_mix=False)
    key.data.foreach_set("co", (rest + off).ravel().astype(np.float32)); key.value = 1.0
    sc = bpy.context.scene
    for ob in sc.objects:
        if ob.type in ("MESH", "CURVE") and ob is not body:
            ob.hide_render = True
    mat = bpy.data.materials.new("REVIEW_ONLY"); mat.diffuse_color = (.72, .55, .45, 1)
    body.data.materials.clear(); body.data.materials.append(mat)
    sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
    sc.display.shading.show_cavity = True; sc.render.resolution_x = 900; sc.render.resolution_y = 1500
    cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
    bpy.context.view_layer.update()
    lo, hi = rest.min(0), rest.max(0); mid = Vector(((lo + hi) / 2).tolist()); cd.ortho_scale = float(hi[2] - lo[2]) * 1.08
    for tag, val in (("V1", 0.0), ("V2", 1.0)):
        key.value = val; bpy.context.view_layer.update()
        for view, dv in {"front": (0, -1, 0), "back": (0, 1, 0), "side": (1, 0, 0), "front34": (0.7, -0.7, 0), "back34": (0.7, 0.7, 0)}.items():
            dvec = Vector(dv).normalized(); cam.location = mid + dvec * 4; cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (-dvec).to_track_quat("-Z", "Y")
            sc.render.filepath = str(OUT / f"{tag}_full_standing_{view}.png"); bpy.ops.render.render(write_still=True)
    print("V2_RENDERED", flush=True)
