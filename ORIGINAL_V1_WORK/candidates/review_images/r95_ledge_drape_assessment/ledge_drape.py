import json
import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
S = {"weights-only": np.load(SP + r"\r92_base_dump.npz", allow_pickle=True), "r93": np.load(SP + r"\r93_scap_dump_drv.npz", allow_pickle=True),
     "r95": np.load(SP + r"\r95_full_dump.npz", allow_pickle=True), "P3B1(r42)": np.load(SP + r"\r42_full_dump.npz", allow_pickle=True)}
d = S["r95"]
rest, tris, reg, E, W = d["rest"], d["tris"], d["region"], d["edges"], d["W"]
rn = [str(x) for x in d["region_names"]]; bones = [str(b) for b in d["bones"]]
nV = len(rest)
# triangle adjacency
ed = {}
for t, (a, b, c) in enumerate(tris):
    for u, v in ((a, b), (b, c), (c, a)):
        ed.setdefault((min(u, v), max(u, v)), []).append(t)
keys = [k for k, v in ed.items() if len(v) == 2]
pairs = np.array([ed[k] for k in keys])


def fn(P):
    n = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]]); l = np.linalg.norm(n, axis=1, keepdims=True)
    return n / np.maximum(l, 1e-18), 0.5 * l[:, 0]


n0, A0 = fn(rest)
cos0 = (n0[pairs[:, 0]] * n0[pairs[:, 1]]).sum(axis=1)
mid0 = np.array([(rest[a] + rest[b]) / 2 for a, b in keys])
ups = np.isin(reg, [rn.index("torso"), rn.index("shoulder"), rn.index("neck")])
vp = np.array([ups[a] and ups[b] for a, b in keys])
# ---- feature 1: ledge = upper-back band (rear, mid-back below the scapula); feature 2: drape = neck-base/trapezius skin
LEDGE = vp & (mid0[:, 1] > 0.0) & (mid0[:, 2] > 1.20) & (mid0[:, 2] < 1.46) & (np.abs(mid0[:, 0]) < 0.24) & (cos0 > 0.5)
DRAPE = vp & (mid0[:, 1] > 0.0) & (mid0[:, 2] >= 1.46) & (np.abs(mid0[:, 0]) < 0.26) & (cos0 > 0.5)
print("rest-smooth edge pairs: ledge band %d, drape band %d" % (LEDGE.sum(), DRAPE.sum()))
tin = lambda mask: np.unique(pairs[mask].ravel())
TL, TD = tin(LEDGE), tin(DRAPE)
r0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
vL = np.unique(np.array([keys[i] for i in np.nonzero(LEDGE)[0]]).ravel()); vD = np.unique(np.array([keys[i] for i in np.nonzero(DRAPE)[0]]).ravel())
inL = np.zeros(nV, bool); inL[vL] = True
inD = np.zeros(nV, bool); inD[vD] = True
eL = inL[E[:, 0]] & inL[E[:, 1]]; eD = inD[E[:, 0]] & inD[E[:, 1]]
print("%-22s %-14s | ledge: min dihedral cos (deg), #<0.9, #<0.7, #<0.5 | tri area/rest max p99 | edge ratio min max || drape: min cos, #<0.9, #<0.7 | area/rest max p99 p50 | edge ratio min max | max SI-free (n/a)" % ("entry", "state"))
entries = ["press_bottom", "press_top@0.500", "press_top@0.625", "press_top@0.750", "press_top@0.875", "press_top", "press_top_rhythm", "pullup_hang", "pullup_hang_rhythm", "pullup_top"]
for ent in entries:
    for name, dd in S.items():
        pn = [str(p) for p in dd["poses"]]
        if ent not in pn: continue
        P = dd["evaluated"][pn.index(ent)]
        nn, AA = fn(P)
        cs = (nn[pairs[:, 0]] * nn[pairs[:, 1]]).sum(axis=1)
        er = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / r0
        ar = AA / A0
        la = ar[TL]; da = ar[TD]
        print("%-22s %-14s | %5.2f (%3.0f) %3d %3d %3d | %.2f %.2f | %.2f %.2f || %5.2f %3d %3d | %.2f %.2f %.2f | %.2f %.2f" % (
            ent, name, cs[LEDGE].min(), np.degrees(np.arccos(np.clip(cs[LEDGE].min(), -1, 1))), (cs[LEDGE] < 0.9).sum(), (cs[LEDGE] < 0.7).sum(), (cs[LEDGE] < 0.5).sum(),
            la.max(), np.percentile(la, 99), er[eL].min(), er[eL].max(),
            cs[DRAPE].min(), (cs[DRAPE] < 0.9).sum(), (cs[DRAPE] < 0.7).sum(), da.max(), np.percentile(da, 99), np.median(da), er[eD].min(), er[eD].max()))
    print()
# ---- where exactly is the ledge in r95 press_top
P = S["r95"]["evaluated"][[str(p) for p in S["r95"]["poses"]].index("press_top")]
nn, AA = fn(P)
cs = (nn[pairs[:, 0]] * nn[pairs[:, 1]]).sum(axis=1)
ids = np.nonzero(LEDGE)[0]
w = ids[np.argsort(cs[ids])[:25]]
print("ledge: 25 sharpest edge pairs in r95 press_top: rest-mid bbox", np.round(mid0[w].min(0), 3), np.round(mid0[w].max(0), 3))
vs = np.unique(np.array([keys[i] for i in w]).ravel())
print("   regions", {rn[k]: int((reg[vs] == k).sum()) for k in range(len(rn)) if (reg[vs] == k).any()})
domb = [bones[int(np.argmax(W[v]))] for v in vs]
from collections import Counter
print("   dominant bones", Counter(domb).most_common(5))
print("   edge mid examples:", [(round(float(mid0[i][0]), 3), round(float(mid0[i][2]), 3), round(float(cs[i]), 2)) for i in w[:6]])
np.savez(SP + r"\ledge_ids.npz", pairs=w, verts=vs)
ids = np.nonzero(DRAPE)[0]
w2 = ids[np.argsort(cs[ids])[:25]]
vs2 = np.unique(np.array([keys[i] for i in w2]).ravel())
print("drape: 25 sharpest pairs in r95 press_top: rest-mid bbox", np.round(mid0[w2].min(0), 3), np.round(mid0[w2].max(0), 3), "regions", {rn[k]: int((reg[vs2] == k).sum()) for k in range(len(rn)) if (reg[vs2] == k).any()})
print("   dominant bones", Counter([bones[int(np.argmax(W[v]))] for v in vs2]).most_common(5))
# drape sag: height of the posed drape surface above the straight chord between neck base and the raised acromion/clavicle end
