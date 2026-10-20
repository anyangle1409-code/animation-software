"""R58 feasibility bound: can ANY S7-only dense increment keep the R47 marked pose and pass the 0.5 mm motion guard?

For each of the worst posterior vertices (by R52 excess) and each coordinate, solve a small linear program over the 72
one-degree S7 controls (95..166 deg):

  minimise   max over press frames |second difference of the increment along the 161-frame press|
  subject to increment(95) = increment(110) = increment(166) = 0           (protected controls, unchanged)
             increment(135.625 deg) = R52's value there                    (the owner-approved R47 marked pose, t = 0.625)
             outward component <= 0.05 mm before 110 deg                   (early-outward guard)
             |component| <= 45 mm                                          (material cap)

The frame displacement is approximated by the rest-space increment interpolated linearly between controls (as installed),
ignoring the bone rotation that also acts on it, and the baseline (R41) acceleration is taken as zero.  So the result is
an indicative LOWER BOUND on the extra frame acceleration any S7-only edit must add, x16 for the guard's scale (0.5 mm).
If it is above 0.5 mm the guards conflict for S7-only edits, and the next step is an owner scope decision, not another
S7 study.  Read-only; nothing is fitted into the model.
  python3 feasibility_r58_lower_bound.py --source source.npz --r52 solved.npz --points r52_points.npz --out bound.json
"""
import argparse
import json

import numpy as np
from scipy.optimize import linprog

ANG = np.arange(95.0, 167.0)                     # control k <-> 95 + k deg
PROTECTED = (0, 15, 71)                          # 95, 110, 166
MARKED_T = 0.625


def ht_of(t):
    k = np.clip(t, 0, 1)
    return 70.0 + 96.0 * k * k * (3 - 2 * k)


def interp_matrix(hts):
    """rows: angles, cols: 72 controls; linear interpolation, zero below 95 (ghost) and held at 166."""
    M = np.zeros((len(hts), 72))
    for r, h in enumerate(hts):
        if h <= 95.0:
            continue
        if h >= 166.0:
            M[r, 71] = 1.0
            continue
        k = int(np.floor(h - 95.0)); f = h - 95.0 - k
        M[r, k] += 1 - f; M[r, k + 1] += f
    return M


def solve(target, outward_sign, coord, A2, M_mark, early_rows_M):
    # variables: 72 control values (m) + z (bound on |acc|); minimise z
    n = 72
    c = np.zeros(n + 1); c[-1] = 1.0
    rows, rhs = [], []
    for s in (1, -1):                                # +-A2 x - z <= 0
        rows.append(np.hstack([s * A2, -np.ones((len(A2), 1))])); rhs.append(np.zeros(len(A2)))
    if coord == 0 and len(early_rows_M):            # outward (x * side sign) <= 0.05 mm before 110 deg
        rows.append(np.hstack([outward_sign * early_rows_M, np.zeros((len(early_rows_M), 1))])); rhs.append(np.full(len(early_rows_M), 0.05e-3))
    A_ub = np.vstack(rows); b_ub = np.concatenate(rhs)
    A_eq = [np.hstack([M_mark, [0.0]])]; b_eq = [target]
    for p in PROTECTED:
        e = np.zeros(n + 1); e[p] = 1.0; A_eq.append(e); b_eq.append(0.0)
    bounds = [(-0.045, 0.045)] * n + [(0, None)]
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=np.array(A_eq), b_eq=np.array(b_eq), bounds=bounds, method="highs")
    return res.fun if res.success else None


def main():
    ap = argparse.ArgumentParser()
    for a in ("--source", "--r52", "--points", "--out"):
        ap.add_argument(a, required=True)
    ap.add_argument("--top", type=int, default=40)
    a = ap.parse_args()
    with np.load(a.source) as z:
        rest = z["rest"]
    dense = np.load(a.r52)["dense_delta"]
    with np.load(a.points) as z:
        base, cur, ids = z["baseline"], z["current"], z["back_vertex_ids"]
    ex = np.linalg.norm(np.diff(cur, n=2, axis=0), axis=2) - np.linalg.norm(np.diff(base, n=2, axis=0), axis=2)
    worst = ids[np.argsort(-ex.max(axis=0))[:a.top]]
    hts = ht_of(np.arange(161) / 160.0)
    M = interp_matrix(hts)                           # 161 x 72
    A2 = np.diff(M, n=2, axis=0)                     # 159 x 72: frame second difference
    M_mark = interp_matrix([ht_of(MARKED_T)])[0]
    early_M = M[hts < 110.0]
    rows = []
    for v in worst:
        target = M_mark @ dense[:, v, :]             # R52 increment at the marked pose (3,)
        side = 1.0 if rest[v, 0] > 0 else -1.0
        bounds = [solve(target[c], side, c, A2, M_mark, early_M) for c in range(3)]
        if any(b is None for b in bounds):
            rows.append({"vertex": int(v), "infeasible": True}); continue
        lb = float(np.sqrt(sum(b * b for b in bounds)) * 1000 * 16)      # vector bound, mm, x16 guard scale
        r52 = float(np.abs(A2 @ dense[:, v, :]).max(axis=0).max() * 1000 * 16)
        rows.append({"vertex": int(v), "marked_increment_mm": round(float(np.linalg.norm(target) * 1000), 2),
                     "lower_bound_mm_x16": round(lb, 3), "r52_profile_mm_x16": round(r52, 3)})
    ok = [r for r in rows if not r.get("infeasible")]
    report = {"kind": "R58_S7_ONLY_FEASIBILITY_BOUND", "read_only": True, "model_saved": False, "approved": False,
              "guard_mm_x16": 0.5, "vertices": len(rows), "infeasible": sum(1 for r in rows if r.get("infeasible")),
              "max_lower_bound_mm_x16": max((r["lower_bound_mm_x16"] for r in ok), default=None),
              "vertices_whose_bound_exceeds_guard": sum(1 for r in ok if r["lower_bound_mm_x16"] > 0.5),
              "approximation": "rest-space increment, linear between controls, bone rotation and R41 baseline acceleration ignored",
              "rows": rows}
    text = json.dumps(report, indent=1)
    open(a.out, "w").write(text + "\n")
    print("R58_FEASIBILITY_SUMMARY", json.dumps({k: report[k] for k in ("vertices", "infeasible", "max_lower_bound_mm_x16", "vertices_whose_bound_exceeds_guard")}))
    for r in sorted(ok, key=lambda r: -r["lower_bound_mm_x16"])[:12]:
        print("R58_FEASIBILITY_ROW", json.dumps(r))


if __name__ == "__main__":
    main()
