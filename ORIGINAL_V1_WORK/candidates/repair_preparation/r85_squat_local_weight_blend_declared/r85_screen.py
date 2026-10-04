import json
import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
REPO = r"C:\Users\Mark\Documents\animation-software\repo"
d1 = np.load(SP + r"\r81_arc_dump.npz", allow_pickle=True)
d0 = np.load(SP + r"\r68_arc_dump.npz", allow_pickle=True)
rest, E, reg, mats, poses = d1["rest"], d1["edges"], d1["region"], d1["mats"].astype(np.float64), [str(p) for p in d1["poses"]]
rn = [str(x) for x in d1["region_names"]]
W1, W0 = d1["W"], d0["W"]
dec = json.load(open(REPO + r"\ORIGINAL_V1_WORK\candidates\repair_preparation\r85_squat_local_weight_blend_declared\squat_subzone_declared_before_edit.json"))
ids = np.array(dec["vertex_ids"])
C = np.array(dec["centres_m"])
R = dec["radius_m"]
dist = np.min(np.linalg.norm(rest[:, None, :] - C[None], axis=2), axis=1)
R1 = np.c_[rest, np.ones(len(rest))]
r0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
final = [i for i, p in enumerate(poses) if "@" not in p]


def ev(W, p):
    return np.einsum("vij,vj->vi", np.einsum("vb,bij->vij", W, mats[p]), R1)[:, :3]


def stats(W):
    out = {}
    for i in final:
        P = ev(W, i)
        r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / r0
        for k, rg in enumerate(rn):
            sel = (reg[E[:, 0]] == k) & (reg[E[:, 1]] == k)
            if sel.any():
                out[(poses[i], rg)] = (r[sel].min(), r[sel].max())
    return out


def top4(W):
    W = W.copy()
    idx = np.argsort(-W, axis=1)[:, 4:]
    np.put_along_axis(W, idx, 0, axis=1)
    return W / W.sum(1, keepdims=True)


base = stats(W1)
print("%-26s %s" % ("variant", "squat arm / squat sho | worst min drop vs r83 | worst max rise vs r83 | #min drops>0.02"))
for a in (0.0, 0.25, 0.5, 0.75, 1.0):
    for fall in ("smooth",):
        t = np.clip(dist / R, 0, 1)
        alpha = a * (1 - (3 * t ** 2 - 2 * t ** 3))
        alpha[~np.isin(np.arange(len(rest)), ids)] = 0
        W = top4(W1 + alpha[:, None] * (W0 - W1))
        s = stats(W)
        drops = [(k, base[k][0] - s[k][0]) for k in s]
        rises = [(k, s[k][1] - base[k][1]) for k in s]
        wd = max(drops, key=lambda x: x[1]); wr = max(rises, key=lambda x: x[1])
        nd = sum(1 for k, v in drops if v > 0.02)
        print("a=%.2f %-18s %.3f / %.3f | %s %.3f | %s %.3f | %d" % (a, fall, s[("squat_bottom", "arm")][0], s[("squat_bottom", "shoulder")][0], wd[0], wd[1], wr[0], wr[1], nd))
        np.save(SP + r"\r85_W_a%.2f.npy" % a, W)
