"""FIRST-PARTY anatomy relief for OUR Body v2 mesh (canonical skeleton), in the rest (bind) pose.

Port of the procedural definition pass that was tuned on the MPFB benchmark (scripts/mpfb_experimental/
define_mpfb_candidate.py) to our own mesh: only our code and our vertices; nothing from MPFB is copied.  The relief is
a smooth scalar field of Gaussian grooves / bulges placed from our canonical bones (trunk landmarks as fractions of
stature, matched to where the benchmark placed them), displaced along the rest normals and added to the basis AND every
shape key (relative keys keep their offsets), so the definition rides through all movement keys.

  usage: python3.13 anatomy_relief_blender.py -- <in .blend> <out dir>
  env:   V2_DEF (mm scale, default 1.0), V2_DEF_EXTRA (default 1.0), V2_SEX (male|female), V2_PEC_* as in the MPFB pass,
         V2_DEF_SMOOTH (field smoothing passes, default 4)
"""
import json
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from scipy.sparse import csr_matrix

a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(a[0]), Path(a[1]); OUT.mkdir(parents=True, exist_ok=True)
K = float(os.environ.get("V2_DEF", "1.0")) / 1000.0
bpy.ops.wm.open_mainfile(filepath=str(SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import character_profile  # noqa: E402
bn_, rn_ = character_profile.blender_names()
body, rig = bpy.data.objects[bn_], bpy.data.objects[rn_]
me = body.data; n = len(me.vertices)
R0 = np.empty(n * 3); me.vertices.foreach_get("co", R0); R0 = R0.reshape(-1, 3)
mw = np.array(body.matrix_world); W = R0 @ mw[:3, :3].T + mw[:3, 3]
N = np.empty(n * 3); me.vertices.foreach_get("normal", N); N = N.reshape(-1, 3) @ mw[:3, :3].T
N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
GN = {g.index: g.name for g in body.vertex_groups}
G = {}
for v in me.vertices:
    for g in v.groups:
        nm = GN.get(g.group)
        if nm:
            G.setdefault(nm, np.zeros(n))[v.index] = g.weight
gw = lambda *ks: sum((w for nm, w in G.items() if any(k in nm for k in ks)), np.zeros(n))
B = {b.name: (np.array(rig.matrix_world @ b.head_local), np.array(rig.matrix_world @ b.tail_local)) for b in rig.data.bones}
assert B["foot_l"][1][1] < B["foot_l"][0][1], "expects the body facing -y"
armw = gw("upperarm", "forearm", "hand", "thumb", "index", "middle", "ring", "pinky", "metacarpal")
legw = gw("thigh", "shin", "foot", "toe")
trunk = (armw < 0.3) & (legw < 0.5)
x, y, z = W[:, 0], W[:, 1], W[:, 2]; ax = np.abs(x)
front, back = trunk & (N[:, 1] < -0.3), trunk & (N[:, 1] > 0.3)
z0 = float(z.min()); H = float(z.max() - z0)
# trunk landmarks as fractions of stature where the benchmark placed them (its pelvis / spine_03 / clavicle heads at
# 0.522 / 0.649 / 0.806 H); our rig's spine segmentation differs, so its bones are not used for these three
LMK = {"pelvis": np.array([0, 0, z0 + 0.522 * H]), "spine_03": np.array([0, 0, z0 + 0.649 * H]),
       "clavicle": np.array([0, 0, z0 + 0.806 * H])}
D = np.zeros(n)


def gauss(d, s):
    return np.exp(-0.5 * (d / s) ** 2)


def ramp(v, lo, hi):
    t = np.clip((v - lo) / (hi - lo), 0, 1); return t * t * (3 - 2 * t)


def band(v, lo, hi, f=0.01):
    return ramp(v, lo - f, lo + f) * (1 - ramp(v, hi - f, hi + f))


def seg_dist(P2, a2, b2):
    ab = b2 - a2; t = np.clip(((P2 - a2) @ ab) / (ab @ ab), 0, 1); return np.linalg.norm(P2 - (a2 + t[:, None] * ab), axis=1), t


def line_xz(mask, p0, p1, depth, s):
    d, t = seg_dist(np.c_[ax, z], np.array(p0), np.array(p1))
    D[:] += mask * depth * gauss(d, s) * ramp(t, 0.0, 0.08) * (1 - ramp(t, 0.92, 1.0))


pel, sp3, clav = LMK["pelvis"], LMK["spine_03"], LMK["clavicle"]
zn = pel[2] + 0.095                                          # navel
zx = sp3[2] + 0.03                                           # xiphoid region
znip = zx + 0.085                                            # nipple line
# --- abdomen: linea alba, three tendinous intersections, linea semilunaris, inguinal lines
line_xz(front, (0, zn - 0.03), (0, zx), -2.6 * K, 0.0055)
for zi, w in ((zn + 0.045, 0.060), (zn + 0.095, 0.064), (zn + 0.145, 0.066)):
    d = np.abs(z - (zi + 0.010 * (ax / w) ** 2))
    D[:] += front * -2.2 * K * gauss(d, 0.0045) * (1 - ramp(ax, w - 0.012, w + 0.004))
for s_ in (1,):
    line_xz(front, (0.072, zx), (0.060, zn - 0.04), -2.6 * K, 0.0065)
    line_xz(front, (0.060, zn - 0.04), (0.035, pel[2] - 0.05), -2.0 * K, 0.006)
line_xz(front, (0.125, pel[2] + 0.04), (0.035, pel[2] - 0.07), -2.2 * K, 0.007)   # inguinal ("Adonis") line
FEMALE = os.environ.get('V2_SEX', 'male') == 'female'
# --- chest: sternal groove, lower pectoral border with the pectoral mass above it, deltopectoral groove
line_xz(front & (not FEMALE), (0, znip - 0.04), (0, clav[2] - 0.05), -2.2 * K, 0.007)
xb = np.clip(ax, 0.015, 0.17); zb = znip - 0.050 + float(os.environ.get('V2_PEC_RISE', '0.075')) * ((xb - 0.015) / 0.155) ** 1.6
pm = front & (ax < 0.17) & (not FEMALE)   # the male pectoral features only
D[:] += pm * -3.0 * K * gauss(z - zb, 0.0075)
D[:] += pm * float(os.environ.get('V2_PEC_MASS', '2.0')) * K * gauss(z - (zb + 0.04), 0.022)
# upper (clavicular) pectoral fill: flat, broad chest rather than a low, rounded mass (owner 3 Nov: "chest too puffy")
D[:] += pm * float(os.environ.get('V2_PEC_UPPER', '0.0')) * K * gauss(z - (clav[2] - 0.075), 0.03) * (1 - ramp(ax, 0.12, 0.17)) * ramp(ax, 0.01, 0.03)
# flatten the lower pectoral bulge (inferior to the nipple line, above the border): negative mass there
D[:] += pm * -float(os.environ.get('V2_PEC_FLATTEN', '0.0')) * K * gauss(z - (zb + 0.012), 0.012) * (1 - ramp(ax, 0.12, 0.16)) * (1 - ramp(ax, 0.13, 0.17))
gh = B["upperarm_l"][0]
# pectoral shelf (owner 3 Nov: chest still not like the reference): a sharp lower border with the pectoral edge standing
# proud just above it (undercut shadow), carried laterally into the armpit; the MakeHuman nipple flattened; a soft
# infraclavicular line where the pectoral starts under the clavicle
NIP = float(os.environ.get("V2_NIPPLE_FLAT", "0.0"))          # flatten the MakeHuman nipple bump (mm)
if NIP > 0:
    for sg_ in (1.0, -1.0):
        cand = np.nonzero(front & (np.sign(x) == sg_) & (np.abs(z - znip) < 0.05) & (ax > 0.06) & (ax < 0.14))[0]
        if len(cand):
            pn = W[cand[np.argmin(y[cand])]]
            D[:] += front * -NIP * K / 2.3 * gauss(np.linalg.norm(W - pn, axis=1), 0.010)
SH = float(os.environ.get("V2_PEC_SHELF", "0.0"))
if SH > 0:
    pw = front & (ax < 0.19)
    # lower border as in the photographs: lowest just below / outside the nipple (x_low), rising gently to the sternum
    # and sweeping up into the armpit
    xb2 = np.clip(ax, 0.015, 0.19)
    nz = []
    for sg_ in (1.0, -1.0):
        cand = np.nonzero(front & (np.sign(x) == sg_) & (np.abs(z - znip) < 0.05) & (ax > 0.06) & (ax < 0.14))[0]
        nz.append(W[cand[np.argmin(y[cand])]] if len(cand) else np.array([0.10, 0, znip]))
    xlow = float(np.mean([abs(p_[0]) for p_ in nz])) + 0.005; zlow = float(np.mean([p_[2] for p_ in nz])) - float(os.environ.get("V2_PEC_DROP", "0.028"))
    zb2 = np.where(xb2 < xlow, zlow + 0.016 * ((xlow - xb2) / (xlow - 0.015)) ** 2, zlow + 0.065 * ((xb2 - xlow) / (0.19 - xlow)) ** 2)
    dz = z - zb2
    D[:] += pw * -SH * 1.4 * K * gauss(dz + 0.002, 0.0055)                         # deep, narrow border
    D[:] += pw * SH * 1.0 * K * gauss(dz - 0.012, 0.009) * (1 - ramp(ax, 0.17, 0.19))   # edge standing proud above it
    for sg_ in (1.0, -1.0):                                                        # nipples: flatten the bump
        cand = np.nonzero(front & (np.sign(x) == sg_) & (np.abs(z - znip) < 0.05) & (ax > 0.06) & (ax < 0.14))[0]
        if len(cand):
            pn = W[cand[np.argmin(y[cand])]]
            D[:] += front * -SH * 0.9 * K * gauss(np.linalg.norm(W - pn, axis=1), 0.009)
    line_xz(front, (0.03, clav[2] - 0.03), (abs(gh[0]) - 0.07, clav[2] - 0.035), -SH * 0.5 * K, 0.006)
line_xz(trunk | (armw > 0), (abs(clav[0]) + 0.10, clav[2] - 0.035), (abs(gh[0]) - 0.025, gh[2] - 0.10), -2.6 * K, 0.007)


def limb(bone, w_mask, feats):
    """cylindrical features around a bone: (t0, t1, angle centre deg (0 = lateral, 90 = front), angle width deg, depth)"""
    for sd in ("l", "r"):
        h, t = B[bone.format(sd)]; L = np.linalg.norm(t - h); a_ = (t - h) / L
        sel = w_mask(sd)
        rel = W - h; tt = rel @ a_ / L; rad = rel - np.outer(rel @ a_, a_)
        lat = np.array([np.sign(h[0]) or 1.0, 0, 0]); lat = lat - a_ * (lat @ a_); lat /= np.linalg.norm(lat)
        fr = np.cross(a_, lat) if np.cross(a_, lat)[1] < 0 else -np.cross(a_, lat)
        ang = np.degrees(np.arctan2(rad @ fr, rad @ lat))
        for t0, t1, ac, aw, dep in feats:
            da = (ang - ac + 180) % 360 - 180
            D[:] += sel * dep * K * band(tt, t0, t1, 0.05) * gauss(da, aw)


limb("upperarm_{}", lambda s: G.get(f"upperarm_{s}", np.zeros(n)) > 0.45,
     [(0.38, 0.52, 0, 35, -2.0), (0.45, 0.92, 15, 9, -2.0), (0.45, 0.92, 180, 10, -1.6), (0.15, 0.40, 0, 60, 1.2)])
limb("forearm_{}", lambda s: G.get(f"forearm_{s}", np.zeros(n)) > 0.5, [(0.10, 0.55, 60, 12, -1.4)])
limb("thigh_{}", lambda s: G.get(f"thigh_{s}", np.zeros(n)) > 0.5,
     [(0.30, 0.85, 35, 9, -2.4), (0.15, 0.75, 125, 9, -1.8), (0.30, 0.90, -5, 10, -1.4),
      (0.74, 0.92, 135, 22, 3.2), (0.55, 0.85, 70, 25, 1.4)])
limb("shin_{}", lambda s: G.get(f"shin_{s}", np.zeros(n)) > 0.5,
     [(0.10, 0.42, -125, 25, 2.6), (0.10, 0.38, -60, 22, 1.8), (0.12, 0.40, -92, 8, -1.4), (0.42, 0.52, -90, 70, -1.6)])
# --- back: spinal groove between the erector columns, lower latissimus border, lower trapezius, scapular border
line_xz(back, (0, pel[2] - 0.02), (0, clav[2] - 0.08), -3.2 * K, 0.008)
line_xz(back, (0.020, pel[2] + 0.02), (0.020, sp3[2] + 0.08), 1.6 * K, 0.012)
line_xz(back, (abs(gh[0]) - 0.06, gh[2] - 0.15), (0.075, pel[2] + 0.07), -2.0 * K, 0.008)
line_xz(back, (0.02, sp3[2]), (0.11, gh[2] - 0.05), -0.8 * K, 0.013)
line_xz(back, (0.075, gh[2] - 0.02), (0.095, gh[2] - 0.16), -1.4 * K, 0.007)
# --- added 3 Nov (owner: "better definition"): serratus digitations, external oblique border, deltoid head separations,
# infraspinatus / teres border
sideF = trunk & (np.abs(N[:, 0]) > 0.35) & (N[:, 1] < 0.35)
for k_ in range(3):
    zc = znip - 0.035 - 0.028 * k_
    line_xz(sideF, (abs(gh[0]) - 0.075, zc + 0.012), (abs(gh[0]) - 0.105, zc - 0.012), -1.8 * K, 0.005)
line_xz(trunk & (N[:, 1] < 0.2), (0.115, zx - 0.01), (0.120, pel[2] + 0.06), -1.8 * K, 0.008)
line_xz(back, (abs(gh[0]) - 0.075, gh[2] - 0.05), (abs(gh[0]) - 0.02, gh[2] - 0.11), -1.6 * K, 0.007)
limb("upperarm_{}", lambda s: G.get(f"upperarm_{s}", np.zeros(n)) > 0.3, [(0.02, 0.36, 50, 8, -1.6), (0.02, 0.36, -45, 8, -1.6)])
# --- added (owner: biceps-to-forearm transition, legs): brachioradialis / extensor mass on the upper forearm, the
# biceps' lower end tapering into the elbow crease, quadriceps (vastus lateralis) mass, patella outline
limb("forearm_{}", lambda s: G.get(f"forearm_{s}", np.zeros(n)) > 0.3, [(0.0, 0.45, 40, 30, 2.2 * (0.5 if FEMALE else 1.0)), (0.0, 0.45, 120, 28, 1.4 * (0.5 if FEMALE else 1.0)), (0.05, 0.6, 90, 9, -1.2 * (0.4 if FEMALE else 1.0))])
limb("upperarm_{}", lambda s: G.get(f"upperarm_{s}", np.zeros(n)) > 0.3, [(0.55, 0.85, 95, 30, 1.6), (0.88, 1.0, 95, 40, -1.6 * (0.3 if FEMALE else 1.0))])
limb("thigh_{}", lambda s: G.get(f"thigh_{s}", np.zeros(n)) > 0.4, [(0.25, 0.80, 15, 25, 2.2), (0.10, 0.60, 95, 30, 1.6), (0.92, 1.02, 90, 50, -1.5)])
# --- added (owner 3 Nov: "still need more definition"): gluteal fold, hamstring split, triceps horseshoe, rear deltoid,
# trapezius / rhomboid relief, stronger erector columns, oblique ridge, medial gastrocnemius
X2 = float(os.environ.get("V2_DEF_EXTRA", "1.0"))
if X2 > 0:
    legs_back = (legw > 0.3) & (N[:, 1] > 0.2)
    line_xz(legs_back | (back & (legw > 0.1)), (0.025, pel[2] - 0.115), (0.115, pel[2] - 0.095), -2.4 * X2 * K, 0.007)   # gluteal fold
    limb("thigh_{}", lambda s: G.get(f"thigh_{s}", np.zeros(n)) > 0.4,
         [(0.20, 0.80, -95, 8, -2.0 * X2), (0.15, 0.55, -60, 25, 1.2 * X2), (0.15, 0.55, -130, 25, 1.2 * X2)])   # hamstring split
    limb("upperarm_{}", lambda s: G.get(f"upperarm_{s}", np.zeros(n)) > 0.35,
         [(0.55, 0.80, -90, 35, -1.8 * X2), (0.25, 0.55, -90, 30, 1.4 * X2), (0.02, 0.30, -60, 25, 1.4 * X2)])   # triceps horseshoe, rear delt
    line_xz(back, (0.0, clav[2] - 0.02), (abs(gh[0]) - 0.05, clav[2] - 0.045), 1.4 * X2 * K, 0.014)                 # upper trapezius mass
    line_xz(back, (0.03, gh[2] - 0.06), (0.09, gh[2] - 0.14), -0.6 * X2 * K, 0.014)                                 # rhomboid / scapular border (soft: v9 drew 'V' marks)
    line_xz(back, (0.035, pel[2] + 0.01), (0.035, sp3[2] + 0.05), 1.8 * X2 * K, 0.013)                              # erector columns
    line_xz(trunk & (N[:, 1] < 0.3), (0.13, zx - 0.02), (0.125, pel[2] + 0.05), 1.4 * X2 * K, 0.010)               # oblique ridge
    limb("shin_{}", lambda s: G.get(f"shin_{s}", np.zeros(n)) > 0.5, [(0.08, 0.40, -140, 22, 1.6 * X2), (0.30, 0.48, -150, 30, -1.2 * X2)])
E = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
A = csr_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n))
Dinv = 1.0 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)
for _ in range(int(os.environ.get("V2_DEF_SMOOTH", "4"))):
    D = 0.5 * D + 0.5 * (A @ D) * Dinv
Nl = np.empty(n * 3); me.vertices.foreach_get("normal", Nl); Nl = Nl.reshape(-1, 3)
Dl = D[:, None] * Nl
for kb in (me.shape_keys.key_blocks if me.shape_keys else []):
    c = np.empty(n * 3); kb.data.foreach_get("co", c); kb.data.foreach_set("co", (c.reshape(-1, 3) + Dl).ravel())
me.vertices.foreach_set("co", (R0 + Dl).ravel()); me.update()
rep = {"source": SRC.name, "def_scale": K * 1000, "vertices": n, "max_in_mm": round(float(D.min()) * 1000, 2),
       "max_out_mm": round(float(D.max()) * 1000, 2), "moved_over_0.5mm": int((np.abs(D) > 5e-4).sum())}
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / SRC.name), copy=True)
(OUT / "anatomy_relief_report.json").write_text(json.dumps(rep, indent=1)); print("RELIEF", json.dumps(rep), flush=True)
