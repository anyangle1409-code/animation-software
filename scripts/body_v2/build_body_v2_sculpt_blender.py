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
abd = np.interp(rest[:, 2], [0.95, 1.02, 1.10, 1.22, 1.30, 1.34], [0, 0.7, 1.0, 1.0, 0.4, 0]) * ss(-nrm[:, 1] / 0.5) * ss(1 - np.abs(rest[:, 0]) / 0.13) * (1 - ARM) * (rest[:, 1] < 0)
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
    piv = np.array([0.0, 0.0, 1.70])
    hw_ = ss((rest[:, 2] - 1.585) / 0.035) * ss((0.12 - np.abs(rest[:, 0])) / 0.03)
    off = off + (rest + off - piv) * ((HEAD_SCALE - 1.0) * hw_)[:, None]
# R77e: relax the offset field around the shoulders (drop field + deltoid bellies meeting) - measured extra roughness
# on the deltoid came from the overlap shrink, the shoulder drop and the bellies, in that order
_sh = ss((np.abs(rest[:, 0]) - 0.12) / 0.04) * ss((rest[:, 2] - 1.24) / 0.06) * ss((1.62 - rest[:, 2]) / 0.04)
for _ in range(int(os.environ.get("V2_SHOULDER_RELAX", "8"))):
    off = off + 0.5 * _sh[:, None] * (np.stack([avg(off[:, k]) for k in range(3)], axis=1) - off)
# R77 (owner chose "Standing pose"): the body is shown standing with the arms ~9 deg out, so overlaps are tested in that
# pose (in the build pose the forearms hang against the hips, and testing there removed all new forearm volume)
import math as _m
import build_original_movement_benchmarks_blender as _bench
import original_v1_review_candidate_drives as _drives
_STAND = tuple(float(x) for x in os.environ.get("V2_STAND", "9:6").split(":"))
_fitkey = body.shape_key_add(name="V2_FIT", from_mix=False); _fitkey.value = 1.0


def stand_eval(offsets):
    _fitkey.data.foreach_set("co", (rest + offsets).ravel().astype(np.float32))
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
WIDTH_REPORT = {"overlap_iterations": ov_log, "clearance_iterations": clr_iters, "min_scale": round(float(scale.min()), 3), "waist_mm": WAIST_MM, "chest_mm": CHEST_MM, "max_side_push_mm": round(float(push.max() * 1000), 2)}
np.savez_compressed(OUT / "body_v2_offsets.npz", offsets=off.astype(np.float32))
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
    # R77 (owner chose "Standing pose"): natural standing pose with the arms slightly out, like the reference photos -
    # upper arms abducted V2_STAND_ABD deg (Work's convention: upper-arm local -Z abducts _r, +Z abducts _l), elbows
    # flexed V2_STAND_ELBOW deg.  The build (bind) pose is unchanged; this is a pose, like any exercise pose.
    import math
    import build_original_movement_benchmarks_blender as bench
    import original_v1_review_candidate_drives as drives
    abd, elb = (float(x) for x in os.environ.get("V2_STAND", "9:6").split(":"))
    for tag, val in (("V1", 0.0), ("V2", 1.0)):
        key.value = val
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
