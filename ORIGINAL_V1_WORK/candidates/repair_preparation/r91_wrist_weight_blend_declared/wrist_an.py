import json
import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
a, b = np.load(SP + r"\pl_r47.npz"), np.load(SP + r"\pl_r90.npz")
rest, bones = a["rest"], [str(x) for x in a["bones"]]
Wa, Wb = a["W"], b["W"]
B = json.load(open(SP + r"\pl_r90.json"))
extra = [p for p in B["pairs"] if tuple(p["polys"]) in {(9400, 9474), (9404, 9477), (9408, 9480)}]
pv = sorted({v for p in extra for vs in p["verts"] for v in vs})
print("pair vertices (left)", pv)
c = rest[pv].mean(axis=0)
print("rest centroid of pair vertices", np.round(c, 4), "bbox", np.round(rest[pv].min(0), 4), np.round(rest[pv].max(0), 4))
d = np.abs(Wa - Wb).max(axis=1)
left = rest[:, 0] <= 1e-8
near = np.linalg.norm(rest - c, axis=1)
for R in (0.02, 0.03, 0.04, 0.06):
    m = left & (near < R)
    print("R %.2f: vertices %d, with changed weights r47->r90: %d" % (R, m.sum(), (m & (d > 1e-6)).sum()))
m = left & (near < 0.05) & (d > 1e-6)
print("wrist-band candidates (changed r47->r90, within 5 cm):", m.sum())
for v in pv:
    top = lambda W: " ".join("%s %.2f" % (bones[i], W[v, i]) for i in np.argsort(-W[v])[:3])
    print(" v%5d r47: %-52s r90: %s" % (v, top(Wa), top(Wb)))
