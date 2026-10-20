"""R58 read-only diagnostic: WHEN and WHERE the R52/R57 shoulder S7 increments add extra motion (Claude, 20 Oct 2026).

R57 smoothed the dense S7 increments over 114-122 deg at the hotspots and moved the 161-pose motion excess only from
40.64 to 39.38 mm (guard 0.5 mm), so the dominant temporal defect is probably not at 118 deg.  This localises it, without
fitting, saving or changing anything:

  1. per frame (161 press samples, t = i/160, ht = 70 + 96 * smoothstep(t), lockout 166 deg): the excess frame
     acceleration |d2 current| - |d2 baseline| per posterior vertex (the exact quantity of
     measure_original_review_r52_dense_motion_blender.py, x16 for the original-grid scale);
  2. for the worst vertices: the frame / elevation of their peak excess, and their dense S7 increment profile over the 72
     one-degree controls (95..166) with its node-to-node second difference - a kink in that profile is what a frame-level
     acceleration spike looks like when the press sweeps through that degree;
  3. early outward: which vertices move outward before 110 deg, and at what elevation.

Inputs (all immutable CI artifacts): R52 source.npz (rest), R52 solved.npz and R57 candidate.npz (dense_delta,
72 x nv x 3), and the dense-motion points files (baseline = R41, current = candidate; 161 x nback x 3).
  python3 diagnose_r58_temporal_hotspots.py --source source.npz --r52 solved.npz --r57 candidate.npz
      --points52 r52_points.npz --points57 r57_points.npz --out r58_report.json
"""
import argparse
import json

import numpy as np

DENSE_ANGLES = np.arange(95.0, 167.0)          # 72 controls; index 0 = 95 (ghost), 15 = 110, 71 = 166 (protected zero)
HOTSPOTS = (19057, 20913, 18081, 21057)        # R55/R56 named vertices


def press_ht(t):
    k = np.clip(t, 0, 1)
    k = k * k * (3 - 2 * k)
    return 70.0 + (166.0 - 70.0) * k


def excess_field(points):
    with np.load(points) as z:
        base, cur, ids = z["baseline"], z["current"], z["back_vertex_ids"]
    before = np.linalg.norm(np.diff(base, n=2, axis=0), axis=2)
    after = np.linalg.norm(np.diff(cur, n=2, axis=0), axis=2)
    ex = (after - before) * 1000.0                  # mm, frames 1..159 (centre of each 3-frame window)
    return base, cur, ids, ex


def profile(dense, v):
    m = np.linalg.norm(dense[:, v, :], axis=1) * 1000.0            # increment magnitude per control, mm
    d2 = np.linalg.norm(np.diff(dense[:, v, :], n=2, axis=0), axis=1) * 1000.0   # node-to-node second difference
    return m, d2


def analyse(tag, points, dense, rest):
    base, cur, ids, ex = excess_field(points)
    frames = np.arange(1, 160)
    hts = press_ht(frames / 160.0)
    out = {"tag": tag, "max_excess_mm_x16": round(float(ex.max() * 16), 4)}
    # timeline: worst excess per frame
    per_frame = ex.max(axis=1)
    out["timeline_top_frames"] = [
        {"frame": int(frames[i]), "ht_deg": round(float(hts[i]), 2), "excess_mm_x16": round(float(per_frame[i] * 16), 3),
         "vertex": int(ids[ex[i].argmax()])} for i in np.argsort(-per_frame)[:15]]
    # elevation bands: how much of the excess lives where
    bands = [(70, 95), (95, 110), (110, 114), (114, 123), (123, 136), (136, 156), (156, 166.1)]
    out["excess_by_elevation_band_mm_x16"] = {f"{a}-{b}": round(float(per_frame[(hts >= a) & (hts < b)].max(initial=0) * 16), 3) for a, b in bands}
    # worst vertices and their dense S7 increment profiles
    worst_v = np.argsort(-ex.max(axis=0))[:12]
    rows = []
    for j in list(worst_v) + [int(np.where(ids == h)[0][0]) for h in HOTSPOTS if h in ids]:
        v = int(ids[j]); i = int(ex[:, j].argmax())
        m, d2 = profile(dense, v)
        k = int(d2.argmax()) + 1                                    # control index at the centre of the worst kink
        rows.append({"vertex": v, "rest_m": [round(float(x), 4) for x in rest[v]],
                     "peak_frame": int(frames[i]), "peak_ht_deg": round(float(hts[i]), 2),
                     "peak_excess_mm_x16": round(float(ex[i, j] * 16), 3),
                     "increment_mm_at": {str(int(a)): round(float(m[int(a - 95)]), 2) for a in (95, 105, 110, 111, 112, 114, 118, 122, 123, 130, 136, 145, 156, 165, 166)},
                     "worst_increment_kink_deg": float(DENSE_ANGLES[k]), "worst_increment_kink_mm": round(float(d2.max()), 3),
                     "top3_kinks": [{"deg": float(DENSE_ANGLES[q + 1]), "mm": round(float(d2[q]), 3)} for q in np.argsort(-d2)[:3]],
                     "increment_max_mm": round(float(m.max()), 2), "increment_max_deg": float(DENSE_ANGLES[int(m.argmax())])})
    out["worst_vertices"] = rows
    # early outward (before 110 deg): outward = displacement vs baseline along the vertex's side
    hts_all = press_ht(np.arange(161) / 160.0)
    sgn = np.sign(rest[ids, 0])
    outward = (cur - base)[:, :, 0] * sgn[None] * 1000.0
    early = hts_all < 110.0
    eo = np.where(early[:, None], np.maximum(outward, 0), 0)
    fi, vj = np.unravel_index(eo.argmax(), eo.shape)
    out["early_outward"] = {"max_mm": round(float(eo.max()), 4), "frame": int(fi), "ht_deg": round(float(hts_all[fi]), 2),
                            "vertex": int(ids[vj]), "vertices_over_0_05mm": int((eo.max(axis=0) > 0.05).sum())}
    # does the increment exist before 110 at all (protected 95 / 110 are zero; 96..109 are free)
    pre = np.linalg.norm(dense[1:15][:, ids, :], axis=2) * 1000.0
    out["increment_96_109_max_mm"] = round(float(pre.max()), 3)
    return out


def main():
    ap = argparse.ArgumentParser()
    for a in ("--source", "--r52", "--r57", "--points52", "--points57", "--out"):
        ap.add_argument(a, required=a in ("--source", "--out"))
    a = ap.parse_args()
    with np.load(a.source) as z:
        rest = z["rest"]
    report = {"kind": "R58_TEMPORAL_HOTSPOT_LOCALISATION", "read_only": True, "model_saved": False, "approved": False,
              "ht_formula": "70 + 96 * smoothstep(t), lockout 166", "results": []}
    for tag, pts, sol in (("R52", a.points52, a.r52), ("R57", a.points57, a.r57)):
        if pts and sol:
            dense = np.load(sol)["dense_delta"]
            assert dense.shape[0] == 72, dense.shape
            report["results"].append(analyse(tag, pts, dense, rest))
    text = json.dumps(report, indent=1)
    open(a.out, "w").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
