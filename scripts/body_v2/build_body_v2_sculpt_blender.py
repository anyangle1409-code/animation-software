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
_STAND = tuple(float(x) for x in os.environ.get("V2_STAND", "12:6").split(":"))
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
    REFINE_REPORT, _mi, _mw = refine(body, th_mm=REFINE_MM)
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
        er = np.maximum(er, ss((fz_ - 0.70) / 0.02) * ss((0.80 - fz_) / 0.02) * ss((0.165 - ax_) / 0.03) * front_ * (1 - _keep))
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
        blocks = [  # (z_lo(x), z_hi(x), x_out at z_lo, x_out at z_hi, amp mm)
            (0.684 - 0.03 * xh, 0.706 - 0.10 * xh, 0.068, 0.058, 7.0),
            (0.660 + 0.00 * xh, 0.684 - 0.03 * xh, 0.071, 0.070, 9.0),
            (0.636 + 0.10 * xh, 0.660 + 0.00 * xh, 0.056, 0.066, 5.5),
        ]
        seg = np.zeros(nv)
        for zlo_, zhi_, xa_, xb_, amp_ in blocks:
            t_ = np.clip((fz_ - zlo_) / np.maximum(zhi_ - zlo_, 1e-4), 0, 1)
            xout = Hs * (xa_ + (xb_ - xa_) * t_)
            u_ = np.clip((ax_ - 0.004) / np.maximum(xout - 0.004, 1e-3), 0, 1)
            # dome centred a little above the middle of the block and towards the middle of the column
            r_ = (np.abs(2 * u_ - 1.0) ** 2.3 + np.abs((2 * t_ - 1.0) - 0.12) ** 2.3) ** (1 / 2.3)
            # soft edges (cos^2): a steep edge read as a hard horizontal line (v9g/v9h); the pillows meet in gentle valleys
            seg += amp_ * np.cos(0.5 * np.pi * np.clip(r_, 0, 1)) ** 2 * (fz_ > zlo_) * (fz_ < zhi_) * (ax_ < xout)
        h += float(os.environ.get("V2_ABS_SEG_SCALE", "1.0")) * seg
        top = ss((0.706 - 0.10 * xh - fz_) / 0.010)
        # linea alba: sternum to navel, fading out below it
        la = np.interp(fz_, [0.565, 0.60, 0.62, 0.72, 0.74], [0, 0.6, 1.0, 1.0, 0.6])
        h -= 4.5 * la * np.exp(-0.5 * (ax_ / 0.0060) ** 2)   # wide enough for the 4 mm mesh; frames the blocks (R87)
        # linea semilunaris: soft groove at the rectus' outer edge, above the navel
        h -= 2.6 * np.exp(-0.5 * ((ax_ - xo - 0.004) / 0.010) ** 2) * ss((fz_ - 0.60) / 0.03) * top
        # pectoralis major: full masses out towards the armpit; lower border level across the middle, rising at the side,
        # sharp below (crisp shadow), long and soft above towards the clavicle; shallow sternal groove
        pc = 0.744 + 0.30 * np.clip(ax_ - 0.10, 0, None)
        dz_ = fz_ - pc
        pec = np.exp(-0.5 * ((ax_ - 0.095) / np.where(ax_ > 0.095, 0.060, 0.075)) ** 2) * \
              np.where(dz_ > 0, np.exp(-0.5 * ((dz_ - 0.018) / 0.040) ** 2) * (dz_ > 0.018) + (dz_ <= 0.018) * 1.0, np.exp(-0.5 * (dz_ / 0.0065) ** 2))
        h += float(os.environ.get("V2_PEC_MM", "11")) * pec * ss((ax_ - 0.004) / 0.012) * ss((0.175 - ax_) / 0.03)   # stops short of the arm
        h -= 1.0 * np.exp(-0.5 * (ax_ / 0.007) ** 2) * ss((fz_ - 0.712) / 0.01) * ss((0.80 - fz_) / 0.02)
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
        DETAIL_REPORT["front_muscles"] = {"abs_erase_steps": int(os.environ.get("V2_ABS_ERASE", "150")), "intersections": ints,
                                           "max_mm": round(float(h.max()), 2), "min_mm": round(float(h.min()), 2)}
    # R85 (owner, with the reference figure's groin close-ups: "Can we have the groin area match this ... I still see the
    # weird line at the top of the legs where it meets the torso ... There is no line there and it's smooth transition"):
    # the model had a horizontal fold across both thigh tops at ~0.49 of stature, just above the crotch, and a flat wide
    # shelf for the pubic area.  Reference: the inguinal creases are long soft curves from the side of the hip (~0.56,
    # |x| ~0.08 of stature) to beside the crotch (~0.48); between them a rounded pubic wedge with a U-shaped bottom; no
    # horizontal line.  So: flatten the whole groin band (plain normal-only cotangent steps: removes the fold and the
    # shelf), then the wedge and the creases on the reference curve.
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
        CR_MM = float(os.environ.get("V2_GROIN_CREASE_MM", "3.0"))
        h -= CR_MM * np.exp(-0.5 * (best / 0.010) ** 2) * ss(tpar / 0.12) * ss((1 - tpar) / 0.30) * frontish   # fades before the crotch: a U, not a point
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
    GLUTE_D = float(os.environ.get("V2_GLUTE_FOLD_MM", "5"))
    off += groove([(0.022, cz - 0.004), (0.06, cz - 0.022), (0.11, cz - 0.018), (0.15, cz + 0.005)], 0.007, GLUTE_D, +1)
    DETAIL_REPORT.update({"navel_mm": NAVEL_MM, "navel_z": round(float(zn), 4), "inguinal_mm": ING_D, "glute_fold_mm": GLUTE_D, "crotch_z": round(float(cz), 4)})
    # overlaps on the refined surface, standing pose (same shrink as above, smaller steps)
    ov2 = []
    for it in range(int(os.environ.get("V2_OVERLAP_ITERS_FINE", "30"))):
        P_ = stand_eval(off)
        tr = _BVH.FromPolygons([Vector(v) for v in P_], _ft, all_triangles=True)
        pr = [(a_, b_) for a_, b_ in tr.overlap(tr) if a_ < b_ and not (_fs[a_] & _fs[b_])]
        ov2.append(len(pr))
        if not pr or (len(ov2) > 4 and min(ov2[-4:]) >= min(ov2[:-4])):       # stop when it no longer improves
            break
        hit = np.zeros(nv); hit[np.unique(faces[np.array(pr).ravel()].ravel())] = 1.0
        for _ in range(16):                              # fine mesh: ~3x the coarse loop's reach, so the shrink stays smooth
            hit = np.maximum(hit, avg(hit))
        for _ in range(60):
            hit = 0.5 * hit + 0.5 * avg(hit)
        off = off * (1.0 - 0.2 * np.clip(hit * 2, 0, 1))[:, None]
    DETAIL_REPORT["overlap_iterations"] = ov2
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
rep["refine"] = REFINE_REPORT; rep["detail"] = DETAIL_REPORT
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
    abd, elb = (float(x) for x in os.environ.get("V2_STAND", "12:6").split(":"))
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
    bench._reset(rig)
    print("V2_RENDERED", flush=True)
