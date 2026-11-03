"""BODY V3 - a NEW first-party body, built from anatomical muscle forms on the canonical skeleton.

Owner, 3 Nov 2026: option B - "build a new first-party body from scratch in code".  Every form is written here
(no MPFB / MakeHuman vertex, topology, rig, weight or texture is read).  MPFB was used only as a proportion reference
(the owner-approved Option 5 numbers; see the measurement report).

Method
  * The canonical skeleton's rest frames (export_skeleton_blender.py) are posed to the review stance (arms out in the
    frontal plane, elbows slightly bent).
  * Each major muscle / bony landmark is a signed-distance primitive (ellipsoid, round cone, capsule) placed in its
    bone's frame: (lateral, front, fraction along the bone).  Primitives are combined with smooth unions whose blend
    radius k sets how soft the groove between two forms is (small k = crisp border, e.g. the lower pectoral edge).
  * The field is sampled on a grid (V3_VOXEL_MM) and meshed with marching cubes into one closed, seam-free skin.
  * REVIEW ONLY: a static standing sculpt.  Retopology, binding and movement come after the owner approves the shape.

usage: python3.13 build_body_v3_blender.py -- <skeleton.json> <params.json> <out dir>
"""
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np

a = sys.argv[sys.argv.index("--") + 1:]
SK = json.loads(Path(a[0]).read_text())["bones"]
PR = json.loads(Path(a[1]).read_text())
OUT = Path(a[2]); OUT.mkdir(parents=True, exist_ok=True)
VOX = float(os.environ.get("V3_VOXEL_MM", PR.get("voxel_mm", 3.0))) / 1000.0
P = lambda k, d: PR.get(k, d)

# ------------------------------------------------------------------ skeleton + pose
J = {n: (np.array(b["head"]), np.array(b["tail"])) for n, b in SK.items()}


def rot(axis, ang):
    axis = np.asarray(axis, float); axis = axis / np.linalg.norm(axis)
    c, s = math.cos(ang), math.sin(ang); x, y, z = axis
    return np.array([[c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s],
                     [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s],
                     [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)]])


ARM_OUT, ELBOW = math.radians(P("arms_out_deg", 10.0)), math.radians(P("elbow_deg", 12.0))
for sd, sg in (("l", -1.0), ("r", 1.0)):
    chain = [n for n in J if n.endswith("_" + sd) and any(k in n for k in ("upperarm", "forearm", "hand", "thumb", "index",
                                                                          "middle", "ring", "pinky", "metacarpal"))]
    gh = J[f"upperarm_{sd}"][0].copy()
    R1 = rot([0, 1.0, 0], -sg * ARM_OUT)                   # abduction in the frontal plane (y axis, sign per side)
    for n in chain:
        h, t = J[n]; J[n] = (gh + R1 @ (h - gh), gh + R1 @ (t - gh))
    el = J[f"forearm_{sd}"][0].copy(); ua = J[f"upperarm_{sd}"]
    ax_el = np.cross(ua[1] - ua[0], [0, -1.0, 0]); R2 = rot(ax_el, -ELBOW)
    if (R2 @ (J[f"forearm_{sd}"][1] - el))[1] > (J[f"forearm_{sd}"][1] - el)[1]:   # flex forwards (towards -y)
        R2 = rot(ax_el, ELBOW)
    for n in chain:
        if n.startswith("upperarm"):
            continue
        h, t = J[n]; J[n] = (el + R2 @ (h - el), el + R2 @ (t - el))


FC = math.radians(P("finger_curl_deg", 14.0))                 # relaxed finger curl, per joint, towards the palm
for sd in ("l", "r"):
    nrm = np.array([-np.sign(J[f"hand_{sd}"][0][0]), 0.0, 0.0])
    for f in ("index", "middle", "ring", "pinky"):
        segs = [f"{f}_01_{sd}", f"{f}_02_{sd}", f"{f}_03_{sd}"]
        for i_, sg in enumerate(segs):
            piv = J[sg][0].copy(); d_ = J[sg][1] - J[sg][0]; ax_ = np.cross(d_, nrm)
            Rc = rot(ax_, FC * (0.7 if i_ == 0 else 1.0))
            for sg2 in segs[i_:]:
                h, t = J[sg2]; J[sg2] = (piv + Rc @ (h - piv), piv + Rc @ (t - piv))


def frame(bone):
    """(origin, along unit, length, lateral unit, front unit) of a posed bone"""
    h, t = J[bone]; ax = t - h; L = np.linalg.norm(ax); ax = ax / L
    lat = np.array([np.sign(h[0]) if abs(h[0]) > 1e-4 else 1.0, 0, 0]); lat = lat - ax * (lat @ ax); lat /= np.linalg.norm(lat)
    fr = np.cross(ax, lat)
    if fr[1] > 0:
        fr = -fr
    return h, ax, L, lat, fr


def at(bone, u, lat=0.0, front=0.0):
    """point at fraction u along the bone, offset laterally / forwards (metres)"""
    h, ax, L, la, fr = frame(bone); return h + ax * L * u + la * lat + fr * front


def basis(bone):
    h, ax, L, la, fr = frame(bone); return np.c_[la, fr, ax]   # columns: x = lateral, y = front, z = along


# ------------------------------------------------------------------ SDF primitives (numpy, evaluated on point arrays)
def sd_ellipsoid(p, c, R, r):
    q = (p - c) @ R / r                       # R columns = local axes; r = radii
    k0 = np.linalg.norm(q, axis=-1); k1 = np.linalg.norm(q / r, axis=-1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def sd_roundcone(p, a_, b_, r1, r2):
    ba = b_ - a_; l2 = ba @ ba; rr = r1 - r2; a2 = l2 - rr * rr; il2 = 1.0 / l2
    pa = p - a_; y = pa @ ba; z = y - l2
    x2v = pa * l2 - y[..., None] * ba; x2 = np.einsum("...i,...i", x2v, x2v); y2 = y * y * l2; z2 = z * z * l2
    k = np.sign(rr) * rr * rr * x2
    d = np.where(np.sign(z) * a2 * z2 > k, np.sqrt(x2 + z2) * il2 - r2,
                 np.where(np.sign(y) * a2 * y2 < k, np.sqrt(x2 + y2) * il2 - r1,
                          (np.sqrt(x2 * a2 * il2) + y * rr) * il2 - r1))
    return d


def sd_rbox(p, c, R, b, rr):
    q = np.abs((p - c) @ R) - (np.asarray(b) - rr)
    return np.linalg.norm(np.maximum(q, 0), axis=-1) + np.minimum(q.max(-1), 0) - rr


def smin(d1, d2, k):
    if k <= 0:
        return np.minimum(d1, d2)
    h = np.clip(0.5 + 0.5 * (d2 - d1) / k, 0, 1); return d2 * (1 - h) + d1 * h - k * h * (1 - h)


def smax_sub(d1, d2, k):                       # smooth subtraction of d2 from d1
    h = np.clip(0.5 - 0.5 * (d1 + d2) / k, 0, 1); return d1 * (1 - h) + (-d2) * h + k * h * (1 - h)


PRIMS = []                                     # (kind, params, k, op, aabb_lo, aabb_hi, name)


def _add(kind, prm, k, op, lo, hi, name):
    PRIMS.append((kind, prm, k, op, np.asarray(lo) - k - 0.03, np.asarray(hi) + k + 0.03, name))


def ell(name, c, R, r, k=0.015, op="u"):
    c = np.asarray(c, float); r = np.asarray(r, float); R = np.asarray(R, float); e = np.abs(R) @ r
    _add("ell", (c, R, r), k, op, c - e, c + e, name)


def box(name, c, R, b, rr, k=0.01, op="u"):
    c = np.asarray(c, float); b = np.asarray(b, float); R = np.asarray(R, float); e = np.abs(R) @ b
    _add("box", (c, R, b, rr), k, op, c - e, c + e, name)


def cone(name, p1, p2, r1, r2, k=0.015, op="u"):
    p1, p2 = np.asarray(p1, float), np.asarray(p2, float); m = max(r1, r2)
    _add("cone", (p1, p2, r1, r2), k, op, np.minimum(p1, p2) - m, np.maximum(p1, p2) + m, name)


def Rxyz(rx=0.0, ry=0.0, rz=0.0):
    return rot([0, 0, 1], math.radians(rz)) @ rot([0, 1, 0], math.radians(ry)) @ rot([1, 0, 0], math.radians(rx))


I3 = np.eye(3)
MX = lambda s, v: np.array([s * v[0], v[1], v[2]])   # mirror an x coordinate
MR = lambda s, R: np.diag([s, 1, 1]) @ R @ np.diag([s, 1, 1])
SC = P("scale", {})                                     # per-region size multipliers
sc = lambda key: float(SC.get(key, 1.0))

# ------------------------------------------------------------------ the body (male defaults; params can scale regions)
H = P("stature_m", 1.856)
# ---- trunk core (the muscles below sit ON these, protruding 0.5-2.5 cm, as on a lean athlete)
ell("ribcage", [0, 0.025, 1.360], Rxyz(rx=-6), np.array([0.158, 0.112, 0.185]) * [sc("chest_w"), sc("chest_d"), 1], k=0.04)
ell("girdle", [0, 0.035, 1.462], I3, np.array([0.185, 0.085, 0.070]) * [sc("shoulder_w"), 1, 1], k=0.04)
ell("abdomen", [0, 0.008, 1.130], I3, np.array([0.135, 0.098, 0.150]) * [sc("waist_w"), sc("waist_d"), 1], k=0.05)
ell("pelvis", [0, 0.015, 0.960], I3, np.array([0.168, 0.106, 0.110]) * [sc("hip_w"), 1, 1], k=0.05)
ell("lower_belly", [0, -0.035, 1.010], Rxyz(rx=12), [0.100, 0.055, 0.075], k=0.04)
ell("sacrum", [0, 0.082, 0.975], I3, [0.060, 0.028, 0.060], k=0.04)
for s in (-1.0, 1.0):
    # ---- back: latissimus (V taper from the armpit), erectors, scapular mass, trapezius sheets
    lw = sc("lats")
    ell("lat", MX(s, [0.135, 0.068, 1.300]), MR(s, Rxyz(ry=18)), [0.045 * lw, 0.062, 0.135], k=0.035)
    cone("erector", MX(s, [0.034, 0.092, 0.990]), MX(s, [0.032, 0.100, 1.340]), 0.030, 0.022, k=0.025)
    ell("scapular", MX(s, [0.100, 0.100, 1.405]), MR(s, Rxyz(rz=-10)), [0.058, 0.030, 0.060], k=0.04)
    ell("teres", MX(s, [0.165, 0.085, 1.385]), MR(s, Rxyz(ry=-30)), [0.040, 0.030, 0.022], k=0.02)
    ell("trap_upper", MX(s, [0.095, 0.058, 1.560]), MR(s, Rxyz(ry=36)), [0.100 * sc("traps"), 0.048, 0.028], k=0.03)
    ell("trap_mid", MX(s, [0.055, 0.098, 1.445]), MR(s, Rxyz(rz=-25)), [0.070, 0.032, 0.090], k=0.04)
    # ---- chest: pectoralis major (crisp lower border: small k), its tendon to the humerus
    pk = P("pec_k", 0.012); pw = sc("pecs")
    ell("pec", MX(s, [0.090, -0.064, 1.400]), MR(s, Rxyz(ry=-12, rz=24)), [0.100 * pw, 0.019 * pw, 0.064], k=pk)
    ell("pec_upper", MX(s, [0.080, -0.055, 1.455]), MR(s, Rxyz(ry=-6, rz=22)), [0.090, 0.030, 0.045], k=0.04)   # clavicular head blends up to the clavicle
    cone("pec_tendon", MX(s, [0.150, -0.045, 1.425]), at(f"upperarm_{'l' if s < 0 else 'r'}", 0.17, 0.0, 0.010), 0.026, 0.016, k=0.025)
    # ---- side: serratus digitations, external obliques
    ell("oblique", MX(s, [0.118, -0.002, 1.095]), MR(s, Rxyz(ry=8)), [0.030, 0.070, 0.075], k=0.035)
    # ---- abdominals: rectus segments (small k between them -> the grooves)
    ell("rectus_sheath", MX(s, [0.034, -0.068, 1.150]), Rxyz(rx=-4), [0.040, 0.026 * sc("abs"), 0.175], k=0.03)
    # ---- glutes
    gw = sc("glutes")
    ell("glute_max", MX(s, [0.068, 0.060, 0.895]), MR(s, Rxyz(rx=10, rz=-12)), [0.074, 0.054 * gw, 0.088], k=0.05)
    ell("glute_med", MX(s, [0.128, 0.035, 0.985]), MR(s, Rxyz(rz=10)), [0.045, 0.055, 0.060], k=0.035)
    ell("masseter", MX(s, [0.052, -0.010, 1.665]), MR(s, Rxyz(ry=10)), [0.016, 0.026, 0.030], k=0.02)
# ---- neck + head
cone("neck", [0, 0.030, 1.480], [0, 0.030, 1.650], 0.064 * sc("neck"), 0.056, k=0.03)
ell("neck_back", [0, 0.075, 1.560], I3, [0.060, 0.035, 0.070], k=0.04)
for s in (-1.0, 1.0):
    cone("scm", MX(s, [0.055, 0.035, 1.690]), MX(s, [0.016, -0.045, 1.495]), 0.016, 0.013, k=0.015)
    cone("clavicle", MX(s, [0.018, -0.032, 1.500]), MX(s, [0.168, 0.025, 1.518]), 0.011, 0.011, k=0.02)
ell("cranium", [0, 0.030, 1.750], Rxyz(rx=-8), [0.076, 0.098, 0.106], k=0.02)
ell("jaw", [0, -0.028, 1.668], Rxyz(rx=-18), [0.056, 0.060, 0.048], k=0.025)
ell("chin", [0, -0.080, 1.640], I3, [0.024, 0.020, 0.020], k=0.02)
ell("face", [0, -0.060, 1.715], I3, [0.062, 0.050, 0.060], k=0.03)
cone("nose", [0, -0.098, 1.738], [0, -0.118, 1.692], 0.007, 0.013, k=0.012)
cone("brow", [-0.042, -0.080, 1.757], [0.042, -0.080, 1.757], 0.012, 0.012, k=0.03)
for s in (-1.0, 1.0):
    ell("cheek", MX(s, [0.048, -0.068, 1.708]), I3, [0.024, 0.020, 0.018], k=0.02)
    ell("ear", MX(s, [0.075, 0.018, 1.714]), MR(s, Rxyz(rz=15, rx=-10)), [0.011, 0.020, 0.030], k=0.010)
    ell("eye_socket", MX(s, [0.033, -0.098, 1.736]), I3, [0.019, 0.016, 0.014], k=0.008, op="s")
    ell("eyeball", MX(s, [0.033, -0.083, 1.736]), I3, [0.0125, 0.0125, 0.0125], k=0.004)
    ell("lip", MX(s * 0.3, [0.010, -0.098, 1.665 + 0.0]), I3, [0.022, 0.010, 0.008], k=0.006)
ell("lip_low", [0, -0.094, 1.652], I3, [0.020, 0.010, 0.007], k=0.006)
# ---- arms
for sd in ("l", "r"):
    ua, fa, hd = f"upperarm_{sd}", f"forearm_{sd}", f"hand_{sd}"
    Rua, Rfa = basis(ua), basis(fa); aw = sc("arms")
    gh = J[ua][0]
    cone("humerus", at(ua, 0.02), at(ua, 0.98), 0.044, 0.034, k=0.02)
    ell("shoulder_joint", gh + np.array([0, -0.01, 0.01]), I3, [0.050, 0.055, 0.050], k=0.045)
    cone("axilla_front", [np.sign(gh[0]) * 0.140, -0.035, 1.415], at(ua, 0.20, -0.010, 0.012), 0.032, 0.026, k=0.035)
    cone("axilla_back", [np.sign(gh[0]) * 0.140, 0.075, 1.400], at(ua, 0.22, -0.010, -0.020), 0.034, 0.026, k=0.035)
    # deltoid: three heads around the humeral head, tapering to the insertion (~45 % down the humerus)
    dw = sc("delts")
    ell("delt_ant", at(ua, 0.17, 0.010, 0.040), Rua @ Rxyz(rx=-8), [0.032 * dw, 0.030 * dw, 0.090], k=0.012)
    ell("delt_lat", at(ua, 0.20, 0.046, 0.002), Rua, [0.032 * dw, 0.042 * dw, 0.092], k=0.012)
    ell("delt_post", at(ua, 0.17, 0.012, -0.040), Rua @ Rxyz(rx=8), [0.032 * dw, 0.030 * dw, 0.088], k=0.012)
    ell("delt_cap", at(ua, 0.05, 0.030, 0.0), Rua, [0.040 * dw, 0.048 * dw, 0.045], k=0.02)
    ell("biceps", at(ua, 0.60, 0.004, 0.030), Rua, [0.031 * aw, 0.034 * aw, 0.092], k=0.012)
    ell("brachialis", at(ua, 0.76, 0.024, 0.012), Rua, [0.024, 0.024, 0.065], k=0.012)
    ell("triceps_long", at(ua, 0.45, -0.012, -0.034), Rua, [0.030 * aw, 0.034 * aw, 0.105], k=0.012)
    ell("triceps_lat", at(ua, 0.36, 0.024, -0.024), Rua, [0.026 * aw, 0.030 * aw, 0.085], k=0.012)
    ell("triceps_tendon", at(ua, 0.80, 0.0, -0.030), Rua, [0.026, 0.016, 0.055], k=0.015)
    ell("elbow", at(fa, 0.0), Rfa, [0.036, 0.034, 0.030], k=0.02)
    ell("olecranon", at(fa, 0.02, 0.0, -0.030), I3, [0.015, 0.015, 0.016], k=0.012)
    # forearm: brachioradialis / extensors (lateral-front), flexors (medial-front), tapering to a flat wrist
    fw = sc("forearms")
    ell("brachioradialis", at(fa, 0.22, 0.022, 0.012), Rfa, [0.026 * fw, 0.026 * fw, 0.080], k=0.012)
    ell("extensors", at(fa, 0.30, 0.020, -0.012), Rfa, [0.024 * fw, 0.022 * fw, 0.085], k=0.012)
    ell("flexors", at(fa, 0.28, -0.018, 0.010), Rfa, [0.026 * fw, 0.026 * fw, 0.090], k=0.012)
    cone("forearm_core", at(fa, 0.05), J[f"forearm_tw1_{sd}"][1], 0.030, 0.021, k=0.02)
    wr = J[f"forearm_tw1_{sd}"][1]
    ell("wrist", wr, Rfa, [0.029, 0.019, 0.022], k=0.012)
    # hand: palm + fingers from the finger bones
    m_i, m_p = J[f"metacarpal_index_{sd}"], J[f"metacarpal_pinky_{sd}"]
    pc = (m_i[0] + m_i[1] + m_p[0] + m_p[1] + J[f"metacarpal_middle_{sd}"][1] * 2) / 6
    along = (J[f"metacarpal_middle_{sd}"][1] - J[f"metacarpal_middle_{sd}"][0]); along /= np.linalg.norm(along)
    across = m_i[1] - m_p[1]; across -= along * (across @ along); across /= np.linalg.norm(across)
    nrm = np.cross(along, across)
    ell("palm", pc, np.c_[across, nrm, along], [0.044, 0.016, 0.050], k=0.012)
    ell("thenar", J[f"thumb_01_{sd}"][0] * 0.6 + J[f"thumb_01_{sd}"][1] * 0.4, np.c_[across, nrm, along], [0.018, 0.015, 0.024], k=0.01)
    for f, r0 in (("index", 0.0095), ("middle", 0.0100), ("ring", 0.0095), ("pinky", 0.0082), ("thumb", 0.0105)):
        segs = [f"{f}_01_{sd}", f"{f}_02_{sd}", f"{f}_03_{sd}"]
        for i_, sg in enumerate(segs):
            h_, t_ = J[sg]; ra, rb = r0 * (1 - 0.09 * i_), r0 * (1 - 0.09 * (i_ + 1))
            cone("finger", h_, t_ - (t_ - h_) * (0.0 if i_ < 2 else 0.12), ra, rb, k=0.004)
# ---- legs
for sd in ("l", "r"):
    th, sh, ft = f"thigh_{sd}", f"shin_{sd}", f"foot_{sd}"
    Rth, Rsh = basis(th), basis(sh); lw = sc("thighs")
    cone("femur", at(th, 0.00, 0.010, 0.0), at(th, 0.97), 0.070 * lw, 0.046, k=0.03)
    ell("rectus_fem", at(th, 0.45, 0.004, 0.050), Rth, [0.036 * lw, 0.032 * lw, 0.175], k=0.014)
    ell("vastus_lat", at(th, 0.50, 0.052, 0.008), Rth, [0.040 * lw, 0.046 * lw, 0.175], k=0.014)
    ell("vastus_med", at(th, 0.80, -0.032, 0.018), Rth @ Rxyz(ry=-10), [0.030 * lw, 0.028 * lw, 0.070], k=0.02)
    ell("adductors", at(th, 0.25, -0.050, 0.004), Rth @ Rxyz(ry=12), [0.040 * lw, 0.046 * lw, 0.130], k=0.02)
    ell("hamstring_lat", at(th, 0.50, 0.022, -0.048), Rth, [0.034 * lw, 0.036 * lw, 0.170], k=0.014)
    ell("hamstring_med", at(th, 0.50, -0.022, -0.048), Rth, [0.034 * lw, 0.036 * lw, 0.165], k=0.014)
    cone("sartorius", at(th, 0.02, 0.040, 0.060), at(th, 0.92, -0.040, 0.004), 0.011, 0.010, k=0.012)
    ell("knee", at(sh, 0.0), Rsh, [0.050, 0.048, 0.058], k=0.02)
    ell("patella", at(sh, 0.0, 0.0, 0.040), Rsh, [0.024, 0.012, 0.028], k=0.012)
    cone("tibia", at(sh, 0.05), at(sh, 0.96), 0.042, 0.027, k=0.02)
    cw = sc("calves") * 1.08
    ell("gastroc_med", at(sh, 0.28, -0.020, -0.040), Rsh, [0.040 * cw, 0.040 * cw, 0.105], k=0.015)
    ell("gastroc_lat", at(sh, 0.26, 0.022, -0.036), Rsh, [0.035 * cw, 0.035 * cw, 0.090], k=0.015)
    ell("soleus", at(sh, 0.48, 0.0, -0.020), Rsh, [0.046, 0.032, 0.135], k=0.025)
    ell("tib_ant", at(sh, 0.32, 0.020, 0.030), Rsh, [0.018, 0.016, 0.110], k=0.012)
    cone("achilles", at(sh, 0.62, 0.0, -0.028), at(sh, 0.97, 0.0, -0.034), 0.016, 0.011, k=0.012)
    # foot from the ankle: heel, arch, ball, toes; sized to our foot (heel y +0.06 to toe tip y -0.233)
    an = J[sh][1]; x0 = an[0]; s = np.sign(x0)
    for name_, p_, r_ in (("malleolus_lat", [x0 + s * 0.030, 0.010, 0.080], 0.016), ("malleolus_med", [x0 - s * 0.026, 0.0, 0.088], 0.016)):
        ell(name_, p_, I3, [r_ * 0.8, r_, r_], k=0.012)
    ell("heel", [x0, 0.030, 0.042], I3, [0.030, 0.035, 0.038], k=0.02)
    cone("foot_out", [x0 + s * 0.022, 0.020, 0.030], [x0 + s * 0.036, -0.155, 0.022], 0.024, 0.020, k=0.02)
    cone("foot_in", [x0 - s * 0.012, 0.010, 0.050], [x0 - s * 0.024, -0.160, 0.028], 0.028, 0.023, k=0.02)
    cone("instep", [x0, -0.005, 0.075], [x0 - s * 0.005, -0.120, 0.040], 0.028, 0.020, k=0.02)
    for i_, (dx, ln, r_) in enumerate(((-0.026, 0.073, 0.0125), (-0.006, 0.062, 0.0095), (0.010, 0.056, 0.0090), (0.025, 0.050, 0.0085), (0.039, 0.042, 0.0080))):
        y0 = -0.165 + 0.012 * i_
        cone("toe", [x0 + s * dx, y0, 0.020], [x0 + s * dx, y0 - ln + 0.012 * i_, 0.012], r_, r_ * 0.85, k=0.006)

# ------------------------------------------------------------------ evaluate the field
lo = np.array([-0.46, -0.30, -0.005]); hi = np.array([0.46, 0.21, H + 0.02])
nx, ny, nz = (np.ceil((hi - lo) / VOX).astype(int) + 1)
F = np.full((nx, ny, nz), 1.0, np.float32)
xs, ys, zs = (lo[i] + VOX * np.arange(n) for i, n in enumerate((nx, ny, nz)))
t0 = time.time()


def apply(prims):
  global F
  for kind, prm, k, op, blo, bhi, name in prims:
    i0 = np.clip(np.floor((blo - lo) / VOX).astype(int), 0, [nx, ny, nz]); i1 = np.clip(np.ceil((bhi - lo) / VOX).astype(int) + 1, 0, [nx, ny, nz])
    if np.any(i1 <= i0):
        continue
    X, Y, Z = np.meshgrid(xs[i0[0]:i1[0]], ys[i0[1]:i1[1]], zs[i0[2]:i1[2]], indexing="ij")
    p = np.stack([X, Y, Z], -1)
    d = sd_ellipsoid(p, *prm) if kind == "ell" else (sd_rbox(p, *prm) if kind == "box" else sd_roundcone(p, *prm))
    sub = F[i0[0]:i1[0], i0[1]:i1[1], i0[2]:i1[2]]
    F[i0[0]:i1[0], i0[1]:i1[1], i0[2]:i1[2]] = (smin(sub, d, k) if op == "u" else smax_sub(sub, d, k)).astype(np.float32)


apply(PRIMS)


def surf_y(x, z, side):
    """y of the skin at (x, z), found along the grid column from the front (-y) or the back (+y)"""
    ix = int(round((x - lo[0]) / VOX)); iz = int(round((z - lo[2]) / VOX)); col = F[ix, :, iz]
    idx = np.nonzero(col < 0)[0]
    if not len(idx):
        return None
    j = idx[0] if side == "front" else idx[-1]
    j0 = j - 1 if side == "front" else j + 1; f0, f1 = col[j0], col[j]          # linear zero crossing
    return float(ys[j0] + (ys[j] - ys[j0]) * f0 / (f0 - f1))


def groove(name, side, pts, r, depth, k):
    """carve a soft groove along a polyline drawn on the skin (x, z points), depth in metres"""
    pts = np.asarray(pts, float); sm = []
    for a_, b_ in zip(pts[:-1], pts[1:]):
        n_ = max(2, int(np.linalg.norm(b_ - a_) / 0.008))
        sm += [a_ + (b_ - a_) * t for t in np.linspace(0, 1, n_, endpoint=False)]
    sm.append(pts[-1]); C = []
    for x_, z_ in sm:
        y_ = surf_y(x_, z_, side)
        if y_ is not None:
            C.append([x_, y_ - (r - depth) * (1 if side == "front" else -1), z_])   # capsule reaches `depth` under the skin
    G_ = []
    for c1, c2 in zip(C[:-1], C[1:]):
        c1, c2 = np.array(c1), np.array(c2)
        G_.append(("cone", (c1, c2, r, r), k, "s", np.minimum(c1, c2) - r - k - 0.01, np.maximum(c1, c2) + r + k + 0.01, name))
    apply(G_)


GD = float(P("groove_scale", 1.0))
groove("linea_alba", "front", [(0, 1.30), (0, 0.985)], 0.011, 0.0030 * GD, 0.008)
for zi, w in ((1.222, 0.068), (1.155, 0.066), (1.088, 0.064)):
    groove("tendinous", "front", [(-w, zi + 0.008), (-w / 2, zi), (0, zi - 0.004), (w / 2, zi), (w, zi + 0.008)], 0.009, 0.0026 * GD, 0.007)
for s_ in (-1, 1):
    groove("semilunaris", "front", [(s_ * 0.080, 1.300), (s_ * 0.074, 1.180), (s_ * 0.066, 1.060), (s_ * 0.048, 0.975)], 0.014, 0.0030 * GD, 0.010)
    groove("inguinal", "front", [(s_ * 0.122, 1.000), (s_ * 0.085, 0.950), (s_ * 0.040, 0.905)], 0.013, 0.0030 * GD, 0.010)
    for i_, z_ in enumerate((1.330, 1.295, 1.260)):
        groove("serratus", "front", [(s_ * 0.150, z_ + 0.012), (s_ * 0.128, z_ - 0.010)], 0.008, 0.0020 * GD, 0.006)
    groove("lat_border", "back", [(s_ * 0.165, 1.330), (s_ * 0.120, 1.180), (s_ * 0.075, 1.060)], 0.022, 0.0022 * GD, 0.015)
groove("spine", "back", [(0, 0.985), (0, 1.200), (0, 1.420)], 0.016, 0.0045 * GD, 0.012)
BL = float(P("skin_blur_mm", 3.5)) / 1000.0                     # subcutaneous layer: blur the field (rounds
if BL > 0:                                                         # the forms like skin over muscle) then offset
    from scipy.ndimage import gaussian_filter                      # it out a little so volumes stay the same
    F = gaussian_filter(F, BL / VOX).astype(np.float32) - float(P("skin_offset_mm", 1.0)) / 1000.0
F[:, :, 0] = np.maximum(F[:, :, 0], 0.001)                       # flat soles: close the field at the floor
print(f"FIELD {nx}x{ny}x{nz} prims={len(PRIMS)} {time.time() - t0:.1f}s", flush=True)
from skimage.measure import marching_cubes  # noqa: E402
Vv, Ff, _, _ = marching_cubes(F, 0.0, spacing=(VOX, VOX, VOX))
Vv = Vv + lo
np.savez_compressed(OUT / "body_v3_mesh.npz", V=Vv.astype(np.float32), F=Ff.astype(np.int32))
print("MESH", len(Vv), len(Ff), flush=True)
from scipy.spatial import ConvexHull  # noqa: E402


def _per(pts):
    if len(pts) < 8:
        return 0.0
    q = pts[ConvexHull(pts).vertices]; return float(np.linalg.norm(q - np.roll(q, 1, 0), axis=1).sum())


def hcirc(z, xmax):
    m = (np.abs(Vv[:, 2] - z) < 0.002) & (np.abs(Vv[:, 0]) < xmax); return _per(Vv[m, :2])


def bcirc(bone, u, rmax):
    h, ax, L, la, fr = frame(bone); rel = Vv - h; d = rel @ ax - u * L; rad = rel - np.outer(rel @ ax, ax)
    m = (np.abs(d) < 0.002) & (np.linalg.norm(rad, axis=1) < rmax); return _per(np.c_[rad[m] @ la, rad[m] @ fr])


MEAS = {"chest": max(hcirc(z, 0.195) for z in np.arange(1.30, 1.44, 0.01)),
        "waist": min(hcirc(z, 0.20) for z in np.arange(1.04, 1.17, 0.01)),
        "hip": max(hcirc(z, 0.20) for z in np.arange(0.84, 0.98, 0.01)),
        "upper_arm": max(bcirc("upperarm_r", u, 0.085) for u in np.arange(0.3, 0.71, 0.05)),
        "forearm": max(bcirc("forearm_r", u, 0.07) for u in np.arange(0.1, 0.5, 0.05)),
        "thigh": max(bcirc("thigh_r", u, 0.13) for u in np.arange(0.05, 0.41, 0.04)),
        "calf": max(bcirc("shin_r", u, 0.09) for u in np.arange(0.15, 0.51, 0.04)),
        "bideltoid": float(np.ptp(Vv[(Vv[:, 2] > 1.36) & (Vv[:, 2] < 1.50), 0]))}
MEAS = {k_: round(v_ * 100, 1) for k_, v_ in MEAS.items()}
print("MEAS_CM", json.dumps(MEAS), flush=True)

# ------------------------------------------------------------------ Blender object, light relax, save
import bpy  # noqa: E402
import bmesh  # noqa: E402
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new("BODY_V3_REVIEW"); me.from_pydata(Vv.tolist(), [], Ff[:, ::-1].tolist()); me.update()
ob = bpy.data.objects.new("BODY_V3_REVIEW", me); bpy.context.scene.collection.objects.link(ob)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
seen = np.zeros(len(bm.verts), bool); best = []
for v0 in bm.verts:
    if seen[v0.index]:
        continue
    st, comp = [v0], []; seen[v0.index] = True
    while st:
        v = st.pop(); comp.append(v.index)
        for e in v.link_edges:
            o = e.other_vert(v)
            if not seen[o.index]:
                seen[o.index] = True; st.append(o)
    if len(comp) > len(best):
        best = comp
keep = np.zeros(len(bm.verts), bool); keep[best] = True
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep[v.index]], context="VERTS")
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free()
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
m = ob.modifiers.new("RELAX", "LAPLACIANSMOOTH"); m.iterations = int(P("relax", 3)); m.lambda_factor = 0.5; m.use_volume_preserve = True
bpy.ops.object.modifier_apply(modifier=m.name)
for poly in me.polygons:
    poly.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "body_v3.blend"))
z = np.array([v.co.z for v in me.vertices])
rep = {"measurements_cm": MEAS, "voxel_mm": VOX * 1000, "primitives": len(PRIMS), "vertices": len(me.vertices), "faces": len(me.polygons),
       "stature_m": round(float(z.max() - z.min()), 4), "params": PR}
(OUT / "body_v3_report.json").write_text(json.dumps(rep, indent=1)); print("V3", json.dumps({k: rep[k] for k in list(rep)[1:6]}), flush=True)
