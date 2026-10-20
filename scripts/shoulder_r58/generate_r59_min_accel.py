"""R59 unsaved S7-only candidate: minimum-acceleration timing of the R52 dense increments (Claude, 20 Oct 2026).

R58 showed the R52 motion excess is spread over 95-156 deg because each posterior vertex's dense S7 increment is rough at
1-degree resolution, and that no S7-only profile holding the R47 marked pose can reach the 0.5 mm guard (bound ~1.26 mm).
R59 asks how close the SMOOTHEST profile gets, within the existing permission and without touching the outline:

  for every vertex v and coordinate c, the 72 control values m minimise  sum over the 161 press frames of
  (second difference of the interpolated increment)^2,  subject to
    m[k] = 0 wherever allowed_dense(src)[k, v] is False   (the unchanged R47/R52 per-control permission, incl. 95/110/166)
    increment(135.625 deg) = R52's value                  (the R47 marked pose, t = 0.625, held exactly)
    x-component of controls up to 110 deg = 0              (early-outward guard; applied only where R52 moved outward early)
  The solution is target * Q_FF^-1 c_F / (c_F' Q_FF^-1 c_F): one shape per permission pattern, scaled by the target, so
  spatially smooth targets give spatially smooth profiles.  Material cap 45 mm checked (clipped and reported if exceeded).

Nothing is saved to a .blend; the candidate is the same npz form R57 used (dense_delta, delta = dense_delta[SOURCE]).
  python3 generate_r59_min_accel.py --r57src <R57 checkout> --response source.npz --solution solved.npz --out candidate.npz
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np


def ht_of(t):
    k = np.clip(t, 0, 1)
    return 70.0 + 96.0 * k * k * (3 - 2 * k)


def interp_matrix(hts):
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


def main():
    ap = argparse.ArgumentParser()
    for a in ("--r57src", "--response", "--solution", "--out"):
        ap.add_argument(a, required=True)
    a = ap.parse_args()
    sys.path[:0] = [str(Path(a.r57src) / "scripts"), str(Path(a.r57src) / "scripts" / "anatomy_fit")]
    from original_review_r52_projection import allowed_dense
    from original_review_r52_temporal import SOURCE, oscillation

    with np.load(a.response) as src, np.load(a.solution) as sol:
        rest = src["rest"]; old = sol["dense_delta"].astype(float)
        mask = np.asarray(allowed_dense(src), bool)
    assert old.shape[0] == 72 and mask.shape == old.shape[:2], (old.shape, mask.shape)
    assert not np.any(old[~mask]), "R52 input violates its own permission mask"
    hts = ht_of(np.arange(161) / 160.0)
    M = interp_matrix(hts)
    A2 = np.diff(M, n=2, axis=0)
    Q = A2.T @ A2 + 1e-12 * np.eye(72)
    c_mark = interp_matrix([ht_of(0.625)])[0]
    early_ctrl = np.arange(72) <= 15                       # controls 95..110: the only ones active before 110 deg
    target = np.einsum("k,knj->nj", c_mark, old)           # R52 increment at the marked pose, (nv, 3)
    side = np.where(rest[:, 0] > 0, 1.0, -1.0)
    early_out = ((M[hts < 110.0] @ old[:, :, 0]) * side[None] > 0.05e-3).any(axis=0)   # vertices R52 moves outward early

    out = np.zeros_like(old)
    cache = {}
    unreachable = 0
    for v in np.flatnonzero(np.abs(target).sum(axis=1) > 0):
        for c in range(3):
            free = mask[:, v].copy()
            if c == 0 and early_out[v]:
                free &= ~early_ctrl
            key = free.tobytes()
            if key not in cache:
                F = np.flatnonzero(free)
                cF = c_mark[F]
                if not np.any(cF):
                    cache[key] = None
                else:
                    y = np.linalg.solve(Q[np.ix_(F, F)], cF)
                    shape = np.zeros(72); shape[F] = y / (cF @ y)
                    cache[key] = shape
            shape = cache[key]
            if shape is None:
                unreachable += 1
                continue
            out[:, v, c] = target[v, c] * shape
    norms = np.linalg.norm(out, axis=2)
    capped = int((norms > 0.045).any(axis=0).sum())
    over = norms > 0.045
    out[over] *= (0.045 / norms[over])[:, None]
    assert not np.any(out[~mask]), "scope error"
    assert not np.any(out[[0, 15, 71]]), "protected control changed"
    marked_err = float(np.abs(np.einsum("k,knj->nj", c_mark, out) - target).max() * 1000)
    acc_old = np.abs(np.einsum("fk,knj->fnj", A2, old)).max() * 1000 * 16
    acc_new = np.abs(np.einsum("fk,knj->fnj", A2, out)).max() * 1000 * 16
    early_new = float(np.maximum((M[hts < 110.0] @ out[:, :, 0]) * side[None], 0).max() * 1000)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(a.out, dense_delta=out, delta=out[SOURCE])
    metrics = {"status": "R59_IN_MEMORY_STUDY_NOT_ACCEPTED", "model_saved": False, "owner_approved": False,
               "material_scope_expanded": False, "permission_patterns": len(cache),
               "unreachable_vertex_coords_kept_zero": unreachable, "vertices_capped_at_45mm": capped,
               "marked_pose_increment_max_error_mm": round(marked_err, 6),
               "rest_space_profile_accel_mm_x16": {"r52": round(float(acc_old), 3), "r59": round(float(acc_new), 3)},
               "rest_space_early_outward_mm": round(early_new, 4),
               "vertices_with_early_outward_clamped": int(early_out.sum()),
               "max_adjacent_control_mm": {"r52": oscillation(old)["maximum_adjacent_mm"], "r59": oscillation(out)["maximum_adjacent_mm"]},
               "note": "rest-space figures are indicative; the native 161-pose, 83-pose, benchmark and render gates decide"}
    Path(a.out + ".json").write_text(json.dumps(metrics, indent=2) + "\n")
    print("R59_GENERATOR", json.dumps(metrics))


if __name__ == "__main__":
    main()
