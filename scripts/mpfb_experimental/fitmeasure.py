"""Silhouette / landmark comparison of a body mesh against the owner's five-view reference (front + side panels).

Reference: binary masks from the reference sheet (ref_seg masks.npz: 'front' (closed), 'front_raw' (arm gaps kept),
'side'), figure height = stature + hair (~2.5 cm) + shoe sole (~3 cm).  Model: the mesh is rasterised orthographically
(2 mm pixels) into the same two views; trunk-only triangles give the model's torso width directly.

Measures per 2 % of stature: front total width, torso width (where the reference arms are separate), per-leg width,
side depth and front / back edges (trunk aligned on the hips, legs on the shin), plus landmarks: neck (narrowest
front width between 0.80 and 0.90 H), crotch height (front mask), shoulder width (max total width 0.72-0.82 H).

python3 fitmeasure.py <masks.npz> <mesh.npz with V, F, R> [--json out] [--quiet]
"""
import json
import sys

import numpy as np

HREF, HAIR, SHOE = 1.856, 0.025, 0.030
LV = np.round(np.arange(0.04, 0.965, 0.02), 2)
PX = 0.002


def runs(xs, gap):
    if not len(xs):
        return []
    xs = np.sort(xs); br = np.nonzero(np.diff(xs) > gap)[0]
    return list(zip(np.r_[xs[0], xs[br + 1]], np.r_[xs[br], xs[-1]]))


def ref_masks(path):
    M = np.load(path); out = {}
    for k in ("front", "front_raw", "side"):
        m = M[k]; rows = np.nonzero(M["front" if k != "side" else "side"].any(1))[0]
        top, bot = rows.min(), rows.max(); ppm = (bot - top) / (HREF + HAIR + SHOE)
        out[k] = (m, bot - SHOE * ppm, ppm)                   # mask, floor row (sole of the foot), pixels per metre
    return out


def raster(P2, F, px=PX):
    lo = P2.min(0) - 2 * px; hi = P2.max(0) + 2 * px
    W = int(np.ceil((hi[0] - lo[0]) / px)) + 1; H = int(np.ceil((hi[1] - lo[1]) / px)) + 1
    m = np.zeros((H, W), bool); Q = (P2 - lo) / px
    for a, b, c in F:
        pa, pb, pc = Q[a], Q[b], Q[c]
        x0, x1 = int(np.floor(min(pa[0], pb[0], pc[0]))), int(np.ceil(max(pa[0], pb[0], pc[0])))
        y0, y1 = int(np.floor(min(pa[1], pb[1], pc[1]))), int(np.ceil(max(pa[1], pb[1], pc[1])))
        if x1 - x0 > 400 or y1 - y0 > 400:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        d = (pb[1] - pc[1]) * (pa[0] - pc[0]) + (pc[0] - pb[0]) * (pa[1] - pc[1])
        if abs(d) < 1e-12:
            continue
        l1 = ((pb[1] - pc[1]) * (xs - pc[0]) + (pc[0] - pb[0]) * (ys - pc[1])) / d
        l2 = ((pc[1] - pa[1]) * (xs - pc[0]) + (pa[0] - pc[0]) * (ys - pc[1])) / d
        ins = (l1 >= -0.02) & (l2 >= -0.02) & (1 - l1 - l2 >= -0.02)
        m[ys[ins], xs[ins]] = True
    return m, lo                                                # row = y index (metres up), col = x


def ref_profile(R):
    out = {}
    mf, fl, ppm = R["front"]; mr = R["front_raw"][0]; ms, fls, ppms = R["side"]
    for f in LV:
        f = float(f); p = {}
        y = int(round(fl - f * HREF * ppm)); xs = np.nonzero(mf[y])[0] / ppm
        rr = runs(xs, 1.5 / ppm)
        if rr:
            p["total"] = rr[-1][1] - rr[0][0]
            if f < 0.37:
                legs = [q for q in rr if q[1] - q[0] > 0.04]
                if legs:
                    p["leg"] = float(np.mean([q[1] - q[0] for q in legs]))
        r3 = [q for q in runs(np.nonzero(mr[y])[0] / ppm, 2.5 / ppm) if q[1] - q[0] > 0.02]
        if len(r3) == 3 and f >= 0.56:
            p["torso"] = r3[1][1] - r3[1][0]
        ys = int(round(fls - f * HREF * ppms)); xs2 = np.nonzero(ms[ys])[0] / ppms
        r2 = runs(xs2, 1.5 / ppms)
        if r2:
            q = max(r2, key=lambda q: q[1] - q[0]) if f < 0.40 else (r2[0][0], r2[-1][1])
            p["sfront"], p["sback"] = q[1], q[0]                 # image +x = the figure's front
        out[f] = p
    return out


def model_profile(V, F, R):
    z0 = V[:, 2].min(); H = V[:, 2].max() - z0; Z = (V[:, 2] - z0)
    mf, lof = raster(np.c_[V[:, 0], Z], F)
    trunkF = F[(R[F] == 0).all(1)]; mt, lot = raster(np.c_[V[:, 0], Z], trunkF)
    ms, los = raster(np.c_[-V[:, 1], Z], F)
    out = {}
    for f in LV:
        f = float(f); p = {}
        zz = f * H
        y = int(round((zz - lof[1]) / PX)); xs = np.nonzero(mf[y])[0] * PX + lof[0]
        rr = runs(xs, 0.003)
        if rr:
            p["total"] = rr[-1][1] - rr[0][0]
            if f < 0.37:
                legs = [q for q in rr if q[1] - q[0] > 0.04]
                if legs:
                    p["leg"] = float(np.mean([q[1] - q[0] for q in legs]))
        yt = int(round((zz - lot[1]) / PX))
        if 0 <= yt < mt.shape[0]:
            xt = np.nonzero(mt[yt])[0]
            if len(xt):
                p["torso"] = (xt.max() - xt.min()) * PX
        ys = int(round((zz - los[1]) / PX)); xs2 = np.nonzero(ms[ys])[0] * PX + los[0]
        r2 = runs(xs2, 0.003)
        if r2:
            q = max(r2, key=lambda q: q[1] - q[0]) if f < 0.40 else (r2[0][0], r2[-1][1])
            p["sfront"], p["sback"] = q[1], q[0]
        out[f] = p
    return out, H


def landmarks(P):
    nk = [(f, P[f]["total"]) for f in P if 0.80 <= f <= 0.90 and "total" in P[f]]
    sh = [(f, P[f]["total"]) for f in P if 0.72 <= f <= 0.82 and "total" in P[f]]
    legs = [f for f in P if f < 0.56 and "leg" in P[f]]
    return {"neck_f": min(nk, key=lambda t: t[1])[0] if nk else None,
            "shoulder_width": max(t[1] for t in sh) if sh else None, "leg_top_f": max(legs) if legs else None}


def compare(refp, modp):
    def al(P, f0):
        return (P[f0]["sfront"] + P[f0]["sback"]) / 2 if "sfront" in P.get(f0, {}) else 0.0
    ra_l, ma_l, ra_t, ma_t = al(refp, 0.14), al(modp, 0.14), al(refp, 0.50), al(modp, 0.50)
    rows, loss = [], 0.0
    for f in map(float, LV):
        r, m = refp.get(f, {}), modp.get(f, {}); row = {"f": f}
        for k in ("total", "torso", "leg"):
            if k in r and k in m:
                row[k] = (r[k], m[k])
        if "sfront" in r and "sfront" in m:
            a1, a2 = (ra_l, ma_l) if f < 0.40 else (ra_t, ma_t)
            row["front_edge"] = (r["sfront"] - a1, m["sfront"] - a2); row["back_edge"] = (r["sback"] - a1, m["sback"] - a2)
            row["depth"] = (r["sfront"] - r["sback"], m["sfront"] - m["sback"])
        # loss: widths that the reference shows reliably (no shorts 0.40-0.56 width, no hands beside the thighs)
        wt = {"torso": 1.0, "leg": 1.0, "depth": 1.0, "front_edge": 0.5, "back_edge": 0.5,
              "total": 1.0 if (f >= 0.70 or f > 0.84) else 0.0}
        if 0.40 <= f < 0.56:
            wt["depth"] = 0.4
        for k, w in wt.items():
            if k in row and w:
                loss += w * (row[k][1] - row[k][0]) ** 2
        rows.append(row)
    return rows, loss


if __name__ == "__main__":
    a = sys.argv[1:]
    R = ref_masks(a[0]); d = np.load(a[1])
    V, F = d["V"].astype(float), d["F"]; Rg = d["R"] if "R" in d.files else np.zeros(len(V), np.int8)
    refp = ref_profile(R); modp, Hm = model_profile(V, F, Rg)
    rows, loss = compare(refp, modp)
    lm = {"reference": landmarks(refp), "model": landmarks(modp)}
    if "--quiet" not in a:
        print(" f   | total ref/mod   | torso ref/mod  | leg ref/mod   | depth ref/mod  | front-edge     | back-edge")
        c = lambda r, k: (f"{r[k][0]*100:5.1f} {r[k][1]*100:5.1f} {100*(r[k][1]-r[k][0]):+5.1f}" if k in r else " " * 17)
        for r in rows:
            print(f"{r['f']:.2f} | " + " | ".join(c(r, k) for k in ("total", "torso", "leg", "depth", "front_edge", "back_edge")))
        print("LANDMARKS", json.dumps(lm))
    print("LOSS", round(loss * 1e4, 2))
    if "--json" in a:
        json.dump({"rows": rows, "loss_cm2": loss * 1e4, "landmarks": lm}, open(a[a.index("--json") + 1], "w"), indent=1, default=float)
