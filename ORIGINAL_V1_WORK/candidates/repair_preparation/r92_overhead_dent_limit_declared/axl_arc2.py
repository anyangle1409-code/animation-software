import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
w = np.load(SP + r"\r81_arc_dump.npz", allow_pickle=True); import sys
c = np.load(sys.argv[1], allow_pickle=True)
rest, tris, reg = c["rest"], c["tris"], c["region"]
pc = [str(p) for p in c["poses"]]; pw = [str(p) for p in w["poses"]]
def vol(P): return np.einsum("ij,ij->i", P[tris[:, 0]], np.cross(P[tris[:, 1]], P[tris[:, 2]])).sum() / 6
def vnorm(P):
    n = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]]); vn = np.zeros_like(P)
    for k in range(3): np.add.at(vn, tris[:, k], n)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-18)
left = rest[:, 0] <= 0
print("%-24s %6s %5s | %-22s %-24s %-14s" % ("entry", "theta", "lam", "deepest dent (cm)", "dents > 2 cm (verts, L)", "volume change"))
for name in ("press_bottom@0.500", "press_bottom@0.750", "press_bottom", "press_top@0.250", "press_top@0.375", "press_top@0.500", "press_top@0.625", "press_top@0.750", "press_top@0.875", "press_top", "press_top_rhythm", "pullup_hang", "pullup_hang_rhythm", "pullup_top", "squat_bottom"):
    if name not in pc or name not in pw: continue
    i, j = pc.index(name), pw.index(name)
    Pc, Pw = c["evaluated"][i], w["evaluated"][j]
    nd = ((Pc - Pw) * vnorm(Pw)).sum(axis=1)
    print("%-24s %6.1f %5.2f | %-22.2f %-24d %+.2e (%.2f%%)" % (name, c["theta"][i][0], c["lam"][i][0], 100 * nd[left].min(), int((nd[left] < -0.02).sum()), vol(Pc) - vol(Pw), 100 * (vol(Pc) - vol(Pw)) / vol(rest)))