import json
import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
REPO = r"C:\Users\Mark\Documents\animation-software\repo"
decl = json.load(open(REPO + r"\ORIGINAL_V1_WORK\candidates\repair_preparation\r94_wing_scapula_weight_declared\wing_zone_declared_before_edit.json"))
d = np.load(SP + r"\r92_base_dump.npz", allow_pickle=True)
rest, E, reg, W, mats = d["rest"], d["edges"], d["region"], d["W"], d["mats"].astype(np.float64)
rn = [str(x) for x in d["region_names"]]; bones = [str(b) for b in d["bones"]]; poses = [str(p) for p in d["poses"]]
scl, scr = bones.index("scapula_l"), bones.index("scapula_r")
s2l, s3l = bones.index("spine_02"), bones.index("spine_03")
left = np.array(decl["left_owned_vertex_ids"]); right = np.array(decl["mirror_of_strict_left_vertex_ids"])
depth = {int(k): v for k, v in decl["ring_depth_left"].items()}
key = {tuple(np.round(rest[i], 5)): i for i in range(len(rest))}
mir = {int(v): key[tuple(np.round(rest[v] * [-1, 1, 1], 5))] for v in left if rest[v, 0] < -1e-8}
R1 = np.c_[rest, np.ones(len(rest))]
r0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
TRUNK = ("pelvis", "spine_01", "spine_02", "spine_03", "neck", "head")
tcols = [bones.index(b) for b in TRUNK]


def top4(Wm):
    Wm = Wm.copy(); idx = np.argsort(-Wm, axis=1)[:, 4:]; np.put_along_axis(Wm, idx, 0, axis=1)
    return Wm / Wm.sum(1, keepdims=True)


def modify(beta):
    Wn = W.copy()
    for v in left:
        f = min(1.0, (depth[int(v)] - 1) / 2.0)
        freed = Wn[v, scl] * beta * f
        Wn[v, scl] -= freed
        share = np.array([W[v, s2l], W[v, s3l]])
        if share.sum() < 1e-6:
            share = np.array([1.0, 0.0])
        share = share / share.sum()
        Wn[v, s2l] += freed * share[0]; Wn[v, s3l] += freed * share[1]
        if int(v) in mir and rest[v, 0] < -1e-8:
            m = mir[int(v)]
            Wn[m] = Wn[v][_swap]       # exact mirror: swap _l/_r columns
    return top4(Wn)


# column swap map (_l <-> _r)
_swap = np.arange(len(bones))
for i, b in enumerate(bones):
    if b.endswith("_l") and b[:-2] + "_r" in bones:
        _swap[i] = bones.index(b[:-2] + "_r")
    elif b.endswith("_r") and b[:-2] + "_l" in bones:
        _swap[i] = bones.index(b[:-2] + "_l")


def evalP(Wm, i):
    return np.einsum("vij,vj->vi", np.einsum("vb,bij->vij", Wm, mats[i]), R1)[:, :3]


tris = d["tris"]


def vn(P):
    n = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]]); v = np.zeros_like(P)
    for k in range(3): np.add.at(v, tris[:, k], n)
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-18)


vrest = vn(rest)


def offset(Wm, i):
    P = evalP(Wm, i)
    Wt = Wm[:, tcols]; s = Wt.sum(axis=1, keepdims=True); Wn = Wt / np.maximum(s, 1e-9)
    M = np.einsum("vb,bij->vij", Wn, mats[i][tcols]); Ptr = np.einsum("vij,vj->vi", M, R1)[:, :3]
    n = np.einsum("vij,vj->vi", M[:, :3, :3], vrest); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-18)
    return ((P - Ptr) * n).sum(axis=1), P


final = [i for i, p in enumerate(poses) if "@" not in p]
wing = np.load(SP + r"\wing_ids.npz")["ids"]


def stats(Wm):
    out = {}
    for i in final:
        P = evalP(Wm, i)
        r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / r0
        for k, rg in enumerate(rn):
            s = (reg[E[:, 0]] == k) & (reg[E[:, 1]] == k)
            if s.any():
                out[(poses[i], rg)] = (float(r[s].min()), float(r[s].max()))
    return out


base = stats(W)
print("%-7s | wing offset max/mean in press_top, rhythm, hang (cm) | worst region-min drop | worst region-max rise | #(min drop > 0.02) | #(max rise > 0.1)" % "beta")
for beta in (0.0, 0.3, 0.5, 0.7):
    Wm = modify(beta) if beta > 0 else W
    off = []
    for p in ("press_top", "press_top_rhythm", "pullup_hang"):
        o, _ = offset(Wm, poses.index(p)); off.append("%.1f/%.1f" % (100 * o[wing].max(), 100 * o[wing].mean()))
    s = stats(Wm)
    dmin = sorted(((base[k][0] - s[k][0], k) for k in s), reverse=True)[0]
    dmax = sorted(((s[k][1] - base[k][1], k) for k in s), reverse=True)[0]
    nmin = sum(1 for k in s if base[k][0] - s[k][0] > 0.02); nmax = sum(1 for k in s if s[k][1] - base[k][1] > 0.1)
    print("%-7.1f | %-26s | %.3f %s | %.3f %s | %d | %d" % (beta, "  ".join(off), dmin[0], dmin[1], dmax[0], dmax[1], nmin, nmax))
    np.savez(SP + r"\wing_W_b%.1f.npz" % beta, W=Wm)
