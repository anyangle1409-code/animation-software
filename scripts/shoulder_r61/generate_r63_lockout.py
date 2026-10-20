"""R63 unsaved press candidate: posed-space lockout sculpt for 146-166 deg (Claude, 20 Oct 2026).

Owner, on R60/R61 at 156 deg: from ~148 deg to the top the arm stops flowing into the body and a dip appears under the
arm; R61 (holding the REST-space fill to lockout) pushed skin into the arm (contacts 7 -> 165).  Owner: "go ahead with the
lockout sculpt" (20 Oct).

Work's R52 data gives, for every recorded press pose s, the posed skin as an exact affine function of the 72 one-degree S7
controls:  posed_s = base_s + mat_s @ blend(dense, decode(weight_s))  (verified natively to 0.01 mm by the gates).  So the
lockout shape is designed IN THE POSED POSE and solved back:

  1. start from the R62b candidate (R60 smoothing + 15 mm upper-trapezius bunching);
  2. for each press sample with elevation >= --from, compute the posed skin; per side, seen from behind (u = outward, z = up),
     fit a straight line to the outer edge of the raised upper arm and push the side of the torso below the armpit out to
     it (gain, fading over --depth below the armpit and with distance in from the torso outline, Gaussian --sigma), the
     R29 LAT_WEB construction that matched the owner's reference; ramp in with elevation from --from to --full;
  3. smooth that push over the mesh;
  4. per affected vertex, least-squares solve the controls 146..166 so the posed skin at those samples reaches the target,
     with a temporal second-difference penalty (continuity with 144/145 kept) and a weak tie to the start values.

Controls <= 145 (incl. the approved marked pose) are untouched.  95/110 stay zero; 166 is released (owner, 20 Oct).
Nothing is saved to a .blend.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

K0, K1 = 51, 71                      # controls 146 .. 166 (index = deg - 95)


def ht_of(t):
    k = np.clip(t, 0, 1)
    return 70.0 + 96.0 * k * k * (3 - 2 * k)


def smoothstep(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def neighbours(faces, nv):
    nb = [set() for _ in range(nv)]
    for a, b, c in faces:
        nb[a].update((b, c)); nb[b].update((a, c)); nb[c].update((a, b))
    return [np.fromiter(s, int) for s in nb]


def lat_fill(P, armw, wholearm, gain, depth, sigma, maxpush):
    D = np.zeros_like(P)
    info = {}
    for k, side in enumerate("lr"):
        sg = -1.0 if side == "l" else 1.0
        u = sg * P[:, 0]; z = P[:, 2]
        arm = armw[k] >= 0.5
        if arm.sum() < 50:
            continue
        za0, za1 = np.percentile(z[arm], [5, 95])
        zz, uu = [], []
        for z0 in np.arange(za0 + 0.03, za1 - 0.03, 0.01):
            m = arm & (z >= z0) & (z < z0 + 0.01)
            if m.sum() > 2:
                zz.append(z0 + 0.005); uu.append(u[m].max())
        if len(zz) < 4:
            continue
        b, a = np.polyfit(zz, uu, 1)
        torso = (wholearm[k] < 0.3) & (u > 0.03)
        pushes = []
        for z0 in np.arange(za0 - depth, za0 + 0.02, 0.01):
            m = np.flatnonzero(torso & (z >= z0) & (z < z0 + 0.01))
            if len(m) < 3:
                continue
            edge = u[m].max(); want = a + b * (z0 + 0.005)
            fade = smoothstep((z0 - (za0 - depth)) / (0.4 * depth))
            d = min(max(want - edge, 0.0) * gain * fade, maxpush)
            if d <= 0:
                continue
            f = np.exp(-((edge - u[m]) / sigma) ** 2)
            D[m, 0] = sg * np.maximum(sg * D[m, 0], d * f)
            pushes.append(d)
        info[side] = {"arm_edge_deg_from_vertical": round(float(np.degrees(np.arctan(abs(b)))), 1),
                      "armpit_z": round(float(za0), 3), "max_push_mm": round(float(max(pushes, default=0) * 1000), 1)}
    return D, info


def main():
    ap = argparse.ArgumentParser()
    for a in ("--r57src", "--response", "--start", "--out"):
        ap.add_argument(a, required=True)
    ap.add_argument("--arm", default=str(Path(__file__).resolve().parent / "r63_arm_weights.npz"))
    ap.add_argument("--gain", type=float, default=0.6)
    ap.add_argument("--depth", type=float, default=0.25)
    ap.add_argument("--sigma", type=float, default=0.05)
    ap.add_argument("--maxpush", type=float, default=0.04)
    ap.add_argument("--from", dest="hfrom", type=float, default=146.0)
    ap.add_argument("--full", type=float, default=152.0)
    ap.add_argument("--smooth", type=int, default=30)
    ap.add_argument("--lam", type=float, default=0.3)
    ap.add_argument("--tie", type=float, default=0.02)
    a = ap.parse_args()
    sys.path[:0] = [str(Path(a.r57src) / "scripts")]
    from original_review_r52_temporal import decode, oscillation

    z = np.load(a.response)
    rest, faces = z["rest"], z["faces"]
    nv = len(rest)
    d0 = np.load(a.start)["dense_delta"].astype(float)
    arm = np.load(a.arm)
    ci = arm["check_ids"].astype(int)
    dpos = float(np.abs(arm["check_rest"] - rest[ci]).max() * 1000)
    assert dpos < 1.0, f"arm weight file does not match the source rest mesh ({dpos:.3f} mm)"
    armw = arm["upperarm_weight"].astype(float); whole = arm["whole_arm_weight"].astype(float)
    nb = neighbours(faces, nv)

    samples = [s for s in range(41) if ht_of(s / 40) >= a.hfrom - 1.0]
    targets, maps, report_s = {}, {}, []
    for s in samples:
        lo, hi, t = decode(z["weight"][s][None])
        lo, hi, t = lo[0].astype(int), hi[0].astype(int), t[0]
        maps[s] = (lo, hi, t)
        v = np.arange(nv)
        inc = (1 - t)[:, None] * d0[lo, v] + t[:, None] * d0[hi, v]
        P = z["base"][s] + np.einsum("nij,nj->ni", z["mat"][s], inc)
        D, info = lat_fill(P, armw, whole, a.gain, a.depth, a.sigma, a.maxpush)
        ramp = smoothstep((ht_of(s / 40) - a.hfrom) / (a.full - a.hfrom))
        D *= ramp
        zone = np.flatnonzero(np.abs(D).sum(1) > 0)
        if len(zone):
            zone = np.unique(np.concatenate([zone] + [nb[i] for i in zone]))
            for _ in range(a.smooth):
                D[zone] = 0.5 * D[zone] + 0.5 * np.array([D[nb[i]].mean(0) for i in zone])
        targets[s] = (P, D)
        report_s.append({"sample": s, "ht_deg": round(float(ht_of(s / 40)), 2), "ramp": round(float(ramp), 3), "sides": info,
                         "max_target_push_mm": round(float(np.linalg.norm(D, axis=1).max() * 1000), 2)})
        print("R63_TARGET", json.dumps(report_s[-1]), flush=True)

    Dmax = np.max([np.linalg.norm(targets[s][1], axis=1) for s in samples], axis=0)
    affected = np.flatnonzero(Dmax > 0.2e-3)
    K = np.arange(K0, K1 + 1); nk = len(K); kidx = {k: i for i, k in enumerate(K)}
    # temporal second differences over controls 144..166 (144/145 fixed from the start candidate)
    span = np.arange(K0 - 2, K1 + 1)
    out = d0.copy()
    fit_err = []
    for v in affected:
        A_rows, b_rows = [], []
        for s in samples:
            lo, hi, t = maps[s]
            P, D = targets[s]
            Mv = z["mat"][s][v]                       # 3x3
            want = (P[v] + D[v]) - z["base"][s][v]    # posed-space increment wanted, = Mv @ blend
            coef = np.zeros(nk); fixed = np.zeros(3)
            for k, w in ((lo[v], 1 - t[v]), (hi[v], t[v])):
                if k in kidx:
                    coef[kidx[k]] += w
                else:
                    fixed += w * d0[k, v]
            if not coef.any():
                continue
            A_rows.append(np.kron(coef[None], Mv))    # 3 x 3nk  (x laid out control-major, xyz-minor)
            b_rows.append(want - Mv @ fixed)
        if not A_rows:
            continue
        A = np.vstack(A_rows); bvec = np.concatenate(b_rows)
        # smoothness over span, unknowns are K, 144/145 fixed
        S_rows, S_rhs = [], []
        for j in range(1, len(span) - 1):
            ks = span[j - 1:j + 2]; c = np.array([1.0, -2.0, 1.0])
            row = np.zeros((3, 3 * nk)); rhs = np.zeros(3)
            for kk, cc in zip(ks, c):
                if kk in kidx:
                    row[:, 3 * kidx[kk]:3 * kidx[kk] + 3] += cc * np.eye(3)
                else:
                    rhs -= cc * d0[kk, v]
            S_rows.append(row); S_rhs.append(rhs)
        S = np.vstack(S_rows) * np.sqrt(a.lam); srhs = np.concatenate(S_rhs) * np.sqrt(a.lam)
        T = np.sqrt(a.tie) * np.eye(3 * nk); trhs = np.sqrt(a.tie) * d0[K, v].reshape(-1)
        x, *_ = np.linalg.lstsq(np.vstack([A, S, T]), np.concatenate([bvec, srhs, trhs]), rcond=None)
        out[K, v] = x.reshape(nk, 3)
        fit_err.append(float(np.abs(A @ x - bvec).max()))
    norms = np.linalg.norm(out, axis=2)
    capped = int((norms > 0.045).any(axis=0).sum())
    over = norms > 0.045
    out[over] *= (0.045 / norms[over])[:, None]
    assert not np.any(out[[0, 15]]), "protected 95/110 control changed"
    assert np.array_equal(out[:K0], d0[:K0]), "controls <= 145 must be untouched"
    from original_review_r52_temporal import SOURCE
    np.savez_compressed(a.out, dense_delta=out, delta=out[SOURCE])
    metrics = {"status": "R63_IN_MEMORY_STUDY_NOT_ACCEPTED", "model_saved": False, "owner_approved": False,
               "scope_change": "owner-approved lockout sculpt (20 Oct): controls 146..166 re-solved in posed space; 166 released",
               "params": {k: getattr(a, k) for k in ("gain", "depth", "sigma", "maxpush", "hfrom", "full", "smooth", "lam", "tie")},
               "samples": report_s, "affected_vertices": int(len(affected)), "vertices_capped_at_45mm": capped,
               "posed_fit_max_error_mm": round(max(fit_err, default=0) * 1000, 3),
               "max_change_from_start_mm": round(float(np.linalg.norm(out - d0, axis=2).max() * 1000), 2),
               "max_adjacent_control_mm": oscillation(out)["maximum_adjacent_mm"],
               "arm_file_match_mm": round(dpos, 4)}
    Path(a.out + ".json").write_text(json.dumps(metrics, indent=2) + "\n")
    print("R63_GENERATOR", json.dumps({k: v for k, v in metrics.items() if k != "samples"}))


if __name__ == "__main__":
    main()
