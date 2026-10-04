import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
D = {n: np.load(SP + "\\" + f, allow_pickle=True) for n, f in (("r68", "r68_arc_dump.npz"), ("r81w", "r81_arc_dump.npz"), ("r83", "r83_flex_dump.npz"), ("r87", "r87_dump.npz"))}
d = D["r87"]
tris, rest, reg = d["tris"], d["rest"], d["region"]
rn = [str(x) for x in d["region_names"]]


def tri_vol(P):
    a, b, c = P[tris[:, 0]], P[tris[:, 1]], P[tris[:, 2]]
    return np.einsum("ij,ij->i", a, np.cross(b, c)) / 6.0


V0 = tri_vol(rest)
treg = reg[tris[:, 0]]
print("rest volume %.5f" % V0.sum())
res = {}
for n, dd in D.items():
    i = [str(p) for p in dd["poses"]].index("squat_bottom")
    v = tri_vol(dd["evaluated"][i])
    res[n] = v
    print("%-5s squat volume ratio %.4f" % (n, v.sum() / V0.sum()))
print("\nper-region volume change (m^3 x 1e4), by region of the triangle's first vertex")
print("%-10s %9s %9s %9s %9s %9s" % ("region", "r68", "r81w-r68", "r83-r81w", "r87-r83", "r87 total"))
for k, nm in enumerate(rn):
    m = treg == k
    if not m.any():
        continue
    f = lambda a, b=None: ((res[a][m].sum() - (res[b][m].sum() if b else V0[m].sum())) * 1e4)
    print("%-10s %9.2f %9.2f %9.2f %9.2f %9.2f" % (nm, f("r68"), f("r81w", "r68"), f("r83", "r81w"), f("r87", "r83"), f("r87")))
print("\ntotal change r87 - r83: %.2f e-4 ; r81w - r68: %.2f e-4" % ((res["r87"].sum() - res["r83"].sum()) * 1e4, (res["r81w"].sum() - res["r68"].sum()) * 1e4))
