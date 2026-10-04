import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
w = np.load(SP + r"\r92_base_dump.npz", allow_pickle=True)           # weights-only (wrist base), 51 entries
ids = np.load(SP + r"\wing_ids.npz")["ids"]
rest, W, tris = w["rest"], w["W"], w["tris"]
bones = [str(b) for b in w["bones"]]; poses = [str(p) for p in w["poses"]]
mats = w["mats"].astype(np.float64)
heads = w["heads"]
TRUNK = ("pelvis", "spine_01", "spine_02", "spine_03", "neck", "head")
tcols = [bones.index(b) for b in TRUNK]
R1 = np.c_[rest, np.ones(len(rest))]


def vn(P):
    n = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]]); v = np.zeros_like(P)
    for k in range(3): np.add.at(v, tris[:, k], n)
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-18)


vrest = vn(rest)


def rotvec(R):
    c = (np.trace(R) - 1) / 2; ang = np.arccos(np.clip(c, -1, 1))
    if ang < 1e-9: return np.zeros(3), 0.0
    ax = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]) / (2 * np.sin(ang))
    return ax * ang, ang


def wing_offset(i):
    Wt = W[:, tcols]; s = Wt.sum(axis=1, keepdims=True); Wn = Wt / np.maximum(s, 1e-9)
    M = np.einsum("vb,bij->vij", Wn, mats[i][tcols]); Ptr = np.einsum("vij,vj->vi", M, R1)[:, :3]
    P = w["evaluated"][i]
    n = np.einsum("vij,vj->vi", M[:, :3, :3], vrest); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-18)
    return ((P - Ptr) * n).sum(axis=1)


sl, c3, ul, cl = bones.index("scapula_l"), bones.index("spine_03"), bones.index("upperarm_l"), bones.index("clavicle_l")
head_s = heads[sl]
print("%-24s %7s | wing max cm | rot angle (rel trunk) | rotvec comps in trunk frame (x lat, y ant, z up) deg | scapula-head excursion cm | theta" % ("pose", "theta"))
rows = []
for i, p in enumerate(poses):
    if p.startswith("neutral") or p == "grip" or p == "lunge": pass
    Rs = mats[i][sl][:3, :3]; Rt = mats[i][c3][:3, :3]
    rel = Rt.T @ Rs
    rv, ang = rotvec(rel)
    rv_trunk = np.degrees(rv)
    # excursion of the scapula pivot: posed scapula head vs trunk-rigid head
    hs = (mats[i][sl] @ np.r_[head_s, 1])[:3]; ht = (mats[i][c3] @ np.r_[head_s, 1])[:3]
    exc = np.linalg.norm(hs - ht)
    off = wing_offset(i)[ids]
    rows.append((p, w["theta"][i][0], off.max(), np.degrees(ang), rv_trunk, exc))
for p, th, om, ang, rv, exc in rows:
    if "@" in p or p in ("neutral", "grip", "curl_peak", "curl_handle", "lunge", "pullup_bar", "pullup_top", "row", "squat_bottom", "pushup_bottom", "press_bottom", "press_top", "press_top_rhythm", "pullup_hang", "pullup_hang_rhythm"):
        print("%-24s %7.1f | %6.1f | %6.1f | %6.1f %6.1f %6.1f | %6.1f" % (p, th, 100 * om, ang, rv[0], rv[1], rv[2], 100 * exc))
y = np.array([100 * r[2] for r in rows]);
for name, f in (("theta", lambda r: r[1]), ("rot angle", lambda r: r[3]), ("|rv_y| (anterior-axis component)", lambda r: abs(r[4][1])), ("|rv_x|", lambda r: abs(r[4][0])), ("|rv_z|", lambda r: abs(r[4][2])), ("excursion", lambda r: 100 * r[5])):
    x = np.array([f(r) for r in rows]); print("corr(wing max, %s) = %.2f" % (name, np.corrcoef(x, y)[0, 1]))
