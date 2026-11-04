"""Joint-centre estimates from a static body mesh (Meshy A-pose) and comparison with the canonical skeleton.
Mesh scaled to the canonical stature (1.856 m) for the comparison; the source file is not changed.
usage: python3 landmarks_meshy.py <mesh.npz with V (z-up, front -y)> <canonical skeleton.json> <out.json>"""
import json
import sys

import numpy as np
from scipy.spatial import ConvexHull

d = np.load(sys.argv[1]); V = d["V"].astype(float); SK = json.load(open(sys.argv[2]))["bones"]
H0 = V[:, 2].max() - V[:, 2].min(); V[:, 2] -= V[:, 2].min(); k = 1.856 / H0; V *= k
f = V[:, 2] / 1.856


def perim(P):
    if len(P) < 6:
        return np.inf
    q = P[ConvexHull(P).vertices]; return float(np.linalg.norm(q - np.roll(q, 1, 0), axis=1).sum())


def axis_profile(pts_sel, ax, c0, t_range, slab=0.004):
    """circumference + centre of slices perpendicular to axis ax through c0, t in t_range (m)"""
    out = []
    u = np.cross(ax, [0, 0, 1.0]); u = u / np.linalg.norm(u) if np.linalg.norm(u) > 1e-6 else np.array([1.0, 0, 0]); w = np.cross(ax, u)
    rel = pts_sel - c0; t = rel @ ax
    for tt in t_range:
        s = np.abs(t - tt) < slab
        if s.sum() < 8:
            out.append((tt, np.inf, None)); continue
        P2 = np.c_[rel[s] @ u, rel[s] @ w]; c = P2.mean(0)
        out.append((tt, perim(P2), c0 + ax * tt + u * c[0] + w * c[1]))
    return out


res = {"scale_to_canonical": round(k, 5), "native_stature_m": round(float(H0), 4)}
for side, sg in (("l", -1.0), ("r", 1.0)):           # canonical: left = -x
    # ---- arm: vertices well outside the trunk at A-pose heights
    arm = V[(sg * V[:, 0] > 0.24) & (f > 0.40) & (f < 0.80)]
    c = arm.mean(0); _, _, vt = np.linalg.svd(arm - c); ax = vt[0] * np.sign(vt[0] @ np.array([sg, 0, -1.0]))   # outward-down
    prof = axis_profile(arm, ax, c, np.arange(-0.35, 0.40, 0.005))
    ts = np.array([p[0] for p in prof]); pr = np.array([p[1] for p in prof])
    valid = np.isfinite(pr)
    # wrist: min circumference in the distal part before the hand widens; elbow: min between biceps and forearm bellies
    dist = (ts > -0.06) & (ts < 0.10)          # wrist: the narrowest slice between the forearm and the palm
    iw = np.argmin(np.where(valid & dist, pr, np.inf)); wrist = prof[iw][2]
    mid = valid & (ts > ts[iw] - 0.36) & (ts < ts[iw] - 0.18)
    ie = np.argmin(np.where(mid, pr, np.inf)); elbow = prof[ie][2]
    # shoulder (GH): along the arm axis, one upper-arm length (canonical ratio) proximal to the elbow is not allowed
    # (that would assume the answer); instead take the axis point level with the armpit fold top: the most proximal
    # slice whose cross-section still closes on its own (perimeter < 0.5 m)
    prox = valid & (ts < ts[ie]) & (pr < 0.50)
    ig = np.nonzero(prox)[0].min(); axilla_t = ts[ig]
    gh_est = c + ax * (axilla_t - 0.035)                  # GH ~3.5 cm proximal of the free-arm start (armpit)
    cl = [p[2] for p in prof if p[2] is not None and np.isfinite(p[1]) and p[0] <= ts[iw]]
    res[f"arm_{side}_centerline"] = [np.round(q, 4).tolist() for q in cl]
    res[f"arm_{side}"] = {"axis_deg_from_vertical": round(float(np.degrees(np.arccos(-ax[2]))), 1),
                          "wrist": np.round(wrist, 4).tolist(), "elbow": np.round(elbow, 4).tolist(), "gh_est": np.round(gh_est, 4).tolist(),
                          "wrist_circ_cm": round(pr[iw] * 100, 1), "elbow_circ_cm": round(pr[ie] * 100, 1),
                          "forearm_len_m": round(float(np.linalg.norm(wrist - elbow)), 4), "upperarm_len_est_m": round(float(np.linalg.norm(elbow - gh_est)), 4)}
    # ---- leg: section centres at fixed heights; knee = min circumference 0.24-0.32 H; ankle = min 0.03-0.08 H
    leg = V[(sg * V[:, 0] > 0.0) & (f < 0.46)]
    cent = {}
    for fr in np.arange(0.02, 0.46, 0.005):
        s = np.abs(leg[:, 2] / 1.856 - fr) < 0.002
        cent[round(fr, 3)] = (perim(leg[s, :2]), leg[s].mean(0) if s.sum() > 8 else None)
    knee_f = min((fr for fr in cent if 0.24 <= fr <= 0.32), key=lambda fr: cent[fr][0])
    ank_f = min((fr for fr in cent if 0.035 <= fr <= 0.08), key=lambda fr: cent[fr][0])
    crotch = V[(np.abs(V[:, 0]) < 0.01) & (f > 0.38) & (f < 0.55)][:, 2].min()
    def centre_at(z):
        s_ = (sg * V[:, 0] > 0.0) & (np.abs(V[:, 2] - z) < 0.003) & (np.abs(V[:, 0]) < 0.30)
        return V[s_].mean(0)
    res[f"leg_{side}_at_canonical"] = {"knee": np.round(centre_at(0.515), 4).tolist(), "ankle": np.round(centre_at(0.085), 4).tolist()}
    res[f"leg_{side}"] = {"knee_f": knee_f, "knee": np.round(cent[knee_f][1], 4).tolist(), "ankle_f": ank_f,
                          "ankle": np.round(cent[ank_f][1], 4).tolist(), "knee_circ_cm": round(cent[knee_f][0] * 100, 1),
                          "shin_len_m": round(float(np.linalg.norm(cent[knee_f][1] - cent[ank_f][1])), 4),
                          "crotch_z": round(float(crotch), 4)}
B = lambda n, e="head": np.array(SK[n][e])
canon = {"gh_l": B("upperarm_l"), "elbow_l": B("forearm_l"), "wrist_l": B("hand_l"), "hip_l": B("thigh_l"), "knee_l": B("shin_l"),
         "ankle_l": B("foot_l")}
res["canonical"] = {k_: np.round(v, 4).tolist() for k_, v in canon.items()}
res["canonical_lengths_m"] = {"upperarm": round(float(np.linalg.norm(canon["elbow_l"] - canon["gh_l"])), 4),
                              "forearm": round(float(np.linalg.norm(canon["wrist_l"] - canon["elbow_l"])), 4),
                              "thigh": round(float(np.linalg.norm(canon["knee_l"] - canon["hip_l"])), 4),
                              "shin": round(float(np.linalg.norm(canon["ankle_l"] - canon["knee_l"])), 4),
                              "gh_spacing": round(float(2 * abs(canon["gh_l"][0])), 4)}
ml = res["leg_l"]; ma = res["arm_l"]
res["meshy_lengths_m"] = {"upperarm_est": ma["upperarm_len_est_m"], "forearm": ma["forearm_len_m"], "shin": ml["shin_len_m"],
                          "gh_spacing_est": round(abs(res["arm_l"]["gh_est"][0]) + abs(res["arm_r"]["gh_est"][0]), 4),
                          "knee_z": ml["knee"][2], "ankle_z": ml["ankle"][2], "canonical_knee_z": canon["knee_l"][2],
                          "canonical_ankle_z": canon["ankle_l"][2], "crotch_z": ml["crotch_z"]}
json.dump(res, open(sys.argv[3], "w"), indent=1)
print(json.dumps({k_: res[k_] for k_ in ("scale_to_canonical", "canonical_lengths_m", "meshy_lengths_m")}, indent=1))
print("ARM", res["arm_l"]["axis_deg_from_vertical"], res["arm_r"]["axis_deg_from_vertical"])
