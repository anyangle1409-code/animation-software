"""R119 (owner chose "New leg & foot mesh"): replace the legs and feet of the finished v2 body with new geometry.

The v2 legs are R41's coarse leg tubes pushed about by many sculpt layers; R118 showed they cannot be re-shaped into the
reference's lean, defined legs without wrinkling.  So below a horizontal cut (V2_LEGS_CUT, fraction of stature) each
leg is rebuilt:

  * leg: rings of evenly spaced vertices from the cut loop (ring 0 is the cut loop itself) down to the ankle.  Each ring
    is a super-ellipse sized from the owner's reference figure (front widths and side depths about each leg's own
    centre line, as R117) with anatomical relief (vastus lateralis / medialis, rectus and sartorius grooves, IT band,
    hamstring split, patella and its tendon hollows, popliteal hollow, gastrocnemius heads, soleus, tibialis anterior,
    tibial crest).  The relief only shapes the skin between the outline points: each quadrant is rescaled to the
    reference outline afterwards.  It blends from the old surface over the first few centimetres below the cut.
  * foot: a signed-distance model (heel, talus, malleoli, lateral column, medial arch, instep, metatarsal heads, five
    toes with knuckles, Achilles tendon, ankle) at ANSUR II proportions for this stature and the reference's foot
    length, surfaced with marching cubes, cut at the ankle and stitched to the last leg ring.
  * skin weights and every shape key's delta are carried over from the nearest old leg / foot vertices (inverse
    distance, 4 neighbours), so the rig, the drivers and the correctives keep working; then the weights are smoothed.

usage: blender python legs_v2_blender.py -- <body_v2.blend> <r57src root> <out dir>
"""
import json
import math
import os
import sys
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
SRC, ROOT, OUT = Path(args[0]).resolve(), Path(args[1]).resolve(), Path(args[2])
OUT.mkdir(parents=True, exist_ok=True)
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts/anatomy_fit"), str(HERE)]
from scipy.spatial import cKDTree
from skimage.measure import marching_cubes

bpy.ops.wm.open_mainfile(filepath=str(SRC))
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
assert np.allclose(np.array(body.matrix_world), np.eye(4), atol=1e-6), "body object transform is not identity"
REP = {}


def ss(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


me = body.data
nv0 = len(me.vertices)
V0 = np.empty(nv0 * 3); me.vertices.foreach_get("co", V0); V0 = V0.reshape(-1, 3)
z0 = float(V0[:, 2].min()); H = float(V0[:, 2].max()) - z0
GN = [g.name for g in body.vertex_groups]
W0 = np.zeros((nv0, len(GN)), np.float32)
for v in me.vertices:
    for g in v.groups:
        W0[v.index, g.group] = g.weight
gi = {n: i for i, n in enumerate(GN)}
ARMK = ("upperarm", "forearm", "hand", "thumb", "index", "middle", "ring", "pinky", "finger", "wrist", "clav")
ARM = W0[:, [i for i, n in enumerate(GN) if any(k in n.lower() for k in ARMK)]].sum(1)
SIDES = (("r", 1.0), ("l", -1.0))     # R41: _r is +x
LEGW = {sd: sum(W0[:, gi[f"{b}_{sd}"]] for b in ("thigh", "shin", "foot", "toe") if f"{b}_{sd}" in gi) for sd, _ in SIDES}
KEYS = [kb.name for kb in me.shape_keys.key_blocks] if me.shape_keys else []
KD0 = {}
for kb in (me.shape_keys.key_blocks if me.shape_keys else []):
    c_ = np.empty(nv0 * 3); kb.data.foreach_get("co", c_); KD0[kb.name] = c_.reshape(-1, 3) - V0
REP["groups"] = len(GN); REP["shape_keys"] = len(KEYS); REP["stature_m"] = round(H, 4)

# rig (rest, world) - ankle centre and knee
RM = rig.matrix_world
BONE = {b.name: (np.array(RM @ b.head_local), np.array(RM @ b.tail_local)) for b in rig.data.bones}

# ------------------------------------------------------------------ reference targets (fractions of stature)
_ls = json.load(open(HERE / "fit" / "ref_leg_side_profile.json"))
_lf = json.load(open(HERE / "fit" / "ref_front_profile.json"))
Fb = np.array(_ls["f"]); rFs = np.array(_ls["front"]); rBs = np.array(_ls["back"])
Ff = np.array(_lf["f"]); rIn = np.array([np.nan if v is None else v for v in _lf["leg_in"]]); rOut = np.array([np.nan if v is None else v for v in _lf["leg_out"]])
okf = ~np.isnan(rIn); rIn = np.interp(Fb, Ff[okf], rIn[okf]); rOut = np.interp(Fb, Ff[okf], rOut[okf])
fr0 = (V0[:, 2] - z0) / H; fw0 = -V0[:, 1] / H


def _centre(c_):
    """straight-line fits of a centre line over the thigh and the shin (as R117), blended across the knee (R117 switched
    between them at 0.285, which is a step of up to a centimetre - harmless for a displacement, a ledge for new rings)"""
    fit_ = [np.polyval(np.polyfit(Fb[(Fb >= lo_) & (Fb <= hi_)], c_[(Fb >= lo_) & (Fb <= hi_)], 1), Fb) for lo_, hi_ in ((0.09, 0.27), (0.30, 0.45))]
    w_ = ss((Fb - 0.255) / 0.06)
    return (1 - w_) * fit_[0] + w_ * fit_[1]


def _smooth(d_, n=7):
    k_ = np.ones(n) / n
    return np.convolve(np.pad(d_, n // 2, mode="edge"), k_, mode="valid")


cRy, cRx = _centre(0.5 * (rFs + rBs)), _centre(0.5 * (rIn + rOut))
# below 0.085 the side outline takes in the instep and heel: hold the ankle values there
_lo = Fb < 0.085
TF, TB, TI, TO = (_smooth(np.where(_lo, np.interp(0.085, Fb, a_), a_)) for a_ in (rFs - cRy, cRy - rBs, cRx - rIn, rOut - cRx))
# the old legs' own centre lines (R117 fitted the outline about them, so the new legs stay where the old ones stood)
MC = {}
for sd, sg in SIDES:
    one = (LEGW[sd] > 0.6) & (V0[:, 0] * sg > 0) & (ARM < 0.3)
    mF = np.full(len(Fb), np.nan); mB = mF.copy(); mI = mF.copy(); mO = mF.copy()
    for i_, f_ in enumerate(Fb):
        s_ = one & (np.abs(fr0 - f_) < 0.0025)
        if s_.sum() > 5:
            ax_ = np.abs(V0[s_, 0]) / H
            mF[i_], mB[i_], mI[i_], mO[i_] = fw0[s_].max(), fw0[s_].min(), ax_.min(), ax_.max()
    ok_ = ~np.isnan(mF)
    mF, mB, mI, mO = (np.interp(Fb, Fb[ok_], m_[ok_]) for m_ in (mF, mB, mI, mO))
    MC[sd] = (_centre(0.5 * (mF + mB)), _centre(0.5 * (mI + mO)))

CUT = float(os.environ.get("V2_LEGS_CUT", "0.43"))          # fraction of stature
zc = z0 + CUT * H
FJ = float(os.environ.get("V2_LEGS_JOIN", "0.085"))         # foot / leg join
zj = z0 + FJ * H
DZ = float(os.environ.get("V2_LEGS_DZ", "0.004"))
NEX = float(os.environ.get("V2_LEGS_SUPER", "2.25"))        # super-ellipse exponent (2 = ellipse)
RELIEF = float(os.environ.get("V2_LEGS_RELIEF", "1.8"))


def _bump(th, f, thc, thw, f0, f1, amp, fe=0.012):
    """relief (m) at angle th (deg; 0 front, +90 outward), fraction f: cosine lobe in angle, smooth band in height"""
    dth = (th - thc + 180.0) % 360.0 - 180.0
    a_ = np.where(np.abs(dth) < thw, 0.5 + 0.5 * np.cos(np.pi * dth / thw), 0.0)
    return amp * 1e-3 * a_ * ss((f - f0) / fe) * ss((f1 - f) / fe)


def relief(th, f):
    """anatomical relief, mm-scaled lobes; positive outward.  Angles as R115/R116 (0 = front, +90 = outward)."""
    r = np.zeros_like(th)
    # thigh
    r += _bump(th, f, 55, 40, 0.30, 0.44, 4.0)        # vastus lateralis sweep
    r += _bump(th, f, 28, 12, 0.31, 0.44, -2.5)       # groove: rectus femoris / vastus lateralis
    r += _bump(th, f, 0, 26, 0.32, 0.44, 2.5)         # rectus femoris
    r += _bump(th, f, -55, 30, 0.285, 0.335, 6.0, 0.015)   # vastus medialis teardrop (low, inner)
    r += _bump(th, f, -40, 12, 0.34, 0.44, -2.0)      # sartorius line
    r += _bump(th, f, -95, 35, 0.36, 0.44, 2.0)       # adductors
    r += _bump(th, f, 95, 18, 0.31, 0.42, -2.0)       # IT band flat
    r += _bump(th, f, 150, 25, 0.31, 0.43, 3.0)       # biceps femoris
    r += _bump(th, f, -150, 25, 0.31, 0.43, 3.0)      # semitendinosus / semimembranosus
    r += _bump(th, f, 180, 10, 0.32, 0.42, -1.5)      # hamstring split
    # knee
    r += _bump(th, f, 0, 24, 0.274, 0.298, 4.0, 0.010)     # patella
    r += _bump(th, f, 35, 14, 0.255, 0.280, -3.0, 0.008)   # infrapatellar hollows either side of the tendon
    r += _bump(th, f, -35, 14, 0.255, 0.280, -3.0, 0.008)
    r += _bump(th, f, 180, 35, 0.262, 0.295, -2.0, 0.010)  # popliteal hollow
    # lower leg
    r += _bump(th, f, -140, 35, 0.175, 0.255, 7.0, 0.020)  # gastrocnemius, medial head (fuller, lower)
    r += _bump(th, f, 140, 32, 0.190, 0.255, 5.0, 0.018)   # gastrocnemius, lateral head
    r += _bump(th, f, 180, 8, 0.19, 0.25, -1.5)            # between the heads
    r += _bump(th, f, -100, 25, 0.12, 0.20, 2.0, 0.02)     # soleus, inner
    r += _bump(th, f, 105, 25, 0.12, 0.20, 2.0, 0.02)      # soleus, outer
    r += _bump(th, f, 28, 20, 0.14, 0.25, 3.0, 0.02)       # tibialis anterior
    r += _bump(th, f, -15, 10, 0.12, 0.25, -1.5, 0.02)     # tibial crest (flat inner face beside it)
    r += _bump(th, f, -45, 25, 0.12, 0.25, -1.5, 0.02)
    return r * RELIEF


TH = np.linspace(-180.0, 180.0, 721)[:-1]


def design_section(f):
    """designed cross-section (u outward, w forward), in metres about the leg centre, at fraction f"""
    F_, B_, I_, O_ = (float(np.interp(f, Fb, a_)) * H for a_ in (TF, TB, TI, TO))
    t = np.radians(TH); su, cw = np.sin(t), np.cos(t)
    a_ = np.where(su >= 0, O_, I_); b_ = np.where(cw >= 0, F_, B_)
    n = NEX + 0.10 * ss((f - 0.255) / 0.02) * ss((0.31 - f) / 0.02)       # a little squarer at the knee
    r = 1.0 / ((np.abs(su) / a_) ** n + (np.abs(cw) / b_) ** n) ** (1.0 / n)
    r = r + relief(TH, f)
    u, w = r * su, r * cw
    u = np.where(u >= 0, u * O_ / u.max(), u * I_ / -u.min()); w = np.where(w >= 0, w * F_ / w.max(), w * B_ / -w.min())
    return u, w


def polar(u, w):
    """periodic polar table r(theta) of a star-shaped closed curve (theta deg, 0 = +w, +90 = +u)"""
    th = np.degrees(np.arctan2(u, w)); r = np.hypot(u, w); o = np.argsort(th)
    th, r = th[o], r[o]
    th = np.concatenate([th - 360, th, th + 360]); r = np.concatenate([r, r, r])
    return lambda q: np.interp(((np.asarray(q) + 180.0) % 360.0) - 180.0, th, r)


# ------------------------------------------------------------------ foot: signed distance model
FL = float(os.environ.get("V2_FOOT_LEN", "0.156")) * H     # reference 0.159 H, ANSUR II 0.1535 H
SC = FL / 0.290                                              # dimensions below are for a 290 mm foot


def _sd_ell(P, c, r):
    q = (P - c) / r; k0 = np.linalg.norm(q, axis=-1); k1 = np.linalg.norm(q / r, axis=-1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def _sd_cone(P, a, b, ra, rb):
    """round cone (capsule with linearly varying radius; approximate distance)"""
    ab = b - a; t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[..., None] * ab), axis=-1) - (ra + (rb - ra) * t)


def _smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)


def foot_sdf(P):
    """P: (..., 3) in the foot frame (u outward, v forward, z up from the ground), metres; 290 mm foot"""
    S = lambda *x: np.array(x) * 1.0
    d = _sd_ell(P, S(0.003, -0.026, 0.033), S(0.034, 0.034, 0.033))                    # heel (calcaneus)
    d = _smin(d, _sd_ell(P, S(-0.002, 0.012, 0.074), S(0.030, 0.036, 0.040)), 0.026)  # talus / ankle
    d = _smin(d, _sd_cone(P, S(0.020, -0.015, 0.022), S(0.036, 0.118, 0.012), 0.017, 0.012), 0.018)   # lateral column
    d = _smin(d, _sd_cone(P, S(-0.006, 0.005, 0.064), S(-0.024, 0.140, 0.030), 0.026, 0.018), 0.028)  # medial arch
    d = _smin(d, _sd_ell(P, S(0.002, 0.062, 0.052), S(0.039, 0.085, 0.034)), 0.026)   # instep / dorsum
    d = _smin(d, _sd_ell(P, S(0.006, 0.168, 0.015), S(0.044, 0.020, 0.012)), 0.012)   # toe web / forefoot pad
    d = _smin(d, _sd_cone(P, S(-0.029, 0.155, 0.021), S(0.040, 0.123, 0.015), 0.021, 0.014), 0.016)   # metatarsal heads
    d = _smin(d, _sd_cone(P, S(0.000, -0.045, 0.050), S(0.000, -0.034, 0.160), 0.013, 0.011), 0.014)  # Achilles tendon
    d = _smin(d, _sd_ell(P, S(0.000, -0.004, 0.230), S(0.031, 0.040, 0.140)), 0.030)  # ankle column (cut away above)
    d = _smin(d, _sd_ell(P, S(-0.027, 0.002, 0.080), S(0.008, 0.012, 0.016)), 0.016)  # medial malleolus
    d = _smin(d, _sd_ell(P, S(0.029, -0.010, 0.066), S(0.008, 0.012, 0.018)), 0.016)  # lateral malleolus (lower, behind)
    toes = (((-0.027, 0.160, 0.022), (-0.028, 0.196, 0.021), (-0.029, 0.220, 0.015), 0.017, 0.0145, 0.0135),
            ((-0.006, 0.165, 0.017), (-0.005, 0.198, 0.017), (-0.004, 0.221, 0.009), 0.0110, 0.0090, 0.0078),
            ((0.010, 0.158, 0.016), (0.011, 0.188, 0.016), (0.012, 0.208, 0.009), 0.0105, 0.0085, 0.0074),
            ((0.024, 0.149, 0.015), (0.025, 0.175, 0.015), (0.026, 0.194, 0.009), 0.0100, 0.0080, 0.0070),
            ((0.037, 0.136, 0.014), (0.039, 0.158, 0.013), (0.040, 0.175, 0.009), 0.0095, 0.0075, 0.0067))
    dt = None
    for a_, m_, b_, ra, rm, rb in toes:
        a_, m_, b_ = S(*a_), S(*m_), S(*b_)
        t_ = np.minimum(_sd_cone(P, a_, m_, ra, rm), _sd_cone(P, m_, b_, rm, rb))
        dt = t_ if dt is None else _smin(dt, t_, 0.0035)
    d = _smin(d, dt, 0.010)
    return np.maximum(d, -(P[..., 2] - 0.0))           # flat sole on the ground


def build_foot(sg, ank):
    """marching-cubes foot for side sg (+1 = +x), ankle centre ank (x, y); returns verts (world), tris"""
    vox = float(os.environ.get("V2_FOOT_VOX", "0.0022"))
    lo = np.array([-0.07, -0.09, -0.004]); hi = np.array([0.08, 0.25, (zj - z0) / SC + 0.03])
    n = np.ceil((hi - lo) / (vox / SC)).astype(int) + 1
    g = [np.linspace(lo[i], hi[i], n[i]) for i in range(3)]
    P = np.stack(np.meshgrid(*g, indexing="ij"), -1)
    D = foot_sdf(P)
    v, f, _, _ = marching_cubes(D, 0.0, spacing=tuple((hi - lo) / (n - 1)))
    v = v + lo
    # foot frame -> world: u outward (sg * x), v forward (-y)
    X = np.stack([ank[0] + sg * v[:, 0] * SC, ank[1] - v[:, 1] * SC, z0 + v[:, 2] * SC], 1)
    if sg < 0:
        f = f[:, ::-1]
    # marching cubes orients by the gradient; make the triangles face outward (positive signed volume)
    vol = np.einsum("ij,ij->i", X[f[:, 0]], np.cross(X[f[:, 1]], X[f[:, 2]])).sum()
    if vol < 0:
        f = f[:, ::-1]
    return X, f


# ------------------------------------------------------------------ cut the old legs
bm = bmesh.new(); bm.from_mesh(me)
bm.verts.ensure_lookup_table()
oid = bm.verts.layers.int.new("old_id")
for v in bm.verts:
    v[oid] = v.index
dl = bm.verts.layers.deform.verify()
shl = [bm.verts.layers.shape[k] for k in KEYS] if KEYS else []
DEL = np.zeros(nv0, bool); LOOPS = {}
for sd, sg in SIDES:
    legv = (LEGW[sd] > 0.5) & (V0[:, 0] * sg > 0) & (ARM < 0.3)
    faces = [f for f in bm.faces if all(legv[v[oid]] if v[oid] >= 0 else True for v in f.verts)
             and min(v.co.z for v in f.verts) < zc + 0.03]
    geom = list({e for f in faces for e in f.edges}) + faces + list({v for f in faces for v in f.verts})
    pre = set(bm.verts)
    res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, zc), plane_no=(0, 0, 1), clear_inner=True)
    cutv = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMVert)]
    for v in cutv:
        if v not in pre:
            v[oid] = -1
    # ordered boundary loop
    bset = {v for v in cutv if v.is_boundary}
    start = min(bset, key=lambda v: (v.co.x * sg, v.co.y))   # innermost: a fixed seam on the inner leg
    loop = [start]; prev = None
    while True:
        nxt = [e.other_vert(loop[-1]) for e in loop[-1].link_edges if e.is_boundary and e.other_vert(loop[-1]) in bset]
        nxt = [v for v in nxt if v is not prev and (len(loop) < 2 or v is not loop[-2])]
        if not nxt or nxt[0] is loop[0]:
            break
        prev = loop[-1]; loop.append(nxt[0])
    assert len(loop) == len(bset), f"cut loop {sd}: {len(loop)} of {len(bset)} boundary verts ordered"
    LOOPS[sd] = loop
    REP[f"cut_loop_{sd}"] = len(loop)
bm.verts.index_update()

# old leg / foot vertices (the ones removed) - weights and shape-key deltas are carried from them
for sd, sg in SIDES:
    DEL |= (LEGW[sd] > 0.5) & (V0[:, 0] * sg > 0) & (ARM < 0.3) & (V0[:, 2] < zc + 0.004)

# ------------------------------------------------------------------ new legs and feet
def stitch(A, B, flip):
    """triangle strip between closed loops A and B running the same way round (zipper by arc length).  Unflipped it
    uses A's edges forward and B's backward; flip when A's edges are already used forward by the faces beyond it."""
    pa = np.array([tuple(v.co) for v in A]); pb = np.array([tuple(v.co) for v in B])
    s0 = int(np.argmin(np.linalg.norm(pb - pa[0], axis=1))); B = B[s0:] + B[:s0]; pb = np.roll(pb, -s0, 0)
    sa = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(np.vstack([pa, pa[:1]]), axis=0), axis=1))]); sa /= sa[-1]
    sb = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(np.vstack([pb, pb[:1]]), axis=0), axis=1))]); sb /= sb[-1]
    i = j = 0; na, nb = len(A), len(B)
    while i < na or j < nb:
        if j >= nb or (i < na and sa[i + 1] <= sb[j + 1]):
            tri = (A[i], A[(i + 1) % na], B[j % nb]); i += 1
        else:
            tri = (A[i % na], B[(j + 1) % nb], B[j]); j += 1
        try:
            bm.faces.new(tri[::-1] if flip else tri).smooth = True
        except ValueError:
            pass


newv = []           # (bm vert, world position)
REP["rings"] = {}
for sd, sg in SIDES:
    loop = LOOPS[sd]
    L = np.array([tuple(v.co) for v in loop]); N = len(L)
    c0 = L[:, :2].mean(0)
    # loop direction: make the angle (0 front, +90 outward) increase along the loop
    th0 = np.degrees(np.arctan2(sg * (L[:, 0] - c0[0]), -(L[:, 1] - c0[1])))
    dth = (np.diff(np.concatenate([th0, th0[:1]])) + 180) % 360 - 180
    if dth.sum() < 0:
        loop = loop[:1] + loop[1:][::-1]; L = np.array([tuple(v.co) for v in loop])
        th0 = np.degrees(np.arctan2(sg * (L[:, 0] - c0[0]), -(L[:, 1] - c0[1])))
    # the cut crosses the fine triangles every ~1 mm: the new rings get their own count, ~V2_LEGS_DU apart, and are
    # stitched to the cut loop with a strip of triangles
    per = float(np.linalg.norm(np.diff(np.vstack([L, L[:1]]), axis=0), axis=1).sum())
    M = int(round(per / float(os.environ.get("V2_LEGS_DU", "0.004"))))
    unif = th0[0] + 360.0 * np.arange(M) / M
    r0 = polar(sg * (L[:, 0] - c0[0]), -(L[:, 1] - c0[1]))
    # ankle (shin tail) - the foot is placed under it
    ank = BONE[f"shin_{sd}"][1]
    FX, FT = build_foot(sg, ank[:2])
    # foot: cut at the join, keep below
    fb = bmesh.new()
    fvs = [fb.verts.new(p) for p in FX]
    for t in FT:
        try:
            fb.faces.new((fvs[t[0]], fvs[t[1]], fvs[t[2]]))
        except ValueError:
            pass
    bmesh.ops.remove_doubles(fb, verts=fb.verts, dist=1e-6)
    for _ in range(int(os.environ.get("V2_FOOT_SMOOTH", "6"))):       # Taubin: shrink-free smoothing of the voxel steps
        bmesh.ops.smooth_vert(fb, verts=fb.verts, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
        cos = {v: v.co.copy() for v in fb.verts}
        for v in fb.verts:
            nb = [e.other_vert(v).co for e in v.link_edges]
            if nb:
                m_ = sum(nb, Vector()) / len(nb); v.co = cos[v] - 0.53 * (m_ - cos[v])
    bmesh.ops.beautify_fill(fb, faces=fb.faces, edges=fb.edges, method="ANGLE")
    r_ = bmesh.ops.bisect_plane(fb, geom=list(fb.verts) + list(fb.edges) + list(fb.faces), plane_co=(0, 0, zj), plane_no=(0, 0, 1), clear_outer=True)
    fb.verts.ensure_lookup_table()
    fbnd = [v for v in fb.verts if v.is_boundary]
    fl = [fbnd[0]]
    while True:
        nxt = [e.other_vert(fl[-1]) for e in fl[-1].link_edges if e.is_boundary]
        nxt = [v for v in nxt if len(fl) < 2 or v is not fl[-2]]
        if not nxt or nxt[0] is fl[0]:
            break
        fl.append(nxt[0])
    FLP = np.array([tuple(v.co) for v in fl]); cf = FLP[:, :2].mean(0)
    thf = np.degrees(np.arctan2(sg * (FLP[:, 0] - cf[0]), -(FLP[:, 1] - cf[1])))
    if ((np.diff(np.concatenate([thf, thf[:1]])) + 180) % 360 - 180).sum() < 0:
        fl = fl[::-1]; FLP = FLP[::-1]; thf = thf[::-1]
    rf = polar(sg * (FLP[:, 0] - cf[0]), -(FLP[:, 1] - cf[1]))
    REP[f"foot_{sd}"] = {"verts": len(fb.verts), "join_loop": len(fl), "length_mm": round(FL * 1000, 1),
                         "breadth_mm": round(float(np.ptp(FX[FX[:, 2] < z0 + 0.03, 0])) * 1000, 1)}
    # rings
    zs = np.arange(zc - DZ, zj + 0.6 * DZ, -DZ)
    rings = []
    cyM, cxM = MC[sd]
    for z in zs:
        f = (z - z0) / H
        b = ss((zc - z) / float(os.environ.get("V2_LEGS_BLEND", "0.08")))     # old cut shape -> designed shape
        bf = ss((zj + 0.06 - z) / 0.06)                                       # designed -> foot join shape
        cd = np.array([sg * float(np.interp(f, Fb, cxM)) * H, -float(np.interp(f, Fb, cyM)) * H])
        u_, w_ = design_section(min(max(f, Fb[0]), Fb[-1]))
        rd = polar(u_, w_)
        ang = unif
        R = (1 - b) * r0(ang) + b * rd(ang)
        C = (1 - b) * c0 + b * cd
        R = (1 - bf) * R + bf * rf(ang); C = (1 - bf) * C + bf * cf
        a_ = np.radians(ang)
        X = np.stack([C[0] + sg * R * np.sin(a_), C[1] - R * np.cos(a_), np.full(M, z)], 1)
        ring = []
        for p in X:
            v = bm.verts.new(p); v[oid] = -2; ring.append(v); newv.append(v)
        rings.append(ring)
    REP["rings"][sd] = {"count": len(rings), "verts_per_ring": M, "cut_loop_verts": N, "spacing_mm": DZ * 1000}
    # face winding: the old face on each cut-loop edge uses it one way; the new face must use it the other way
    a0, a1 = loop[0], loop[1]
    ef = [f for f in a0.link_faces if a1 in f.verts][0]
    fv = list(ef.verts); ia = fv.index(a0)
    fwd = fv[(ia + 1) % len(fv)] is a1           # old face runs a0 -> a1
    stitch(loop, rings[0], fwd)
    for k in range(len(rings) - 1):
        A, B = rings[k], rings[k + 1]
        for i in range(M):
            j = (i + 1) % M
            q = (A[j], A[i], B[i], B[j]) if fwd else (A[i], A[j], B[j], B[i])
            bm.faces.new(q).smooth = True
    # foot into the body mesh, then stitch the last ring to the foot's join loop (zipper by arc length)
    fmap = {}
    for v in fb.verts:
        nvv = bm.verts.new(v.co); nvv[oid] = -3; fmap[v] = nvv; newv.append(nvv)
    for f in fb.faces:
        bm.faces.new([fmap[v] for v in f.verts]).smooth = True
    A = rings[-1]; Bl = [fmap[v] for v in fl]
    # align the foot loop's start with the ring's start
    pa = np.array([tuple(v.co) for v in A]); pb = np.array([tuple(v.co) for v in Bl])
    s0 = int(np.argmin(np.linalg.norm(pb - pa[0], axis=1))); Bl = Bl[s0:] + Bl[:s0]; pb = np.roll(pb, -s0, 0)
    stitch(A, Bl, fwd)
    fb.free()

# the cut seam and the join: a light relaxation of the new vertices only (old ones held)
bm.verts.ensure_lookup_table(); bm.verts.index_update()
NEW = set(newv)
for _ in range(int(os.environ.get("V2_LEGS_RELAX", "4"))):
    cos = {v: v.co.copy() for v in NEW}
    for v in NEW:
        nb = [e.other_vert(v).co for e in v.link_edges]
        m_ = sum(nb, Vector()) / len(nb)
        near_join = abs(cos[v].z - zj) < 0.012 or abs(cos[v].z - zc) < 0.02
        v.co = cos[v] + (0.5 if near_join else 0.15) * (m_ - cos[v])
# orientation check: every interior edge used once each way
bad = 0
for e in bm.edges:
    if len(e.link_faces) == 2:
        f1, f2 = e.link_faces
        if (e.verts[0] in NEW or e.verts[1] in NEW) and e.calc_face_angle(0) is not None:
            l1 = [l for l in f1.loops if l.edge is e][0]; l2 = [l for l in f2.loops if l.edge is e][0]
            bad += int(l1.vert is l2.vert)
REP["winding_conflicts"] = bad
REP["non_manifold_edges_new"] = sum(1 for e in bm.edges if not e.is_manifold and (e.verts[0] in NEW or e.verts[1] in NEW))

# ------------------------------------------------------------------ weights and shape keys from the old legs
src = np.where(DEL)[0]
tree = cKDTree(V0[src])
TGT = list(NEW)                 # (the cut-loop vertices keep the weights the bisect interpolated)
P = np.array([tuple(v.co) for v in TGT])
d_, j_ = tree.query(P, k=4)
w_ = 1.0 / np.maximum(d_, 1e-4) ** 2; w_ /= w_.sum(1, keepdims=True)
idx = src[j_]
WN = np.einsum("nk,nkg->ng", w_, W0[idx])
REP["weight_source_dist_mm"] = {"median": round(float(np.median(d_[:, 0])) * 1000, 1), "max": round(float(d_[:, 0].max()) * 1000, 1)}
# smooth the carried weights over the new surface (nearest-old-vertex patches would show as facets when posed)
pos = {v: i for i, v in enumerate(TGT)}
nbr = [[pos[e.other_vert(v)] for e in v.link_edges if e.other_vert(v) in pos] for v in TGT]
for _ in range(int(os.environ.get("V2_LEGS_WSMOOTH", "10"))):
    WN = 0.5 * WN + 0.5 * np.array([WN[n].mean(0) if n else WN[i] for i, n in enumerate(nbr)])
WN /= np.maximum(WN.sum(1, keepdims=True), 1e-6)
for v, wr in zip(TGT, WN):
    dv = v[dl]; dv.clear()
    for g in np.nonzero(wr > 1e-4)[0]:
        dv[int(g)] = float(wr[g])
for k, sl in zip(KEYS, shl):
    D = np.einsum("nk,nkc->nc", w_, KD0[k][idx])
    for v, dd in zip(TGT, D):
        v[sl] = v.co + Vector(dd)

# ------------------------------------------------------------------ write back
bm.to_mesh(me); bm.free(); me.update()
REP["verts_before_after"] = [nv0, len(me.vertices)]
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "body_v2_legs.blend"), copy=True)
V1 = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", V1); V1 = V1.reshape(-1, 3)
REP["stature_after_m"] = round(float(V1[:, 2].max() - V1[:, 2].min()), 4)
(OUT / "legs_v2_report.json").write_text(json.dumps(REP, indent=1))
print("LEGS_V2", json.dumps(REP), flush=True)

# ------------------------------------------------------------------ standing renders (same set-up as the builder)
if os.environ.get("V2_LEGS_RENDER", "1") == "1":
    import build_original_movement_benchmarks_blender as bench
    import original_v1_review_candidate_drives as drives
    sc = bpy.context.scene
    for ob in sc.objects:
        if ob.type in ("MESH", "CURVE") and ob is not body:
            ob.hide_render = True
    abd, elb = (float(x) for x in os.environ.get("V2_STAND", "16:6").split(":"))
    bench._reset(rig)
    for sd, sg in (("r", -1.0), ("l", 1.0)):
        pb = rig.pose.bones[f"upperarm_{sd}"]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (0.0, 0.0, math.radians(sg * abd))
        fb_ = rig.pose.bones[f"forearm_{sd}"]; fb_.rotation_mode = "XYZ"; fb_.rotation_euler = (math.radians(-elb), 0.0, 0.0)
    bpy.context.view_layer.update(); drives.drive(rig, body); bpy.context.view_layer.update()
    lo, hi = V1.min(0), V1.max(0); mid = Vector(((lo + hi) / 2).tolist())
    cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
    cd.ortho_scale = float(hi[2] - lo[2]) * 1.08
    sc.render.film_transparent = True
    mat = bpy.data.materials.new("REVIEW_ONLY"); mat.diffuse_color = (.72, .55, .45, 1)
    body.data.materials.clear(); body.data.materials.append(mat)
    sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
    sc.display.shading.show_cavity = True; sc.render.resolution_x = 900; sc.render.resolution_y = 1500
    VIEWS = {"front": (0, -1, 0), "back": (0, 1, 0), "side": (1, 0, 0), "front34": (0.7, -0.7, 0)}

    def aim(centre, dv):
        dvec = Vector(dv).normalized(); cam.location = centre + dvec * 4; cam.rotation_mode = "QUATERNION"
        cam.rotation_quaternion = (-dvec).to_track_quat("-Z", "Y")
    for view, dv in VIEWS.items():
        aim(mid, dv); sc.render.filepath = str(OUT / f"V2_full_stand_{view}.png"); bpy.ops.render.render(write_still=True)
    # skin (as R103 / R114)
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = int(os.environ.get("V2_SKIN_SAMPLES", "48"))
    try:
        sc.cycles.use_denoising = True
    except Exception:
        pass
    sm = bpy.data.materials.new("REVIEW_SKIN"); sm.use_nodes = True
    bsdf = sm.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.62, 0.40, 0.30, 1); bsdf.inputs["Roughness"].default_value = float(os.environ.get("V2_SKIN_ROUGH", "0.62"))
    for nm, val in (("Subsurface Weight", 0.2), ("Subsurface Scale", 0.012), ("Specular IOR Level", 0.28)):
        if nm in bsdf.inputs:
            bsdf.inputs[nm].default_value = val
    body.data.materials.clear(); body.data.materials.append(sm)
    if sc.world is None:
        sc.world = bpy.data.worlds.new("W")
    sc.world.use_nodes = True; sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.055, 1)
    sc.render.film_transparent = False
    try:
        sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "None"
    except Exception:
        pass
    lights = []
    for nm, loc, energy, size in (("KEY", (-1.6, -2.6, 2.6), 70, 1.6), ("FILL", (2.2, -2.0, 1.4), 18, 2.5), ("RIM", (1.2, 2.6, 2.4), 45, 1.2)):
        ld = bpy.data.lights.new(nm, "AREA"); ld.energy = energy; ld.size = size
        lo_ = bpy.data.objects.new(nm, ld); sc.collection.objects.link(lo_); lo_.location = loc
        lo_.rotation_mode = "QUATERNION"; lo_.rotation_quaternion = (mid - Vector(loc)).to_track_quat("-Z", "Y"); lights.append(lo_)

    def key_at(loc):
        lights[0].location = loc; lights[0].rotation_quaternion = (mid - lights[0].location).to_track_quat("-Z", "Y")
    _sk = float(os.environ.get("V2_SKIN_SCALE", "2"))
    sc.render.resolution_x = int(900 * _sk); sc.render.resolution_y = int(1500 * _sk)
    for view, dv in {"front": (0, -1, 0), "side": (1, 0, 0), "front34": (0.7, -0.7, 0), "back": (0, 1, 0)}.items():
        key_at({"side": (2.6, -1.6, 2.6), "back": (-1.6, 2.6, 2.6)}.get(view, (-1.6, -2.6, 2.6)))
        aim(mid, dv); sc.render.filepath = str(OUT / f"V2_skin_stand_{view}.png"); bpy.ops.render.render(write_still=True)
    # leg and foot close-ups
    sc.render.resolution_x = 1000; sc.render.resolution_y = 1400
    for name, zf, scale in (("legs", 0.25, 0.56), ("feet", 0.05, 0.20)):
        cd.ortho_scale = scale * H; c_ = Vector((0.0, float(mid.y), z0 + zf * H))
        if name == "feet":
            sc.render.resolution_y = 1000
        for view, dv in {"front": (0, -1, 0), "side": (1, 0, 0), "back": (0, 1, 0), "front34": (0.7, -0.7, 0)}.items():
            key_at({"side": (2.6, -1.6, 2.6), "back": (-1.6, 2.6, 2.6)}.get(view, (-1.6, -2.6, 2.6)))
            aim(c_, dv); sc.render.filepath = str(OUT / f"V2_skin_{name}_{view}.png"); bpy.ops.render.render(write_still=True)
    bench._reset(rig)
    print("LEGS_V2_RENDERED", flush=True)
