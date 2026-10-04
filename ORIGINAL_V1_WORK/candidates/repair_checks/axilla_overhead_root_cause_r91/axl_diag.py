import json, sys
import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
S = {"wonly": np.load(SP + r"\r81_arc_dump.npz", allow_pickle=True), "r91": np.load(SP + r"\r91_full_dump.npz", allow_pickle=True),
     "r68": np.load(SP + r"\r68_arc_dump.npz", allow_pickle=True), "r42": np.load(SP + r"\r42_full_dump.npz", allow_pickle=True)}
d = S["r91"]
rest, tris, E, reg = d["rest"], d["tris"], d["edges"], d["region"]
rn = [str(x) for x in d["region_names"]]
POSE = sys.argv[1] if len(sys.argv) > 1 else "press_top"
TRUNK = ("pelvis", "spine_01", "spine_02", "spine_03", "neck", "head")


def vnormals(P):
    a, b, c = P[tris[:, 0]], P[tris[:, 1]], P[tris[:, 2]]
    n = np.cross(b - a, c - a)
    vn = np.zeros_like(P)
    for k in range(3):
        np.add.at(vn, tris[:, k], n)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-18), n


def trunk_ref(dd, i):
    bn = [str(b) for b in dd["bones"]]
    cols = [bn.index(b) for b in TRUNK if b in bn]
    W = dd["W"][:, cols]
    s = W.sum(axis=1, keepdims=True)
    Wn = W / np.maximum(s, 1e-9)
    M = np.einsum("vb,bij->vij", Wn, dd["mats"][i][cols].astype(np.float64))
    R1 = np.c_[dd["rest"], np.ones(len(dd["rest"]))]
    P = np.einsum("vij,vj->vi", M, R1)[:, :3]
    return P, M[:, :3, :3], s[:, 0]


out = {}
rn0, _ = vnormals(rest)
vn_rest, _ = vnormals(rest)
res = {}
for name, dd in S.items():
    pn = [str(p) for p in dd["poses"]]
    if POSE not in pn:
        continue
    i = pn.index(POSE)
    P = dd["evaluated"][i]
    Ptr, Rtr, ws = trunk_ref(dd, i)
    ntr = np.einsum("vij,vj->vi", Rtr, vn_rest)
    ntr /= np.maximum(np.linalg.norm(ntr, axis=1, keepdims=True), 1e-18)
    dn = ((P - Ptr) * ntr).sum(axis=1)          # outward offset from where the thorax surface would be if rigid with the trunk (m)
    dt = np.linalg.norm((P - Ptr) - dn[:, None] * ntr, axis=1)
    res[name] = dict(P=P, Ptr=Ptr, dn=dn, dt=dt, ws=ws)

torso = (reg == rn.index("torso")) | (reg == rn.index("shoulder"))
left = rest[:, 0] <= 0
print("pose", POSE)
for name, r in res.items():
    m = torso & left & (r["ws"] > 0.5)
    dn = r["dn"][m]
    print("%-6s torso/shoulder-left vertices %d : outward offset dn min %.3f  p1 %.3f  p99 %.3f  max %.3f  | #dn<-2cm %d  #dn>+2cm %d" % (name, m.sum(), dn.min(), np.percentile(dn, 1), np.percentile(dn, 99), dn.max(), (dn < -0.02).sum(), (dn > 0.02).sum()))
w, c = res["wonly"], res["r91"]
corr = np.linalg.norm(c["P"] - w["P"], axis=1)
print("\ncorrective footprint (|r91 - weights-only| > 5 mm): %d vertices, max %.3f m; by region:" % ((corr > 0.005).sum(), corr.max()), {rn[k]: int(((corr > 0.005) & (reg == k)).sum()) for k in range(len(rn)) if ((corr > 0.005) & (reg == k)).any()})
# pit vertices: strongly inward relative to the thorax reference in r91
m = torso & left & (c["ws"] > 0.5)
idx = np.nonzero(m)[0]
pit = idx[np.argsort(c["dn"][idx])[:60]]
flap = idx[np.argsort(-c["dn"][idx])[:60]]
bones = [str(b) for b in d["bones"]]


def desc(v):
    top = np.argsort(-d["W"][v])[:3]
    return " ".join("%s %.2f" % (bones[b], d["W"][v, b]) for b in top)


def cluster(ids, label):
    print("\n%s: %d vertices; rest bbox min %s max %s; mean dn r91 %.3f / weights-only %.3f / r42 %.3f; corrective move mean %.3f m" % (
        label, len(ids), np.round(rest[ids].min(0), 3), np.round(rest[ids].max(0), 3), c["dn"][ids].mean(), w["dn"][ids].mean(), res["r42"]["dn"][ids].mean() if "r42" in res else float("nan"), corr[ids].mean()))
    regs = {rn[k]: int((reg[ids] == k).sum()) for k in range(len(rn)) if (reg[ids] == k).any()}
    print("   regions", regs)
    for v in ids[:8]:
        print("   v%5d rest %s r91 dn %.3f wonly dn %.3f corr %.3f | %s" % (v, np.round(rest[v], 3), c["dn"][v], w["dn"][v], corr[v], desc(v)))


cluster(pit, "PIT (most inward vs trunk reference, r91, left half)")
cluster(flap, "FLAP (most outward vs trunk reference, r91, left half)")
np.savez(SP + r"\axl_diag_%s.npz" % POSE, pit=pit, flap=flap)
