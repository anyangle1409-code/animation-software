"""R66 temporal torso smoothing for the press (Claude, 20 Oct 2026).

Owner (on R65g): "Why does the body still pulse when the arms move?"  Measured on the review video: the upper back under
the arms narrows, widens, narrows and widens again (~1.5 cm per side) between ~118 and 166 deg - identically in R52, so
it is inherited from the S7 dense increments, not from the lockout sculpt.  The first dip sits on the approved marked
pose (135.6 deg, controls 135/136, outline locked to 1 mm), so the neighbouring poses do not flow through it.

Fix, in posed space with Work's exact affine pose model (posed_s = base_s + mat_s @ blend(dense, decode(weight_s))):
  1. for every torso vertex, take its posed trajectory over the 41 main press samples;
  2. low-pass it in time: min  sum_s a_s |X_s - P_s|^2 + beta sum_s |X_{s-1} - 2 X_s + X_{s+1}|^2, with samples that use
     only fixed controls (<=110 deg, and the marked pose's 135/136) held exactly (a_s = 1e6);
  3. solve the free controls (111..134 and 137..166) per vertex, batched least squares, so the posed skin follows the
     smoothed trajectory, with a second-difference penalty over controls and a weak tie to the current values.
Controls 95..110 and 135/136 are never changed, so the early poses and the approved marked pose are untouched.
"""
import numpy as np


def free_controls():
    m = np.zeros(72, bool)
    m[16:40] = True            # 111 .. 134 deg
    m[42:72] = True            # 137 .. 166 deg
    return m


def posed(z, s, dense, lo, hi, t, vids):
    inc = (1 - t[vids])[:, None] * dense[lo[vids], vids] + t[vids][:, None] * dense[hi[vids], vids]
    return z["base"][s][vids] + np.einsum("nij,nj->ni", z["mat"][s][vids], inc)


def smooth_targets(X, fixed, beta):
    """X (S, n, 3) trajectories; fixed (S, n) bool.  Returns the time-smoothed trajectories, fixed samples kept."""
    S, n, _ = X.shape
    D2 = np.zeros((S - 2, S))
    for i in range(S - 2):
        D2[i, i:i + 3] = (1.0, -2.0, 1.0)
    R = beta * (D2.T @ D2)
    a = np.where(fixed, 1e6, 1.0).T                                   # (n, S)
    A = R[None] + a[:, :, None] * np.eye(S)[None]                     # (n, S, S)
    rhs = a[:, :, None] * X.transpose(1, 0, 2)                        # (n, S, 3)
    return np.linalg.solve(A, rhs).transpose(1, 0, 2)


def run(z, decode, out, torso_ids, beta, lam, tie, min_mm, chunk=300):
    """Return (new dense array, report).  out is not modified."""
    out = out.copy()
    free = free_controls()
    fidx = np.flatnonzero(free); nf = len(fidx); col = -np.ones(72, int); col[fidx] = np.arange(nf)
    S = 41
    maps = []
    for s in range(S):
        lo, hi, t = decode(z["weight"][s][None])
        maps.append((lo[0].astype(int), hi[0].astype(int), t[0]))
    X = np.stack([posed(z, s, out, *maps[s], torso_ids) for s in range(S)])              # (S, n, 3)
    fixed = np.stack([~free[maps[s][0][torso_ids]] & ~free[maps[s][1][torso_ids]] for s in range(S)])
    Xs = smooth_targets(X, fixed, beta)
    dev = np.linalg.norm(Xs - X, axis=2).max(axis=0)
    act = np.flatnonzero(dev > min_mm / 1000.0)
    report = {"torso_vertices": int(len(torso_ids)), "vertices_moved": int(len(act)),
              "max_temporal_correction_mm": round(float(dev.max() * 1000), 2),
              "beta": beta, "fixed_samples_per_vertex_median": int(np.median(fixed.sum(0)))}
    if not len(act):
        return out, report
    # second difference over all 72 controls; fixed controls enter as constants
    rows = []
    for k in range(1, 71):
        rows.append((k - 1, k, k + 1))
    worst_fit = 0.0
    for c0 in range(0, len(act), chunk):
        sel = act[c0:c0 + chunk]; vids = torso_ids[sel]; nA = len(vids)
        H = np.zeros((nA, 3 * nf, 3 * nf)); g = np.zeros((nA, 3 * nf))
        for s in range(S):
            lo, hi, t = maps[s]
            l_, h_, t_ = lo[vids], hi[vids], t[vids]
            coef = np.zeros((nA, nf)); fixed_inc = np.zeros((nA, 3))
            for kk, w in ((l_, 1 - t_), (h_, t_)):
                isf = free[kk]
                coef[np.flatnonzero(isf), col[kk[isf]]] += w[isf]
                o_ = np.flatnonzero(~isf)
                fixed_inc[o_] += w[o_, None] * out[kk[o_], vids[o_]]
            use = coef.any(axis=1)
            if not use.any():
                continue
            Mv = z["mat"][s][vids]
            want = Xs[s, sel] - z["base"][s][vids]
            rhs = want - np.einsum("nij,nj->ni", Mv, fixed_inc)
            MtM = np.einsum("nki,nkj->nij", Mv, Mv); Mtr = np.einsum("nki,nk->ni", Mv, rhs)
            nz = np.flatnonzero(coef.any(axis=0))
            for p in nz:
                cp = coef[:, p]
                g[:, 3 * p:3 * p + 3] += cp[:, None] * Mtr
                for q in nz:
                    cq = coef[:, q]
                    if (cp * cq).any():
                        H[:, 3 * p:3 * p + 3, 3 * q:3 * q + 3] += (cp * cq)[:, None, None] * MtM
        for ks in rows:
            crow = np.zeros(nf); cfix = np.zeros((nA, 3))
            for kk, c in zip(ks, (1.0, -2.0, 1.0)):
                if free[kk]:
                    crow[col[kk]] += c
                else:
                    cfix += c * out[kk, vids]
            if not crow.any():
                continue
            Ck = np.kron(crow[None], np.eye(3))
            H += lam * (Ck.T @ Ck)[None]
            g += -lam * np.einsum("ik,ni->nk", Ck, cfix)
        H += tie * np.eye(3 * nf)[None]
        g += tie * out[fidx][:, vids].transpose(1, 0, 2).reshape(nA, -1)
        x = np.linalg.solve(H, g[..., None])[..., 0]
        out[fidx[:, None], vids[None, :]] = x.reshape(nA, nf, 3).transpose(1, 0, 2)
        for s in range(S):
            if (~fixed[s, sel]).any():
                e = np.linalg.norm(posed(z, s, out, *maps[s], vids) - Xs[s, sel], axis=1)
                worst_fit = max(worst_fit, float(e[~fixed[s, sel]].max()))
    report["posed_fit_max_error_mm"] = round(worst_fit * 1000, 2)
    X2 = np.stack([posed(z, s, out, *maps[s], torso_ids) for s in range(S)])
    acc0 = np.linalg.norm(X[2:] - 2 * X[1:-1] + X[:-2], axis=2).max()
    acc1 = np.linalg.norm(X2[2:] - 2 * X2[1:-1] + X2[:-2], axis=2).max()
    report["torso_max_second_difference_mm"] = {"before": round(float(acc0 * 1000), 2), "after": round(float(acc1 * 1000), 2)}
    return out, report
