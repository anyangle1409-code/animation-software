import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
w = np.load(SP + r"\r81_arc_dump.npz", allow_pickle=True); c = np.load(SP + r"\r91_full_dump.npz", allow_pickle=True)
rest, reg = c["rest"], c["region"]; rn = [str(x) for x in c["region_names"]]; bones = [str(b) for b in c["bones"]]
pn = [str(p) for p in c["poses"]]; i = pn.index("press_top")
Pw = w["evaluated"][[str(p) for p in w["poses"]].index("press_top")]; Pc = c["evaluated"][i]
D = Pc - Pw
d = np.load(SP + r"\axl_corr_press_top.npz"); nd = d["nd"]; mag = d["mag"]
sh = (reg == rn.index("shoulder")) & (rest[:, 0] <= 0) & (rest[:, 2] > 1.44)
ids = np.nonzero(sh & (mag > 0.015))[0]
print("shoulder-top (z>1.44) left vertices moved >1.5 cm:", len(ids), " of ", int(sh.sum()))
tang = np.sqrt(np.maximum(mag[ids] ** 2 - nd[ids] ** 2, 0))
print("   mean |D| %.3f  mean |normal part| %.3f  mean |tangential part| %.3f  max |D| %.3f" % (mag[ids].mean(), np.abs(nd[ids]).mean(), tang.mean(), mag[ids].max()))
print("   mean displacement vector (armature frame, m) %s ; rest centroid %s" % (np.round(D[ids].mean(0), 3), np.round(rest[ids].mean(0), 3)))
# compression of the area between the moved set and its surroundings: tri area ratio inside the set, r91 vs weights-only
tris = c["tris"]; m = np.isin(tris, ids).all(axis=1)
def area(P): return 0.5 * np.linalg.norm(np.cross(P[tris[m, 1]] - P[tris[m, 0]], P[tris[m, 2]] - P[tris[m, 0]]), axis=1)
print("   triangles inside the moved set: %d; total area weights-only %.5f -> r91 %.5f m^2 (%.1f%%)" % (m.sum(), area(Pw).sum(), area(Pc).sum(), 100 * (area(Pc).sum() / area(Pw).sum() - 1)))
top = ids[np.argsort(-mag[ids])[:6]]
for v in top: print("   v%5d rest %s |D| %.3f normal %+.3f | %s" % (v, np.round(rest[v], 3), mag[v], nd[v], " ".join("%s %.2f" % (bones[b], c["W"][v, b]) for b in np.argsort(-c["W"][v])[:3])))