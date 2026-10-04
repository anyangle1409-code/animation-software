import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
w = np.load(SP + r"\r92_base_dump.npz", allow_pickle=True); c = np.load(SP + r"\r92_full_dump.npz", allow_pickle=True)
rest, tris, reg = c["rest"], c["tris"], c["region"]; rn = [str(x) for x in c["region_names"]]
S = np.load(SP + r"\clav_region.npz")["S"]; inS = np.zeros(len(rest), bool); inS[S] = True
def area(P, m): return 0.5 * np.linalg.norm(np.cross(P[tris[m, 1]] - P[tris[m, 0]], P[tris[m, 2]] - P[tris[m, 0]]), axis=1)
pc = [str(p) for p in c["poses"]]; pw = [str(p) for p in w["poses"]]
# any triangle touching the region (the web includes boundary triangles toward the upper arm / neck)
tm = inS[tris].any(axis=1)
A0 = area(rest, tm); idx = np.nonzero(tm)[0]
print("triangles touching the region:", int(tm.sum()))
for name in ("press_top@0.625", "press_top", "press_top_rhythm", "pullup_hang"):
    i, j = pc.index(name), pw.index(name)
    ac = area(c["evaluated"][i], tm) / A0; aw = area(w["evaluated"][j], tm) / A0
    o = np.argsort(-ac)[:6]
    print(name, "| r92 area/rest: max %.2f p99 %.2f p95 %.2f ; weights-only max %.2f p99 %.2f ; # r92 > 1.5x: %d, > 2x: %d (weights-only: %d, %d)" % (ac.max(), np.percentile(ac, 99), np.percentile(ac, 95), aw.max(), np.percentile(aw, 99), (ac > 1.5).sum(), (ac > 2).sum(), (aw > 1.5).sum(), (aw > 2).sum()))
    if name == "press_top":
        for k in o:
            t = tris[idx[k]]; print("    tri %6d rest mid %s area/rest r92 %.2f weights-only %.2f regions %s" % (idx[k], np.round(rest[t].mean(0), 3), ac[k], aw[k], sorted({rn[reg[v]] for v in t})))
# edge ratio tail inside/at region
E = c["edges"]; me = inS[E[:, 0]] | inS[E[:, 1]]
r0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
for name in ("press_top",):
    i, j = pc.index(name), pw.index(name)
    for lab, P in (("r92", c["evaluated"][i]), ("weights-only", w["evaluated"][j])):
        r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / r0
        print(lab, "edges touching region: n=%d  max %.2f  p99 %.2f  min %.2f" % (me.sum(), r[me].max(), np.percentile(r[me], 99), r[me].min()))