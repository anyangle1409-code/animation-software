"""Fit a posed, defined MakeHuman-based body (define_mpfb_candidate.py output) to the owner's reference silhouettes.

Owner decision 4 Nov 2026 (option 1): the MakeHuman CC0 base mesh may be used as the starting point of the production
body, with full provenance recorded.  This pass reshapes the static review mesh so its outline matches the reference
sheet, region by region and height by height:

  * reference masks (ref_seg masks.npz: front / side panels, figure incl. hair + shoes) give, at every 2 % of stature,
    - front: the torso width and the two arm widths where they are separate (3 runs), the total width where the arms
      touch the trunk, and each leg's width below the crotch;
    - side: the front and back edges (legs aligned on the shin, trunk on the hips).
  * the model is measured the same way from its own vertices (regions from the MakeHuman rig's vertex groups);
  * per-height ratio fields (smoothed, clamped) scale each region about its own centre line: trunk x and y (y as an
    affine map of the back edge -> front edge), arms radially about the arm axis, each leg in x and y;
  * the displacement is blended across region borders by the skin weights and Laplacian-smoothed.

usage: python3.13 silhouette_fit_blender.py -- <defined .blend> <masks.npz> <out dir> [iterations]
"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from scipy.sparse import csr_matrix

a = sys.argv[sys.argv.index("--") + 1:]
SRC, MASKS, OUT = Path(a[0]), Path(a[1]), Path(a[2]); OUT.mkdir(parents=True, exist_ok=True)
ITERS = int(a[3]) if len(a) > 3 else 3
HREF, HAIR, SHOE = 1.856, 0.025, 0.030
LV = np.round(np.arange(0.04, 0.965, 0.02), 2)
bpy.ops.wm.open_mainfile(filepath=str(SRC))
ob = bpy.data.objects.get("MPFB_DEFINED_REVIEW")
src_body = max((o for o in bpy.data.objects if o.type == "MESH" and o is not ob and "FLOOR" not in o.name),
               key=lambda o: len(o.data.vertices))
me = ob.data; n = len(me.vertices)
V0 = np.empty(n * 3); me.vertices.foreach_get("co", V0); V0 = V0.reshape(-1, 3)
mw = np.array(ob.matrix_world); W = V0 @ mw[:3, :3].T + mw[:3, 3]
GN = {g.index: g.name for g in src_body.vertex_groups}; G = {}
for v in me.vertices:
    for g in v.groups:
        nm = GN.get(g.group)
        if nm:
            G.setdefault(nm, np.zeros(n))[v.index] = g.weight
gw = lambda *ks: np.clip(sum((w for nm, w in G.items() if any(k in nm for k in ks)), np.zeros(n)), 0, 1)
ARM = gw("upperarm", "lowerarm", "hand", "thumb", "index", "middle", "ring", "pinky")
LEG = gw("thigh", "calf", "foot", "ball")
TRUNK = np.clip(1 - ARM - LEG, 0, 1)
E = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
A = csr_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n))
Dinv = 1.0 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)


def runs(xs, gap):
    xs = np.sort(xs)
    if not len(xs):
        return []
    br = np.nonzero(np.diff(xs) > gap)[0]
    return list(zip(np.r_[xs[0], xs[br + 1]], np.r_[xs[br], xs[-1]]))


# ---------------------------------------------------------------- reference profiles (metres)
M = np.load(MASKS)


def ref_profiles():
    out = {}
    for view in ("front", "side"):
        m = M[view]; rows = np.nonzero(m.any(1))[0]; top, bot = rows.min(), rows.max(); ppm = (bot - top) / (HREF + HAIR + SHOE)
        prof = {}
        for f in LV:
            y = int(round(bot - (SHOE + f * HREF) * ppm)); xs = np.nonzero(m[y])[0] / ppm
            prof[float(f)] = runs(xs, 1.5 / ppm)
        out[view] = prof
    return out


RP = ref_profiles()
# raw (un-closed) front mask runs for torso / arm separation: rebuild from the closed mask is not possible, so the
# segmentation script stores the raw front mask as 'front_raw' when available
if "front_raw" in M.files:
    m = M["front_raw"]; rows = np.nonzero(M["front"].any(1))[0]; top, bot = rows.min(), rows.max()
    ppm = (bot - top) / (HREF + HAIR + SHOE)
    for f in LV:
        y = int(round(bot - (SHOE + f * HREF) * ppm)); xs = np.nonzero(m[y])[0] / ppm
        r_ = [q for q in runs(xs, 2.5 / ppm) if q[1] - q[0] > 0.02]
        if len(r_) == 3:
            RP["front"][float(f)] = r_


def ref_targets():
    T = {}
    s_rows = RP["side"]
    mid = lambda f: (s_rows[f][0][0] + s_rows[f][-1][1]) / 2 if s_rows.get(f) else None
    shin, hip = mid(0.14), mid(0.50)
    for f in map(float, LV):
        t = {}
        fr = RP["front"][f]
        if f < 0.43:
            legs = [q for q in fr if q[1] - q[0] > 0.04]
            if legs:
                t["leg_w"] = float(np.mean([q[1] - q[0] for q in legs]))
        elif len(fr) == 3:
            t["torso_w"] = fr[1][1] - fr[1][0]; t["arm_w"] = ((fr[0][1] - fr[0][0]) + (fr[2][1] - fr[2][0])) / 2
        elif fr:
            t["total_w"] = fr[-1][1] - fr[0][0]
        sr = s_rows.get(f)
        if sr:
            a0 = shin if f < 0.43 else hip
            if f < 0.43:          # one leg in the side view: the widest run
                q = max(sr, key=lambda q: q[1] - q[0])
            else:
                q = (sr[0][0], sr[-1][1])
            t["front"] = q[1] - a0; t["back"] = q[0] - a0     # +x in the image = the figure's front
        T[f] = t
    return T


TG = ref_targets()


# ---------------------------------------------------------------- model profiles
def model_profiles(X):
    z0 = X[:, 2].min(); Hm = X[:, 2].max() - z0; f_ = (X[:, 2] - z0) / Hm
    P = {}
    sl = lambda f: np.abs(f_ - f) < 0.004
    side_mid = {}
    for f0 in (0.14, 0.50):
        s = sl(f0) & ((LEG > 0.5) & (X[:, 0] > 0) if f0 < 0.43 else (TRUNK > 0.5))
        side_mid[f0] = -(X[s, 1].min() + X[s, 1].max()) / 2
    for f in map(float, LV):
        s = sl(f); p = {}
        if f < 0.43:
            for sd, sg in (("l", 1), ("r", -1)):
                q = s & (LEG > 0.5) & (np.sign(X[:, 0]) == sg)
                if q.sum() > 10:
                    p["leg_w_" + sd] = float(np.ptp(X[q, 0])); p["leg_cx_" + sd] = float((X[q, 0].min() + X[q, 0].max()) / 2)
                    p["leg_front_" + sd] = float(-X[q, 1].min() - side_mid[0.14]); p["leg_back_" + sd] = float(-X[q, 1].max() - side_mid[0.14])
        else:
            q = s & (TRUNK > 0.5)
            if q.sum() > 10:
                p["torso_w"] = float(np.ptp(X[q, 0]))
                p["front"] = float(-X[q, 1].min() - side_mid[0.50]); p["back"] = float(-X[q, 1].max() - side_mid[0.50])
            qa = [s & (ARM > 0.5) & (np.sign(X[:, 0]) == sg) for sg in (1, -1)]
            if all(x.sum() > 10 for x in qa):
                p["arm_w"] = float(np.mean([np.ptp(X[x, 0]) for x in qa]))
            if s.any():
                p["total_w"] = float(np.ptp(X[s, 0]))
        P[f] = p
    return P, z0, Hm


def smooth_curve(fs, vals, sig=1.2):
    fs = np.asarray(fs); vals = np.asarray(vals, float); ok = np.isfinite(vals)
    if ok.sum() == 0:
        return lambda f: np.ones_like(f)
    full = np.interp(LV, fs[ok], vals[ok])
    k = np.exp(-0.5 * ((np.arange(-4, 5)) / sig) ** 2); k /= k.sum()
    full = np.convolve(np.pad(full, 4, mode="edge"), k, mode="valid")
    return lambda f: np.interp(f, LV, full)


X = W.copy(); log = []
for it in range(ITERS):
    P, z0, Hm = model_profiles(X); f_ = (X[:, 2] - z0) / Hm
    D = np.zeros_like(X)
    # ---- trunk: width ratio (torso width where measurable, total width where the arms touch), side affine map
    fs, rx = [], []
    for f in map(float, LV):
        t, p = TG[f], P[f]
        if f >= 0.44 and "torso_w" in t and "torso_w" in p:
            fs.append(f); rx.append(t["torso_w"] / p["torso_w"])
        elif f >= 0.44 and "total_w" in t and "total_w" in p:
            fs.append(f); rx.append(t["total_w"] / p["total_w"])
    sx = smooth_curve(fs, np.clip(rx, 0.86, 1.12))
    fs2, fr_, bk_ = [], [], []
    for f in map(float, LV):
        t, p = TG[f], P[f]
        if f >= 0.44 and "front" in t and "front" in p:
            fs2.append(f); fr_.append(t["front"] - p["front"]); bk_.append(t["back"] - p["back"])
    dF, dB = smooth_curve(fs2, np.clip(fr_, -0.05, 0.05)), smooth_curve(fs2, np.clip(bk_, -0.05, 0.05))
    # trunk x scale about the midline; y: model -y is "front", map back..front edges linearly
    up = f_ >= 0.40
    Pf = np.array([P[float(f)].get("front", np.nan) for f in LV]); Pb = np.array([P[float(f)].get("back", np.nan) for f in LV])
    ok = np.isfinite(Pf)
    pf_i = np.interp(f_, LV[ok], Pf[ok]); pb_i = np.interp(f_, LV[ok], Pb[ok])
    mid50 = -np.median(X[(np.abs(f_ - 0.5) < 0.004) & (TRUNK > 0.5), 1])
    u = np.clip(((-X[:, 1] - mid50) - pb_i) / np.maximum(pf_i - pb_i, 0.02), -0.2, 1.2)  # 0 back edge .. 1 front edge
    dy_front = dB(f_) + (dF(f_) - dB(f_)) * u                        # displacement along "front" (= -y)
    wt = TRUNK * up
    sxf = sx(f_)
    D[:, 0] += wt * X[:, 0] * (sxf - 1)
    D[:, 1] += -wt * dy_front
    # arms follow the shoulders: at shoulder height (where the arms join the trunk outline) they scale with the trunk;
    # below it the whole arm shifts rigidly by the shoulder's change, so the arm keeps its shape
    fsh = 0.74; s_sh = float(sx(np.array([fsh]))[0])
    hi = np.clip((f_ - 0.70) / 0.04, 0, 1)
    D[:, 0] += ARM * (hi * X[:, 0] * (sxf - 1) + (1 - hi) * np.sign(X[:, 0]) * 0.235 * (s_sh - 1))
    # legs: per-leg width scale about the leg's centre, side edges as an affine map
    fsl, rl, lf, lb = [], [], [], []
    for f in map(float, LV):
        t, p = TG[f], P[f]
        if f < 0.43 and "leg_w" in t and "leg_w_l" in p:
            fsl.append(f); rl.append(t["leg_w"] / np.mean([p["leg_w_l"], p["leg_w_r"]]))
            if "front" in t:
                lf.append(t["front"] - np.mean([p["leg_front_l"], p["leg_front_r"]])); lb.append(t["back"] - np.mean([p["leg_back_l"], p["leg_back_r"]]))
            else:
                lf.append(np.nan); lb.append(np.nan)
    if fsl:
        sl_, dLF, dLB = smooth_curve(fsl, np.clip(rl, 0.85, 1.2)), smooth_curve(fsl, np.clip(lf, -0.04, 0.04)), smooth_curve(fsl, np.clip(lb, -0.04, 0.04))
        for sd, sg in (("l", 1), ("r", -1)):
            q = (LEG > 0.05) & (np.sign(X[:, 0]) == sg) & (f_ < 0.47)
            cxs = np.array([P[float(f)].get("leg_cx_" + sd, np.nan) for f in LV]); okc = np.isfinite(cxs)
            cx = np.interp(f_[q], LV[okc], cxs[okc])
            fr2 = np.array([P[float(f)].get("leg_front_" + sd, np.nan) for f in LV]); bk2 = np.array([P[float(f)].get("leg_back_" + sd, np.nan) for f in LV])
            ok2 = np.isfinite(fr2); pf2 = np.interp(f_[q], LV[ok2], fr2[ok2]); pb2 = np.interp(f_[q], LV[ok2], bk2[ok2])
            mid14 = -np.median(X[(np.abs(f_ - 0.14) < 0.004) & (LEG > 0.5) & (X[:, 0] > 0), 1])
            u2 = np.clip(((-X[q, 1] - mid14) - pb2) / np.maximum(pf2 - pb2, 0.02), -0.2, 1.2)
            dyf = dLB(f_[q]) + (dLF(f_[q]) - dLB(f_[q])) * u2
            w_ = LEG[q] * np.clip((0.47 - f_[q]) / 0.05, 0, 1)
            D[q, 0] += w_ * (X[q, 0] - cx) * (sl_(f_[q]) - 1); D[q, 1] += -w_ * dyf
    for _ in range(25):
        D = 0.5 * D + 0.5 * (A @ D) * Dinv[:, None]
    X = X + D
    log.append({"iter": it, "max_move_mm": round(float(np.linalg.norm(D, axis=1).max()) * 1000, 1)})
    print("FITITER", log[-1], flush=True)

me.vertices.foreach_set("co", ((X - mw[:3, 3]) @ np.linalg.inv(mw[:3, :3]).T).ravel()); me.update()
np.savez_compressed(OUT / "fitted_mesh.npz", V=X.astype(np.float32))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "mpfb_candidate_defined.blend"))
(OUT / "silhouette_fit_report.json").write_text(json.dumps({"source": SRC.name, "iterations": log}, indent=1))
print("SILFIT done", flush=True)
