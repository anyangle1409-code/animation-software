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


ANGLES_ALL = np.arange(95.0, 167.0)


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
    ap.add_argument("--variant", default="a", choices=("a", "b", "c", "d"))
    ap.add_argument("--hold-from", type=float, default=145.0, help="R61 (variant d): hold the fill from this elevation to lockout")
    ap.add_argument("--trap-mm", type=float, default=0.0, help="R62: upper-trapezius bunching peak, mm (0 = off)")
    ap.add_argument("--trap-region", default=str(Path(__file__).resolve().parents[1] / "shoulder_r61" / "r62_upper_trap_region.npz"))
    ap.add_argument("--trap-from", type=float, default=136.0)
    ap.add_argument("--trap-full", type=float, default=160.0)
    ap.add_argument("--fidelity", type=float, default=1.0, help="R60 (variant c): weight of staying on R52 per frame vs smoothness")
    ap.add_argument("--envelope-mm", type=float, default=2.0)
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
    if a.variant == "d":
        # R61 (owner, on R60 at 156 deg: the arm-into-body flow turns into a dip from ~148 deg to the top; "finish the
        # press first"; owner wants the high range corrected): the 166 deg control was a protected zero holding the
        # pre-R47 lockout shape, so the R47 fill had to drain away after ~148 deg.  R61 releases control 166 (owner's
        # go-ahead, 20 Oct) for every vertex already allowed at 165 deg, and makes the fidelity target HOLD each vertex's
        # R52 value at --hold-from deg from there to lockout instead of draining.  Then the R60 smoothing (variant c).
        mask = mask.copy()
        mask[71] = mask[70]
        R52f_hold = np.einsum("fk,knj->fnj", M, old)
        hold_ix = int(np.argmin(np.abs(hts - a.hold_from)))
        late = hts >= a.hold_from
        R52f_hold[late] = R52f_hold[hold_ix]
        a.variant = "c"
        a._r61 = True
    if a.variant == "c":
        # R60 (owner, on R59: "something looks wrong" - crumpled skin behind the armpit at 145-156 deg): R59 REPLACED
        # each vertex's R52 increment by one fixed smooth shape scaled to the marked pose, so after 136 deg it no longer
        # followed R52 (whose late values keep the skin apart) and vertices with no marked-pose increment lost their
        # correction entirely.  R60 SMOOTHS R52 instead: per vertex and coordinate, minimise
        #     |A2 m|^2 + fidelity * s^2 * |M m - M m52|^2        (s = typical frame-acceleration-to-value scale)
        # with the marked pose held exactly, protected / masked controls zero and every control up to 110 deg zero.
        # Linear: one solve per permission pattern, applied to every vertex sharing it.
        free_all = mask & ~early_ctrl[:, None]
        R52f = R52f_hold if getattr(a, "_r61", False) else np.einsum("fk,knj->fnj", M, old)
        s2 = (np.linalg.norm(A2, 2) / np.linalg.norm(M, 2)) ** 2
        lam = a.fidelity * s2
        H = Q + lam * (M.T @ M)
        pats = {}
        for v in range(old.shape[1]):
            if not free_all[:, v].any():
                continue
            pats.setdefault(free_all[:, v].tobytes(), []).append(v)
        for key, vs in pats.items():
            F = np.flatnonzero(np.frombuffer(key, dtype=bool))
            HF = H[np.ix_(F, F)]; cF = c_mark[F]
            vs = np.array(vs)
            rhs = lam * (M[:, F].T @ R52f[:, vs, :].reshape(161, -1))      # (|F|, nv*3)
            if not np.any(cF):
                m = np.linalg.solve(HF, rhs)                                  # marked pose not in this pattern
            else:
                Hinv_c = np.linalg.solve(HF, cF); Hinv_r = np.linalg.solve(HF, rhs)
                tgt = target[vs].reshape(-1)
                mu = (tgt - cF @ Hinv_r) / (cF @ Hinv_c)
                m = Hinv_r + np.outer(Hinv_c, mu)
            out[np.ix_(F, vs)] = m.reshape(len(F), len(vs), 3)
        cache = pats
    if a.variant == "b":
        # R59b: (1) every control up to 110 deg is zero for every coordinate (R59 rose early on the free 96..109 controls:
        # early outward 0.62 -> 1.55 mm); (2) at every press frame each coordinate stays inside R52's own range there,
        # widened by --envelope-mm (R59's smoother profile carried larger mid-press values: contacts 7 -> 39).
        # Minimum-acceleration least squares with those bounds, by an active-set loop of equality-constrained solves.
        delta = a.envelope_mm / 1000.0
        R52f = np.einsum("fk,knj->fnj", M, old)                    # R52 increment per frame (161, nv, 3)
        iters_hist = []
        for v in np.flatnonzero(np.abs(target).sum(axis=1) > 0):
            for c in range(3):
                free = mask[:, v] & ~early_ctrl
                F = np.flatnonzero(free)
                if not np.any(c_mark[F]):
                    unreachable += 1
                    continue
                lo = np.minimum(R52f[:, v, c], 0) - delta; hi = np.maximum(R52f[:, v, c], 0) + delta
                QF = Q[np.ix_(F, F)]; MF = M[:, F]
                rows = [c_mark[F]]; vals = [target[v, c]]; active = {}
                for it in range(25):
                    C = np.array(rows + [MF[f] for f in active]); d = np.array(vals + list(active.values()))
                    keep = np.abs(C).sum(axis=1) > 0
                    C, d = C[keep], d[keep]
                    Y = np.linalg.solve(QF, C.T)
                    lam = np.linalg.lstsq(C @ Y, d, rcond=None)[0]
                    m = Y @ lam
                    x = MF @ m
                    bad = np.flatnonzero((x > hi + 1e-7) | (x < lo - 1e-7))
                    bad = [f for f in bad if f not in active]
                    if not bad:
                        break
                    for f in bad:
                        active[f] = float(np.clip(x[f], lo[f], hi[f]))
                iters_hist.append(it)
                out[F, v, c] = m
    for v in (np.flatnonzero(np.abs(target).sum(axis=1) > 0) if a.variant == "a" else []):
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
    trap_info = None
    scope_ok = not np.any(out[~mask])          # the S7 increments stay inside the (R61) permission, checked before R62
    if a.trap_mm > 0:
        # R62 (owner, 20 Oct: "there should be muscle bunching at the shoulder next to the neck in the higher position";
        # sources: the upper trapezius is an upward rotator of the scapula and is strongly active in the overhead press,
        # and the scapula rotates up ~48-61 deg at 150 deg of elevation): with the arms high the upper trapezius is short
        # and contracted, so it bulges between the neck and the acromion.  Add an outward (rest-normal) swell over the
        # model's own muscle_trap_l/r helper region, scaled by that weight, faded in by elevation (smoothstep from, default 136 deg so the approved marked pose is untouched,
        # --trap-from to --trap-full deg).  Added on top of the R61 increments; marked pose (135.6 deg) moves only by
        # the small fade-in amount there, which the outline gate measures.
        tz = np.load(a.trap_region)
        ids = tz["vertex_ids"].astype(int); w = tz["trap_weight"].astype(float); nrm = tz["rest_normal"].astype(float)
        dpos = float(np.abs(tz["rest_position"] - rest[ids]).max() * 1000)
        assert dpos < 1.0, f"trap region does not match the source rest mesh ({dpos:.3f} mm)"
        k = np.clip(w / 0.35, 0, 1); k = k * k * (3 - 2 * k)
        x = np.clip((ANGLES_ALL - a.trap_from) / (a.trap_full - a.trap_from), 0, 1); g = x * x * (3 - 2 * x)
        g[[0, 15]] = 0.0
        add = (a.trap_mm / 1000.0) * g[:, None, None] * (k[:, None] * nrm)[None]
        out[:, ids, :] += add
        trap_info = {"vertices": int(len(ids)), "peak_mm": a.trap_mm, "fade_deg": [a.trap_from, a.trap_full], "region_match_mm": round(dpos, 4),
                     "added_at_marked_pose_mm": round(float(a.trap_mm * np.interp(135.625, ANGLES_ALL, g)), 3)}
    norms = np.linalg.norm(out, axis=2)
    capped = int((norms > 0.045).any(axis=0).sum())
    over = norms > 0.045
    out[over] *= (0.045 / norms[over])[:, None]
    assert scope_ok, "scope error"
    assert not np.any(out[[0, 15] if getattr(a, "_r61", False) else [0, 15, 71]]), "protected control changed"
    marked_err = float(np.abs(np.einsum("k,knj->nj", c_mark, out) - target).max() * 1000)
    acc_old = np.abs(np.einsum("fk,knj->fnj", A2, old)).max() * 1000 * 16
    acc_new = np.abs(np.einsum("fk,knj->fnj", A2, out)).max() * 1000 * 16
    early_new = float(np.maximum((M[hts < 110.0] @ out[:, :, 0]) * side[None], 0).max() * 1000)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(a.out, dense_delta=out, delta=out[SOURCE])
    metrics = {"status": "R59_IN_MEMORY_STUDY_NOT_ACCEPTED", "variant": a.variant, "envelope_mm": a.envelope_mm if a.variant == "b" else None, "fidelity": a.fidelity if a.variant == "c" else None, "r61_released_166_hold_from": (a.hold_from if getattr(a, "_r61", False) else None), "r62_upper_trap": trap_info,
               "active_set_iterations_max": (int(max(iters_hist)) if a.variant == "b" and iters_hist else None), "model_saved": False, "owner_approved": False,
               "material_scope_expanded": bool(getattr(a, "_r61", False)), "scope_change": ("release of the 166 deg S7 control requested by the owner (20 Oct); installed by Claude's R61 installer copy (scripts/shoulder_r61/claude_r61_native.py)" if getattr(a, "_r61", False) else None), "permission_patterns": len(cache),
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
