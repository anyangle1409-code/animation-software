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
# R83 (owner chose "Refine the torso mesh"): split the coarse torso / pelvis / glute / neck triangles (13-26 mm edges)
# down to <= V2_REFINE_MM, carrying skin weights and every shape key over linearly (refine_torso_blender.py).  0 = off.
REFINE_MM = float(os.environ.get("V2_REFINE_MM", "8"))
REFINE_REPORT = None
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


_GW_CACHE = {}


def gw(*names):
    """skin-weight mask of the given groups, relaxed on the surface (R77d: the raw weights jump vertex to vertex around
    the shoulder, where several bones blend, and turned smooth volume into crumpled skin on the deltoid)"""
    key_ = tuple(names)
    if key_ in _GW_CACHE:
        return _GW_CACHE[key_]
    out = np.zeros(nv)
    for n in names:
        if n in gidx and gidx[n] in W:
            out += W[gidx[n]]
    out = np.clip(out, 0, 1)
    if "_nbr" in globals():
        for _ in range(int(os.environ.get("V2_MASK_SMOOTH", "10"))):
            out = 0.5 * out + 0.5 * _nbr(out)
    _GW_CACHE[key_] = out
    return out


def ss(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def bone(name):
    b = rig.data.bones[name]
    if name.startswith("forearm_"):                 # R77: the forearm bone ends mid-forearm (twist bones below) - use elbow -> wrist
        return np.array(b.head_local), np.array(rig.data.bones["hand_" + name[-1]].head_local)
    return np.array(b.head_local), np.array(b.tail_local)


# ---- muscle specification (right side; rest coordinates: +x lateral right, -y front, +y back, +z up; metres, mm) ----
LIMB = [  # bone, t0, tp, t1, facing, half-width deg, amp mm, mask groups
    ("upperarm", 0.12, 0.58, 0.90, (0, -1, 0), 75, 11.0, ("upperarm",)),         # biceps
    ("upperarm", 0.04, 0.35, 0.82, (0.3, 1, 0), 80, 11.0, ("upperarm",)),        # triceps (long + lateral heads)
    ("upperarm", 0.45, 0.75, 0.98, (1, -0.4, 0), 55, 4.0, ("upperarm",)),        # brachialis, lateral
    ("upperarm", 0.00, 0.50, 1.00, (1, 0, 0), 180, 4.0, ("upperarm",)),          # overall arm thickness (R77: ref 1.06-1.16x)
    ("forearm", 0.06, 0.32, 0.75, (1, -0.3, 0), 75, 9.0, ("forearm", "forearm_tw0", "forearm_tw1")),   # brachioradialis / extensors
    ("forearm", 0.06, 0.33, 0.72, (-0.6, -0.8, 0), 75, 8.0, ("forearm", "forearm_tw0", "forearm_tw1")),  # flexors
    ("forearm", 0.10, 0.40, 0.95, (1, 0, 0), 180, 4.0, ("forearm", "forearm_tw0", "forearm_tw1")),
    ("forearm", 0.45, 0.82, 1.06, (1, 0, 0), 180, 5.0, ("forearm", "forearm_tw0", "forearm_tw1", "hand")),   # R77: lower forearm / wrist (wrist 37 mm wide, real ~60)
    ("thigh", 0.30, 0.62, 0.97, (0, -1, 0), 60, 8.0, ("thigh",)),                # rectus femoris (R76d: mid-thigh)
    ("thigh", 0.38, 0.66, 0.95, (1, -0.4, 0), 55, 4.0, ("thigh",)),              # vastus lateralis (R76c: lower, no hip bulge)
    ("thigh", 0.55, 0.85, 1.00, (-0.7, -0.7, 0), 45, 9.0, ("thigh",)),           # vastus medialis (teardrop)
    ("thigh", 0.22, 0.50, 0.88, (0, 1, 0), 70, 8.0, ("thigh",)),                 # hamstrings
    ("thigh", 0.20, 0.40, 0.70, (-1, 0, 0), 60, 2.0, ("thigh",)),                # adductors
    ("thigh", 0.35, 0.65, 1.00, (1, 0, 0), 180, 2.0, ("thigh",)),
    ("shin", 0.06, 0.26, 0.62, (-0.45, 1, 0), 55, 9.0, ("shin",)),               # gastrocnemius medial head (R76f: not sticking out)
    ("shin", 0.06, 0.24, 0.55, (0.5, 1, 0), 50, 7.0, ("shin",)),                 # gastrocnemius lateral head
    ("shin", 0.10, 0.35, 0.70, (0.6, -0.8, 0), 45, 4.0, ("shin",)),              # tibialis anterior
    ("shin", 0.00, 0.40, 0.85, (1, 0, 0), 180, 2.0, ("shin",)),
]
BLOB = [  # centre, radii (x,y,z), facing, min facing dot, amp mm, mask ("torso" = off the arms, "arm" = upper arm/shoulder)
    # R77f removed (owner: ridge, keep the original's natural curve): ((0.262, 0.030, 1.420), (0.055, 0.075, 0.085), (1, 0, 0.35), -0.3, 10.0, "shoulder"),   # deltoid (lateral; R76h: shoulders already 0.332 H vs reference 0.300)
    # R77f removed (owner: ridge, keep the original's natural curve): ((0.240, -0.035, 1.415), (0.045, 0.045, 0.075), (0.5, -1, 0.2), -0.1, 7.0, "shoulder"),  # anterior deltoid
    # R77f removed (owner: ridge, keep the original's natural curve): ((0.240, 0.095, 1.415), (0.045, 0.045, 0.075), (0.5, 1, 0.2), -0.1, 7.0, "shoulder"),    # posterior deltoid
    ((0.100, -0.112, 1.360), (0.100, 0.060, 0.080), (0.25, -1, 0.15), 0.25, 7.0, "torso"),   # pectoralis major (R76m: was 13 - chest stood 40 mm ahead of the belly, reference ~10)
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


_nb0 = [[] for _ in range(nv)]
for f_ in faces:
    for i_ in range(len(f_)):
        _nb0[f_[i_]] += [f_[(i_ + 1) % len(f_)], f_[i_ - 1]]
_nb0 = [np.unique(n) for n in _nb0]
_r0 = np.repeat(np.arange(nv), [len(n) for n in _nb0]); _c0 = np.concatenate(_nb0); _d0 = np.array([len(n) for n in _nb0], float)


def _nbr(x):
    acc = np.zeros_like(x); np.add.at(acc, _r0, x[_c0]); return acc / _d0


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
# R76l (owner: "I think it's the same thing with the hamstrings too"): side profile of the back of the thigh - from the
# glute peak it drops ~55 mm within 14 cm (a hard fold under the glutes), the reference ~34 mm to mid-thigh.  Fill the
# upper / middle hamstrings (back-facing thigh skin, peak rest z 0.76) so the line from glute to knee runs smoothly.
HAM_MM = float(os.environ.get("V2_HAM_MM", "20"))
thw = gw("thigh_r", "thigh_l")
ham = np.interp(rest[:, 2], [0.52, 0.62, 0.72, 0.80, 0.86, 0.90], [0, 0.45, 1.0, 0.85, 0.35, 0]) * ss(nrm[:, 1] / 0.45) * thw * (1 - ARM)
amt += HAM_MM / 1000.0 * ham
# R76m (owner: posture - chest pushed forward): the spine bones are straight; the forward chest is the surface (V1 chest
# 22 mm ahead of the abdomen, v2 L 40 mm, reference ~10).  Fuller abdominal wall (front-facing skin, rest z 0.98..1.30),
# keeping the sculpted ab lines (a normal push preserves them).
ABS_MM = float(os.environ.get("V2_ABS_MM", "15"))
abd = np.interp(rest[:, 2], [0.86, 0.98, 1.10, 1.22, 1.30, 1.34], [0, 0.45, 1.0, 1.0, 0.4, 0]) * ss(-nrm[:, 1] / 0.5) * ss(1 - np.abs(rest[:, 0]) / 0.13) * (1 - ARM) * (rest[:, 1] < 0)
amt += ABS_MM / 1000.0 * abd
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
# R77c: push along a smoothed normal field - around the deltoid the rest normals vary sharply vertex to vertex, which
# turned smooth volume into crumpled skin (seen on drafts K-U, with and without the overlap step)
nrm_s = nrm.copy()
for _ in range(int(os.environ.get("V2_NORMAL_SMOOTH", "12"))):
    nrm_s = 0.5 * nrm_s + 0.5 * np.stack([avg(nrm_s[:, k]) for k in range(3)], axis=1)
    nrm_s /= np.maximum(np.linalg.norm(nrm_s, axis=1, keepdims=True), 1e-12)
off = nrm_s * amt[:, None]
# R77 (owner's photo grid): the shoulder line.  Top-of-shoulder contour on the front view, as y/H against |x|/H: the
# model (V1 already) sits 6-8 cm above the reference - skin top 8 cm above the humeral-head centre, upper trapezius ~7 cm
# above the clavicle (real: ~4-5 cm / ~3-5 cm).  Lower the upward-facing shoulder / trapezius skin along -z, sloping from
# the neck out to the acromion; the side of the deltoid keeps its roundness (upward-facing skin only).
DROP = [float(v) for v in os.environ.get("V2_SHOULDER_DROP", "0.055:0,0.29:0").replace(":", ",").split(",")]
dx, dmm = np.array(DROP[0::2]), np.array(DROP[1::2])
ax_ = np.abs(rest[:, 0])
# R77b (owner on draft T: "The shoulders look messed up now and sharp instead of sloped"): moving only the upward-facing
# skin folded a jagged ridge where it met the side of the deltoid.  Now the whole shoulder cap moves down as one smooth
# field of rest x and z only (no normal mask), fading out below the deltoid, so the slope from neck to arm is continuous.
drop = np.interp(ax_, dx, dmm) / 1000.0 * ss((rest[:, 2] - 1.33) / 0.15) * (1 - HEAD)
drop *= ss((ax_ - 0.045) / 0.03)                                   # the neck itself stays
for _ in range(20):
    drop = 0.5 * drop + 0.5 * avg(drop)
off[:, 2] -= drop
SHOULDER_REPORT = {"max_drop_mm": round(float(drop.max() * 1000), 1)}
# R76h (owner: "the torso ... seems very slim and the photos I sent are a bit wider"): measured as fractions of height on
# the front view - waist (torso only) 0.156 vs reference 0.187, chest 0.179 vs 0.20.  Widen the ribcage / waist sides
# (lateral-facing torso skin, rest z 0.95..1.45), most at the waist, but never closer than 4 mm to the hanging arm.
WAIST_MM = float(os.environ.get("V2_WAIST_MM", "24")); CHEST_MM = float(os.environ.get("V2_CHEST_MM", "16"))
from scipy.spatial import cKDTree as _T
z_ = rest[:, 2]
prof_w = np.interp(z_, [0.84, 0.98, 1.10, 1.22, 1.34, 1.44, 1.50], [0, WAIST_MM * 0.55, WAIST_MM, WAIST_MM * 0.9, CHEST_MM, CHEST_MM * 0.6, 0]) / 1000.0
# R80 (owner: "Can we sort out the waist also?"): the profile above pushed the natural waist (z 1.10-1.22, 0.59-0.66 of
# stature, iliac crest to 10th rib) out as far as the chest, so the torso read as a box: front-view waist 0.171-0.174 of
# stature against the reference's 0.166-0.170, and barely narrower than the hips.  Side push now (mm, at rest z):
# hips kept, waist pulled in, ribs / lats fuller (still capped by the arm clearance below).
SIDE_PROF = os.environ.get("V2_SIDE_PROFILE", "0.84:0,0.98:13,1.05:15,1.12:13,1.17:13,1.26:20,1.34:20,1.44:10,1.50:0")
if SIDE_PROF:
    _k = np.array([[float(v) for v in kv.split(":")] for kv in SIDE_PROF.split(",")])
    prof_w = np.interp(z_, _k[:, 0], _k[:, 1]) / 1000.0
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
off = off + nrm_s * push[:, None]
# R76i: clearance between the arms (incl. hands) and the body.  The muscle volume made the inner upper arm press into the
# lats / armpit (~400 overlapping triangle pairs) and the hands into the front of the thighs (~70).  Wherever a vertex
# of one part ends up closer to the other part than min(its rest clearance, 4 mm), shrink the new volume of both sides
# there, and repeat.
CLEAR = float(os.environ.get("V2_CLEAR_MM", "0")) / 1000.0   # R77: 0 = off (the overlap test now runs in the standing pose)
A_ = ARM > 0.5; B_ = ~A_
ta0 = _T(rest[B_]); tb0 = _T(rest[A_])
d0A, _ = ta0.query(rest[A_]); d0B, _ = tb0.query(rest[B_])
needA = np.minimum(d0A, CLEAR); needB = np.minimum(d0B, CLEAR)
scale = np.ones(nv); clr_iters = 0
for it in range(25 if CLEAR > 0 else 0):
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
# R77f (owner, pointing at the ORIGINAL shoulder: "look at the natural curve of the shoulder ... how it slopes down without
# the ridge"): the separate deltoid bellies left an edge where they met the lowered shoulder top.  Instead, expand the
# original shoulder smoothly about the humeral head (a 3D field, not per-normal bumps), so the original's continuous
# neck-to-arm curve is kept, just rounder.  Only skin on the outward side of the joint moves (no dent on the chest wall).
SH_K = float(os.environ.get("V2_SHOULDER_EXPAND", "0.06")); SH_R = float(os.environ.get("V2_SHOULDER_R", "0.13"))   # owner chose Z2 (6 %)
for sd, sg in (("r", 1.0), ("l", -1.0)):
    c = np.array(rig.data.bones[f"upperarm_{sd}"].head_local)
    v_ = rest - c; dist = np.linalg.norm(v_, axis=1); u_ = v_ / np.maximum(dist[:, None], 1e-9)
    w_ = ss(1 - dist / SH_R) * ss(np.einsum("ij,ij->i", u_, nrm_s) / 0.5) * (1 - HEAD) * (sg * rest[:, 0] > 0)
    for _ in range(6):
        w_ = 0.5 * w_ + 0.5 * avg(w_)
    off = off + v_ * (SH_K * w_)[:, None]
# R78 (photo grid): the head is 0.11 of stature (chin 1.62 -> top 1.82 = 0.20 m); a real adult man is ~0.13 (~23 cm),
# the reference ~0.14.  Scale the head about a pivot at ear level (top rises ~1.8 cm, chin drops ~1.2 cm), blended into
# the neck over 3.5 cm so the neck surface stays continuous.
HEAD_SCALE = float(os.environ.get("V2_HEAD_SCALE", "1.15"))
if HEAD_SCALE != 1.0:
    piv = np.array([0.0, -0.02, float(os.environ.get("V2_HEAD_PIVOT_Z", "1.628"))])   # R78b (owner: "not much of a neck now"): pivot at chin level, the head grows upward, the neck keeps its length
    hw_ = ss((rest[:, 2] - 1.555) / 0.085) * ss((0.12 - np.abs(rest[:, 0])) / 0.03)   # R78d: long blend (a 3 cm blend left a ring round the neck)
    off = off + (rest + off - piv) * ((HEAD_SCALE - 1.0) * hw_)[:, None]
    NECK_MM = float(os.environ.get("V2_NECK_MM", "8"))         # R78d (owner: "need to have a neck"): lengthen the neck a little
    off[:, 2] += NECK_MM / 1000.0 * hw_
# R79 (owner: "The torso seem very long and the legs short"; chose "Longer legs, same height"): measured against ANSUR II
# male (n = 4,082, stature-conditioned OLS at the v3e stature 1.857 m) the hip, knee and ankle joints are at normal heights
# (knee 0.515 vs 0.525, trochanter ~0.968 vs 0.962) but the crotch is 0.837 m against 0.905 m (-2.8 SD); the
# project's own proportion audit (F-PROP-001) already had it at z -1.85 on V1.  So the bones stay; the crotch and the top
# of the inner thighs are lifted (height unchanged): a vertical lift, full at the midline and fading to zero at the thigh
# axis, rising from z 0.60 to the old crotch and fading out by z 1.12 above it.
CROTCH_MM = float(os.environ.get("V2_CROTCH_MM", "58"))
if CROTCH_MM > 0:
    Q = rest + off
    zc = 0.84
    up = np.where(Q[:, 2] < zc, ss((Q[:, 2] - 0.60) / (zc - 0.60)), ss((1.12 - Q[:, 2]) / (1.12 - zc)))
    up = up * ss(1 - np.maximum(np.abs(rest[:, 0]) - 0.015, 0) / 0.095) * (1 - ARM)
    # only the surfaces between the legs (facing sideways or down); lifting the front / back faces too pushed the lower
    # belly into a fold above the groin (v3f/v3g)
    up = up * ss((0.85 - np.abs(nrm[:, 1])) / 0.5)
    for _ in range(3):
        up = 0.5 * up + 0.5 * avg(up)
    off[:, 2] += CROTCH_MM / 1000.0 * up
# (applied before the hip-band and groin relax below, so they smooth the lifted surface)
# R80b (owner: "the groin looks to be very high"): the lower belly met the thighs along a horizontal line ~4-5 cm above
# the crotch, so the legs seemed to start there.  On a lean man the junction is a V: the inguinal grooves run from the
# front of the hip bone (ASIS landmark, |x| 0.108, z 1.00) down to the pubis beside the crotch.  A soft groove (depth
# V2_INGUINAL_MM, half-width 18 mm) along that line on the front-facing skin, fading out at both ends.
ING_MM = float(os.environ.get("V2_INGUINAL_MM", "12"))
if ING_MM > 0:
    Q = rest + off
    A_ = np.array([0.112, 1.005]); B_ = np.array([0.028, 0.895])            # (|x|, z): ASIS -> pubic tubercle (lifted crotch)
    d_ = B_ - A_; L_ = np.linalg.norm(d_); u_ = d_ / L_
    p_ = np.stack([np.abs(Q[:, 0]), Q[:, 2]], axis=1) - A_
    t_ = np.clip(p_ @ u_ / L_, 0, 1)
    dist = np.linalg.norm(p_ - np.outer(t_ * L_, u_), axis=1)
    g_ = ss(1 - dist / 0.018) * ss(t_ / 0.25) * ss((1 - t_) / 0.15) * ss((-nrm[:, 1] - 0.3) / 0.4) * (1 - ARM)
    for _ in range(3):
        g_ = 0.5 * g_ + 0.5 * avg(g_)
    off = off - nrm_s * (ING_MM / 1000.0 * g_)[:, None]
# R78c (owner: "a very noticeable line departing [torso and legs]"): a ridge runs round the hips where the torso meets
# the thighs (faint in V1, stronger with the waist/abdomen fills ending above it and the thigh fills starting below).
# Taubin-relax the POSITIONS in that band (removes the ridge itself, volume-preserving) and keep the change as offsets.
HIPB = float(os.environ.get("V2_HIP_BLEND", "120"))
if HIPB > 0:
    band = ss(1 - np.abs((rest + off)[:, 2] - float(os.environ.get("V2_HIP_BAND_Z", "0.95"))) / float(os.environ.get("V2_HIP_BAND_HW", "0.10"))) * (1 - ARM)
    for _ in range(4):
        band = 0.5 * band + 0.5 * avg(band)
    Q = rest + off
    for _ in range(int(HIPB)):
        L1 = np.stack([avg(Q[:, k]) for k in range(3)], axis=1) - Q; Q = Q + 0.5 * band[:, None] * L1
        L2 = np.stack([avg(Q[:, k]) for k in range(3)], axis=1) - Q; Q = Q - 0.53 * band[:, None] * L2
    off = Q - rest
# R78e (owner circled the lower belly / groin / top of the thighs on v3c): the front of the groin read as a flat, boxy
# panel with V1's faceted V-crease pattern along the groin lines, and the lower belly met it with a shelf.  Stronger
# Taubin relax of the positions over the front of the lower belly, groin and top of the thighs.
GROIN = float(os.environ.get("V2_GROIN_RELAX", "80"))
if GROIN > 0:
    gz = ss(1 - np.abs(rest[:, 2] - 0.95) / 0.13) * ss(1 - np.abs(rest[:, 0]) / 0.17) * ss((-nrm[:, 1] + 0.2) / 0.6) * (1 - ARM)
    for _ in range(4):
        gz = 0.5 * gz + 0.5 * avg(gz)
    Q = rest + off
    for _ in range(int(GROIN)):
        L1 = np.stack([avg(Q[:, k]) for k in range(3)], axis=1) - Q; Q = Q + 0.5 * gz[:, None] * L1
        L2 = np.stack([avg(Q[:, k]) for k in range(3)], axis=1) - Q; Q = Q - 0.53 * gz[:, None] * L2
    off = Q - rest
# R82 (owner, with two front/side/back reference figures: "This is how the pelvis and groin and legs should look"):
# front silhouette measured on both figures and on the owner's first photo, as fractions of stature (stature-normalised
# masks, scripts/body_v2/fit/proportions.py for ANSUR):
#   hips at 0.50: 0.207-0.211 vs model 0.187; waist 0.58-0.62: 0.164-0.178 vs 0.161-0.166; ribs 0.66-0.70: 0.162-0.187
#   vs 0.178-0.200 (R80 lat push too strong); one thigh just above the knee (0.32-0.36): 0.065-0.086 vs 0.083-0.097,
#   upper thigh (0.44-0.46): ~0.105 vs 0.089-0.094 - the model's thighs were narrow at the top and bulged above the knee,
#   the references are widest at the top and taper to the knee, with the legs parting soon below the crotch.
# Silhouette field: per-side horizontal push (mm, + out) at height fractions of stature on the outward-facing skin, and
# for the legs a second one on the inward-facing (medial) skin, which also opens the gap between the thighs.
SIL_LAT = os.environ.get("V2_SIL_LAT", "0.27:0,0.30:-3,0.32:-12,0.34:-16,0.36:-15,0.38:-12,0.40:-5,0.42:6,0.44:18,0.46:24,"
                                        "0.48:24,0.50:20,0.52:9,0.54:6,0.56:8,0.58:9,0.60:10,0.62:5,0.64:-4,0.66:-11,0.68:-14,0.70:-10,0.73:-4,0.76:0")
SIL_MED = os.environ.get("V2_SIL_MED", "0.27:0,0.30:-4,0.32:-14,0.34:-19,0.36:-17,0.38:-14,0.40:-6,0.42:-1,0.44:0")
if SIL_LAT or SIL_MED:
    Q = rest + off
    fz = (Q[:, 2] - Q[:, 2].min()) / (Q[:, 2].max() - Q[:, 2].min())
    hn = nrm_s[:, :2] / np.maximum(np.linalg.norm(nrm_s[:, :2], axis=1, keepdims=True), 1e-9)
    side = np.sign(Q[:, 0]) + (Q[:, 0] == 0)
    outw = hn[:, 0] * side                                                   # +1 facing away from the midline
    sil_l = np.zeros(nv); sil_m = np.zeros(nv)
    if SIL_LAT:
        k_ = np.array([[float(v) for v in kv.split(":")] for kv in SIL_LAT.split(",")])
        sil_l = np.interp(fz, k_[:, 0], k_[:, 1], left=0, right=0) * ss((outw - 0.05) / 0.6)
    if SIL_MED:                                                             # medial skin: + moves it towards the midline
        k_ = np.array([[float(v) for v in kv.split(":")] for kv in SIL_MED.split(",")])
        sil_m = np.interp(fz, k_[:, 0], k_[:, 1], left=0, right=0) * ss((-outw - 0.05) / 0.6) * (np.abs(Q[:, 0]) > 0.012)
    for sil_ in (sil_l, sil_m):
        sil_ *= (1 - ARM) * (1 - HEAD)
        for _ in range(8):
            sil_[:] = 0.5 * sil_ + 0.5 * avg(sil_)
    off[:, 0] += side * (sil_l - sil_m) / 1000.0 * np.abs(hn[:, 0])
    sil = sil_l + sil_m
    off[:, 1] += sil / 1000.0 * hn[:, 1] * 0.5 * (sil < 0)                  # pulling in: a little depth too (thigh taper)
# R82b: belly button (both references: ~0.61-0.62 of stature; ANSUR omphalion 0.606) - a soft dimple on the front midline
NAVEL_MM = float(os.environ.get("V2_NAVEL_MM", "7"))
if NAVEL_MM > 0 and REFINE_MM <= 0:
    Q = rest + off
    zn = Q[:, 2].min() + 0.612 * (Q[:, 2].max() - Q[:, 2].min())
    fr = (Q[:, 1] < 0) & (-nrm[:, 1] > 0.6)
    rr = np.sqrt(Q[:, 0] ** 2 + ((Q[:, 2] - zn) / 1.2) ** 2)
    dimple = np.where(fr, ss(1 - rr / 0.011) - 0.25 * ss(1 - np.abs(rr - 0.014) / 0.005), 0.0)
    off -= nrm * (NAVEL_MM / 1000.0 * dimple)[:, None]
# R82c: the V of the groin - the thigh front just below / outside the inguinal line comes forward a little (both
# references), so the crease reads as a fold between the lower belly / pubic wedge and the thighs
ING_FILL = float(os.environ.get("V2_INGUINAL_FILL_MM", "6"))
if ING_FILL > 0:
    Q = rest + off
    A_ = np.array([0.112, 1.005]); B_ = np.array([0.028, 0.895]); d_ = B_ - A_; L_ = np.linalg.norm(d_); u_ = d_ / L_
    nperp = np.array([u_[1], -u_[0]])                                      # points to the thigh side (out / down)
    p_ = np.stack([np.abs(Q[:, 0]), Q[:, 2]], axis=1) - A_
    t_ = np.clip(p_ @ u_ / L_, 0, 1); sd_ = p_ @ nperp
    fill = ss(sd_ / 0.012) * ss(1 - (sd_ - 0.012) / 0.07) * ss(t_ / 0.2) * ss((1 - t_) / 0.2) * ss((-nrm[:, 1] - 0.3) / 0.4) * (1 - ARM)
    for _ in range(4):
        fill = 0.5 * fill + 0.5 * avg(fill)
    off += nrm_s * (ING_FILL / 1000.0 * fill)[:, None]
# R77e: relax the offset field around the shoulders (drop field + deltoid bellies meeting) - measured extra roughness
# on the deltoid came from the overlap shrink, the shoulder drop and the bellies, in that order
_sh = ss((np.abs(rest[:, 0]) - 0.12) / 0.04) * ss((rest[:, 2] - 1.24) / 0.06) * ss((1.62 - rest[:, 2]) / 0.04)
for _ in range(int(os.environ.get("V2_SHOULDER_RELAX", "8"))):
    off = off + 0.5 * _sh[:, None] * (np.stack([avg(off[:, k]) for k in range(3)], axis=1) - off)
# R81 (owner: "Fix them now" - the arm and shoulder findings of the ANSUR check, scripts/body_v2/fit/proportions.py):
# at the v3h stature (1.857 m) against ANSUR II male (stature-conditioned OLS), acromion -> fingertip 0.780 m vs 0.843 m
# (-3.0 SD): acromion-radiale 0.329 vs 0.356, radiale-stylion 0.261 vs 0.284, hand 0.189 vs 0.203; acromion height
# 1.510 vs 1.531 (-1.3 SD).  A skeleton change: the upper arm and forearm bones are lengthened, the hand scaled about the
# wrist, and the shoulder girdle (clavicle tip, scapula, arm) raised.  The skin follows its own bones (skin-weighted,
# like the skinning itself), so the elbow and wrist transitions stay continuous; the girdle lift fades out towards the
# neck so the neck is not shortened.  Kept as a separate field (PROP) so the overlap shrink below cannot undo it; the rig
# in this scene is edited to match (edits written to skeleton_edits.json).
ARM_U = float(os.environ.get("V2_ARM_UPPER_MM", "27")) / 1000.0
ARM_F = float(os.environ.get("V2_ARM_FORE_MM", "23")) / 1000.0
HAND_S = 1.0 + float(os.environ.get("V2_HAND_MM", "14")) / 1000.0 / 0.189
SH_UP = float(os.environ.get("V2_SHOULDER_UP_MM", "15")) / 1000.0
PROP = np.zeros_like(rest)
SKEL_EDITS = {}
_FORE = ("forearm", "forearm_tw0", "forearm_tw1")
_HAND = ("hand", "metacarpal_index", "metacarpal_middle", "metacarpal_ring", "metacarpal_pinky", "thumb_01", "thumb_02",
         "thumb_03") + tuple(f"{f_}_0{i}" for f_ in ("index", "middle", "ring", "pinky") for i in (1, 2, 3))


def _girdle(P):
    """shoulder-girdle lift weight of points (torso side), 0 at the neck, 1 out at the shoulder"""
    return ss((np.abs(P[..., 0]) - 0.08) / 0.12) * ss((P[..., 2] - 1.25) / 0.10)


if ARM_U or ARM_F or HAND_S != 1.0 or SH_UP:
    _armw = np.zeros(nv)
    for sd in ("r", "l"):
        bn = rig.data.bones
        gh = np.array(bn[f"upperarm_{sd}"].head_local); el = np.array(bn[f"upperarm_{sd}"].tail_local)
        wr = np.array(bn[f"hand_{sd}"].head_local)
        dU = (el - gh) / np.linalg.norm(el - gh); dF = (wr - el) / np.linalg.norm(wr - el)
        LU = np.linalg.norm(el - gh); LF = np.linalg.norm(wr - el)

        def mapping(P, kind):
            """displacement of points P belonging to a bone of the given kind"""
            if kind == "upper":
                t = np.clip((P - gh) @ dU / LU, 0, 1); return np.outer(t * ARM_U, dU)
            if kind == "fore":
                t = np.clip((P - el) @ dF / LF, 0, 1); return np.outer(np.ones(len(P)) * ARM_U, dU) + np.outer(t * ARM_F, dF)
            if kind == "hand":
                return ARM_U * dU + ARM_F * dF + (HAND_S - 1.0) * (P - wr)
            return np.zeros_like(P)

        kinds = [(f"upperarm_{sd}", "upper"), (f"shoulder_cap_{sd}", "upper")] + [(f"{b}_{sd}", "fore") for b in _FORE] + [(f"{b}_{sd}", "hand") for b in _HAND]
        for bname, kind in kinds:
            if bname not in gidx or gidx[bname] not in W:
                continue
            w = W[gidx[bname]]; m = w > 0
            PROP[m] += w[m, None] * mapping(rest[m], kind); _armw[m] += w[m]
        # skeleton: arm bones follow the same mapping (head with the parent's rule at the joint), girdle bones are lifted
        for bname, kind in kinds:
            if bname in bn:
                h_, t_ = np.array(bn[bname].head_local), np.array(bn[bname].tail_local)
                SKEL_EDITS[bname] = [(h_ + mapping(h_[None], kind)[0]).tolist(), (t_ + mapping(t_[None], kind)[0]).tolist()]
    # shoulder girdle lift: the whole arm, plus the torso skin fading towards the neck and down the side
    lift = np.maximum(np.clip(_armw, 0, 1), _girdle(rest) * (1 - HEAD))
    for _ in range(6):
        lift = 0.5 * lift + 0.5 * avg(lift)
    # full lift on the arm itself; around the trapezius the raw arm weights jump vertex to vertex, and taking them
    # unsmoothed pleated the neck once the mesh was refined (v5c-v5i) - only clearly-arm skin is forced to 1
    lift = np.maximum(lift, ss((np.clip(_armw, 0, 1) - 0.6) / 0.35))
    for _ in range(4):
        lift = np.where(_armw > 0.95, lift, 0.5 * lift + 0.5 * avg(lift))
    PROP[:, 2] += SH_UP * lift
    for bname in list(SKEL_EDITS):
        SKEL_EDITS[bname] = [(np.array(p) + [0, 0, SH_UP]).tolist() for p in SKEL_EDITS[bname]]
    for sd in ("r", "l"):
        for bname in (f"scapula_{sd}", f"muscle_lat_{sd}", f"muscle_pec_{sd}", f"muscle_trap_{sd}", f"clavicle_{sd}"):
            b_ = rig.data.bones[bname]; h_, t_ = np.array(b_.head_local), np.array(b_.tail_local)
            SKEL_EDITS[bname] = [(h_ + [0, 0, SH_UP * float(_girdle(h_))]).tolist(), (t_ + [0, 0, SH_UP * float(_girdle(t_))]).tolist()]
        # the scapula moves with the arm: full lift
        b_ = rig.data.bones[f"scapula_{sd}"]
        SKEL_EDITS[f"scapula_{sd}"] = [(np.array(b_.head_local) + [0, 0, SH_UP]).tolist(), (np.array(b_.tail_local) + [0, 0, SH_UP]).tolist()]
    # R100 (reshape to the reference, owner's choice): posture.  Side silhouettes (scripts/body_v2/fit/silfit.py, both
    # anchored at the hips) - above the chest the model's front AND back were both forward of the reference by about the
    # same amount (0.80 of stature: centre -0.014; 0.84: -0.022), i.e. the upper body and head leaned forward (the
    # reference stands chest-up).  A rest-posture change of the skeleton: the spine_03 subtree (upper chest, girdle,
    # arms, neck, head) is rotated back by V2_POSTURE_DEG about the spine_02/03 joint; the skin follows through its own
    # weights (like R81), the rig is edited to match.
    POST = float(os.environ.get("V2_POSTURE_DEG", "9"))
    if POST:
        _piv = np.array(rig.data.bones["spine_03"].head_local)
        _sub = [b.name for b in rig.data.bones if b.name == "spine_03" or any(p.name == "spine_03" for p in b.parent_recursive)]
        _a = -np.radians(POST)
        _R = np.array([[1, 0, 0], [0, np.cos(_a), -np.sin(_a)], [0, np.sin(_a), np.cos(_a)]])
        _wr = np.zeros(nv)
        for bname in _sub:
            if bname in gidx and gidx[bname] in W:
                _wr += W[gidx[bname]]
        _wr = np.clip(_wr, 0, 1)
        for _ in range(int(os.environ.get("V2_POSTURE_SMOOTH", "20"))):   # raw weights are jagged where spine_02 / helper
            _wr = 0.5 * _wr + 0.5 * avg(_wr)                               # bones share skin: x a 2-3 cm move = wrinkles (v12e)
        V1_ = rest + PROP
        PROP += _wr[:, None] * (((V1_ - _piv) @ _R.T + _piv) - V1_)
        for bname in _sub:
            b_ = rig.data.bones[bname]
            h_, t_ = SKEL_EDITS.get(bname, [list(b_.head_local), list(b_.tail_local)])
            SKEL_EDITS[bname] = [((np.array(h_) - _piv) @ _R.T + _piv).tolist(), ((np.array(t_) - _piv) @ _R.T + _piv).tolist()]
        # the head stays level (v12d: rotating it with the chest tipped the face up): counter-rotate the neck subtree about
        # the (moved) neck base, using the neck's own skin weights - a chest-up posture with a level head, like the reference
        _np = np.array(SKEL_EDITS["neck"][0])
        _nsub = [b.name for b in rig.data.bones if b.name == "neck" or any(p.name == "neck" for p in b.parent_recursive)]
        _Rb = _R.T
        _wn = np.zeros(nv)
        for bname in _nsub:
            if bname in gidx and gidx[bname] in W:
                _wn += W[gidx[bname]]
        _wn = np.clip(_wn, 0, 1)
        for _ in range(int(os.environ.get("V2_POSTURE_SMOOTH", "20"))):   # (v12e: a jagged neck weight drew a line down the neck)
            _wn = 0.5 * _wn + 0.5 * avg(_wn)
        V2_ = rest + PROP
        PROP += _wn[:, None] * (((V2_ - _np) @ _Rb.T + _np) - V2_)
        for bname in _nsub:
            h_, t_ = SKEL_EDITS[bname]
            SKEL_EDITS[bname] = [((np.array(h_) - _np) @ _Rb.T + _np).tolist(), ((np.array(t_) - _np) @ _Rb.T + _np).tolist()]
        POSTURE_REPORT = {"deg": POST, "pivot": _piv.round(3).tolist(), "bones": len(_sub), "head_level_bones": len(_nsub)}
    # R109 (owner: "Verify the pelvic skeleton and hip joint centres before modifying proportions"): the deformation rig's
    # thigh heads sit at (+-0.092, 0.0, 0.960), the approved anatomical master's hip joint centres (anat_femur_* heads,
    # LM_hip_bone_*__HJC) at (+-0.0833, -0.0193, 0.9297) - which agree with the Bell et al. 1990 and Harrington et al. 2007
    # HJC regressions from the ASIS landmarks within ~5 mm.  So the skin pivoted ~3 cm above and 2 cm behind the real hip
    # joint.  V2_HIP_PIVOT=anat moves the thigh heads onto the anatomical HJC (tails - the knees - unchanged).
    if os.environ.get("V2_HIP_PIVOT", "anat") == "anat":
        for bname, sg in (("thigh_r", 1.0), ("thigh_l", -1.0)):
            b_ = rig.data.bones[bname]
            h_, t_ = SKEL_EDITS.get(bname, [list(b_.head_local), list(b_.tail_local)])
            SKEL_EDITS[bname] = [[sg * 0.0833, -0.0193, 0.9297], list(t_)]
        HIP_PIVOT_REPORT = {"thigh_head_before": [0.092, 0.0, 0.96], "thigh_head_after": [0.0833, -0.0193, 0.9297], "source": "HGPT_ANATOMICAL_MASTER anat_femur_* heads"}
    _before = {b.name: [list(b.head_local), list(b.tail_local)] for b in rig.data.bones if b.name in SKEL_EDITS}
    bpy.context.view_layer.objects.active = rig
    rig.hide_set(False); rig.hide_viewport = False
    bpy.ops.object.mode_set(mode="EDIT")
    eb = rig.data.edit_bones
    for _pass in range(2):                                   # connected children snap to the parent's tail: set twice
        for bname, (h_, t_) in SKEL_EDITS.items():
            eb[bname].head = Vector(h_); eb[bname].tail = Vector(t_)
    bpy.ops.object.mode_set(mode="OBJECT"); bpy.context.view_layer.update()
    _err = max(float(np.linalg.norm(np.array(rig.data.bones[b].head_local) - np.array(h_))) for b, (h_, t_) in SKEL_EDITS.items())
    (OUT / "skeleton_edits.json").write_text(json.dumps({"note": "R81 rig edits (rest head/tail, metres): before -> after", "arm_upper_mm": ARM_U * 1000,
        "arm_fore_mm": ARM_F * 1000, "hand_scale": HAND_S, "shoulder_up_mm": SH_UP * 1000, "max_head_error_m": _err,
        "bones": {b: {"before": _before[b], "after": SKEL_EDITS[b]} for b in SKEL_EDITS}}, indent=1))
# R77 (owner chose "Standing pose"): the body is shown standing with the arms ~9 deg out, so overlaps are tested in that
# pose (in the build pose the forearms hang against the hips, and testing there removed all new forearm volume)
import math as _m
import build_original_movement_benchmarks_blender as _bench
import original_v1_review_candidate_drives as _drives
_STAND = tuple(float(x) for x in os.environ.get("V2_STAND", "16:6").split(":"))   # R104: arms out ~16 deg like the reference
_fitkey = body.shape_key_add(name="V2_FIT", from_mix=False); _fitkey.value = 1.0


def stand_eval(offsets):
    _fitkey.data.foreach_set("co", (rest + PROP + offsets).ravel().astype(np.float32))
    _bench._reset(rig)
    for sd, sg in (("r", -1.0), ("l", 1.0)):
        pb = rig.pose.bones[f"upperarm_{sd}"]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (0.0, 0.0, _m.radians(sg * _STAND[0]))
        fb = rig.pose.bones[f"forearm_{sd}"]; fb.rotation_mode = "XYZ"; fb.rotation_euler = (_m.radians(-_STAND[1]), 0.0, 0.0)
    bpy.context.view_layer.update(); _drives.drive(rig, body); bpy.context.view_layer.update()
    pp, _ = _bench._evaluated(body)
    return np.array([tuple(v) for v in pp])


for it in range(int(os.environ.get("V2_OVERLAP_ITERS", "40"))):
    P_ = stand_eval(off)
    tr = _BVH.FromPolygons([Vector(v) for v in P_], _ft, all_triangles=True)
    pr = [(a_, b_) for a_, b_ in tr.overlap(tr) if a_ < b_ and not (_fs[a_] & _fs[b_])]
    ov_log.append(len(pr))
    if not pr:
        break
    hit = np.zeros(nv); hit[np.unique(faces[np.array(pr).ravel()].ravel())] = 1.0
    for _ in range(3):
        hit = np.maximum(hit, avg(hit))
    for _ in range(6):                                  # R77e: smooth shrink (patchy shrinking crumpled the deltoid skin)
        hit = 0.5 * hit + 0.5 * avg(hit)
    off = off * (1.0 - 0.30 * np.clip(hit * 2, 0, 1))[:, None]
    # and relax the offset vectors where they were shrunk
    zone = np.clip(hit * 3, 0, 1)[:, None]
    for _ in range(3):
        off = off + 0.5 * zone * (np.stack([avg(off[:, k]) for k in range(3)], axis=1) - off)
# R83 (owner chose "Refine the torso mesh"): the shape above is sculpted on the R41 mesh, where every relax / smoothing
# step was tuned (a first try that refined first, v5a, turned those hop-counted steps 3-4x shorter: noisy skin, crumpled
# thighs).  Now the mesh is refined at the end (refine_torso_blender.py: torso / pelvis / glute / neck triangles split
# to <= V2_REFINE_MM, skin weights and every shape key carried over linearly), the finished offset fields are carried
# over by the exact linear map, and the details that need the finer mesh are added on it with sizes in millimetres.
DETAIL_REPORT = {}
if REFINE_MM > 0:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from refine_torso_blender import refine
    body.shape_key_remove(_fitkey)
    # body-part label for the carry-over: the whole arm chain incl. hand and fingers, from the raw skin weights (ARM
    # above stops at the hand bone, so fingers counted as "not arm")
    _arm_c = np.zeros(nv)
    for _gname, _gi in gidx.items():
        if _gname.rsplit("_", 1)[0] in ("upperarm", "shoulder_cap", "forearm", "forearm_tw0", "forearm_tw1") + _HAND and _gi in W:
            _arm_c += W[_gi]
    _arm_c = np.clip(_arm_c, 0, 1)
    _rest_c, _nrm_c, _off_c, _ft_c, _prop_c = rest.copy(), nrm_s.copy(), off.copy(), faces.copy(), PROP.copy()
    # R103: finer discs at the nipples (target 0.751 of stature, |x| 0.077, as in the detail stage), on the front skin
    # (v12s: at |x| 0.077 the nipple sat on the pec's outer lower corner; the reference's are ~0.070 out, on the pec face)
    NIP_X = float(os.environ.get("V2_NIPPLE_X", "0.072")); NIP_Z = float(os.environ.get("V2_NIPPLE_Z", "0.734"))
    _Qc = rest + PROP + off; _zbc = _Qc[:, 2].min(); _Hc = _Qc[:, 2].max() - _zbc
    _spots = []
    if float(os.environ.get("V2_NIPPLE_REFINE_MM", "0")) > 0:
        for _sg in (1, -1):
            _rn = np.sqrt((np.abs(_Qc[:, 0]) / _Hc - NIP_X) ** 2 + ((_Qc[:, 2] - _zbc) / _Hc - NIP_Z) ** 2)
            _rn = np.where((np.sign(_Qc[:, 0]) == _sg) & (_Qc[:, 1] < 0) & (ARM < 0.3), _rn, 9)
            _spots.append((rest[int(np.argmin(_rn))].tolist(), 0.035, float(os.environ.get("V2_NIPPLE_REFINE_MM", "2.0"))))
    # R106 (owner: "rebuild the neck mesh and make the collarbones show"): the neck base / collarbone area rebuilt with
    # even triangles (rest z 1.44-1.58 - below the jaw, |x| < 0.22).  Edge flips only by default (V2_NECK_REMESH_MM 99): v13i
    # also split the area to 4 mm, and the denser patch broke the hop-counted smoothing (jaw creases, 84 overlaps left)
    _rmm = float(os.environ.get("V2_NECK_REMESH_MM", "99"))
    _regions = [((1.44, 1.58, 0.22), _rmm)] if _rmm > 0 else []
    # R113b: the upper back / scapulae too - their mottling is R41's sliver triangulation (in the V1 surface too, and 40
    # normal-only Taubin steps did not remove it), like the neck base
    if os.environ.get("V2_BACK_FLIPS", "1") == "1":
        _regions.append(((1.16, 1.44, 0.22), 99.0))
    # R114 (owner: "There look to be a lot of wrinkly skin"): the same Delaunay flips over the whole body below the head
    # (arms, legs, torso; rest z 0.03-1.60) - R41's sliver triangles everywhere shade as fine wrinkles
    if os.environ.get("V2_BODY_FLIPS", "1") == "1":
        _regions.append(((0.03, 1.60, 0.40), 99.0))
    # R111 (owner: "Fix mesh topology, skin weights and corrective deformations as necessary"): the crotch skin was
    # pulled between thigh_l, thigh_r and the pelvis with sharp weight boundaries - in 40 deg abduction the two inner
    # thighs crossed in an X at the crotch (2,000+ overlap pairs, p0/p1).  Relax all deform weights together around the
    # crotch and the upper inner thighs (sum per vertex kept), on the coarse mesh so the refinement carries it over.
    CROTCH_W = int(os.environ.get("V2_CROTCH_WEIGHTS", "40"))   # p3: 15 passes within 11 cm moved too little
    if CROTCH_W > 0:
        _Qc2 = rest + off
        _mid = (np.abs(_Qc2[:, 0]) < 0.006) & (ARM < 0.3)
        _ic = np.nonzero(_mid)[0][np.argmin(_Qc2[_mid, 2])]
        _dc = np.linalg.norm(_Qc2 - _Qc2[_ic], axis=1)
        _a = ss((float(os.environ.get("V2_CROTCH_WEIGHTS_R", "0.18")) - _dc) / 0.05) * (ARM < 0.3)
        _defn = {b_.name for b_ in rig.data.bones if b_.use_deform}
        _gs = [g for g, i in gidx.items() if g in _defn and i in W and (W[i][_a > 0] > 1e-4).any()]
        Wm = np.stack([W[gidx[g]] for g in _gs], axis=1); _sum0 = Wm.sum(1); _W0 = Wm.copy()
        for _ in range(CROTCH_W):
            Wm = Wm + 0.5 * _a[:, None] * (np.stack([avg(Wm[:, k]) for k in range(Wm.shape[1])], axis=1) - Wm)
        Wm *= (_sum0 / np.maximum(Wm.sum(1), 1e-9))[:, None]
        _chg = np.nonzero(_a > 0)[0]
        for k, g in enumerate(_gs):
            vg = body.vertex_groups[g]
            for i in _chg:
                if Wm[i, k] > 1e-4:
                    vg.add([int(i)], float(Wm[i, k]), "REPLACE")
                elif W[gidx[g]][i] > 0:
                    vg.remove([int(i)])
            W[gidx[g]] = Wm[:, k]
        DETAIL_REPORT["crotch_weights"] = {"iterations": CROTCH_W, "groups": _gs, "vertices": int(len(_chg)),
                                           "max_change": round(float(np.abs(Wm - _W0).max()), 3)}
    # R111b: designed inner-thigh weights.  Relaxing did not stop the inner thighs crossing in an X at 40 deg abduction
    # (p3/p5, already in p0): the upper inner-thigh skin is all thigh weight, so averaging changes nothing there.  On a
    # real body that skin stays largely with the pelvis and stretches: move part of each thigh's weight on the inner
    # upper thigh to the pelvis - up to V2_INNER_THIGH_PELVIS (0.5) at the crotch, fading out ~10 cm down the thigh.
    ITP = float(os.environ.get("V2_INNER_THIGH_PELVIS", "0.5"))
    if ITP > 0 and "pelvis" in gidx:
        _Qc3 = rest + off; _zb3 = _Qc3[:, 2].min(); _H3 = _Qc3[:, 2].max() - _zb3
        _mid = (np.abs(_Qc3[:, 0]) < 0.006) & (ARM < 0.3)
        _cz3 = _Qc3[_mid, 2].min()
        _tri = _Qc3[faces]; _fn = np.cross(_tri[:, 1] - _tri[:, 0], _tri[:, 2] - _tri[:, 0])
        _vn = np.zeros_like(_Qc3); np.add.at(_vn, faces.ravel(), np.repeat(_fn, 3, axis=0))
        for _ in range(4):
            _vn = 0.5 * _vn + 0.5 * np.stack([avg(_vn[:, k]) for k in range(3)], axis=1)
        _vn /= np.maximum(np.linalg.norm(_vn, axis=1, keepdims=True), 1e-12)
        _inner = ss((-(_vn[:, 0] * np.sign(_Qc3[:, 0])) + 0.1) / 0.5)
        _band = ss((_Qc3[:, 2] - (_cz3 - 0.10)) / 0.08) * ss((_cz3 + 0.03 - _Qc3[:, 2]) / 0.03)
        _med = ss((0.06 - (np.abs(_Qc3[:, 0]))) / 0.04)
        _sh = ITP * _inner * _band * _med * (ARM < 0.3)
        for _ in range(10):
            _sh = 0.5 * _sh + 0.5 * avg(_sh)
        _pg = body.vertex_groups["pelvis"]; _moved = 0
        for side_ in ("thigh_l", "thigh_r"):
            if side_ not in gidx or gidx[side_] not in W:
                continue
            wt = W[gidx[side_]]; mv = wt * _sh; idx = np.nonzero(mv > 1e-4)[0]
            vg = body.vertex_groups[side_]
            for i in idx:
                vg.add([int(i)], float(wt[i] - mv[i]), "REPLACE")
                _pg.add([int(i)], float(W[gidx["pelvis"]][i] + mv[i]), "REPLACE")
                W[gidx["pelvis"]][i] += mv[i]
            W[gidx[side_]] = wt - mv; _moved += len(idx)
        DETAIL_REPORT["inner_thigh_pelvis"] = {"max_share": ITP, "vertices": _moved}
    REFINE_REPORT, _mi, _mw = refine(body, th_mm=REFINE_MM, spots=_spots, regions=_regions)
    np.savez_compressed(OUT / "refine_map.npz", idx=_mi.astype(np.int32), w=_mw.astype(np.float32))
    print("V2_REFINE", json.dumps(REFINE_REPORT), flush=True)

    def _lift(X):
        return (X[_mi] * (_mw[..., None] if X.ndim == 2 else _mw)).sum(1)

    off, PROP, amt, ARM, LEG, HEAD, _arm_f = (_lift(X) for X in (off, PROP, amt, ARM, LEG, HEAD, _arm_c))
    me = body.data; nv = len(me.vertices)
    rest = np.array([v.co[:] for v in me.vertices]); nrm = np.array([v.normal[:] for v in me.vertices])
    faces = np.array([p.vertices[:] for p in me.polygons])
    nb = [[] for _ in range(nv)]
    for f in faces:
        for i in range(3):
            nb[f[i]] += [f[(i + 1) % 3], f[i - 1]]
    nb = [np.unique(n) for n in nb]
    rows = np.repeat(np.arange(nv), [len(n) for n in nb]); cols = np.concatenate(nb); deg = np.array([len(n) for n in nb], float)
    _fs = [set(f) for f in faces]; _ft = [tuple(f) for f in faces]
    _fitkey = body.shape_key_add(name="V2_FIT", from_mix=False); _fitkey.value = 1.0
    # the sculpt offsets carried over linearly are piecewise linear over the old triangles, and their kinks along every
    # old edge showed as a diamond cross-hatch on the fine mesh (v5d/v5e).  Carry them over smoothly instead: Gaussian
    # weights over the nearby old vertices (sigma from the local old edge length), only from skin facing the same way
    from scipy.spatial import cKDTree as _KD
    _ec = np.concatenate([_ft_c[:, [0, 1]], _ft_c[:, [1, 2]], _ft_c[:, [2, 0]]])
    _el = np.linalg.norm(_rest_c[_ec[:, 0]] - _rest_c[_ec[:, 1]], axis=1)
    # longest incident edge (not the mean): R41's slivers are dense one way and sparse the other, and a sigma from the
    # mean left one bump per old vertex along the neck ring (v5f-v5m)
    _hc = np.zeros(len(_rest_c)); np.maximum.at(_hc, _ec[:, 0], _el); np.maximum.at(_hc, _ec[:, 1], _el)
    # search only the body's old vertices (arms keep the exact map below): in the bind pose the hands hang against the
    # thighs, and their dense vertices filled the whole neighbour list of the hip skin (v5f-v5l: hip patches)
    _bodyc = np.nonzero(_arm_c < 0.5)[0]
    _dd, _jj = _KD(_rest_c[_bodyc]).query(rest, k=32); _jj = _bodyc[_jj]
    _sig = np.maximum(0.5 * _hc[_jj[:, 0]], 0.003)[:, None]
    nrm_f = nrm
    _ww = np.exp(-0.5 * (_dd / _sig) ** 2) * np.clip((_nrm_c[_jj] * nrm_f[:, None, :]).sum(2), 0, 1) ** 2
    _ww[:, 0] += 1e-9
    _ww /= _ww.sum(1, keepdims=True)
    # arms and hands (dense already, and the hands hang against the thighs in the bind pose) keep the exact linear map
    _a = np.clip((_arm_f - 0.3) / 0.4, 0, 1)[:, None]
    _off_lin = off.copy(); _off_g = (_off_c[_jj] * _ww[..., None]).sum(1)
    off = _a * off + (1 - _a) * _off_g
    # R105b: the skeleton-level field PROP the same way.  Carried over linearly, its 2-3 cm posture / girdle moves (R81,
    # R100) kinked along every old edge where they change fast - the streaky neck base and trapezius seen since v11e/v12
    # (in the unposed renders too, so not the correctives)
    if os.environ.get("V2_PROP_SMOOTH_TRANSFER", "1") == "1":
        PROP = _a * PROP + (1 - _a) * (_prop_c[_jj] * _ww[..., None]).sum(1)
    if os.environ.get("V2_DEBUG_TRANSFER"):
        np.savez_compressed(OUT / "transfer_debug.npz", lin=_off_lin.astype(np.float32), g=_off_g.astype(np.float32), a=_a[:, 0].astype(np.float32),
                            arm=_arm_f.astype(np.float32), rest=rest.astype(np.float32), wsum=_ww.max(1).astype(np.float32))
    # then remove the fine noise left by the coarse field (a cross-hatch 2-3 vertices across, v5d) and R41's own small
    # ripples: Taubin steps along the vertex normal only (no sliding), everywhere except the hands
    Q = rest + off
    # cotangent weights (clamped >= 0): on R41's long thin triangles, now refined, a plain neighbour average moves the
    # surface by its triangulation (neck pleats, v5c-v5j); the cotangent average smooths the surface itself
    _A, _B, _C = (rest[faces[:, k]] for k in range(3))

    def _cot(u, v):
        return (u * v).sum(1) / np.maximum(np.linalg.norm(np.cross(u, v), axis=1), 1e-12)

    _ci = np.clip(np.stack([_cot(_B - _A, _C - _A), _cot(_C - _B, _A - _B), _cot(_A - _C, _B - _C)], axis=1), 0, 20)
    _er = np.concatenate([faces[:, 1], faces[:, 2], faces[:, 2], faces[:, 0], faces[:, 0], faces[:, 1]])
    _ec2 = np.concatenate([faces[:, 2], faces[:, 1], faces[:, 0], faces[:, 2], faces[:, 1], faces[:, 0]])
    _ew = np.concatenate([_ci[:, 0], _ci[:, 0], _ci[:, 1], _ci[:, 1], _ci[:, 2], _ci[:, 2]]) * 0.5 + 1e-6
    _ws = np.zeros(nv); np.add.at(_ws, _er, _ew)

    def cavg(X):
        acc = np.zeros_like(X); np.add.at(acc, _er, _ew[:, None] * X[_ec2]); return acc / _ws[:, None]

    _keep = np.clip((ARM - 0.5) * 4, 0, 1) * (rest[:, 2] < 0.97)
    _w = 1.0 - _keep
    # R41's own neck ring is slightly zig-zag (pleats once refined): many more steps there
    _neck = ss(1 - np.abs(rest[:, 2] - 1.57) / 0.09) * (1 - _keep)
    for _ in range(int(os.environ.get("V2_FINE_NECK_SMOOTH", "40"))):
        for lam in (0.5, -0.53):
            tri = Q[faces]; fn_ = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
            vn_ = np.zeros_like(Q); np.add.at(vn_, faces.ravel(), np.repeat(fn_, 3, axis=0))
            vn_ /= np.maximum(np.linalg.norm(vn_, axis=1, keepdims=True), 1e-12)
            L_ = cavg(Q) - Q
            Q = Q + lam * _neck[:, None] * (L_ * vn_).sum(1)[:, None] * vn_
    for _ in range(int(os.environ.get("V2_FINE_NORMAL_SMOOTH", "12"))):
        for lam in (0.5, -0.53):
            tri = Q[faces]; fn_ = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
            vn_ = np.zeros_like(Q); np.add.at(vn_, faces.ravel(), np.repeat(fn_, 3, axis=0))
            vn_ /= np.maximum(np.linalg.norm(vn_, axis=1, keepdims=True), 1e-12)
            L_ = cavg(Q) - Q
            Q = Q + lam * _w[:, None] * (L_ * vn_).sum(1)[:, None] * vn_
    off = Q - rest
    # normals of the sculpted surface, smoothed ~1 cm
    tri = Q[faces]; fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    qn = np.zeros_like(Q); np.add.at(qn, faces.ravel(), np.repeat(fn, 3, axis=0))
    for _ in range(6):
        qn = 0.5 * qn + 0.5 * np.stack([avg(qn[:, k]) for k in range(3)], axis=1)
    qn /= np.maximum(np.linalg.norm(qn, axis=1, keepdims=True), 1e-12)
    zb = Q[:, 2].min(); Hs = Q[:, 2].max() - zb

    def groove(pts, half_w, depth_mm, facing):
        """soft groove along a polyline of (|x|, z) points, on skin facing `facing` (y sign), faded at both ends"""
        g = np.zeros(nv); ax = np.abs(Q[:, 0])
        segs = list(zip(pts[:-1], pts[1:])); total = sum(np.linalg.norm(np.subtract(b, a)) for a, b in segs); run = 0.0
        for a, b in segs:
            a = np.array(a); b = np.array(b); d = b - a; L = np.linalg.norm(d); u = d / L
            p = np.stack([ax, Q[:, 2]], axis=1) - a
            t = np.clip(p @ u / L, 0, 1); dist = np.linalg.norm(p - np.outer(t * L, u), axis=1)
            s_ = (run + t * L) / total
            g = np.maximum(g, np.exp(-0.5 * (dist / half_w) ** 2) * ss(s_ / 0.15) * ss((1 - s_) / 0.15))
            run += L
        g *= ss((facing * qn[:, 1] - 0.15) / 0.4) * (1 - ARM)
        return -qn * (depth_mm / 1000.0 * g)[:, None]

    # R84 (owner: "please notice the detail in the muscles like the abs etc and how they should look"): measured on both
    # reference figures (fractions of stature): abs top 0.70-0.71 under the pecs, tendinous intersections ~0.685, 0.663,
    # 0.640, navel 0.61; each rectus column ~6-8 cm wide, soft rounded segments; linea alba thin, sternum to navel, gone
    # below it; smooth lower belly; full rounded pecs with a curved lower border rising to the armpit and a sternal
    # groove; serratus fingers on the side of the ribs.  The model's abs were R41's own boxy grid (too narrow, a deep
    # groove running below the navel).  So: erase that grid (normal-only cotangent smoothing of the front of the belly),
    # then sculpt the front torso muscles as a height field along the normal, sizes in mm.
    MUSC = float(os.environ.get("V2_MUSCLE_FRONT", "1"))
    if MUSC > 0:
        fz_ = (Q[:, 2] - zb) / Hs; ax_ = np.abs(Q[:, 0])
        front_ = ss((-qn[:, 1] - 0.25) / 0.35)
        er = ss((fz_ - 0.545) / 0.02) * ss((0.75 - fz_) / 0.02) * ss((0.165 - ax_) / 0.03) * front_ * (1 - _keep)
        # R86: the chest too (R41's own pec shape left a crease across it at ~0.75), so the new pecs start clean
        er = np.maximum(er, ss((fz_ - 0.70) / 0.02) * ss((0.815 - fz_) / 0.02) * ss((0.17 - ax_) / 0.03) * front_ * (1 - _keep))
        # R95b: and the outer lower corner of the pec, into the front of the armpit (R41's own notch there, exaggerated by
        # the pec into a crumpled 'beak' in the side view, v10c-v10f) - off the arm itself
        er = np.maximum(er, ss((fz_ - 0.70) / 0.02) * ss((0.80 - fz_) / 0.02) * ss((ax_ - 0.12) / 0.02) * ss((0.215 - ax_) / 0.02)
                        * ss((0.4 - ARM) / 0.3) * ss((-qn[:, 1] + 0.3) / 0.4) * (1 - _keep))
        for _ in range(int(os.environ.get("V2_ABS_ERASE", "150"))):
            for lam in (0.5,):                    # plain (shrinking) steps: Taubin keeps grooves this broad (v6a)
                tri = Q[faces]; fn_ = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
                vn_ = np.zeros_like(Q); np.add.at(vn_, faces.ravel(), np.repeat(fn_, 3, axis=0))
                vn_ /= np.maximum(np.linalg.norm(vn_, axis=1, keepdims=True), 1e-12)
                Q = Q + lam * er[:, None] * ((cavg(Q) - Q) * vn_).sum(1)[:, None] * vn_
        off = Q - rest
        h = np.zeros(nv)                                                     # mm, + out along the normal
        # R86 (owner on v7b: "The abs are still not right ... they aren't just blocks. They are more rounded and wider ...
        # The top of abs is curved and also the visibility of them is defined but not so prominent.  The pecs still need
        # better defined"): measured on the reference torso - rectus columns out to |x| ~0.07 m, the top row under an arch
        # that follows the rib margin (high at the sternum, lower to the sides), segments soft rounded plateaus with shallow
        # valleys; pecs full masses reaching almost to the armpit, lower border nearly level across the middle and rising
        # towards the armpit, with a crisp shadow under it.
        # R87 (owner: "the abs need to be bigger ... how wide they are in relation to the body and also height"): v8c had
        # the column edge in metres where it was measured as a fraction of stature.  Reference (fractions of stature, on
        # a x/y grid): rectus edge at |x| 0.065 (navel) - 0.072 (0.66) - 0.076 (0.70), i.e. ~80 % of the front of the
        # waist; top under the pecs at 0.715, arching down to ~0.70 at the edge; intersections ~0.640, 0.665, 0.690.
        xo = Hs * np.interp(fz_, [0.50, 0.56, 0.61, 0.64, 0.67, 0.70, 0.72], [0.030, 0.048, 0.056, 0.064, 0.071, 0.062, 0.058])
        # R89 (owner: "Still too many abs ... count how many you have"): contrast-stretched zoom of the reference - three
        # pairs: top 0.705-0.735 right under the pecs (pec lower border ~0.742 at the centre), middle (largest) 0.665-0.705,
        # bottom (faint) 0.642-0.665, then smooth to the navel.  v9f's pec border sat at ~0.725 and the abs top at 0.716,
        # so the strip between them read as a fourth row.
        ftop = 0.706 - 0.10 * ax_ / Hs                                         # R91: top of the abs at the owner's line (0.706)
        top = ss((ftop - fz_) / 0.010)
        pad = ss((xo - ax_) / 0.018) * ss((fz_ - 0.505) / 0.03) * top
        h += 2.0 * pad
        # segments: rounded plateaus (smoothstep shoulders), the valleys between them are the intersections; the top row's
        # upper edge follows the arch
        ints = [0.642, 0.665, 0.705]
        seg = np.zeros(nv)
        # R90 (owner: "The abs have more of a contour than what you have. Use the reference as a guide"): each pair now
        # has its own outline, measured on the contrast-stretched reference (x and z as fractions of stature):
        #   top    0.705-0.735, narrower at the top (follows the rib arch: |x| 0.060 at the top, 0.071 at the bottom),
        #          lower edge sloping down to the side;
        #   middle 0.665-0.705, the largest and widest (|x| to 0.075), well rounded corners;
        #   bottom 0.642-0.665, smaller (|x| to 0.063), lower edge a soft U.
        # Each block is a rounder dome (super-ellipse power 2.3), its height highest a little above its centre.
        # R91 (owner drew the line: "It's the line of the top of the abs in the reference drawing. This is where it should
        # be. Also look at the shape of the abs"): the top of the abs is at ~0.706 of stature; the band 0.706-0.74 under the
        # pecs is smooth lower ribs, not a row (R89/R90 had counted it as the top pair).  Three pairs below the line -
        # 0.684-0.706, 0.660-0.684, 0.636-0.660 - inside a rounded shield outline: widest at the middle pair (|x| ~0.071),
        # narrower at the top (~0.060) and towards the navel (~0.056).
        xh = ax_ / Hs
        # R92 (owner: "you have the abs sitting too high and almost at the bottom of the pecs"): contrast zoom of the
        # reference with the owner's top line at ~0.709 - below it only two pairs: a tall pair 0.665-0.707 and a pair
        # 0.635-0.665, then smooth to the navel.  v9j squeezed three short rows into 0.636-0.706, so the visible blocks
        # sat high, against the pecs.
        blocks = [  # (z_lo(x), z_hi(x), x_out at z_lo, x_out at z_hi, amp mm)
            (0.665 + 0.00 * xh, 0.707 - 0.10 * xh, 0.071, 0.060, 9.0),
            (0.635 + 0.10 * xh, 0.665 + 0.00 * xh, 0.060, 0.070, 7.5),
        ]
        seg = np.zeros(nv)
        for zlo_, zhi_, xa_, xb_, amp_ in blocks:
            t_ = np.clip((fz_ - zlo_) / np.maximum(zhi_ - zlo_, 1e-4), 0, 1)
            xout = Hs * (xa_ + (xb_ - xa_) * t_)
            u_ = np.clip((ax_ - 0.004) / np.maximum(xout - 0.004, 1e-3), 0, 1)
            # dome centred a little above the middle of the block and towards the middle of the column
            r_ = (np.abs(2 * u_ - 1.0) ** 2.3 + np.abs((2 * t_ - 1.0) - 0.12) ** 2.3) ** (1 / 2.3)
            # soft edges (cos^2): a steep edge read as a hard horizontal line (v9g/v9h); the pillows meet in gentle valleys
            # R93 (owner on v9l: "The abs look too raised ... it's a slight contour and definition", marking the outer
            # ends of the blocks): lower relief, and each block fades towards its outer end instead of stepping down
            seg += amp_ * (1 - 0.55 * u_ ** 1.5) * np.cos(0.5 * np.pi * np.clip(r_, 0, 1)) ** 2 * (fz_ > zlo_) * (fz_ < zhi_) * (ax_ < xout)
        h += float(os.environ.get("V2_ABS_SEG_SCALE", "0.6")) * seg
        top = ss((0.706 - 0.10 * xh - fz_) / 0.010)
        # linea alba: sternum to navel, fading out below it
        # R102: stops at the top of the abs - between the pecs the reference has a soft valley, not a line (v12i)
        la = np.interp(fz_, [0.565, 0.60, 0.62, 0.70, 0.73], [0, 0.6, 1.0, 1.0, 0.0])
        h -= 2.5 * la * np.exp(-0.5 * (ax_ / 0.0060) ** 2)   # wide enough for the 4 mm mesh; frames the blocks (R87)
        # linea semilunaris: soft groove at the rectus' outer edge, above the navel
        h -= 1.0 * np.exp(-0.5 * ((ax_ - xo - 0.004) / 0.014) ** 2) * ss((fz_ - 0.60) / 0.03) * top
        # R94 (owner: "the pecs need to be better defined like the reference drawing"): measured on the reference
        # (fractions of stature): lower border a rounded curve - 0.736 at the sternum, lowest ~0.728 mid-pec (|x| 0.05),
        # sweeping up to ~0.772 at the armpit (|x| 0.105); fullest in the lower half (0.74-0.77), fading up under the
        # clavicle (~0.825); a valley between the two pecs at the sternum; a soft deltopectoral line from the clavicle
        # down to the armpit; nipples at ~0.751, |x| ~0.077.  v9m's pec had a flat, straight lower step and little mass.
        # R101 (owner on v11e/v12: "the pecs look more like breasts rather than pecs"): R94-R98 had built a breast - a U-shaped
        # lower border, a dome fullest low down around the nipple, rolling under at the border, and a raised areola.  A male
        # pectoral is a flat fan-shaped plate: a lower border that rises from the sternum towards the armpit (only a slight
        # sag mid-pec), even thickness across, a firm lower edge, thinning up towards the clavicle; small flat nipples.
        PSTY = os.environ.get("V2_PEC_STYLE", "mass")
        # R103b: the pec is placed in the coordinates of the finished body (rest + PROP + off) - PROP's posture and girdle
        # lift raise the chest ~1.7 cm, so heights measured on the reference landed that much too high.  Re-measured on the
        # reference front panel (feet 918, top 18 px): nipples 0.734 of stature, |x| 0.072; lower border ~0.722 at the
        # sternum, lowest ~0.717 under the nipple, 0.727 at |x| 0.09, then turning up into the armpit (0.76 at |x| 0.105);
        # clavicles ~0.826.  (R94's 0.751 / 0.736 were ~0.017 high.)
        _fz_det = fz_
        if PSTY == "mass":
            _Vr = rest + PROP + off; fz_ = (_Vr[:, 2] - _Vr[:, 2].min()) / (_Vr[:, 2].max() - _Vr[:, 2].min())
        if PSTY == "mass":
            # R103 (owner on v12k: "Still not happy with the pecs" - too flat / thin, outline wrong, side view wrong, nipples):
            # the reference's own lower border again (R94's measurement: 0.735 sternum, ~0.729 mid-pec, 0.770 at |x| 0.105 -
            # the nipple sits ~2 cm above it; R101's rising border made the pec small), with a rounded lower-outer corner
            # turning up into the armpit.  What read as a breast was the dome across x, the roll-under and the raised
            # areola, not this border.
            # R104 (owner on v12z: "the pecs start too high maybe and don't drop down low enough ... they go below the
            # armpit"): on the reference the outer lower corner sits ~0.03 below the armpit (0.755) - the border stays low
            # out to |x| ~0.10 and only then turns up behind the arm
            zb_ = np.interp(xh, [0.0, 0.03, 0.05, 0.07, 0.09, 0.100, 0.108, 0.115, 0.125], [0.722, 0.719, 0.717, 0.718, 0.721, 0.726, 0.738, 0.758, 0.790])
        elif PSTY == "plate":
            zb_ = 0.733 - 0.25 * xh + 5.5 * xh ** 2            # 0.733 sternum, 0.730 (|x| 0.023), 0.746 (|x| 0.077), 0.772 (|x| 0.11)
        else:
            zb_ = 0.736 - 0.643 * xh + 9.66 * xh ** 2       # R94: through 0.736 / 0.728 (|x| 0.05) / 0.775 (|x| 0.105)
        zt_ = 0.826 if PSTY == "mass" else 0.832   # R97 (owner: "Too small / not full enough"): bigger, fuller pecs - higher, wider, 20 mm
        v_ = np.clip((fz_ - zb_) / (zt_ - zb_), 0, 1)
        # rounded mass (v10a's plate with a sharp step read as a shelf): a dome across the pec, fullest low-middle
        # R96: rounder and fuller up under the clavicle (v10e-g read flat above the nipple line)
        # R98 (owner, circling the side view: "just seems sharp finish. Refer to model"): the lower pec rolls under in a
        # rounded curve (sqrt-like rise from the border: near-vertical tangent, no corner), fullest around the nipple
        # line, then a long convex slope up to the clavicle
        if PSTY == "mass":
            # a thick muscle mass: a firm, rounded lower edge (quarter-ellipse rise over ~0.2 of the pec height - steep at the
            # border, no undercut), fullest from the nipple line to mid-pec, still ~80 % under the clavicle
            # (v12m's quarter-ellipse over 0.22 was near-vertical: a groove and a step in the side view; a sine quarter over
            # 0.40 keeps a definite but open ~30 deg edge)
            # R104: the mass sits low - fullest from the border to the nipple line, then a long gentle slope up to the
            # clavicle (~45 %); v12z (~80 % up high, R102) read as starting too high
            # (v13b: a rise over 0.30 of the pec height read as an edge ~2 cm above the true border, so the pec still
            # looked like it stopped at the armpit; ~45 deg over 0.20 puts the visible edge on the border)
            e_ = np.clip(v_ / float(os.environ.get("V2_PEC_EDGE", "0.20")), 0, 1)
            prof = np.sin(0.5 * np.pi * e_) * (1.0 - float(os.environ.get("V2_PEC_TOP_THIN_MASS", "0.55")) * ss((v_ - 0.30) / 0.70)) * (fz_ > zb_ - 0.002)
        elif PSTY == "plate":   # rounded lower edge (~5 cm rise), near-flat across the lower half, thinning to ~45 % towards the clavicle
            # R102 (owner: "Do the chest and pecs now", after v12h read flat up high): the reference pec stays full right up to
            # the clavicle - thinning only to ~80 % before the clavicle fade (v12h: ~55 %)
            prof = ss(v_ / 0.30) ** 0.75 * (1.0 - float(os.environ.get("V2_PEC_TOP_THIN", "0.20")) * ss((v_ - 0.55) / 0.45)) * (fz_ > zb_ - 0.002)   # v12g's 0.16 rise: a step in the side view
        else:
            prof = np.sqrt(ss(v_ / 0.30)) * np.sin(np.pi * np.clip(0.12 + 0.88 * v_, 0, 1)) ** 0.8 * (fz_ > zb_ - 0.002)
            prof /= 0.85
        # rounded towards the sternum too, so the two pecs make a soft valley there (not a thin line); out to the armpit
        if PSTY in ("plate", "mass"):   # even across the chest (a sin() dome across x read as a breast), soft valley at the sternum
            # R102: out to the deltopectoral line, as on the reference; R103b: thinning into the armpit (|x| 0.085-0.113) -
            # at full thickness there it pressed into the arm (2,000 standing overlaps, the shrink cut a crease, v12u)
            lat_ = ss((xh - 0.004) / 0.022) * (ss((0.120 - xh) / 0.028) if PSTY == "mass" else ss((0.120 - xh) / 0.032))   # R104: out under the arm
        else:
            lat_ = np.sin(np.pi * np.clip(xh / 0.116, 0, 1)) ** 0.7 * ss((0.108 - xh) / 0.040)   # wide outer fade (v11b: crease at the edge)
        # R95 (owner on v10c: "Still looks wrong. They need to be like the reference model"): side silhouettes, front
        # edge ahead of the front at 0.70 of stature (fraction of stature) - reference: 0.72 -0.003, 0.74 +0.002,
        # 0.75 +0.001 (the lower ribs / upper abs are as far forward as the pecs: one full, smooth chest curve; the pec
        # reads by its outline and a slight overhang); v10c: 0.72 +0.004, 0.74 +0.016, 0.75 +0.014 - the pec stood ~3 cm
        # proud of a recessed rib area, a shelf.  Lower pec projection, and fill the lower ribs forward up to the border.
        PEC = float(os.environ.get("V2_PEC_MM", {"plate": "16", "mass": "20"}.get(PSTY, "20")))
        _hp = PEC * prof * lat_ * ss(((0.828 if PSTY == "mass" else 0.832) - fz_) / 0.030)   # tapers out below the clavicle (v11a/b: neck stripes)
        if PSTY == "mass" and os.environ.get("V2_PEC_CLEARANCE", "1") == "1":
            # R103c: the fuller outer pec ran into the hanging arm in the standing pose (1,900 overlap pairs vs 305 without
            # it; the overlap shrink then cut a crease into the front of the armpit, v12u/v12v).  Limit the pec's thickness
            # to its clearance from the arm in that pose (less a 4 mm gap), as a smoothed ratio so the cut-back is soft.
            from scipy.spatial import cKDTree as _KD
            _Ps = stand_eval(off)
            _am = _arm_f > 0.5
            _cand = np.nonzero((_hp > 0.05) & ~_am)[0]
            _dist = np.full(nv, 9.0)
            _dist[_cand] = _KD(_Ps[_am]).query(_Ps[_cand])[0]
            _cap = np.clip((_dist - 0.004) * 1000.0, 0, None)
            _r = np.where(_hp > 0.05, np.clip(_cap / np.maximum(_hp, 1e-6), 0, 1), 1.0)
            for _ in range(30):
                _r = np.minimum(_r, 0.5 * _r + 0.5 * avg(_r))   # spread the cut-back (never raise it), then soften it
            for _ in range(int(os.environ.get("V2_PEC_CLEAR_SOFTEN", "120"))):   # R113: 30 left a hard vertical edge
                _r = 0.5 * _r + 0.5 * avg(_r)                                    # at the front of the armpit
            DETAIL_REPORT["pec_clearance"] = {"verts_limited": int((_r < 0.98).sum()), "min_ratio": round(float(_r.min()), 3)}
            _hp *= _r
        h += _hp
        RIB = float(os.environ.get("V2_LOWER_RIB_MM", "8"))
        rib = ss((fz_ - 0.686) / 0.025) * ss((zb_ - 0.002 - fz_) / 0.012) * ss((0.075 - xh) / 0.030)   # R98: off the lateral corner
        h -= float(os.environ.get("V2_PEC_SHADOW_MM", "1.8" if PSTY == "mass" else "1.4")) * np.exp(-0.5 * ((fz_ - zb_ + 0.001) / 0.0045) ** 2) * ss((0.098 - xh) / 0.012) * ss(xh / 0.012)   # soft shadow under the border
        h += RIB * rib
        # the front of the abdomen as one broad smooth volume (reference side view: the front is a near-vertical column
        # from the abs up to the pecs; the model's belly sat ~1 cm behind the chest)
        BELLY = float(os.environ.get("V2_BELLY_FILL_MM", "8"))
        h += BELLY * ss((fz_ - 0.585) / 0.03) * ss((0.735 - fz_) / 0.03) * np.exp(-0.5 * (xh / 0.055) ** 2)
        # deltopectoral line
        dl = np.abs(xh - np.interp(fz_, [0.76, 0.80, 0.83], [0.106, 0.100, 0.094]))
        h -= 0.7 * np.exp(-0.5 * (dl / 0.008) ** 2) * ss((fz_ - 0.765) / 0.01) * ss((0.83 - fz_) / 0.01)
        # nipples (small, as on the reference figure)
        _nx, _nz = {"plate": (0.075, 0.755), "mass": (NIP_X, NIP_Z)}.get(PSTY, (0.077, 0.751))   # mass: finished-body coords
        rn = np.sqrt((xh - _nx) ** 2 + (fz_ - _nz) ** 2) * Hs
        # R98 (owner: "Do we add nipple also to complete the pecs?"): areola (raised disc ~13 mm radius) and nipple
        NIP = float(os.environ.get("V2_NIPPLE_MM", {"plate": "1.5", "mass": "6.0"}.get(PSTY, "4")))
        if PSTY == "mass":   # R103: visible, like the reference's - a small firm nipple on a barely raised areola
            # the reference's nipple reads as a ~2 cm bump; sigma 5 mm is what the ~4-5 mm chest mesh can carry (v12p's
            # 3.2 mm vanished; v12s/v12t refined the mesh locally instead, and the unevenly smoothed patch crumpled)
            h += 0.6 * ss((0.014 - rn) / 0.004) + NIP * np.exp(-0.5 * (rn / float(os.environ.get("V2_NIPPLE_SIGMA_MM", "5.0")) * 1000) ** 2)
        elif PSTY == "plate":   # R101: a flat areola and a small nipple (the raised disc + 4 mm cone added to the breast look)
            h += 0.3 * ss((0.011 - rn) / 0.003) + NIP * np.exp(-0.5 * (rn / 0.0030) ** 2)
        else:
            h += 1.2 * ss((0.013 - rn) / 0.004) + NIP * np.exp(-0.5 * (rn / 0.0042) ** 2)
        fz_ = _fz_det
        # R103d: everything above (abs, linea alba, pecs, rib / belly fill, nipples) was placed by height and |x| alone, so
        # it was ALSO pushed out of the upper back and the backs of the armpits at the same heights (found from where the
        # standing-pose overlaps were, v12x: x +-0.17, y 0.0-0.12 - the back half).  Front-facing skin only from here on,
        # fading across the side of the chest.
        if os.environ.get("V2_FRONT_GATE", "1") == "1":
            h *= ss((-qn[:, 1] + 0.10) / 0.35)
        # serratus anterior: four fingers on the side of the ribs, angled down and forward
        lat_ = ss((np.abs(qn[:, 0]) - 0.35) / 0.3) * ss((-qn[:, 1] + 0.3) / 0.4)
        for k_, zf_ in enumerate([0.735, 0.718, 0.701, 0.684]):
            u_ = (fz_ - zf_) + 0.35 * (ax_ - 0.14)
            h += 1.6 * np.exp(-0.5 * (u_ / 0.0045) ** 2) * ss((ax_ - 0.105) / 0.012) * ss((0.165 - ax_) / 0.012) * lat_
        h *= (1 - _keep)
        for _ in range(3):
            h = 0.5 * h + 0.5 * avg(h)
        off += qn * (h / 1000.0)[:, None]
        Q = rest + off
        DETAIL_REPORT["nipple_h_mm"] = round(float(h[np.argmin(rn)]), 2); _nip_i = int(np.argmin(rn))
        DETAIL_REPORT["front_muscles"] = {"abs_erase_steps": int(os.environ.get("V2_ABS_ERASE", "150")), "intersections": ints,
                                           "max_mm": round(float(h.max()), 2), "min_mm": round(float(h.min()), 2)}
    # R105 (owner circled the reference's collarbone / neck-base area: "Can we create this on my model?").  Measured on the
    # reference front panel (fractions of stature, finished-body coordinates): clavicles a ridge from the jugular notch
    # (0.826) out to the acromion, arched to ~0.834 mid-length, a soft infraclavicular hollow under it and a dimple at the
    # deltopectoral triangle (|x| 0.085, 0.822); sternocleidomastoids from under the ears (|x| ~0.045, 0.872) down to the
    # notch (|x| ~0.012, 0.830), with a pit between their heads; trapezius slope fuller (silhouette widths 0.84 / 0.86:
    # reference 0.180 / 0.103 of stature, model 0.161 / 0.079).  The model had none of it, and fine crinkles there.
    NECKD = float(os.environ.get("V2_NECK_DETAIL", "1"))
    if NECKD > 0:
        _Vr = rest + PROP + off; _z0 = _Vr[:, 2].min(); _Hr = _Vr[:, 2].max() - _z0
        fr = (_Vr[:, 2] - _z0) / _Hr; xr = np.abs(_Vr[:, 0]) / _Hr
        noarm = np.clip(1 - _arm_f / 0.7, 0, 1); nohead = 1 - np.clip(HEAD, 0, 1)
        # 1. erase the crinkles over the neck base, collarbones and top of the shoulders (normal-only smoothing)
        er = ss((fr - 0.815) / 0.012) * ss((0.875 - fr) / 0.012)   # (from 0.815: keeps the upper pec) * ss((0.20 - xr) / 0.02) * noarm * nohead * (1 - _keep)
        Q = rest + off
        # even out R41's long thin neck-base triangles first (their streaky shading stayed after v13e/v13f's normal-only
        # smoothing): Taubin relax of the positions (uniform weights - slides vertices along the surface towards even
        # spacing, no shrinking); the vertices move a few mm at most and keep their skin weights
        for _ in range(int(os.environ.get("V2_NECK_RELAX", "25"))):
            Q = Q + 0.5 * er[:, None] * (np.stack([avg(Q[:, k]) for k in range(3)], axis=1) - Q)
            Q = Q - 0.53 * er[:, None] * (np.stack([avg(Q[:, k]) for k in range(3)], axis=1) - Q)
        for _ in range(int(os.environ.get("V2_NECK_ERASE", "150"))):
            tri = Q[faces]; fn_ = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
            vn_ = np.zeros_like(Q); np.add.at(vn_, faces.ravel(), np.repeat(fn_, 3, axis=0))
            vn_ /= np.maximum(np.linalg.norm(vn_, axis=1, keepdims=True), 1e-12)
            Q = Q + 0.5 * er[:, None] * ((cavg(Q) - Q) * vn_).sum(1)[:, None] * vn_
        off = Q - rest

        def _segd(px, pz, pts):
            """distance (stature units, front projection) from (|x|, f) to a polyline, and the position along it 0..1"""
            best = np.full(len(px), 9.0); tt = np.zeros(len(px)); L = 0.0
            segs = list(zip(pts[:-1], pts[1:])); lens = [np.hypot(b_[0] - a_[0], b_[1] - a_[1]) for a_, b_ in segs]; tot = sum(lens)
            for (a_, b_), l_ in zip(segs, lens):
                dx, dz = b_[0] - a_[0], b_[1] - a_[1]
                u = np.clip(((px - a_[0]) * dx + (pz - a_[1]) * dz) / max(l_ * l_, 1e-12), 0, 1)
                d = np.hypot(px - a_[0] - u * dx, pz - a_[1] - u * dz)
                m = d < best; best[m] = d[m]; tt[m] = (L + u[m] * l_) / tot
                L += l_
            return best, tt
        fronty = ss((-qn[:, 1] + 0.10) / 0.35)
        hn = np.zeros(nv)
        # 2. clavicles: a rounded ridge, a soft hollow under it, a dimple at the deltopectoral triangle
        cl = [(0.012, 0.826), (0.030, 0.830), (0.050, 0.833), (0.070, 0.834), (0.090, 0.833), (0.110, 0.830), (0.125, 0.827)]
        dcl, tcl = _segd(xr, fr, cl)
        endf = ss(tcl / 0.08) * ss((1 - tcl) / 0.15)
        CLAV = float(os.environ.get("V2_CLAVICLE_MM", "11.0"))   # (v13d: 3 mm hardly read)
        below = (fr < np.interp(xr, [c_[0] for c_ in cl], [c_[1] for c_ in cl]))
        # R106: narrower ridge with a crisp shadow line right under it (v13h-v13j: a 5.5 mm-wide ridge read faintly)
        hn += CLAV * np.exp(-0.5 * (dcl * _Hr / float(os.environ.get("V2_CLAVICLE_SIGMA_MM", "4.0")) * 1000) ** 2) * endf
        hn -= 3.5 * np.exp(-0.5 * ((dcl * _Hr - 0.008) / 0.0035) ** 2) * below * endf   # (v13k measured: the ridge came out ~3.5 mm of 6.5)
        hn -= 2.5 * np.exp(-0.5 * ((dcl * _Hr - 0.012) / 0.007) ** 2) * below * endf
        hn -= 2.5 * np.exp(-0.5 * (np.hypot(xr - 0.085, fr - 0.821) * _Hr / 0.008) ** 2)
        # 3. sternocleidomastoids, and the jugular notch between their heads
        dsc, tsc = _segd(xr, fr, [(0.012, 0.830), (0.026, 0.850), (0.045, 0.872)])
        SCM = float(os.environ.get("V2_SCM_MM", "5.0"))
        hn += SCM * np.exp(-0.5 * (dsc * _Hr / 0.0065) ** 2) * ss((1 - tsc) / 0.25) * ss(tsc / 0.05)
        hn -= 4.5 * np.exp(-0.5 * (np.hypot(xr, (fr - 0.829) * 1.3) * _Hr / 0.007) ** 2)
        # the hollow above each clavicle, between the sternocleidomastoid and the trapezius (it is what makes the
        # reference's clavicle read; v13e's ridge alone was faint)
        hn -= float(os.environ.get("V2_SUPRACLAV_MM", "7.0")) * np.exp(-0.5 * (((xr - 0.060) / 0.016) ** 2 + ((fr - 0.843) / 0.0065) ** 2))
        hn *= fronty * noarm * nohead
        # 4. trapezius: fuller neck-to-shoulder slope (front and back - it is one muscle over the top)
        upf = ss((qn[:, 2] + 0.1) / 0.4)
        TRAP = float(os.environ.get("V2_TRAP_MM", "12"))
        hn += TRAP * np.exp(-0.5 * (((xr - 0.075) / 0.030) ** 2 + ((fr - 0.848) / 0.012) ** 2)) * upf * noarm * nohead * (1 - _keep)
        for _ in range(3):
            hn = 0.5 * hn + 0.5 * avg(hn)
        off += qn * (hn / 1000.0)[:, None]
        Q = rest + off
        DETAIL_REPORT["neck_detail"] = {"clavicle_mm": CLAV, "scm_mm": SCM, "trap_mm": TRAP, "erase_steps": int(os.environ.get("V2_NECK_ERASE", "150")),
                                        "max_mm": round(float(hn.max()), 2), "min_mm": round(float(hn.min()), 2)}
    # R113 (shoulder / armpit review after the pelvis work): fine crinkles over the front deltoids and the deltopectoral
    # area appeared with the sculpt layers (the V1 surface on the same skeleton is smooth there), and the upper back /
    # scapulae carry R41's faint mottling.  Normal-only Taubin smoothing (no shrinking, no sliding) of the shoulder joint
    # band and the upper back - removes the fine noise, keeps the forms; the clavicle ridge and the pec are left out.
    SHDN = int(os.environ.get("V2_SHOULDER_DENOISE", "40"))
    if SHDN > 0:
        _Vr = rest + PROP + off; _z0 = _Vr[:, 2].min(); _Hr = _Vr[:, 2].max() - _z0
        fr = (_Vr[:, 2] - _z0) / _Hr; xr = np.abs(_Vr[:, 0]) / _Hr
        _as = np.clip(_arm_f, 0, 1)
        for _ in range(20):
            _as = 0.5 * _as + 0.5 * avg(_as)
        root_ = ss(_as / 0.15) * ss((0.95 - _as) / 0.2)                         # the arm-root band (deltoid / armpit)
        upb_ = ss((qn[:, 1] - 0.1) / 0.3) * ss((xr - 0.02) / 0.02) * ss((0.17 - xr) / 0.03)   # upper back, off the spine line
        band_ = ss((fr - 0.66) / 0.02) * ss((0.835 - fr) / 0.015)
        keep_ = ss((0.135 - xr) / 0.02) * ss((-qn[:, 1] - 0.2) / 0.3)               # the front chest (pecs, clavicles)
        er = np.clip(np.maximum(root_, upb_) * band_ * (1 - keep_) * (1 - np.clip(HEAD, 0, 1)), 0, 1)
        Q = rest + off
        for _ in range(SHDN):
            for lam in (0.5, -0.53):
                tri = Q[faces]; fn_ = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
                vn_ = np.zeros_like(Q); np.add.at(vn_, faces.ravel(), np.repeat(fn_, 3, axis=0))
                vn_ /= np.maximum(np.linalg.norm(vn_, axis=1, keepdims=True), 1e-12)
                Q = Q + lam * er[:, None] * ((cavg(Q) - Q) * vn_).sum(1)[:, None] * vn_
        off = Q - rest
        DETAIL_REPORT["shoulder_denoise"] = {"taubin_steps": SHDN, "vertices": int((er > 0.05).sum())}
    # R115 (owner: "look out for muscle definition in the likes of biceps etc. ... The bicep to the forearm doesn't seem
    # right. In the reference model it shows how they both blend together and there I think is a little overlap of
    # each"): limb muscles in bone-local coordinates.  For each arm vertex: the nearest of upperarm / forearm (as edited),
    # t along the bone (0 = proximal joint, 1 = distal), theta around it measured in world terms (0 = front, +90 = outward,
    # 180 = back, -90 = towards the body) - the arms hang in the bind pose with the palms towards the thighs, so the thumb
    # side of the forearm faces forward.  Muscles as smooth bumps along the normal (mm), placed per surface anatomy
    # (Gray's Anatomy; Drake, Gray's Anatomy for Students - upper limb): deltoid cap with its insertion V at ~0.45 of the
    # arm, biceps in front peaking a little below mid-arm, triceps behind (lateral head showing), brachialis to the outer
    # side above the elbow, the medial bicipital groove; brachioradialis / ECRL rising from the lower outer upper arm and
    # running down the thumb side of the forearm - so it overlaps the lower end of the biceps at the elbow, with the
    # cubital fossa between them; flexor mass inside, extensors outside, tapering to a slimmer wrist.
    ARMDEF = float(os.environ.get("V2_ARM_MUSCLES", "1"))
    if ARMDEF > 0:
        _V = rest + PROP + off
        def _seg(bn):
            b_ = rig.data.bones[bn]; return np.array(b_.head_local), np.array(b_.tail_local)
        def _frame(Hh, Tt, sgn, P):
            ax = Tt - Hh; L = np.linalg.norm(ax); u = ax / L
            t = ((P - Hh) @ u) / L
            dv = P - Hh - np.outer(t * L, u)
            ant = np.array([0.0, -1.0, 0.0]); ant = ant - (ant @ u) * u; ant /= np.linalg.norm(ant)
            lat = np.cross(u, ant); lat *= np.sign(lat[0] * sgn) if lat[0] != 0 else 1.0
            th = np.degrees(np.arctan2(dv @ lat, dv @ ant)); r = np.linalg.norm(dv, axis=1)
            return t, th, r, L
        def _bump(t, th, t0, t1, thc, thw, amp, pk=1.0):
            x_ = np.clip((t - t0) / (t1 - t0), 0, 1); prof = np.sin(np.pi * x_) ** pk
            dth = (th - thc + 180.0) % 360.0 - 180.0
            return amp * prof * np.exp(-0.5 * (dth / thw) ** 2)
        ha = np.zeros(nv); armm = np.clip(_arm_f, 0, 1)
        for side_, sgn in (("r", 1.0), ("l", -1.0)):
            sel = (armm > 0.2) & (np.sign(_V[:, 0]) == np.sign(np.array(rig.data.bones[f"upperarm_{side_}"].head_local)[0]))
            idx = np.nonzero(sel)[0]; P = _V[idx]
            uH, uT = _seg(f"upperarm_{side_}"); fH, fT = _seg(f"forearm_{side_}"); sgn = float(np.sign(uH[0]))   # outward = this arm's side
            tu, thu, ru, Lu = _frame(uH, uT, sgn, P); tf, thf, rf, Lf = _frame(fH, fT, sgn, P)
            # blend the two frames across the elbow (a hard switch drew a seam, w3)
            wU = np.clip(1 - ss((tf + 0.04) / 0.10), 0, 1)
            onU = np.ones(len(idx), bool)
            h_ = np.zeros(len(idx))
            # upper arm
            U = tu > -0.15
            # (w2 amplitudes read weaker than the reference - deltoid 6, biceps 8, triceps 6.5; now larger, plus general girth)
            hu = (_bump(tu, thu, -0.05, 0.47, 90, 80, 11.0, 0.8)           # deltoid cap
                  + 3.0 * ss((tu - 0.1) / 0.1) * ss((0.9 - tu) / 0.1)      # upper-arm girth
                  + _bump(tu, thu, 0.05, 0.42, 25, 35, 3.0) + _bump(tu, thu, 0.05, 0.42, 160, 35, 3.0)   # anterior / posterior heads
                  - _bump(tu, thu, 0.38, 0.52, 90, 55, 3.0)               # insertion V under the cap
                  + _bump(tu, thu, 0.28, 0.90, 0, 45, 11.0, 1.3)          # biceps
                  + _bump(tu, thu, 0.12, 0.80, 180, 52, 9.0, 1.2)         # triceps (long + medial heads)
                  + _bump(tu, thu, 0.22, 0.58, 135, 30, 3.0)              # triceps lateral head
                  + _bump(tu, thu, 0.58, 0.92, 70, 22, 3.0)               # brachialis, outer side
                  - _bump(tu, thu, 0.40, 0.92, -95, 18, 2.0)              # medial bicipital groove
                  + _bump(tu, thu, 0.74, 1.10, 40, 30, 4.0))              # brachioradialis / ECRL origin, above the elbow
            h_[U] += (hu * wU)[U]
            # forearm
            F = (tf > -0.2) & (tf < 1.05)
            hf = (_bump(tf, thf, -0.12, 0.55, 20, 38, 10.0, 0.9)          # brachioradialis / ECRL down the thumb side
                  + _bump(tf, thf, -0.02, 0.55, -70, 40, 6.0, 1.1)        # flexor mass
                  + _bump(tf, thf, 0.04, 0.60, 125, 40, 4.0, 1.1)         # extensors
                  - _bump(tf, thf, -0.05, 0.12, -10, 22, 2.5))            # cubital fossa
            hf -= 4.0 * ss((tf - 0.55) / 0.35)                            # slimmer towards the wrist
            h_[F] += (hf * (1 - wU))[F]
            ha[idx] += h_ * ss((1.08 - np.clip(tf, 0, None)) / 0.08)      # off the hand
        ha *= (1 - np.clip(HEAD, 0, 1))
        for _ in range(3):
            ha = 0.5 * ha + 0.5 * avg(ha)
        off += qn * (ARMDEF * ha / 1000.0)[:, None]
        Q = rest + off
        DETAIL_REPORT["arm_muscles"] = {"max_mm": round(float(ha.max()), 2), "min_mm": round(float(ha.min()), 2), "vertices": int((np.abs(ha) > 0.2).sum())}
    # R116 (owner: "the legs still need proportioned properly"; reference front/side: strong quadriceps - the vastus
    # lateralis sweep and the vastus medialis teardrop above the inner knee - a defined patella with hollows beside the
    # patellar tendon, calves fuller and higher on the inside, a slim Achilles and ankle with the malleoli showing).
    # Same bone-local tool as the arms on thigh_* / shin_*: first a normal-only Taubin pass over the legs (the remaining
    # R41 streaks on the thighs), then the muscles (Gray's Anatomy; Drake - lower limb surface anatomy).
    LEGDEF = float(os.environ.get("V2_LEG_MUSCLES", "1"))
    if LEGDEF > 0 and ARMDEF > 0:
        legm = np.clip(LEG, 0, 1)
        for _ in range(10):
            legm = 0.5 * legm + 0.5 * avg(legm)
        _V = rest + PROP + off; _z0 = _V[:, 2].min(); _Hr = _V[:, 2].max() - _z0; frl = (_V[:, 2] - _z0) / _Hr
        erL = ss((legm - 0.4) / 0.4) * ss((frl - 0.07) / 0.02) * ss((0.49 - frl) / 0.02) * (1 - _keep)   # up to the thigh top (w3 streaks at 0.44-0.48)
        Q = rest + off
        for _ in range(int(os.environ.get("V2_LEG_DENOISE", "60"))):
            for lam in (0.5, -0.53):
                tri = Q[faces]; fn_ = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
                vn_ = np.zeros_like(Q); np.add.at(vn_, faces.ravel(), np.repeat(fn_, 3, axis=0))
                vn_ /= np.maximum(np.linalg.norm(vn_, axis=1, keepdims=True), 1e-12)
                Q = Q + lam * erL[:, None] * ((cavg(Q) - Q) * vn_).sum(1)[:, None] * vn_
        # the knee: R41's own surface has a horizontal ring around both knees (in the V1 surface too) - a stronger, local
        # normal-only erase there before the patella / hollows are placed
        # (w5: 150 plain steps in a narrow band flattened the knee into a dark straight band; Taubin keeps the volume)
        erK = ss((legm - 0.4) / 0.4) * np.exp(-0.5 * ((frl - 0.285) / 0.035) ** 2) * (1 - _keep)
        for _ in range(int(os.environ.get("V2_KNEE_ERASE", "60"))):
            for lam in (0.5, -0.53):
                tri = Q[faces]; fn_ = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
                vn_ = np.zeros_like(Q); np.add.at(vn_, faces.ravel(), np.repeat(fn_, 3, axis=0))
                vn_ /= np.maximum(np.linalg.norm(vn_, axis=1, keepdims=True), 1e-12)
                Q = Q + lam * erK[:, None] * ((cavg(Q) - Q) * vn_).sum(1)[:, None] * vn_
        off = Q - rest
        # R118: leg loft.  w5/w6 nudged R41's leg surface towards the reference and kept fighting its rings and lumps.
        # Instead each leg is re-made at every height as a rounded cross-section about its BONE line (thigh / shin, as
        # edited - skeleton first), whose front / back / inner / outer extents are the reference's own (side and front
        # panels, relative to the reference leg's straight centre lines), and every leg vertex is moved radially onto it.
        # The muscles below then go on top.  Blended out at the crotch (0.44-0.48) and above the ankle (0.07-0.10).
        if float(os.environ.get("V2_LEG_LOFT", "0")) > 0:   # off by default (w7: wrinkled cylinders, crotch / knee bands, inner thighs overlapping)
            _ls = json.load(open(Path(__file__).resolve().parent / "fit" / "ref_leg_side_profile.json"))
            _lf = json.load(open(Path(__file__).resolve().parent / "fit" / "ref_front_profile.json"))
            Fb = np.array(_ls["f"]); rFs = np.array(_ls["front"]); rBs = np.array(_ls["back"])
            Ff = np.array(_lf["f"]); rIn = np.array([np.nan if v is None else v for v in _lf["leg_in"]]); rOut = np.array([np.nan if v is None else v for v in _lf["leg_out"]])
            okf = ~np.isnan(rIn); rIn = np.interp(Fb, Ff[okf], rIn[okf]); rOut = np.interp(Fb, Ff[okf], rOut[okf])
            def _cfit(c_):
                out_ = np.zeros_like(c_)
                for lo_, hi_, sel_ in ((0.30, 0.45, Fb >= 0.285), (0.09, 0.27, Fb < 0.285)):
                    m_ = (Fb >= lo_) & (Fb <= hi_); k_ = np.polyfit(Fb[m_], c_[m_], 1); out_[sel_] = np.polyval(k_, Fb[sel_])
                return out_
            kk = np.ones(7) / 7.0
            sm7 = lambda d_: np.convolve(np.pad(d_, 3, mode="edge"), kk, mode="valid")
            cy = _cfit(0.5 * (rFs + rBs)); cx = _cfit(0.5 * (rIn + rOut))
            eF, eB = sm7(rFs - cy), sm7(cy - rBs); eO, eI = sm7(rOut - cx), sm7(cx - rIn)      # extents about the centre line
            _V = rest + PROP + off; _z0 = _V[:, 2].min(); _Hr = _V[:, 2].max() - _z0; frv = (_V[:, 2] - _z0) / _Hr
            legm2 = np.clip(LEG, 0, 1)
            for _ in range(10):
                legm2 = 0.5 * legm2 + 0.5 * avg(legm2)
            disp = np.zeros_like(_V)
            for side_ in ("r", "l"):
                tH, tT = _seg(f"thigh_{side_}"); sH, sT = _seg(f"shin_{side_}"); sgn = float(np.sign(tH[0]))
                idx = np.nonzero((legm2 > 0.15) & (np.sign(_V[:, 0]) == sgn) & (ARM < 0.3) & (frv > 0.06) & (frv < 0.49))[0]
                P = _V[idx]; z_ = P[:, 2]
                # bone line at each vertex's height
                def _axis_at(z):
                    a_ = np.where(z >= sH[2], (z - sH[2]) / (tH[2] - sH[2]), (z - sT[2]) / (sH[2] - sT[2]))
                    p0 = np.where((z >= sH[2])[:, None], sH + a_[:, None] * (tH - sH), sT + a_[:, None] * (sH - sT))
                    return p0
                A_ = _axis_at(z_)
                dvec = P[:, :2] - A_[:, :2]; r_ = np.linalg.norm(dvec, axis=1)
                fwd = -dvec[:, 1]; out = dvec[:, 0] * sgn
                th = np.arctan2(out, fwd)
                fz = (z_ - _z0) / _Hr
                EF = np.interp(fz, Fb, eF) * _Hr; EB = np.interp(fz, Fb, eB) * _Hr; EO = np.interp(fz, Fb, eO) * _Hr; EI = np.interp(fz, Fb, eI) * _Hr
                a1 = np.where(fwd >= 0, EF, EB); a2 = np.where(out >= 0, EO, EI)
                pP = 2.3
                c_, s_ = np.abs(np.cos(th)), np.abs(np.sin(th))
                R_ = 1.0 / np.power((c_ / a1) ** pP + (s_ / a2) ** pP, 1.0 / pP)
                w_ = ss((fz - 0.075) / 0.025) * ss((0.47 - fz) / 0.035) * np.clip((legm2[idx] - 0.15) / 0.5, 0, 1)
                dr = np.clip(R_ - r_, -0.04, 0.04) * w_
                disp[idx, :2] += (dvec / np.maximum(r_[:, None], 1e-6)) * dr[:, None]
            for _ in range(6):
                disp = 0.5 * disp + 0.5 * np.stack([avg(disp[:, k]) for k in range(3)], axis=1)
            off += disp
            DETAIL_REPORT["leg_loft"] = {"max_move_mm": round(float(np.linalg.norm(disp, axis=1).max() * 1000), 1),
                                         "extents_at_0.20_mm": [round(float(v * _Hr * 1000), 1) for v in (np.interp(0.2, Fb, eF), np.interp(0.2, Fb, eB), np.interp(0.2, Fb, eI), np.interp(0.2, Fb, eO))],
                                         "extents_at_0.40_mm": [round(float(v * _Hr * 1000), 1) for v in (np.interp(0.4, Fb, eF), np.interp(0.4, Fb, eB), np.interp(0.4, Fb, eI), np.interp(0.4, Fb, eO))]}
        _V = rest + PROP + off
        hl = np.zeros(nv)
        for side_ in ("r", "l"):
            tH, tT = _seg(f"thigh_{side_}"); sH, sT = _seg(f"shin_{side_}"); sgn = float(np.sign(tH[0]))
            sel = (legm > 0.2) & (np.sign(_V[:, 0]) == sgn)
            idx = np.nonzero(sel)[0]; P = _V[idx]
            tt, tht, rt, Lt = _frame(tH, tT, sgn, P); ts, ths, rs_, Ls = _frame(sH, sT, sgn, P)
            wT = np.clip(1 - ss((ts + 0.04) / 0.10), 0, 1)          # thigh frame -> shin frame across the knee (w3: a ring)
            h_ = np.zeros(len(idx))
            ht = (_bump(tt, tht, 0.12, 0.90, 0, 30, 5.0)                      # rectus femoris
                  + _bump(tt, tht, 0.18, 0.95, 65, 38, 8.0, 1.2)              # vastus lateralis (outer sweep)
                  + _bump(tt, tht, 0.60, 0.98, -45, 34, 6.0, 1.2)             # vastus medialis teardrop (w3: 9 mm read as a lump)
                  + _bump(tt, tht, 0.05, 0.55, -95, 40, 4.0)                  # adductors
                  + _bump(tt, tht, 0.15, 0.88, 180, 45, 5.0)                  # hamstrings
                  - _bump(tt, tht, 0.50, 0.92, 180, 12, 1.5)                  # groove between the hamstrings
                  - _bump(tt, tht, 0.30, 0.92, 100, 14, 2.0)                  # flat band behind vastus lateralis (IT band)
                  + _bump(tt, tht, 0.94, 1.06, 0, 22, 3.0))                   # patella (upper part)
            # sartorius: a soft groove from the outer front of the hip down across the thigh to the inner knee
            sth = 40.0 - 140.0 * np.clip(tt, 0, 1)
            dth = (tht - sth + 180.0) % 360.0 - 180.0
            ht -= 2.0 * np.exp(-0.5 * (dth / 9.0) ** 2) * ss((tt - 0.08) / 0.08) * ss((0.85 - tt) / 0.1)
            T_ = tt > -0.1
            h_[T_] += (ht * wT)[T_]
            S = (ts > -0.2) & (ts < 1.05)
            hs = (_bump(ts, ths, -0.04, 0.06, 0, 30, 3.0)                     # patella (lower part)
                  - _bump(ts, ths, 0.0, 0.10, 50, 16, 3.0) - _bump(ts, ths, 0.0, 0.10, -50, 16, 3.0)   # hollows beside the tendon
                  + _bump(ts, ths, 0.06, 0.52, -145, 38, 12.0, 0.9)           # gastrocnemius, medial head (fuller, lower)
                  + _bump(ts, ths, 0.06, 0.44, 150, 32, 9.0, 0.9)             # gastrocnemius, lateral head
                  + _bump(ts, ths, 0.30, 0.78, -110, 28, 3.0) + _bump(ts, ths, 0.30, 0.74, 110, 28, 3.0)   # soleus at the sides
                  + _bump(ts, ths, 0.06, 0.62, 30, 26, 4.0)                   # tibialis anterior
                  + _bump(ts, ths, 0.92, 1.02, -90, 22, 4.0) + _bump(ts, ths, 0.95, 1.05, 90, 22, 4.0))   # malleoli
            hs -= 4.0 * ss((ts - 0.62) / 0.28) * (1 - _bump(ts, ths, 0.92, 1.06, -90, 22, 1.0) - _bump(ts, ths, 0.95, 1.06, 90, 22, 1.0))   # slimmer ankle / Achilles (not over the malleoli)
            h_[S] += (hs * (1 - wT))[S]
            hl[idx] += h_
        hl *= (1 - _keep)
        for _ in range(3):
            hl = 0.5 * hl + 0.5 * avg(hl)
        off += qn * (LEGDEF * hl / 1000.0)[:, None]
        Q = rest + off
        DETAIL_REPORT["leg_muscles"] = {"max_mm": round(float(hl.max()), 2), "min_mm": round(float(hl.min()), 2)}
    # R85 (owner, with the reference figure's groin close-ups: "Can we have the groin area match this ... I still see the
    # weird line at the top of the legs where it meets the torso ... There is no line there and it's smooth transition"):
    # the model had a horizontal fold across both thigh tops at ~0.49 of stature, just above the crotch, and a flat wide
    # shelf for the pubic area.  Reference: the inguinal creases are long soft curves from the side of the hip (~0.56,
    # |x| ~0.08 of stature) to beside the crotch (~0.48); between them a rounded pubic wedge with a U-shaped bottom; no
    # horizontal line.  So: flatten the whole groin band (plain normal-only cotangent steps: removes the fold and the
    # shelf), then the wedge and the creases on the reference curve.
    PELV = float(os.environ.get("V2_PELVIS", "1"))     # R110 pelvis-to-thigh transition (below); 0 = as v13l
    GROIN2 = float(os.environ.get("V2_GROIN_REBUILD", "1"))
    if GROIN2 > 0:
        fz_ = (Q[:, 2] - zb) / Hs; ax_ = np.abs(Q[:, 0])
        cz = Q[np.abs(Q[:, 0]) < 0.006, 2].min(); fc = (cz - zb) / Hs
        notback = ss((0.35 - qn[:, 1]) / 0.3)
        inner_below = (fz_ < fc + 0.004) * ss((-(qn[:, 0] * np.sign(Q[:, 0])) - 0.2) / 0.3)    # thigh skin facing the other leg
        er = ss((fz_ - (fc - 0.025)) / 0.02) * ss((fc + 0.115 - fz_) / 0.025) * ss((0.20 - ax_) / 0.03) * notback * (1 - inner_below) * (1 - _keep)
        for _ in range(int(os.environ.get("V2_GROIN_ERASE", "200"))):
            tri = Q[faces]; fn_ = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
            vn_ = np.zeros_like(Q); np.add.at(vn_, faces.ravel(), np.repeat(fn_, 3, axis=0))
            vn_ /= np.maximum(np.linalg.norm(vn_, axis=1, keepdims=True), 1e-12)
            Q = Q + 0.5 * er[:, None] * ((cavg(Q) - Q) * vn_).sum(1)[:, None] * vn_
        off = Q - rest
        # crease curve (|x|, z) from the reference, as fractions of stature above the crotch
        cpts = [(0.150, cz + 0.152), (0.118, cz + 0.112), (0.085, cz + 0.070), (0.058, cz + 0.038), (0.040, cz + 0.018), (0.030, cz + 0.006)]
        if PELV > 0:
            # R110: the inguinal fold follows the inguinal ligament from the ASIS (skin landmark rest (0.108, 1.001)) down
            # and in towards the pubic tubercle, then the thigh-pubis sulcus runs on down beside the mound; it ends ~2 cm
            # above the crotch and ~4 cm out from the midline - the two sides no longer meet in a point (v13l's pinch)
            cpts = [(0.122, cz + 0.128), (0.100, cz + 0.100), (0.080, cz + 0.074), (0.062, cz + 0.050), (0.050, cz + 0.032), (0.042, cz + 0.018)]
        # distance to the curve and which side of it (inside = the pubic side, up / towards the midline)
        P2 = np.stack([ax_, Q[:, 2]], axis=1); best = np.full(nv, 9.0); sgn = np.zeros(nv); tpar = np.zeros(nv)
        L_tot = sum(np.linalg.norm(np.subtract(b, a)) for a, b in zip(cpts[:-1], cpts[1:])); run = 0.0
        for a, b in zip(cpts[:-1], cpts[1:]):
            a = np.array(a); b = np.array(b); d = b - a; L = np.linalg.norm(d); u = d / L
            p = P2 - a; t = np.clip(p @ u / L, 0, 1); q = p - np.outer(t * L, u); dist = np.linalg.norm(q, axis=1)
            side_ = np.sign(q @ np.array([-u[1], u[0]]))                     # + = left of the walk = out / down (thigh side)
            m = dist < best; best[m] = dist[m]; sgn[m] = side_[m]; tpar[m] = (run + t[m] * L) / L_tot
            run += L
        frontish = ss((-qn[:, 1] - 0.1) / 0.4) * (1 - _keep)
        h = np.zeros(nv)
        CR_MM = float(os.environ.get("V2_GROIN_CREASE_MM", "2.2" if PELV > 0 else "3.0"))
        h -= CR_MM * np.exp(-0.5 * (best / (0.013 if PELV > 0 else 0.010)) ** 2) * ss(tpar / 0.12) * ss((1 - tpar) / 0.30) * frontish   # fades before the crotch: a U, not a point
        # pubic wedge: raised inside the creases, rounded, fading up into the lower belly
        inside = (sgn < 0) * ss(best / 0.012)
        PUB_MM = float(os.environ.get("V2_PUBIC_MM", "5"))
        h += PUB_MM * inside * np.exp(-0.5 * (ax_ / 0.035) ** 2) * ss((fz_ - fc + 0.004) / 0.016) * ss((fc + 0.085 - fz_) / 0.04) * frontish   # rounded mound
        # thigh side of the crease: the thigh front comes forward a little, so the crease reads as a soft fold
        outside = (sgn > 0) * ss(best / 0.010) * ss((0.06 - best) / 0.03)
        h += 2.0 * outside * ss(tpar / 0.15) * ss((1 - tpar) / 0.15) * frontish
        for _ in range(4):
            h = 0.5 * h + 0.5 * avg(h)
        off += qn * (h / 1000.0)[:, None]
        Q = rest + off
        DETAIL_REPORT["groin_rebuild"] = {"erase_steps": int(os.environ.get("V2_GROIN_ERASE", "200")), "crease_mm": CR_MM, "pubic_mm": PUB_MM,
                                           "crotch_frac": round(float(fc), 4), "crease_points": [[round(a, 3), round(float(b), 3)] for a, b in cpts]}
    # belly button at 0.612 of stature: a dimple 9 mm across with a soft rim
    NAVEL_MM = float(os.environ.get("V2_NAVEL_MM", "6"))
    zn = zb + 0.612 * Hs
    rr = np.sqrt(Q[:, 0] ** 2 + ((Q[:, 2] - zn) / 1.25) ** 2)
    dimple = (np.exp(-0.5 * (rr / 0.0045) ** 2) - 0.18 * np.exp(-0.5 * ((rr - 0.010) / 0.004) ** 2)) * ss((-qn[:, 1] - 0.5) / 0.3)
    off -= qn * (NAVEL_MM / 1000.0 * dimple)[:, None]
    # inguinal creases (the V): from the front of the hip bone down to beside the crotch
    ING_D = float(os.environ.get("V2_INGUINAL_DETAIL_MM", "0" if GROIN2 > 0 else "4"))
    cz = Q[np.abs(Q[:, 0]) < 0.006, 2].min()
    off += groove([(0.118, cz + 0.135), (0.075, cz + 0.07), (0.035, cz + 0.022), (0.018, cz + 0.004)], 0.006, ING_D, -1)
    # gluteal folds: under each buttock, rising slightly to the outside
    GLUTE_D = float(os.environ.get("V2_GLUTE_FOLD_MM", "0" if PELV > 0 else "5"))   # R110 re-makes it below
    off += groove([(0.022, cz - 0.004), (0.06, cz - 0.022), (0.11, cz - 0.018), (0.15, cz + 0.005)], 0.007, GLUTE_D, +1)
    DETAIL_REPORT.update({"navel_mm": NAVEL_MM, "navel_z": round(float(zn), 4), "inguinal_mm": ING_D, "glute_fold_mm": GLUTE_D, "crotch_z": round(float(cz), 4)})
    # R110 (owner: "Correct the pelvis-to-thigh anatomical transition ... overly flat lower pelvis, a pinched central groin
    # junction and an abrupt gluteal-to-thigh transition").  Measured first (v13l / p0 standing renders, fractions of
    # stature): crotch 0.473 (reference 0.475), navel 0.612 (0.616) - heights kept; hip half-width at 0.50 0.104 (0.106);
    # upper outer thigh 0.40-0.47 0.100-0.109 against 0.107-0.116 (the reference's thigh sweeps out below the hip, the
    # model's outline ran straight down); inner-thigh gap similar.  Surface anatomy (Gray's Anatomy; Drake, Gray's Anatomy
    # for Students, surface anatomy of the gluteal region and the femoral triangle): the gluteal fold (infragluteal sulcus)
    # is a crease under the medial part of gluteus maximus, at about the ischial tuberosity, fading out laterally (it is
    # not a full-width crease); gluteus maximus is a rounded mass whose top blends into the lower back over the iliac
    # crest / sacrum without a step; the hypogastric (lower) abdomen is gently convex down to the pubis; the adductors
    # fill the upper inner thigh up to the pubis.  All of it below on Q = rest + off (heights as the groin rebuild above).
    if PELV > 0:
        fz_ = (Q[:, 2] - zb) / Hs; ax_ = np.abs(Q[:, 0]); xh_ = ax_ / Hs; fc = (cz - zb) / Hs
        back_ = ss((qn[:, 1] - 0.05) / 0.35); front_ = ss((-qn[:, 1] - 0.05) / 0.35)
        inner_ = ss((-(qn[:, 0] * np.sign(Q[:, 0])) - 0.2) / 0.3)
        legside = ss((qn[:, 0] * np.sign(Q[:, 0]) - 0.2) / 0.3)
        # 1. buttocks: erase the shelf under them and the band across their top (normal-only cotangent steps)
        er = ss((fz_ - (fc - 0.045)) / 0.015) * ss((fc + 0.12 - fz_) / 0.02) * ss((0.18 - ax_) / 0.03) * back_ * (1 - _keep)
        for _ in range(int(os.environ.get("V2_GLUTE_ERASE", "150"))):
            tri = Q[faces]; fn_ = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
            vn_ = np.zeros_like(Q); np.add.at(vn_, faces.ravel(), np.repeat(fn_, 3, axis=0))
            vn_ /= np.maximum(np.linalg.norm(vn_, axis=1, keepdims=True), 1e-12)
            Q = Q + 0.5 * er[:, None] * ((cavg(Q) - Q) * vn_).sum(1)[:, None] * vn_
        off = Q - rest
        hp = np.zeros(nv)
        # 2. gluteus maximus: a rounded mass, fullest a little below its middle, blending up into the lower back
        GMAX = float(os.environ.get("V2_GLUTE_MM", "9"))
        # R112: taller and longer, so it curves into the lower back above and the hamstrings below (v13p still stepped)
        # R113c: fuller towards the top (longer upper slope) - the reference's buttock carries its volume higher, which the
        # side fit had tried to add as a separate band at 0.53-0.56
        _gs = np.where(fz_ > fc + 0.035, 0.058, 0.036)
        hp += GMAX * np.exp(-0.5 * (((xh_ - 0.052) / 0.036) ** 2 + ((fz_ - fc - 0.035) / _gs) ** 2)) * back_
        # 3. gluteal fold: medial two thirds only, rising slightly outwards, fading laterally into the outer thigh
        gpts = [(0.012, cz - 0.004), (0.040, cz - 0.014), (0.075, cz - 0.016), (0.110, cz - 0.008)]
        P2 = np.stack([ax_, Q[:, 2]], axis=1); gd = np.full(nv, 9.0); gt = np.zeros(nv); run = 0.0
        gL = sum(np.linalg.norm(np.subtract(b, a)) for a, b in zip(gpts[:-1], gpts[1:]))
        for a, b in zip(gpts[:-1], gpts[1:]):
            a = np.array(a); b = np.array(b); dd = b - a; L = np.linalg.norm(dd); u = dd / L
            p = P2 - a; t = np.clip(p @ u / L, 0, 1); dist = np.linalg.norm(p - np.outer(t * L, u), axis=1)
            m = dist < gd; gd[m] = dist[m]; gt[m] = (run + t[m] * L) / gL; run += L
        GF = float(os.environ.get("V2_GLUTE_FOLD_R110_MM", "4"))
        hp -= GF * np.exp(-0.5 * (gd / 0.0065) ** 2) * ss(gt / 0.10) * ss((1 - gt) / 0.45) * back_
        # 4. gluteal-to-hamstring transition: the upper hamstrings fill just under the fold, so the thigh carries on
        #    from the buttock instead of stepping in under a shelf
        hp += 3.0 * np.exp(-0.5 * (((xh_ - 0.050) / 0.035) ** 2 + ((fz_ - fc + 0.040) / 0.025) ** 2)) * back_
        # 5. lower abdomen: gently convex from below the navel down to the pubis (v13l: a flat plane)
        # R112: the pubic triangle between the folds gently convex (mannequin, no genital detail; v13p read flat)
        hp += float(os.environ.get("V2_PUBIC_DOME_MM", "3")) * np.exp(-0.5 * (((xh_) / 0.032) ** 2 + ((fz_ - fc - 0.035) / 0.022) ** 2)) * front_
        hp += float(os.environ.get("V2_LOWER_ABS_MM", "4")) * np.exp(-0.5 * (((xh_) / 0.050) ** 2 + ((fz_ - fc - 0.075) / 0.030) ** 2)) * front_
        # 6. crotch junction: the upper inner thighs ease away from the junction (a rounded U under the mound, not a
        #    slit), and the adductors fill the upper inner thigh just below it so it blends into the pubis
        hp -= 3.0 * np.exp(-0.5 * ((fz_ - fc + 0.008) / 0.010) ** 2) * ss((0.035 - xh_) / 0.02) * inner_ * (1 - back_)
        hp += 2.5 * np.exp(-0.5 * ((fz_ - fc + 0.035) / 0.020) ** 2) * ss((0.06 - xh_) / 0.03) * inner_
        # 7. outer upper thigh: sweeps out below the hip as on the reference (+~1.2 cm at 0.40-0.47, the vastus lateralis /
        #    tensor fasciae latae), tapering into the hip above and the knee below
        _lg = np.clip(LEG, 0, 1)                         # (p2: a hard LEG > 0.5 cut-off drew a jagged ring around each thigh
        for _ in range(60):                              #  along the thigh / pelvis weight boundary)
            _lg = 0.5 * _lg + 0.5 * avg(_lg)
        # sideways (see below): the whole outer half of the thigh, fading across its front and back
        # (p10: with front-facing skin near the midline included, sign(x) pulled the two sides of the crotch apart - a
        # pinched fold and 74 standing overlaps; only the outer, outward-facing part of each thigh now)
        _side = ss((qn[:, 0] * np.sign(Q[:, 0]) - 0.05) / 0.5) * ss((xh_ - 0.045) / 0.025)
        _ot = float(os.environ.get("V2_OUTER_THIGH_MM", "10")) * ss((fz_ - 0.36) / 0.04) * ss((fc + 0.035 - fz_) / 0.03) * _side * ss((_lg - 0.3) / 0.5) * (1 - _keep)
        if _ot.max() > 0:
            # R112: limited by its clearance from the hanging hand / forearm in the standing pose (less 5 mm) - unlimited, it
            # ran into the hands and the overlap shrink crumpled the thighs (p2/p4)
            from scipy.spatial import cKDTree as _KD
            _Ps = stand_eval(off); _am = _arm_f > 0.5; _cd = np.nonzero(_ot > 0.05)[0]
            _dd = np.full(nv, 9.0); _dd[_cd] = _KD(_Ps[_am]).query(_Ps[_cd])[0]
            _r = np.where(_ot > 0.05, np.clip((_dd - 0.005) * 1000.0 / np.maximum(_ot, 1e-6), 0, 1), 1.0)
            for _ in range(30):
                _r = np.minimum(_r, 0.5 * _r + 0.5 * avg(_r))
            for _ in range(30):
                _r = 0.5 * _r + 0.5 * avg(_r)
            _ot *= _r
        # (p9: pushed along the surface normal, the sweep folded the skin where the thigh meets the buttock / hip - the
        # normals converge there - and the overlap shrink crumpled it into a ring.  A sideways move in the skeleton-level
        # field instead: no folding, and the overlap loop does not shrink it.)
        _otx = _ot.copy()
        for _ in range(10):
            _otx = 0.5 * _otx + 0.5 * avg(_otx)
        PROP[:, 0] += np.sign(Q[:, 0]) * _otx / 1000.0
        for _ in range(4):
            hp = 0.5 * hp + 0.5 * avg(hp)
        hp *= (1 - _keep)
        off += qn * (hp / 1000.0)[:, None]
        Q = rest + off
        DETAIL_REPORT["pelvis_r110"] = {"glute_mm": GMAX, "glute_fold_mm": GF, "glute_erase": int(os.environ.get("V2_GLUTE_ERASE", "150")),
                                        "max_mm": round(float(hp.max()), 2), "min_mm": round(float(hp.min()), 2)}
    # R99 (owner chose "Reshape torso to reference first"): fit the torso's side silhouette to the reference figure.
    # Measured with scripts/body_v2/fit/silfit.py (side panel, skin-colour mask), front and back edges per height
    # relative to their own value at 0.50 of stature: on v11e the model's chest front stood ~0.018 of stature (3.3 cm)
    # further forward than the reference and the waist front ~0.009, while the lower back sat ~0.016 further back -
    # the torso was 3-4.5 cm too thick front-to-back, which is why the pecs kept reading as a shelf.  Correction per
    # height, blended across the depth (front edge gets the front correction, back edge the back one), on the torso
    # only (arms and head excluded), after all the muscle relief so the pecs / abs keep their shape relative to the
    # surface around them.
    SIDEFIT = float(os.environ.get("V2_SIDE_FIT", "1"))
    if SIDEFIT > 0:
        # R107 (owner circled the lower back / buttocks, the backs of the legs and the feet in the side view): the fit now
        # runs from the shins up (fit/ref_side_profile_full.json, 0.02-0.89; the reference's hand hangs in front of the
        # thigh at 0.37-0.53, so the thigh front is interpolated there).  The feet (below ~0.06) are left to their own step.
        SFULL = os.environ.get("V2_SIDE_FIT_FULL", "0") == "1"   # off: v13m/v13n (hip-anchored leg fit) banded the thighs; legs need a leg-local fit
        _rp = json.load(open(Path(__file__).resolve().parent / "fit" / ("ref_side_profile_full.json" if SFULL else "ref_side_profile.json")))
        _bf = np.array(_rp["f"]); _rF = np.array(_rp["front"]); _rB = np.array(_rp["back"])
        Q = rest + PROP + off; fzq = (Q[:, 2] - zb) / Hs; fwd = -Q[:, 1] / Hs     # as rendered (incl. the R81/R100 skeleton field)
        _tor = (ARM < 0.3) & (HEAD < 0.5)
        mF = np.zeros(len(_bf)); mB = np.zeros(len(_bf))
        for i_, fb_ in enumerate(_bf):
            sel_ = _tor & (np.abs(fzq - fb_) < 0.003)
            mF[i_], mB[i_] = (fwd[sel_].max(), fwd[sel_].min()) if sel_.any() else (np.nan, np.nan)
        _ok = ~np.isnan(mF)
        mF = np.interp(_bf, _bf[_ok], mF[_ok]); mB = np.interp(_bf, _bf[_ok], mB[_ok])
        i50 = int(np.argmin(np.abs(_bf - 0.50)))
        dF = _rF - (mF - mF[i50]); dB = _rB - (mB - mB[i50])
        if SFULL:
            # the legs: shape only.  v13m moved both legs back 5.6 cm (clip) - relative to the hips the model's legs stand
            # a near-constant 2.5-4 cm further forward than the reference's, which is posture (the skeleton), not shape.
            # Remove that constant centre offset below the buttocks (blended out over 0.46-0.54).
            _lg = (_bf > 0.12) & (_bf < 0.44)
            _cs = float(np.mean(0.5 * (dF[_lg] + dB[_lg])))
            _wl = ss((0.50 - _bf) / 0.04)
            dF = dF - _cs * _wl; dB = dB - _cs * _wl
        _k = np.ones(7) / 7.0
        dF = np.convolve(np.pad(dF, 3, mode="edge"), _k, mode="valid"); dB = np.convolve(np.pad(dB, 3, mode="edge"), _k, mode="valid")
        # long taper below the neck (abrupt ends striped / ridged, v12b/v12c); R102: reaches up to the clavicles (v12j's upper
        # chest stood ~1 cm proud at 0.81-0.84, so the chest front read flat, not the reference's slope down to the nipple);
        # stops below the chin (the 0.87 bin is the chin, not the neck)
        win = (ss((_bf - 0.10) / 0.03) if SFULL else ss((_bf - 0.515) / 0.03)) * ss((float(os.environ.get("V2_SIDE_FIT_TOP", "0.865")) - _bf) / 0.035)
        # R112: the back edge only from above the buttocks - starting at 0.515 it pushed the lower back out by up to 2.5 cm
        # at 0.53-0.56, a second bump over the buttock (the band across the top of the buttocks, v13p)
        # (s2: a 0.03 ramp put a crease across the lower back at ~0.60 - up to 2.9 cm forward within it; 0.06 now)
        winB = win * (ss((_bf - float(os.environ.get("V2_SIDE_FIT_BACK_FROM", "0.60"))) / 0.06) if PELV > 0 else 1.0)
        dF = np.clip(dF, -0.03, 0.03) * win * SIDEFIT; dB = np.clip(dB, -0.03, 0.03) * winB * SIDEFIT
        fv = np.interp(fzq, _bf, dF); bv = np.interp(fzq, _bf, dB)
        Fabs = np.interp(fzq, _bf, mF); Babs = np.interp(fzq, _bf, mB)
        t_ = np.clip((fwd - Babs) / np.maximum(Fabs - Babs, 1e-4), 0, 1)
        # off the arm entirely, and fading across the side of the chest towards the armpit (a half-moved deltoid crumpled,
        # v12a); the side silhouette at chest height is set by the front of the chest, well inside this fade
        # the arms: held still while the chest front beside them moved back 2-3 cm, the skin between sheared and the
        # overlap loop crumpled it (deltoid-front wrinkles in v12a-v12f; gone with the fit off).  Now each arm moves as one
        # piece by the correction at its shoulder joint (rig edited to match), blended into the local correction across a
        # wide, smoothed arm-root zone.
        a_ = np.clip(ARM / 0.6, 0, 1)
        for _ in range(int(os.environ.get("V2_SIDE_FIT_BLEND", "80"))):
            a_ = 0.5 * a_ + 0.5 * avg(a_)
        loc_ = -Hs * (bv + (fv - bv) * t_)
        _sh = np.array(rig.data.bones["upperarm_r"].head_local); fzj = (_sh[2] - zb) / Hs
        tj = float(np.clip((-_sh[1] / Hs - np.interp(fzj, _bf, mB)) / max(np.interp(fzj, _bf, mF) - np.interp(fzj, _bf, mB), 1e-4), 0, 1))
        dyj = float(-Hs * (np.interp(fzj, _bf, dB) + (np.interp(fzj, _bf, dF) - np.interp(fzj, _bf, dB)) * tj))
        # into the skeleton-level field PROP, not the sculpt offsets: the overlap loop below shrinks the offsets where skin
        # touches, and shrinking this 2-3 cm move patchily around the armpit was what wrinkled the deltoid front (v12g)
        PROP[:, 1] += ((1 - a_) * loc_ + a_ * dyj) * (1 - HEAD)
        _asub = [b.name for b in rig.data.bones if b.name in ("upperarm_r", "upperarm_l") or any(p.name in ("upperarm_r", "upperarm_l") for p in b.parent_recursive)]
        _tgt = {bn: (Vector(rig.data.bones[bn].head_local) + Vector((0, dyj, 0)), Vector(rig.data.bones[bn].tail_local) + Vector((0, dyj, 0))) for bn in _asub}
        bpy.context.view_layer.objects.active = rig
        bpy.ops.object.mode_set(mode="EDIT")
        for _pass in range(2):                           # connected children snap to the parent's tail: set twice
            for bn, (h_, t_) in _tgt.items():
                rig.data.edit_bones[bn].head = h_; rig.data.edit_bones[bn].tail = t_
        bpy.ops.object.mode_set(mode="OBJECT"); bpy.context.view_layer.update()
        _sk = json.loads((OUT / "skeleton_edits.json").read_text())
        _sk["side_fit_arm_shift_y_m"] = {"dy": dyj, "bones": _asub}
        (OUT / "skeleton_edits.json").write_text(json.dumps(_sk, indent=1))
        DETAIL_REPORT["side_fit"] = {"arm_shift_y_mm": round(dyj * 1000, 1), "leg_centre_offset_removed_mm": round(_cs * Hs * 1000, 1) if SFULL else 0, "max_front_corr_mm": round(float(np.abs(dF).max() * Hs * 1000), 1), "max_back_corr_mm": round(float(np.abs(dB).max() * Hs * 1000), 1),
                                     "front_corr_mm_at": {str(round(float(f_), 3)): round(float(v_ * Hs * 1000), 1) for f_, v_ in zip(_bf[::6], dF[::6])},
                                     "back_corr_mm_at": {str(round(float(f_), 3)): round(float(v_ * Hs * 1000), 1) for f_, v_ in zip(_bf[::6], dB[::6])}}
    # R108 (owner circled the chest / torso sides and the legs on the full-body sheet): front widths fitted to the reference
    # front silhouette per height (fit/ref_front_profile.json): torso half-width above the crotch (up to the armpits),
    # inner and outer edge of each leg below it.  Into PROP (x only), arms and head held, like the side fit.
    FFIT = float(os.environ.get("V2_FRONT_FIT", "0"))   # off until reviewed
    if FFIT > 0:
        _fp = json.load(open(Path(__file__).resolve().parent / "fit" / "ref_front_profile.json"))
        _ff = np.array(_fp["f"]); _nan = lambda L: np.array([np.nan if v is None else v for v in L])
        rT, rI, rO = _nan(_fp["torso_half"]), _nan(_fp["leg_in"]), _nan(_fp["leg_out"])
        _Vr = rest + PROP + off; _z0 = _Vr[:, 2].min(); _Hr = _Vr[:, 2].max() - _z0
        fr = (_Vr[:, 2] - _z0) / _Hr; xs_ = _Vr[:, 0] / _Hr; ax = np.abs(xs_)
        body_ = (ARM < 0.3) & (HEAD < 0.5)
        crm = float(fr[body_ & (ax < 0.004)].min())
        mT = np.full(len(_ff), np.nan); mI = mT.copy(); mO = mT.copy()
        for i_, fb_ in enumerate(_ff):
            sel_ = body_ & (np.abs(fr - fb_) < 0.0025)
            if not sel_.any():
                continue
            if fb_ > crm + 0.004:
                mT[i_] = 0.5 * (xs_[sel_].max() - xs_[sel_].min())
            elif fb_ < crm - 0.004:
                lg_ = sel_ & (LEG > 0.5)
                if lg_.any():
                    mI[i_], mO[i_] = ax[lg_].min(), ax[lg_].max()
        def _fill(d_):
            ok_ = ~np.isnan(d_)
            if ok_.sum() < 2:
                return np.zeros_like(d_)
            d_ = np.interp(_ff, _ff[ok_], d_[ok_])
            return np.convolve(np.pad(d_, 3, mode="edge"), np.ones(7) / 7.0, mode="valid")
        dT, dI, dO = (_fill(r_ - m_) for r_, m_ in ((rT, mT), (rI, mI), (rO, mO)))
        CL = 0.02
        wtop = ss((0.745 - _ff) / 0.02); wbot = ss((_ff - 0.07) / 0.02)
        dT = np.clip(dT, -CL, CL) * wtop * FFIT; dI = np.clip(dI, -CL, CL) * wbot * FFIT; dO = np.clip(dO, -CL, CL) * wbot * FFIT
        mTf, mIf, mOf = (np.interp(fr, _ff, np.interp(_ff, _ff[~np.isnan(m_)], m_[~np.isnan(m_)])) for m_ in (mT, mI, mO))
        tT = np.clip(ax / np.maximum(mTf, 1e-3), 0, 1)
        dxT = np.interp(fr, _ff, dT) * tT
        tL = np.clip((ax - mIf) / np.maximum(mOf - mIf, 1e-3), 0, 1)
        dxL = np.interp(fr, _ff, dI) + (np.interp(fr, _ff, dO) - np.interp(fr, _ff, dI)) * tL
        up_ = ss((fr - crm) / 0.012)
        dx_ = (up_ * dxT + (1 - up_) * dxL) * np.sign(xs_)
        a2_ = np.clip(ARM / 0.6, 0, 1)
        for _ in range(60):
            a2_ = 0.5 * a2_ + 0.5 * avg(a2_)
        PROP[:, 0] += _Hr * dx_ * (1 - a2_) * (1 - np.clip(HEAD, 0, 1))
        DETAIL_REPORT["front_fit"] = {"crotch_f_model": round(crm, 4),
            "torso_half_corr_mm_at": {str(round(float(f_), 3)): round(float(v_ * _Hr * 1000), 1) for f_, v_ in zip(_ff[::8], dT[::8]) if f_ > 0.48},
            "leg_in_corr_mm_at": {str(round(float(f_), 3)): round(float(v_ * _Hr * 1000), 1) for f_, v_ in zip(_ff[::8], dI[::8]) if f_ < 0.47},
            "leg_out_corr_mm_at": {str(round(float(f_), 3)): round(float(v_ * _Hr * 1000), 1) for f_, v_ in zip(_ff[::8], dO[::8]) if f_ < 0.47}}
    # R117 (owner: "the legs still need proportioned properly"): each leg's outline fitted to the reference about the
    # leg's OWN centre line (the hip-anchored fit, R107, turned posture differences into whole-leg shifts).  Per height:
    # model front / back (side view) and inner / outer (front view) edges of one leg; centre lines = straight fits of the
    # mid-points over the thigh (0.30-0.45) and the shin (0.09-0.27); the reference edges are taken relative to its own
    # centre lines the same way (fit/ref_leg_side_profile.json, fit/ref_front_profile.json) and put onto the model's.
    # Into PROP (skeleton-level, smooth), blended across each section like the torso side fit; feet and the hip excluded.
    LFIT = float(os.environ.get("V2_LEG_FIT", "1"))   # (the leg loft R118 is off: it wrinkled and banded the legs, w7)
    if LFIT > 0:
        _ls = json.load(open(Path(__file__).resolve().parent / "fit" / "ref_leg_side_profile.json"))
        _lf = json.load(open(Path(__file__).resolve().parent / "fit" / "ref_front_profile.json"))
        Fb = np.array(_ls["f"]); rFs = np.array(_ls["front"]); rBs = np.array(_ls["back"])
        Ff = np.array(_lf["f"]); rIn = np.array([np.nan if v is None else v for v in _lf["leg_in"]]); rOut = np.array([np.nan if v is None else v for v in _lf["leg_out"]])
        okf = ~np.isnan(rIn); rIn = np.interp(Fb, Ff[okf], rIn[okf]); rOut = np.interp(Fb, Ff[okf], rOut[okf])
        _V = rest + PROP + off; _z0 = _V[:, 2].min(); _Hr = _V[:, 2].max() - _z0
        fr = (_V[:, 2] - _z0) / _Hr; fw = -_V[:, 1] / _Hr; ax = np.abs(_V[:, 0]) / _Hr
        legm = np.clip(LEG, 0, 1)
        one = (legm > 0.6) & (_V[:, 0] > 0) & (ARM < 0.3)
        mF = np.full(len(Fb), np.nan); mB = mF.copy(); mI = mF.copy(); mO = mF.copy()
        for i_, fb_ in enumerate(Fb):
            s_ = one & (np.abs(fr - fb_) < 0.0025)
            if s_.sum() > 5:
                mF[i_], mB[i_], mI[i_], mO[i_] = fw[s_].max(), fw[s_].min(), ax[s_].min(), ax[s_].max()
        ok_ = ~np.isnan(mF)
        mF, mB, mI, mO = (np.interp(Fb, Fb[ok_], m_[ok_]) for m_ in (mF, mB, mI, mO))
        def _centre(a_, b_):
            c_ = 0.5 * (a_ + b_); out_ = np.zeros_like(c_)
            for lo_, hi_, sel_ in ((0.30, 0.45, Fb >= 0.285), (0.09, 0.27, Fb < 0.285)):
                m_ = (Fb >= lo_) & (Fb <= hi_); k_ = np.polyfit(Fb[m_], c_[m_], 1); out_[sel_] = np.polyval(k_, Fb[sel_])
            return out_
        cMy, cRy = _centre(mF, mB), _centre(rFs, rBs); cMx, cRx = _centre(mI, mO), _centre(rIn, rOut)
        dF = (cMy + (rFs - cRy)) - mF; dB = (cMy + (rBs - cRy)) - mB
        dI = (cMx + (rIn - cRx)) - mI; dO = (cMx + (rOut - cRx)) - mO
        kk = np.ones(11) / 11.0                    # (w5: 5 bins left 2-3 cm swings between neighbouring heights - bands)
        sm = lambda d_: np.convolve(np.pad(d_, 5, mode="edge"), kk, mode="valid")
        wl = ss((Fb - 0.085) / 0.03) * ss((0.45 - Fb) / 0.03) * LFIT
        dF, dB, dI, dO = (np.clip(sm(sm(d_)), -0.015, 0.015) * wl for d_ in (dF, dB, dI, dO))
        ty = np.clip((fw - np.interp(fr, Fb, mB)) / np.maximum(np.interp(fr, Fb, mF) - np.interp(fr, Fb, mB), 1e-4), 0, 1)
        tx = np.clip((ax - np.interp(fr, Fb, mI)) / np.maximum(np.interp(fr, Fb, mO) - np.interp(fr, Fb, mI), 1e-4), 0, 1)
        dy_ = np.interp(fr, Fb, dB) + (np.interp(fr, Fb, dF) - np.interp(fr, Fb, dB)) * ty
        dx_ = np.interp(fr, Fb, dI) + (np.interp(fr, Fb, dO) - np.interp(fr, Fb, dI)) * tx
        wv = np.clip((legm - 0.2) / 0.5, 0, 1) * (ARM < 0.3) * (fr < 0.47)
        for _ in range(20):
            wv = 0.5 * wv + 0.5 * avg(wv)
        PROP[:, 1] -= _Hr * dy_ * wv
        PROP[:, 0] += _Hr * dx_ * wv * np.sign(_V[:, 0])
        DETAIL_REPORT["leg_fit"] = {k_: {str(round(float(f_), 3)): round(float(v_ * _Hr * 1000), 1) for f_, v_ in zip(Fb[::8], d_[::8])}
                                    for k_, d_ in (("front_mm", dF), ("back_mm", dB), ("inner_mm", dI), ("outer_mm", dO))}
    # overlaps on the refined surface, standing pose (same shrink as above, smaller steps)
    ov2 = []
    _off_pre = off.copy(); _first_pairs = None
    for it in range(int(os.environ.get("V2_OVERLAP_ITERS_FINE", "30"))):
        P_ = stand_eval(off)
        tr = _BVH.FromPolygons([Vector(v) for v in P_], _ft, all_triangles=True)
        pr = [(a_, b_) for a_, b_ in tr.overlap(tr) if a_ < b_ and not (_fs[a_] & _fs[b_])]
        ov2.append(len(pr))
        if _first_pairs is None and pr:
            _first_pairs = np.array(pr)
        if not pr or (len(ov2) > 4 and min(ov2[-4:]) >= min(ov2[:-4])):       # stop when it no longer improves
            break
        hit = np.zeros(nv); hit[np.unique(faces[np.array(pr).ravel()].ravel())] = 1.0
        for _ in range(16):                              # fine mesh: ~3x the coarse loop's reach, so the shrink stays smooth
            hit = np.maximum(hit, avg(hit))
        for _ in range(60):
            hit = 0.5 * hit + 0.5 * avg(hit)
        off = off * (1.0 - 0.2 * np.clip(hit * 2, 0, 1))[:, None]
    # a fold (neighbouring triangles crossing) cannot be shrunk away: relax the skin itself around what is left
    for _fix in range(4):
        if not (ov2 and ov2[-1]):
            break
        P_ = stand_eval(off)
        tr = _BVH.FromPolygons([Vector(v) for v in P_], _ft, all_triangles=True)
        pr = [(a_, b_) for a_, b_ in tr.overlap(tr) if a_ < b_ and not (_fs[a_] & _fs[b_])]
        if not pr:
            ov2.append(0); break
        zone = np.zeros(nv); zone[np.unique(faces[np.array(pr).ravel()].ravel())] = 1.0
        for _ in range(6):
            zone = np.maximum(zone, avg(zone))
        for _ in range(6):
            zone = 0.5 * zone + 0.5 * avg(zone)
        Q = rest + off
        for _ in range(30):
            Q = Q + 0.5 * zone[:, None] * (np.stack([avg(Q[:, k]) for k in range(3)], axis=1) - Q)
            Q = Q - 0.53 * zone[:, None] * (np.stack([avg(Q[:, k]) for k in range(3)], axis=1) - Q)
        off = Q - rest
        P_ = stand_eval(off)
        tr = _BVH.FromPolygons([Vector(v) for v in P_], _ft, all_triangles=True)
        ov2.append(sum(1 for a_, b_ in tr.overlap(tr) if a_ < b_ and not (_fs[a_] & _fs[b_])))
    DETAIL_REPORT["overlap_iterations"] = ov2
    # what the fine overlap loop took away (v12q: the nipples did not show at all)
    _lost = np.linalg.norm(off - _off_pre, axis=1)
    _diag = {"lost_max_mm": round(float(_lost.max() * 1000), 1), "verts_lost_gt_2mm": int((_lost > 0.002).sum())}
    if "_nip_i" in globals():
        _diag["nipple_off_mm_before_after"] = [round(float(np.linalg.norm(_off_pre[_nip_i]) * 1000), 1), round(float(np.linalg.norm(off[_nip_i]) * 1000), 1)]
    if _first_pairs is not None:
        _c = 0.5 * (rest[faces[_first_pairs[:, 0]]].mean(1) + rest[faces[_first_pairs[:, 1]]].mean(1))
        _diag["first_pairs_rest_centre_pct"] = np.percentile(_c, [5, 50, 95], axis=0).round(3).tolist()
        _diag["first_pairs_sample"] = _c[:: max(1, len(_c) // 8)].round(3).tolist()
    _w = _lost > 0.002
    if _w.any():
        _diag["lost_region_pct"] = np.percentile(rest[_w], [5, 50, 95], axis=0).round(3).tolist()
    DETAIL_REPORT["overlap_loss"] = _diag
    if ov2 and ov2[-1]:
        P_ = stand_eval(off)
        tr = _BVH.FromPolygons([Vector(v) for v in P_], _ft, all_triangles=True)
        pr = [(a_, b_) for a_, b_ in tr.overlap(tr) if a_ < b_ and not (_fs[a_] & _fs[b_])]
        DETAIL_REPORT["overlap_where_rest"] = [[round(float(c), 3) for c in rest[faces[a_]].mean(0)] + [round(float(c), 3) for c in rest[faces[b_]].mean(0)] for a_, b_ in pr[:12]]
WIDTH_REPORT = {"overlap_iterations": ov_log, "clearance_iterations": clr_iters, "min_scale": round(float(scale.min()), 3), "waist_mm": WAIST_MM, "chest_mm": CHEST_MM, "max_side_push_mm": round(float(push.max() * 1000), 2)}
np.savez_compressed(OUT / "body_v2_offsets.npz", offsets=(off + PROP).astype(np.float32), proportion=PROP.astype(np.float32))   # R81: offsets = sculpt + proportion
mir = {}
rep = {"gain": GAIN, "head_scale": HEAD_SCALE, "shoulder": SHOULDER_REPORT, "abs_mm": ABS_MM, "hamstring_mm": HAM_MM, "width": WIDTH_REPORT, "lumbar_mm": LUMBAR_MM, "spine_mm": SPINE_MM, "union_p": UNION_P, "relax": int(os.environ.get("V2_RELAX", "4")), "max_mm": round(float(amt.max() * 1000), 2), "mean_mm_nonzero": round(float(amt[amt > 1e-4].mean() * 1000), 2),
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
rep["standing_self_intersections"] = {"v1": _pairs(stand_eval(np.zeros_like(off))), "v2": _pairs(stand_eval(off))}
body.shape_key_remove(_fitkey); _bench._reset(rig)
rep["refine"] = REFINE_REPORT; rep["detail"] = DETAIL_REPORT; rep["hip_pivot"] = globals().get("HIP_PIVOT_REPORT")
np.save(OUT / "rest.npy", rest.astype(np.float32)); np.save(OUT / "tris.npy", faces.astype(np.int32))
(OUT / "body_v2_report.json").write_text(json.dumps(rep, indent=1))
print("V2_SCULPT", json.dumps(rep), flush=True)

if os.environ.get("R76_RENDER") == "1":
    key = body.shape_key_add(name="V2_BODY_SCULPT", from_mix=False)
    key.data.foreach_set("co", (rest + PROP + off).ravel().astype(np.float32)); key.value = 1.0
    _co = {"V1": (rest + PROP).ravel().astype(np.float32), "V2": (rest + PROP + off).ravel().astype(np.float32)}   # V1 = original surface on the R81 skeleton
    sc = bpy.context.scene
    for ob in sc.objects:
        if ob.type in ("MESH", "CURVE") and ob is not body:
            ob.hide_render = True
    mat = bpy.data.materials.new("REVIEW_ONLY"); mat.diffuse_color = (.72, .55, .45, 1)
    body.data.materials.clear(); body.data.materials.append(mat)
    sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
    sc.display.shading.show_cavity = os.environ.get("V2_CAVITY", "1") == "1"; sc.render.resolution_x = 900; sc.render.resolution_y = 1500
    cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
    bpy.context.view_layer.update()
    lo, hi = rest.min(0), rest.max(0); mid = Vector(((lo + hi) / 2).tolist()); cd.ortho_scale = float(hi[2] - lo[2]) * 1.08
    for tag, val in (("V1", 0.0), ("V2", 1.0)):
        key.data.foreach_set("co", _co[tag]); key.value = 1.0; bpy.context.view_layer.update()
        for view, dv in {"front": (0, -1, 0), "back": (0, 1, 0), "side": (1, 0, 0), "front34": (0.7, -0.7, 0), "back34": (0.7, 0.7, 0)}.items():
            dvec = Vector(dv).normalized(); cam.location = mid + dvec * 4; cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (-dvec).to_track_quat("-Z", "Y")
            sc.render.filepath = str(OUT / f"{tag}_full_standing_{view}.png"); bpy.ops.render.render(write_still=True)
    # R77 (owner chose "Standing pose"): natural standing pose with the arms slightly out, like the reference photos -
    # upper arms abducted V2_STAND_ABD deg (Work's convention: upper-arm local -Z abducts _r, +Z abducts _l), elbows
    # flexed V2_STAND_ELBOW deg.  The build (bind) pose is unchanged; this is a pose, like any exercise pose.
    import math
    import build_original_movement_benchmarks_blender as bench
    import original_v1_review_candidate_drives as drives
    abd, elb = (float(x) for x in os.environ.get("V2_STAND", "16:6").split(":"))
    for tag, val in (("V1", 0.0), ("V2", 1.0)):
        key.data.foreach_set("co", _co[tag]); key.value = 1.0
        bench._reset(rig)
        for sd, sg in (("r", -1.0), ("l", 1.0)):
            pb = rig.pose.bones[f"upperarm_{sd}"]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (0.0, 0.0, math.radians(sg * abd))
            fb = rig.pose.bones[f"forearm_{sd}"]; fb.rotation_mode = "XYZ"; fb.rotation_euler = (math.radians(-elb), 0.0, 0.0)
        bpy.context.view_layer.update(); drives.drive(rig, body); bpy.context.view_layer.update()
        for view, dv in {"front": (0, -1, 0), "back": (0, 1, 0), "side": (1, 0, 0), "front34": (0.7, -0.7, 0), "back34": (0.7, 0.7, 0)}.items():
            dvec = Vector(dv).normalized(); cam.location = mid + dvec * 4; cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (-dvec).to_track_quat("-Z", "Y")
            sc.render.filepath = str(OUT / f"{tag}_full_stand_{view}.png"); bpy.ops.render.render(write_still=True)
    # R103 (owner chose "Yes, closer lighting"): the grey workbench renders flatten every form; skin-tone renders with soft
    # studio lighting (Cycles, key / fill / rim area lights) closer to the reference figure's.  Review only - the model
    # itself is unchanged.  Still in the V2 standing pose from the loop above.
    if os.environ.get("V2_SKIN_RENDER", "1") == "1":
        sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = int(os.environ.get("V2_SKIN_SAMPLES", "48"))
        try:
            sc.cycles.use_denoising = True
        except Exception:
            pass
        sm = bpy.data.materials.new("REVIEW_SKIN"); sm.use_nodes = True
        bsdf = sm.node_tree.nodes.get("Principled BSDF")
        # R114 (owner: "The texture of the body seems shiny and not smooth"): a satin skin finish - rougher, less specular,
        # a little more subsurface (was roughness 0.42, specular 0.45, subsurface 0.12)
        bsdf.inputs["Base Color"].default_value = (0.62, 0.40, 0.30, 1); bsdf.inputs["Roughness"].default_value = float(os.environ.get("V2_SKIN_ROUGH", "0.62"))
        for nm, val in (("Subsurface Weight", 0.2), ("Subsurface Scale", 0.012), ("Specular IOR Level", 0.28)):
            if nm in bsdf.inputs:
                bsdf.inputs[nm].default_value = val
        body.data.materials.clear(); body.data.materials.append(sm)
        if sc.world is None:
            sc.world = bpy.data.worlds.new("W")
        sc.world.use_nodes = True; sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.055, 1)
        sc.world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
        try:
            sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "None"
        except Exception:
            pass
        lights = []
        for nm, loc, energy, size in (("KEY", (-1.6, -2.6, 2.6), 70, 1.6), ("FILL", (2.2, -2.0, 1.4), 18, 2.5), ("RIM", (1.2, 2.6, 2.4), 45, 1.2)):
            ld = bpy.data.lights.new(nm, "AREA"); ld.energy = energy; ld.size = size
            lo_ = bpy.data.objects.new(nm, ld); sc.collection.objects.link(lo_); lo_.location = loc
            lo_.rotation_mode = "QUATERNION"; lo_.rotation_quaternion = (mid - Vector(loc)).to_track_quat("-Z", "Y"); lights.append(lo_)
        _sk = float(os.environ.get("V2_SKIN_SCALE", "2"))     # R114: 1800 x 3000 for region close-ups against the reference
        sc.render.resolution_x = int(900 * _sk); sc.render.resolution_y = int(1500 * _sk)
        for view, dv in {"front": (0, -1, 0), "side": (1, 0, 0), "front34": (0.7, -0.7, 0), "back": (0, 1, 0)}.items():
            dvec = Vector(dv).normalized(); cam.location = mid + dvec * 4; cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (-dvec).to_track_quat("-Z", "Y")
            if view == "side":   # the reference side view is lit from its front: key light swings round with the camera
                lights[0].location = (2.6, -1.6, 2.6); lights[0].rotation_quaternion = (mid - lights[0].location).to_track_quat("-Z", "Y")
            if view == "back":
                lights[0].location = (-1.6, 2.6, 2.6); lights[0].rotation_quaternion = (mid - lights[0].location).to_track_quat("-Z", "Y")
            sc.render.filepath = str(OUT / f"V2_skin_stand_{view}.png"); bpy.ops.render.render(write_still=True)
        lights[0].location = (-1.6, -2.6, 2.6); lights[0].rotation_quaternion = (mid - lights[0].location).to_track_quat("-Z", "Y")
        sc.render.resolution_x = 900; sc.render.resolution_y = 1500
        # chest close-ups (0.62-0.92 of stature)
        _os = cd.ortho_scale; _H = float(hi[2] - lo[2]); sc.render.resolution_x = 1000; sc.render.resolution_y = 1000
        # framed on the finished body's own height (v12q-v13a framed on the base mesh's, so against the reference the
        # model's chest looked ~0.02 of stature higher than it is)
        _Vf = (rest + PROP + off); _z0 = float(_Vf[:, 2].min()); _H = float(_Vf[:, 2].max()) - _z0
        cd.ortho_scale = 0.30 * _H; _cm = Vector((0.0, mid.y, _z0 + 0.77 * _H))
        lights[0].location = (-1.6, -2.6, 2.6); lights[0].rotation_quaternion = (mid - lights[0].location).to_track_quat("-Z", "Y")
        for view, dv in {"front": (0, -1, 0), "front34": (0.7, -0.7, 0), "side": (1, 0, 0)}.items():
            dvec = Vector(dv).normalized(); cam.location = _cm + dvec * 4; cam.rotation_quaternion = (-dvec).to_track_quat("-Z", "Y")
            if view == "side":
                lights[0].location = (2.6, -1.6, 2.6); lights[0].rotation_quaternion = (mid - lights[0].location).to_track_quat("-Z", "Y")
            sc.render.filepath = str(OUT / f"V2_skin_chest_{view}.png"); bpy.ops.render.render(write_still=True)
        cd.ortho_scale = _os; sc.render.resolution_x = 900; sc.render.resolution_y = 1500
    # R109: pelvis close-ups (standing, skin + grey) and hip deformation tests (owner: "Test standing, hip flexion,
    # abduction, squatting and hip hinging for natural deformation"), each framed on the pelvis, with the standing-pose
    # style overlap count for every pose.
    if os.environ.get("V2_HIP_TESTS", "1") == "1":
        _Vf = (rest + PROP + off); _z0 = float(_Vf[:, 2].min()); _H = float(_Vf[:, 2].max()) - _z0
        sc.render.resolution_x = 900; sc.render.resolution_y = 900
        _osc = cd.ortho_scale
        def _shot(name, centre, scale, views, engine):
            sc.render.engine = engine
            cd.ortho_scale = scale
            for view, dv in views.items():
                dvec = Vector(dv).normalized(); cam.location = centre + dvec * 4; cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (-dvec).to_track_quat("-Z", "Y")
                sc.render.filepath = str(OUT / f"{name}_{view}.png"); bpy.ops.render.render(write_still=True)
        V4 = {"front": (0, -1, 0), "back": (0, 1, 0), "side": (1, 0, 0), "front34": (0.7, -0.7, 0)}
        _pc = Vector((0.0, mid.y, _z0 + 0.49 * _H))
        if os.environ.get("V2_SKIN_RENDER", "1") == "1":
            lights[0].location = (-1.6, -2.6, 2.6); lights[0].rotation_quaternion = (mid - lights[0].location).to_track_quat("-Z", "Y")
            _shot("V2_skin_pelvis", _pc, 0.36 * _H, V4, "CYCLES")
        body.data.materials.clear(); body.data.materials.append(mat)
        _shot("V2_grey_pelvis", _pc, 0.36 * _H, V4, "BLENDER_WORKBENCH")
        rest_heads = {s_: rig.pose.bones[f"foot_{s_}"].head.copy() for s_ in ("l", "r")}

        def _hp_stand():
            pass

        def _hp_flex():
            bench._rot(rig.pose.bones["thigh_r"], x=-90.0); bench._rot(rig.pose.bones["shin_r"], x=90.0)

        def _hp_abd():
            bench._rot(rig.pose.bones["thigh_r"], z=float(os.environ.get("V2_HIP_ABD_SIGN", "-1")) * 40.0)
            bench._rot(rig.pose.bones["thigh_l"], z=-float(os.environ.get("V2_HIP_ABD_SIGN", "-1")) * 40.0)

        def _hp_squat():
            bench.pose_squat(rig, 1.0, rest_heads)

        def _hp_hinge():
            bench._rot(rig.pose.bones["pelvis"], x=60.0)
            for s_ in ("l", "r"):
                bench._rot(rig.pose.bones[f"thigh_{s_}"], x=-60.0); bench._rot(rig.pose.bones[f"shin_{s_}"], x=10.0)

        def _arm(deg):
            def f_():
                for s_, sg in (("r", -1.0), ("l", 1.0)):
                    bench._rot(rig.pose.bones[f"upperarm_{s_}"], z=sg * deg)
            return f_

        HIPTEST = {}
        for nm, fn in (("stand", _hp_stand), ("flex90", _hp_flex), ("abd40", _hp_abd), ("squat", _hp_squat), ("hinge60", _hp_hinge),
                       ("armabd90", _arm(90.0)), ("armup160", _arm(160.0))):
            bench._reset(rig)
            for s_, sg in (("r", -1.0), ("l", 1.0)):
                pb = rig.pose.bones[f"upperarm_{s_}"]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (0.0, 0.0, math.radians(sg * 25.0))
            fn()
            bpy.context.view_layer.update(); drives.drive(rig, body); bpy.context.view_layer.update()
            _isarm = nm.startswith("arm")
            pp_, _ = bench._evaluated(body); P_ = np.array([tuple(v) for v in pp_])
            tr_ = _BVH.FromPolygons([Vector(v) for v in P_], _ft, all_triangles=True)
            prs = [(a_, b_) for a_, b_ in tr_.overlap(tr_) if a_ < b_ and not (_fs[a_] & _fs[b_])]
            # pairs near the pelvis (within 0.25 m of the pelvis bone head) - the region under test
            ph = np.array(rig.pose.bones["pelvis"].head)
            near = [p_ for p_ in prs if np.linalg.norm(P_[faces[p_[0]]].mean(0) - ph) < 0.25]
            HIPTEST[nm] = {"overlap_pairs": len(prs), "overlap_pairs_pelvis": len(near)}
            if _isarm:            # R113: shoulder tests - pairs within 0.2 m of either shoulder joint, framed on the chest
                shs = [np.array(rig.pose.bones[f"upperarm_{s_}"].head) for s_ in ("r", "l")]
                HIPTEST[nm]["overlap_pairs_shoulders"] = sum(1 for p_ in prs if min(np.linalg.norm(P_[faces[p_[0]]].mean(0) - h_) for h_ in shs) < 0.2)
                ph = 0.5 * (shs[0] + shs[1])
            _c = Vector(tuple(P_[np.linalg.norm(P_ - ph, axis=1) < 0.30].mean(0)))
            _shot(f"V2_hip_{nm}", _c, 0.55 * _H, {"front": (0, -1, 0), "side": (1, 0, 0), "back": (0, 1, 0)}, "BLENDER_WORKBENCH")
        (OUT / "hip_tests.json").write_text(json.dumps(HIPTEST, indent=1))
        print("V2_HIPTESTS", json.dumps(HIPTEST), flush=True)
        cd.ortho_scale = _osc; sc.render.resolution_x = 900; sc.render.resolution_y = 1500
    bench._reset(rig)
    print("V2_RENDERED", flush=True)

# R119 (owner chose "New leg & foot mesh"): save the finished body - the V2 shape baked into the basis (every shape key
# moved with it, so the correctives keep their deltas), skin weights and the edited rig - for legs_v2_blender.py.
if os.environ.get("V2_SAVE_BLEND", "0") == "1":
    bench._reset(rig) if "bench" in globals() else None
    _V2 = (rest + PROP + off).astype(np.float64)
    _co = np.empty(nv * 3); body.data.vertices.foreach_get("co", _co); _D = _V2 - _co.reshape(-1, 3)
    if body.data.shape_keys:
        for kb in body.data.shape_keys.key_blocks:
            if kb.name in ("V2_BODY_SCULPT", "V2_FIT"):
                continue
            c_ = np.empty(nv * 3); kb.data.foreach_get("co", c_); kb.data.foreach_set("co", (c_.reshape(-1, 3) + _D).ravel())
        for nm_ in ("V2_BODY_SCULPT", "V2_FIT"):
            if nm_ in body.data.shape_keys.key_blocks:
                body.shape_key_remove(body.data.shape_keys.key_blocks[nm_])
    body.data.vertices.foreach_set("co", _V2.ravel()); body.data.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "body_v2.blend"), copy=True)
    print("V2_SAVED", OUT / "body_v2.blend", flush=True)

