"""Fit an app-safe 4-influence skin binding that reproduces the full binding's deformation (CANDIDATE; numpy only).

Why: glTF engines such as three.js play at most 4 bone influences per vertex.  On the C1 candidate 127,551 of 347,917
vertices have 5-10, and simply keeping the 4 largest (what the glTF exporter does) breaks the press lockout (7 -> 791
skin self-intersections, 8 -> 3062 folds) and the squat (0 -> 1203, 13 -> 3600): helper bones that shape the shoulder
and hip carry the small weights that get dropped.

How: per vertex, among the bones it already uses, every 4-bone subset is solved by least squares - non-negative
weights summing to 1 - so that linear blend skinning with those 4 matches the full binding's posed position over all
training poses (world deform matrices recorded by movement_trajectory_test_blender.py, V2_TRAJ_SAVE_POS=bones).  The
subset with the smallest error wins; if no 4-subset has non-negative weights, 3- and 2-subsets are tried, then the
largest 4 renormalised.  Vertices with 4 or fewer influences keep theirs exactly.

usage: python3 fit_app_binding.py <train dir> <out.npz> [--hold lunge,pulldown,...] [--report out.json]
<train dir> holds binding.npz and deform_<movement>.npy.  The held-out movements are not used to fit; the report gives
the per-movement error (max and p99 vertex error, mm, full binding vs fitted) so generalisation can be judged.
"""
import argparse
import itertools
import json
from pathlib import Path

import numpy as np


def load(train):
    z = np.load(train / "binding.npz", allow_pickle=False)
    mats = {p.stem[len("deform_"):]: np.load(p) for p in sorted(train.glob("deform_*.npy"))}
    return z, mats


def columns(X, M, bones):
    """posed position of rest points X (n,3) under each pose and bone: (n, P, 3, k) for bones (n, k)"""
    Xh = np.concatenate([X, np.ones((len(X), 1))], 1)                       # (n,4)
    Mb = M[:, bones]                                                         # (P, n, k, 3, 4)
    return np.einsum("pnkij,nj->npik", Mb, Xh)


def solve_subsets(G, h, yy, combos):
    """G (n,k,k), h (n,k); combos (c,s): constrained LS for every subset; returns err (n,c), w (n,c,s)"""
    n, c, s = len(G), len(combos), combos.shape[1]
    Gs = G[:, combos[:, :, None], combos[:, None, :]]                        # (n,c,s,s)
    hs = h[:, combos]                                                        # (n,c,s)
    K = np.zeros((n, c, s + 1, s + 1)); K[..., :s, :s] = 2 * Gs; K[..., :s, s] = 1; K[..., s, :s] = 1
    K[..., :s, :s] += np.eye(s) * 1e-12
    rhs = np.concatenate([2 * hs, np.ones((n, c, 1))], -1)
    sol = np.linalg.solve(K, rhs[..., None])[..., 0]
    w = sol[..., :s]
    err = np.einsum("ncs,ncst,nct->nc", w, Gs, w) - 2 * np.einsum("ncs,ncs->nc", w, hs) + yy[:, None]
    return err, w


def fit(z, mats, train_moves, chunk=1500):
    X = z["rest"]; n = len(X); B = len(z["bones"])
    vi, bj, w = z["vi"], z["bj"], z["w"]
    order = np.argsort(vi, kind="stable"); vi, bj, w = vi[order], bj[order], w[order]
    counts = np.bincount(vi, minlength=n); starts = np.concatenate([[0], np.cumsum(counts)[:-1]])
    M = np.concatenate([mats[m] for m in train_moves], 0)                   # (P,B,3,4)
    out_b = np.zeros((n, 4), np.int32); out_w = np.zeros((n, 4), np.float32)
    status = np.zeros(n, np.int8)                                            # 0 kept, 4/3/2 subset size, -1 fallback
    for k in range(1, int(counts.max()) + 1):
        ids = np.where(counts == k)[0]
        if not len(ids):
            continue
        bones = np.stack([bj[starts[ids] + j] for j in range(k)], 1)
        ws = np.stack([w[starts[ids] + j] for j in range(k)], 1).astype(np.float64)
        ws /= ws.sum(1, keepdims=True)
        if k <= 4:
            out_b[ids, :k] = bones; out_w[ids, :k] = ws; continue
        for c0 in range(0, len(ids), chunk):
            sl = slice(c0, c0 + chunk); ii = ids[sl]; bb = bones[sl]; ww = ws[sl]
            C = columns(X[ii], M, bb)                                        # (m,P,3,k)
            Cf = C.reshape(len(ii), -1, k)
            y = np.einsum("nqk,nk->nq", Cf, ww)
            G = np.einsum("nqk,nql->nkl", Cf, Cf); h = np.einsum("nqk,nq->nk", Cf, y); yy = np.einsum("nq,nq->n", y, y)
            done = np.zeros(len(ii), bool)
            for s in (4, 3, 2):
                combos = np.array(list(itertools.combinations(range(k), s)))
                err, wsol = solve_subsets(G, h, yy, combos)
                err = np.where((wsol >= -1e-9).all(-1), err, np.inf)
                best = err.argmin(1); ok = np.isfinite(err[np.arange(len(ii)), best]) & ~done
                for r in np.where(ok)[0]:
                    sel = combos[best[r]]; wr = np.clip(wsol[r, best[r]], 0, None); wr /= wr.sum()
                    out_b[ii[r], :s] = bb[r, sel]; out_w[ii[r], :s] = wr; status[ii[r]] = s
                done |= ok
                if done.all():
                    break
            for r in np.where(~done)[0]:
                top = np.argsort(-ww[r])[:4]; wr = ww[r, top] / ww[r, top].sum()
                out_b[ii[r], :4] = bb[r, top]; out_w[ii[r], :4] = wr; status[ii[r]] = -1
    return out_b, out_w, status


def _lbs(Xh, vi, bj, w, Mp, n):
    t = np.einsum("kij,kj->ki", Mp[bj], Xh[vi]) * w[:, None]
    return np.stack([np.bincount(vi, t[:, i], minlength=n) for i in range(3)], 1)


def evaluate(z, mats, out_b, out_w, moves):
    """per movement: full-binding vs fitted LBS vertex error (mm), max and p99 over frames and vertices"""
    X = z["rest"]; n = len(X); Xh = np.concatenate([X, np.ones((n, 1))], 1)
    vi, bj, w = z["vi"], z["bj"], z["w"].astype(np.float64)
    w = w / np.bincount(vi, w, minlength=n)[vi]                              # Blender normalises per vertex
    va = np.repeat(np.arange(n), 4); ba = out_b.ravel(); wa = out_w.ravel().astype(np.float64)
    keep = wa > 0; va, ba, wa = va[keep], ba[keep], wa[keep]
    res = {}
    for m in moves:
        e = np.stack([np.linalg.norm(_lbs(Xh, vi, bj, w, Mp, n) - _lbs(Xh, va, ba, wa, Mp, n), axis=1) * 1000
                      for Mp in mats[m]])
        res[m] = {"max_mm": round(float(e.max()), 2), "p99_mm": round(float(np.percentile(e, 99)), 3),
                  "vertices_over_2mm_worst_frame": int((e > 2).sum(1).max())}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("train"); ap.add_argument("out"); ap.add_argument("--hold", default="")
    ap.add_argument("--report", default="")
    a = ap.parse_args(); train = Path(a.train)
    z, mats = load(train)
    hold = [m for m in a.hold.split(",") if m]
    tm = [m for m in mats if m not in hold]
    out_b, out_w, status = fit(z, mats, tm)
    np.savez_compressed(a.out, bones=z["bones"], bone_idx=out_b.astype(np.int16), weights=out_w)
    rep = {"train_movements": tm, "held_out": hold, "vertices": int(len(out_b)),
           "status_counts": {str(k): int(v) for k, v in zip(*np.unique(status, return_counts=True))},
           "error_full_vs_fitted": evaluate(z, mats, out_b, out_w, list(mats))}
    if a.report:
        Path(a.report).write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
