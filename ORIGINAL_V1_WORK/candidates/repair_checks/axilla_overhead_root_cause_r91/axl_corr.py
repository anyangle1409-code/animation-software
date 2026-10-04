import sys, json
import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
w = np.load(SP + r"\r81_arc_dump.npz", allow_pickle=True)
c = np.load(SP + r"\r91_full_dump.npz", allow_pickle=True)
rest, tris, reg = c["rest"], c["tris"], c["region"]
rn = [str(x) for x in c["region_names"]]
bones = [str(b) for b in c["bones"]]
POSE = sys.argv[1] if len(sys.argv) > 1 else "press_top"
pn = [str(p) for p in c["poses"]]
Pw = w["evaluated"][[str(p) for p in w["poses"]].index(POSE)]
Pc = c["evaluated"][pn.index(POSE)]
a, b, cc = Pw[tris[:, 0]], Pw[tris[:, 1]], Pw[tris[:, 2]]
n = np.cross(b - a, cc - a)
vn = np.zeros_like(Pw)
for k in range(3):
    np.add.at(vn, tris[:, k], n)
vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-18)
D = Pc - Pw
nd = (D * vn).sum(axis=1)               # + = outward bulge added by the corrective, - = dent
mag = np.linalg.norm(D, axis=1)
left = rest[:, 0] <= 0
print("POSE", POSE, " corrective (r91 minus weights-only), left half, vertices moved > 1 cm:", int(((mag > 0.01) & left).sum()), " max %.3f m" % mag.max())
V0 = np.einsum("ij,ij->i", rest[tris[:, 0]], np.cross(rest[tris[:, 1]], rest[tris[:, 2]])).sum() / 6
def vol(P):
    return np.einsum("ij,ij->i", P[tris[:, 0]], np.cross(P[tris[:, 1]], P[tris[:, 2]])).sum() / 6
print("mesh volume weights-only %.5f -> r91 %.5f (change %+.2e m^3, %.2f%% of rest %.5f)" % (vol(Pw), vol(Pc), vol(Pc) - vol(Pw), 100 * (vol(Pc) - vol(Pw)) / V0, V0))
for name, m in (("DENTS  (normal displacement < -2 cm)", left & (nd < -0.02)), ("BULGES (normal displacement > +2 cm)", left & (nd > 0.02))):
    ids = np.nonzero(m)[0]
    print("\n%s: %d vertices" % (name, len(ids)))
    if len(ids) == 0:
        continue
    print("   regions", {rn[k]: int((reg[ids] == k).sum()) for k in range(len(rn)) if (reg[ids] == k).any()}, " normal disp min %.3f max %.3f" % (nd[ids].min(), nd[ids].max()))
    # simple spatial clusters by rest-position grid (4 cm cells)
    cell = np.floor(rest[ids] / 0.04).astype(int)
    keyc = [tuple(x) for x in cell]
    from collections import defaultdict
    g = defaultdict(list)
    for v, k in zip(ids, keyc):
        g[k].append(v)
    big = sorted(g.values(), key=lambda x: -len(x))[:5]
    for grp in big:
        grp = np.array(grp)
        top = lambda v: bones[int(np.argmax(c["W"][v]))]
        print("   cell near rest %s: %2d verts, mean normal disp %+.3f, regions %s, dominant bones %s" % (np.round(rest[grp].mean(0), 3), len(grp), nd[grp].mean(), {rn[k]: int((reg[grp] == k).sum()) for k in range(len(rn)) if (reg[grp] == k).any()}, sorted({top(v) for v in grp})[:4]))
np.savez(SP + r"\axl_corr_%s.npz" % POSE, nd=nd, mag=mag)
