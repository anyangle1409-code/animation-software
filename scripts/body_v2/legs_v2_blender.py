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
LEGW_ANY = LEGW['r'] + LEGW['l']
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


# v7: the legs follow the reference's own centre-line curve (smoothed), set on the old legs' overall line (v8).
# v1-v6 put reference-relative sizes about the old body's straight-line centre lines; the two disagree at the knee,
# so the front edge jumped 47 mm forward within 0.255-0.31 of stature (the reference's moves as far, but over the
# whole thigh) - a downward-facing slope that read as a dark band across each knee.
_lo = Fb < 0.085
rFs, rBs, rIn, rOut = (np.where(_lo, np.interp(0.085, Fb, a_), a_) for a_ in (rFs, rBs, rIn, rOut))
cRy, cRx = _smooth(_smooth(0.5 * (rFs + rBs), 9), 9), _smooth(_smooth(0.5 * (rIn + rOut), 9), 9)
TF, TB, TI, TO = (_smooth(_smooth(a_, 9), 9) for a_ in (rFs - cRy, cRy - rBs, cRx - rIn, rOut - cRx))
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

CUT = float(os.environ.get("V2_LEGS_CUT", "0.45"))          # fraction of stature
zc = z0 + CUT * H
FJ = float(os.environ.get("V2_LEGS_JOIN", "0.085"))         # foot / leg join
zj = z0 + FJ * H
DZ = float(os.environ.get("V2_LEGS_DZ", "0.004"))
NEX = float(os.environ.get("V2_LEGS_SUPER", "2.25"))        # super-ellipse exponent (2 = ellipse)
RELIEF = float(os.environ.get("V2_LEGS_RELIEF", "1.0"))


def _blob(th, f, thc, sth, fc, sf, amp, tilt=0.0):
    """muscle belly / hollow (m): a gaussian in angle (deg; 0 front, +90 outward) and height (fraction of stature),
    optionally tilted (fc moves by tilt per 90 deg of angle) so its ends run diagonally like the real muscles'"""
    dth = (th - thc + 180.0) % 360.0 - 180.0
    df = f - fc - tilt * dth / 90.0
    return amp * 1e-3 * np.exp(-0.5 * ((dth / sth) ** 2 + (df / sf) ** 2))


def relief(th, f):
    """anatomical relief, positive outward.  v3: rounded bellies (v2's angle x height-band lobes ended in horizontal
    lines across the knee and calf)."""
    r = np.zeros_like(th)
    # thigh, front and sides
    r += _blob(th, f, 62, 24, 0.350, 0.040, 8.0, -0.02)    # vastus lateralis sweep
    r += _blob(th, f, 5, 20, 0.370, 0.050, 4.0)            # rectus femoris
    r += _blob(th, f, 32, 6, 0.360, 0.050, -4.0)           # rectus / vastus lateralis groove
    r += _blob(th, f, -52, 16, 0.307, 0.018, 12.0, 0.012)  # vastus medialis teardrop, above the inner knee
    ths = -70.0 + (f - 0.31) / 0.12 * 60.0                  # sartorius: upper outer -> lower inner
    r += -3.5e-3 * np.exp(-0.5 * (((th - ths + 180) % 360 - 180) / 6.0) ** 2) * ss((f - 0.30) / 0.03) * ss((0.44 - f) / 0.03)
    r += _blob(th, f, -100, 30, 0.400, 0.040, 3.0)         # adductors
    r += _blob(th, f, 95, 12, 0.340, 0.050, -2.5)          # IT band flat
    # thigh, back
    r += _blob(th, f, 150, 22, 0.350, 0.050, 4.0)          # biceps femoris
    r += _blob(th, f, -150, 22, 0.350, 0.050, 4.0)         # semitendinosus / semimembranosus
    r += _blob(th, f, 180, 7, 0.360, 0.050, -2.5)          # hamstring split
    # knee
    r += _blob(th, f, 0, 16, 0.287, 0.012, 2.5)            # patella
    r += _blob(th, f, 35, 10, 0.268, 0.009, -3.0)          # infrapatellar hollows
    r += _blob(th, f, -35, 10, 0.268, 0.009, -3.0)
    r += _blob(th, f, 180, 30, 0.280, 0.012, -2.5)         # popliteal hollow
    # lower leg
    r += _blob(th, f, -145, 28, 0.205, 0.035, 10.0, 0.01)  # gastrocnemius, medial head (fuller, lower)
    r += _blob(th, f, 140, 26, 0.225, 0.030, 7.0, -0.01)   # gastrocnemius, lateral head
    r += _blob(th, f, 180, 6, 0.225, 0.030, -2.0)          # between the heads
    r += _blob(th, f, -105, 22, 0.150, 0.030, 3.0)         # soleus, inner
    r += _blob(th, f, 105, 22, 0.150, 0.030, 3.0)          # soleus, outer
    r += _blob(th, f, 30, 18, 0.200, 0.040, 4.0)           # tibialis anterior
    r += _blob(th, f, -40, 20, 0.180, 0.050, -2.0)         # flat inner face of the tibia
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
    d = _sd_ell(P, S(0.003, -0.026, 0.035), S(0.031, 0.034, 0.035))                    # heel (calcaneus)
    d = _smin(d, _sd_ell(P, S(-0.002, 0.012, 0.074), S(0.030, 0.036, 0.040)), 0.026)  # talus / ankle
    d = _smin(d, _sd_cone(P, S(0.014, 0.005, 0.020), S(0.034, 0.118, 0.012), 0.014, 0.012), 0.018)   # lateral column
    d = _smin(d, _sd_cone(P, S(-0.006, 0.005, 0.064), S(-0.024, 0.140, 0.030), 0.026, 0.018), 0.028)  # medial arch
    d = _smin(d, _sd_ell(P, S(0.002, 0.070, 0.044), S(0.038, 0.090, 0.030)), 0.026)   # instep / dorsum
    d = _smin(d, _sd_cone(P, S(0.000, 0.000, 0.105), S(0.000, 0.100, 0.042), 0.028, 0.020), 0.030)   # ankle front -> dorsum slope
    d = _smin(d, _sd_ell(P, S(0.006, 0.168, 0.015), S(0.044, 0.020, 0.012)), 0.012)   # toe web / forefoot pad
    d = _smin(d, _sd_cone(P, S(-0.029, 0.155, 0.021), S(0.040, 0.123, 0.015), 0.021, 0.014), 0.016)   # metatarsal heads
    d = _smin(d, _sd_cone(P, S(0.000, -0.045, 0.050), S(0.000, -0.034, 0.160), 0.013, 0.011), 0.014)  # Achilles tendon
    d = _smin(d, _sd_ell(P, S(0.000, -0.004, 0.300), S(0.034, 0.042, 0.400)), 0.030)  # ankle column (cut away above)
    d = _smin(d, _sd_ell(P, S(-0.027, 0.002, 0.080), S(0.008, 0.012, 0.016)), 0.016)  # medial malleolus
    d = _smin(d, _sd_ell(P, S(0.029, -0.010, 0.066), S(0.008, 0.012, 0.018)), 0.016)  # lateral malleolus (lower, behind)
    toes = (((-0.027, 0.160, 0.022), (-0.028, 0.196, 0.022), (-0.029, 0.219, 0.017), 0.019, 0.0165, 0.0150),
            ((-0.006, 0.165, 0.018), (-0.005, 0.198, 0.018), (-0.004, 0.219, 0.011), 0.0125, 0.0105, 0.0092),
            ((0.010, 0.158, 0.017), (0.011, 0.188, 0.017), (0.012, 0.207, 0.010), 0.0120, 0.0100, 0.0088),
            ((0.024, 0.149, 0.016), (0.025, 0.175, 0.016), (0.026, 0.193, 0.010), 0.0115, 0.0095, 0.0084),
            ((0.037, 0.136, 0.015), (0.039, 0.158, 0.014), (0.040, 0.174, 0.010), 0.0110, 0.0090, 0.0080))
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


# hands in the standing pose (for the hip fill's clearance) - the mesh is still the old one here
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
STAND = tuple(float(x) for x in os.environ.get("V2_STAND", "16:6").split(":"))


def stand_pose():
    bench._reset(rig)
    for sd_, sg_ in (("r", -1.0), ("l", 1.0)):
        pb = rig.pose.bones[f"upperarm_{sd_}"]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (0.0, 0.0, math.radians(sg_ * STAND[0]))
        fb_ = rig.pose.bones[f"forearm_{sd_}"]; fb_.rotation_mode = "XYZ"; fb_.rotation_euler = (math.radians(-STAND[1]), 0.0, 0.0)
    bpy.context.view_layer.update(); drives.drive(rig, body); bpy.context.view_layer.update()


stand_pose()
_pp, _ = bench._evaluated(body); PP0 = np.array([tuple(v) for v in _pp]); bench._reset(rig); bpy.context.view_layer.update()
HANDS = cKDTree(PP0[(ARM > 0.5) & (V0[:, 2] < z0 + 0.62 * H)])

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
    # v3: the old surface's slope just above the cut, carried on into the new rings (v2's rings started straight
    # down from the cut while the thigh above was still flaring - a crease that read as a tone line across the leg)
    up = (LEGW[sd] > 0.5) & (V0[:, 0] * sg > 0) & (ARM < 0.3) & (V0[:, 2] > zc + 0.008) & (V0[:, 2] < zc + 0.020)
    Pu = V0[up]; cu = Pu[:, :2].mean(0); zu = float(Pu[:, 2].mean())
    thp = np.degrees(np.arctan2(sg * (Pu[:, 0] - cu[0]), -(Pu[:, 1] - cu[1]))); rp = np.hypot(Pu[:, 0] - cu[0], Pu[:, 1] - cu[1])
    bins = np.linspace(-180, 180, 73); bc = 0.5 * (bins[1:] + bins[:-1])
    rb = np.array([np.median(rp[(thp >= bins[k]) & (thp < bins[k + 1])]) if ((thp >= bins[k]) & (thp < bins[k + 1])).any() else np.nan for k in range(72)])
    okb = ~np.isnan(rb); ru = polar(rb[okb] * np.sin(np.radians(bc[okb])), rb[okb] * np.cos(np.radians(bc[okb])))
    dRdz = lambda q: (r0(q) - ru(q)) / (zc - zu); dCdz = (c0 - cu) / (zc - zu)
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
    # v8: the old legs' overall line (straight fit, so the feet stay under the ankles and the top meets the cut) plus
    # the reference's own local curve about its straight fit (v7 took the reference centre whole: its feet stand
    # wider apart, so the legs leaned out - a ledge at the cut and a bent ankle)
    _m = (Fb >= 0.10) & (Fb <= 0.42)
    lin = lambda c_: np.polyval(np.polyfit(Fb[_m], c_[_m], 1), Fb)
    cyM, cxM = lin(cyM) + (cRy - lin(cRy)), lin(cxM) + (cRx - lin(cRx))
    REP.setdefault("centre_local_curve_mm", {})[sd] = [round(float(np.abs(c_ - lin(c_))[_m].max()) * H * 1000, 1) for c_ in (cRy, cRx)]
    for z in zs:
        f = (z - z0) / H
        b = ss((zc - z) / float(os.environ.get("V2_LEGS_BLEND", "0.08")))     # old cut shape -> designed shape
        bf = ss((zj + 0.06 - z) / 0.06)                                       # designed -> foot join shape
        cd = np.array([sg * float(np.interp(f, Fb, cxM)) * H, -float(np.interp(f, Fb, cyM)) * H])
        u_, w_ = design_section(min(max(f, Fb[0]), Fb[-1]))
        rd = polar(u_, w_)
        ang = unif
        R = (1 - b) * (r0(ang) + dRdz(ang) * (z - zc) * (1 - b)) + b * rd(ang)
        C = (1 - b) * (c0 + dCdz * (z - zc) * (1 - b)) + b * cd
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
# v9: a light Taubin band on the old surface just above the cut (its R110 sculpt ripples and the last of the tone
# change at the seam), fading out over V2_LEGS_ABOVE metres
ABOVE = float(os.environ.get("V2_LEGS_ABOVE", "0.09"))
if ABOVE > 0:
    band = {}
    for v in bm.verts:
        if v[oid] >= 0 and zc - 0.002 < v.co.z < zc + ABOVE and LEGW_ANY[v[oid]] > 0.5 and ARM[v[oid]] < 0.3:
            band[v] = float(ss((zc + ABOVE - v.co.z) / (0.6 * ABOVE))) * (0.0 if abs(v.co.z - zc) < 1e-4 else 1.0)
    for it in range(2 * int(os.environ.get("V2_LEGS_ABOVE_STEPS", "15"))):
        lam = 0.5 if it % 2 == 0 else -0.53
        cos = {v: v.co.copy() for v in band}
        for v, w in band.items():
            nb = [e.other_vert(v).co for e in v.link_edges]
            v.co = cos[v] + lam * w * (sum(nb, Vector()) / len(nb) - cos[v])
    for v in band:                       # every shape key moves with the basis (the correctives keep their deltas)
        d0 = v.co - v[shl[0]] if shl else None
        for sl in shl[1:]:
            v[sl] = v[sl] + d0
        if shl:
            v[shl[0]] = v.co.copy()
    REP["above_cut_smoothed_verts"] = len(band)
# v10: outer hip fill.  The old outline dips up to 13 mm inside the reference's at 0.46-0.49 (between the thigh and
# the hip), which reads as a saddlebag; the reference narrows smoothly from thigh to waist.  The outer side is moved
# sideways to the reference outline (smoothed field), kept 15 mm clear of the hands in the standing pose.
HIPFILL = float(os.environ.get("V2_LEGS_HIPFILL", "1.0"))
if HIPFILL > 0:
    bm.normal_update()
    _fo = np.array([np.nan if a_ is None else a_ for a_ in _lf["leg_out"]]); _ft = np.array([np.nan if a_ is None else a_ for a_ in _lf["torso_half"]])
    _ref = np.where(np.isnan(_fo), _ft, _fo); _okr = ~np.isnan(_ref)
    Fh = np.arange(0.40, 0.58, 0.005); refo = np.interp(Fh, Ff[_okr], _ref[_okr]) * H
    zone = [v for v in bm.verts if z0 + 0.41 * H < v.co.z < z0 + 0.57 * H and (v[oid] < 0 or ARM[v[oid]] < 0.3)]
    REP["hip_fill_mm"] = {}
    for sd, sg in SIDES:
        zs_ = [v for v in zone if v.co.x * sg > 0.02]
        P_ = np.array([tuple(v.co) for v in zs_]); fv_ = (P_[:, 2] - z0) / H
        mo = np.array([np.abs(P_[np.abs(fv_ - f_) < 0.003, 0]).max() if (np.abs(fv_ - f_) < 0.003).any() else np.nan for f_ in Fh])
        mo = np.interp(Fh, Fh[~np.isnan(mo)], mo[~np.isnan(mo)])
        dfc = np.clip(refo - mo, 0, 0.015)
        dfc = _smooth(_smooth(dfc, 5), 5) * ss((Fh - 0.425) / 0.02) * ss((0.545 - Fh) / 0.02) * HIPFILL
        REP["hip_fill_mm"][sd] = {str(round(float(f_), 3)): round(float(d_) * 1000, 1) for f_, d_ in zip(Fh[::4], dfc[::4])}
        w_ = np.array([float(ss((v.normal.x * sg - 0.15) / 0.6)) for v in zs_])
        dx = np.interp(fv_, Fh, dfc) * w_
        idx_ = {v: i for i, v in enumerate(zs_)}
        nb_ = [[idx_[e.other_vert(v)] for e in v.link_edges if e.other_vert(v) in idx_] for v in zs_]
        for _ in range(12):
            dx = 0.5 * dx + 0.5 * np.array([dx[n].mean() if n else dx[i] for i, n in enumerate(nb_)])
        dh, _j = HANDS.query(P_ + np.c_[sg * dx, np.zeros((len(dx), 2))])
        dx = np.minimum(dx, np.maximum(0.0, dx - (0.015 - dh)))
        for v, d_ in zip(zs_, dx):
            if d_ > 1e-5:
                v.co.x += sg * d_
                for sl in shl:
                    v[sl] = v[sl] + Vector((sg * d_, 0, 0))
# v11 (owner: "Really look at the definition of each area"): torso relief.  The torso's front and side outlines
# already match the reference within ~5 mm (0.48-0.74 of stature); what it lacks is surface definition.  Gaussian
# reliefs along the vertex normal, laid out on the reference figure's front panel (x and height as fractions of
# stature, midline 0; rows of the rectus at 0.699 / 0.672 / 0.646 / 0.624, navel 0.615), and the back.
TORSO = float(os.environ.get("V2_TORSO_RELIEF", "1.0"))


def _g(x, f, xc, sx, fc, sf, amp):
    return amp * 1e-3 * np.exp(-0.5 * (((x - xc) / sx) ** 2 + ((f - fc) / sf) ** 2))


def _win(f, f0, f1, e=0.01):
    return ss((f - f0) / e) * ss((f1 - f) / e)


def torso_front(ax, f):
    """ax = |x| / H; relief (m), positive outward, for front-facing skin"""
    r = np.zeros_like(ax)
    r += -3.0e-3 * np.exp(-0.5 * (ax / 0.0032) ** 2) * _win(f, 0.625, 0.716)            # linea alba
    r += -1.2e-3 * np.exp(-0.5 * (ax / 0.0035) ** 2) * _win(f, 0.55, 0.625)
    for fi, dep in ((0.699, 2.5), (0.672, 2.8), (0.646, 2.5), (0.624, 1.2)):        # tendinous intersections
        fl = fi + 0.10 * ax ** 2 / 0.065                                              # rising a little to the sides
        r += -dep * 1e-3 * np.exp(-0.5 * ((f - fl) / 0.0050) ** 2) * ss((0.068 - ax) / 0.012)
    for fc in (0.7075, 0.6855, 0.659, 0.635):                                        # the blocks between them
        r += _g(ax, f, 0.033, 0.016, fc + 0.03 * 0.034 ** 2 / 0.065, 0.0085, 4.0 if fc > 0.64 else 3.0)
    r += _g(ax, f, 0.0, 0.0038, 0.613, 0.0035, -6.0)                                  # navel
    xs = np.interp(f, [0.52, 0.58, 0.63, 0.70, 0.72], [0.040, 0.057, 0.066, 0.070, 0.070])   # linea semilunaris
    r += -3.0e-3 * np.exp(-0.5 * ((ax - xs) / 0.0040) ** 2) * _win(f, 0.53, 0.712, 0.015)
    r += _g(ax, f, 0.096, 0.014, 0.597, 0.022, 5.0)                                  # external oblique (flank)
    for xc, fc in ((0.100, 0.700), (0.096, 0.684), (0.091, 0.668)):                  # serratus anterior digits
        r += _g(ax, f, xc, 0.0065, fc, 0.0048, 2.5)
    return r


def torso_back(ax, f):
    r = np.zeros_like(ax)
    r += -6.0e-3 * np.exp(-0.5 * (ax / 0.0045) ** 2) * _win(f, 0.55, 0.79, 0.02)       # spine groove
    r += _g(ax, f, 0.026, 0.011, 0.600, 0.045, 10.0)                                 # erector spinae
    r += _g(ax, f, 0.100, 0.022, 0.695, 0.030, 8.0)                                  # latissimus
    r += _g(ax, f, 0.070, 0.018, 0.757, 0.013, 6.0)                                  # infraspinatus over the scapula
    r += _g(ax, f, 0.104, 0.011, 0.737, 0.010, 5.0)                                  # teres major
    r += _g(ax, f, 0.035, 0.020, 0.745, 0.028, 4.0)                                  # lower trapezius
    r += _g(ax, f, 0.050, 0.010, 0.735, 0.020, -3.0)                                 # medial scapular border hollow
    r += _g(ax, f, 0.060, 0.034, 0.515, 0.026, 14.0)                                 # gluteus maximus
    r += _g(ax, f, 0.105, 0.018, 0.548, 0.016, 4.0)                                  # gluteus medius
    r += -3.0e-3 * np.exp(-0.5 * ((f - 0.474 - 0.15 * ax) / 0.004) ** 2) * ss((ax - 0.01) / 0.01) * ss((0.10 - ax) / 0.02)   # gluteal fold
    return r


if TORSO > 0:
    bm.normal_update()
    tv = [v for v in bm.verts if (v[oid] < 0 or ARM[v[oid]] < 0.15) and z0 + 0.42 * H < v.co.z < z0 + 0.80 * H]
    Pt = np.array([tuple(v.co) for v in tv]); Nt = np.array([tuple(v.normal) for v in tv])
    idx_ = {v: i for i, v in enumerate(tv)}
    nb_ = [[idx_[e.other_vert(v)] for e in v.link_edges if e.other_vert(v) in idx_] for v in tv]
    for _ in range(6):                                   # smoothed normals: the skin's small ripples must not steer it
        Nt = 0.5 * Nt + 0.5 * np.array([Nt[n].mean(0) if n else Nt[i] for i, n in enumerate(nb_)])
    Nt /= np.linalg.norm(Nt, axis=1, keepdims=True)
    axt, ft = np.abs(Pt[:, 0]) / H, (Pt[:, 2] - z0) / H
    wf = ss((-Nt[:, 1] + 0.05) / 0.40); wb = ss((Nt[:, 1] + 0.05) / 0.40)
    armfade = np.array([1.0 if v[oid] < 0 else float(ss((0.15 - ARM[v[oid]]) / 0.15)) for v in tv])
    armfade *= ss((ft - 0.425) / 0.02) * ss((0.795 - ft) / 0.02)
    # v12: erase the builder's own abs first (stacked with these they read as a ladder of six thin grooves) - Taubin
    # on the front of the abdomen only
    abz = (wf > 0.5) & (axt < 0.085) & (ft > 0.585) & (ft < 0.725)
    wab = (ss((0.085 - axt) / 0.02) * ss((ft - 0.585) / 0.015) * ss((0.725 - ft) / 0.015) * wf)
    Q = Pt.copy()
    for it in range(2 * int(os.environ.get("V2_ABS_ERASE", "60"))):
        lam = 0.5 if it % 2 == 0 else -0.53
        M_ = np.array([Q[n].mean(0) if n else Q[i] for i, n in enumerate(nb_)])
        Q = Q + lam * wab[:, None] * (M_ - Q)
    for v, q_, p_ in zip(tv, Q, Pt):
        dv = Vector((q_ - p_).tolist())
        if dv.length > 1e-7:
            v.co += dv
            for sl in shl:
                v[sl] = v[sl] + dv
    dn = (wf * torso_front(axt, ft) + wb * torso_back(axt, ft)) * armfade * TORSO
    for _ in range(2):
        dn = 0.5 * dn + 0.5 * np.array([dn[n].mean() if n else dn[i] for i, n in enumerate(nb_)])
    for v, d_, n_ in zip(tv, dn, Nt):
        dv = Vector((n_ * d_).tolist()); v.co += dv
        for sl in shl:
            v[sl] = v[sl] + dv
    REP["torso_relief"] = {"verts": len(tv), "max_mm": round(float(dn.max()) * 1000, 1), "min_mm": round(float(dn.min()) * 1000, 1)}
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
