import json
import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
d1 = np.load(SP + r"\r81_arc_dump.npz", allow_pickle=True)
d0 = np.load(SP + r"\r68_arc_dump.npz", allow_pickle=True)
rest, E, reg, mats, poses = d1["rest"], d1["edges"], d1["region"], d1["mats"].astype(np.float64), [str(p) for p in d1["poses"]]
rn = [str(x) for x in d1["region_names"]]
W1, W0 = d1["W"], d0["W"]
z = json.load(open(r"C:\Users\Mark\Documents\animation-software\repo\ORIGINAL_V1_WORK\candidates\repair_preparation\r81_dilated_weight_smoothing_declared\weight_smoothing_zone_declared_before_edit.json"))
zone = np.zeros(len(rest), bool)
zone[z["left_owned_vertex_ids"]] = True
zone[z["mirror_of_strict_left_vertex_ids"]] = True
print("zone z range", rest[zone, 2].min(), rest[zone, 2].max(), "n", zone.sum())
R1 = np.c_[rest, np.ones(len(rest))]
r0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)


def evalw(W, p):
    M = np.einsum("vb,bij->vij", W, mats[p])
    return np.einsum("vij,vj->vi", M, R1)[:, :3]


print("check vs dump", abs(evalw(W1, 23) - d1["evaluated"][23]).max())
final = [i for i, p in enumerate(poses) if "@" not in p]
KEY = [("squat_bottom", "arm"), ("squat_bottom", "shoulder"), ("press_bottom", "torso"), ("press_top", "arm"), ("pullup_hang", "arm"), ("pullup_top", "torso"), ("press_top_rhythm", "arm")]


def report(W, label):
    out = []
    for pn, rg in KEY:
        i = poses.index(pn)
        P = evalw(W, i)
        r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / r0
        k = rn.index(rg)
        sel = (reg[E[:, 0]] == k) & (reg[E[:, 1]] == k)
        out.append("%s/%s %.3f" % (pn[:9], rg[:3], r[sel].min()))
    print("%-12s" % label, " | ".join(out))


report(W0, "r68")
report(W1, "r81 smooth")
for zc in (1.40, 1.43, 1.46, 1.49):
    W = W1.copy()
    m = zone & (rest[:, 2] < zc)
    W[m] = W0[m]
    report(W, "revert z<%.2f" % zc)

C = np.array([[0.174, 0.07, 1.389], [0.178, 0.065, 1.369], [0.151, -0.051, 1.442], [0.144, -0.062, 1.442]])
C = np.vstack([C, C * [-1, 1, 1]])
dist = np.min(np.linalg.norm(rest[:, None, :] - C[None], axis=2), axis=1)
for rad in (0.02, 0.03, 0.04, 0.05, 0.07):
    W = W1.copy()
    m = zone & (dist < rad)
    W[m] = W0[m]
    report(W, "local r=%.2f n=%d" % (rad, m.sum()))
