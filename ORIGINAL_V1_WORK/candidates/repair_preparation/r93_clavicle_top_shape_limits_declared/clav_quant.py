import numpy as np, json
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
w = np.load(SP + r"\r92_base_dump.npz", allow_pickle=True); c = np.load(SP + r"\r92_full_dump.npz", allow_pickle=True)
rest, tris, reg, W = c["rest"], c["tris"], c["region"], c["W"]
rn = [str(x) for x in c["region_names"]]; bones = [str(b) for b in c["bones"]]
clav = bones.index("clavicle_l")
left = rest[:, 0] <= 0
for zmin in (1.40, 1.44, 1.46):
  for wc in (0.25, 0.35, 0.5):
    S = left & (reg == rn.index("shoulder")) & (rest[:, 2] > zmin) & (W[:, clav] > wc)
    print("zmin %.2f clavicle weight > %.2f : %d vertices" % (zmin, wc, S.sum()))
S = left & (reg == rn.index("shoulder")) & (rest[:, 2] > 1.44) & (W[:, clav] > 0.35)
print("chosen probe region: %d vertices; rest bbox %s %s" % (S.sum(), np.round(rest[S].min(0), 3), np.round(rest[S].max(0), 3)))
tm = S[tris].all(axis=1)
def area(P): return 0.5 * np.linalg.norm(np.cross(P[tris[tm, 1]] - P[tris[tm, 0]], P[tris[tm, 2]] - P[tris[tm, 0]]), axis=1)
A0 = area(rest)
pc = [str(p) for p in c["poses"]]; pw = [str(p) for p in w["poses"]]
print("triangles in region:", int(tm.sum()), " rest area %.5f m^2" % A0.sum())
print("%-22s %6s | area/rest weights-only (median, p95) | area/rest r92 (median, p95) | growth r92/weights-only (median p95 max) | tangential slide (mean cm) | outward bulge (max cm)" % ("entry", "theta"))
def vn(P):
    n = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]]); v = np.zeros_like(P)
    for k in range(3): np.add.at(v, tris[:, k], n)
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-18)
for name in ("press_bottom", "press_top@0.500", "press_top@0.625", "press_top@0.750", "press_top@0.875", "press_top", "press_top_rhythm", "pullup_hang", "pullup_top"):
    i, j = pc.index(name), pw.index(name)
    Pc, Pw = c["evaluated"][i], w["evaluated"][j]
    ac, aw = area(Pc) / A0, area(Pw) / A0
    g = area(Pc) / np.maximum(area(Pw), 1e-12)
    D = Pc[S] - Pw[S]; n = vn(Pw)[S]; nd = (D * n).sum(axis=1); tg = np.sqrt(np.maximum((D ** 2).sum(axis=1) - nd ** 2, 0))
    print("%-22s %6.1f | %.2f %.2f | %.2f %.2f | %.2f %.2f %.2f | %.2f | %.2f" % (name, c["theta"][i][0], np.median(aw), np.percentile(aw, 95), np.median(ac), np.percentile(ac, 95), np.median(g), np.percentile(g, 95), g.max(), 100 * tg.mean(), 100 * nd.max()))
np.savez(SP + r"\clav_region.npz", S=np.nonzero(S)[0])