import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
w = np.load(SP + r"\r92_base_dump.npz", allow_pickle=True); c = np.load(SP + r"\r92_full_dump.npz", allow_pickle=True)
rest, tris, W, E = c["rest"], c["tris"], c["W"], c["edges"]
bones = [str(b) for b in c["bones"]]
S = np.load(SP + r"\clav_region.npz")["S"]
pc = [str(p) for p in c["poses"]]; pw = [str(p) for p in w["poses"]]
i, j = pc.index("press_top"), pw.index("press_top")
Pc, Pw = c["evaluated"][i], w["evaluated"][j]
def vn(P):
    n = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]]); v = np.zeros_like(P)
    for k in range(3): np.add.at(v, tris[:, k], n)
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-18)
n = vn(Pw); D = Pc - Pw; nd = (D * n).sum(axis=1); tg = np.sqrt(np.maximum((D ** 2).sum(axis=1) - nd ** 2, 0))
print("region vertices", len(S), ": outward bulge > 1 cm: %d, > 1.5 cm: %d ; tangential slide > 1.5 cm: %d, > 2.5 cm: %d ; max bulge %.2f max slide %.2f cm" % ((nd[S] > .01).sum(), (nd[S] > .015).sum(), (tg[S] > .015).sum(), (tg[S] > .025).sum(), 100 * nd[S].max(), 100 * tg[S].max()))
# bump height of r92 vs weights-only against their own local smooth surface (umbrella Laplacian along normal)
nV = len(rest); deg = np.zeros(nV); np.add.at(deg, E[:, 0], 1); np.add.at(deg, E[:, 1], 1)
def umb(P):
    s = np.zeros_like(P); np.add.at(s, E[:, 0], P[E[:, 1]]); np.add.at(s, E[:, 1], P[E[:, 0]]); return P - s / deg[:, None]
bc = (umb(Pc) * vn(Pc)).sum(axis=1); bw = (umb(Pw) * vn(Pw)).sum(axis=1)
print("signed local bump height (umbrella offset along normal, +outward) in region: r92 max %.2f cm p99 %.2f cm | weights-only max %.2f cm p99 %.2f cm" % (100 * bc[S].max(), 100 * np.percentile(bc[S], 99), 100 * bw[S].max(), 100 * np.percentile(bw[S], 99)))
top = S[np.argsort(-bc[S])[:12]]
for v in top: print("  v%5d rest %s bump r92 %.2f cm (weights-only %.2f) bulge %.2f slide %.2f cm | %s" % (v, np.round(rest[v], 3), 100 * bc[v], 100 * bw[v], 100 * nd[v], 100 * tg[v], " ".join("%s %.2f" % (bones[b], W[v, b]) for b in np.argsort(-W[v])[:3])))