import sys
import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
S = {"wonly": np.load(SP + r"\r81_arc_dump.npz", allow_pickle=True), "r91": np.load(SP + r"\r91_full_dump.npz", allow_pickle=True), "r42": np.load(SP + r"\r42_full_dump.npz", allow_pickle=True)}
d = S["r91"]
rest, E, reg = d["rest"], d["edges"], d["region"]
rn = [str(x) for x in d["region_names"]]
bones = [str(b) for b in d["bones"]]
POSE = sys.argv[1] if len(sys.argv) > 1 else "press_top"
nV = len(rest)
deg = np.zeros(nV)
np.add.at(deg, E[:, 0], 1)
np.add.at(deg, E[:, 1], 1)
L0len = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
mel = np.zeros(nV)
np.add.at(mel, E[:, 0], L0len)
np.add.at(mel, E[:, 1], L0len)
mel /= np.maximum(deg, 1)


def lap(P):
    s = np.zeros_like(P)
    np.add.at(s, E[:, 0], P[E[:, 1]])
    np.add.at(s, E[:, 1], P[E[:, 0]])
    return P - s / np.maximum(deg, 1)[:, None]


Lr = np.linalg.norm(lap(rest), axis=1) / mel
UP = np.isin(reg, [rn.index(x) for x in ("shoulder", "torso", "neck", "arm")]) & (rest[:, 2] > 1.2) & (rest[:, 0] <= 0)
res = {}
for name, dd in S.items():
    pn = [str(p) for p in dd["poses"]]
    P = dd["evaluated"][pn.index(POSE)]
    res[name] = np.linalg.norm(lap(P), axis=1) / mel
    ex = res[name] - Lr
    print("%-6s upper-left vertices: Laplacian/edge  p99 %.2f  max %.2f   (rest p99 %.2f)  #> 0.6: %d  #> 0.9: %d" % (name, np.percentile(res[name][UP], 99), res[name][UP].max(), np.percentile(Lr[UP], 99), (res[name][UP] > 0.6).sum(), (res[name][UP] > 0.9).sum()))
r = res["r91"]
idx = np.nonzero(UP)[0]
top = idx[np.argsort(-r[idx])[:40]]
print("\nr91 top-40 curvature-spike vertices (left): rest bbox", np.round(rest[top].min(0), 3), np.round(rest[top].max(0), 3), "regions", {rn[k]: int((reg[top] == k).sum()) for k in range(len(rn)) if (reg[top] == k).any()})
for v in top[:12]:
    tb = np.argsort(-d["W"][v])[:3]
    print("  v%5d rest %s lap r91 %.2f wonly %.2f r42 %.2f rest %.2f | %s" % (v, np.round(rest[v], 3), r[v], res["wonly"][v], res["r42"][v], Lr[v], " ".join("%s %.2f" % (bones[b], d["W"][v, b]) for b in tb)))
np.savez(SP + r"\axl_lap_%s.npz" % POSE, top=top)
