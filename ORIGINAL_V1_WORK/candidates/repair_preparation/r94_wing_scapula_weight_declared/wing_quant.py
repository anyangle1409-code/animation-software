import json
import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
S = {"weights-only": np.load(SP + r"\r92_base_dump.npz", allow_pickle=True), "r93": np.load(SP + r"\r93_full_dump.npz", allow_pickle=True)}
d = S["r93"]
rest, tris, reg, W = d["rest"], d["tris"], d["region"], d["W"]
rn = [str(x) for x in d["region_names"]]; bones = [str(b) for b in d["bones"]]
scl = bones.index("scapula_l")
TRUNK = ("pelvis", "spine_01", "spine_02", "spine_03", "neck", "head")
left = rest[:, 0] <= 0


def vn(P):
    n = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]]); v = np.zeros_like(P)
    for k in range(3): np.add.at(v, tris[:, k], n)
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-18)


vrest = vn(rest)


def trunk_ref(dd, i):
    bn = [str(b) for b in dd["bones"]]
    cols = [bn.index(b) for b in TRUNK if b in bn]
    Wt = dd["W"][:, cols]; s = Wt.sum(axis=1, keepdims=True); Wn = Wt / np.maximum(s, 1e-9)
    M = np.einsum("vb,bij->vij", Wn, dd["mats"][i][cols].astype(np.float64))
    R1 = np.c_[dd["rest"], np.ones(len(dd["rest"]))]
    return np.einsum("vij,vj->vi", M, R1)[:, :3], M[:, :3, :3]


def offsets(name, pose):
    dd = S[name]; pn = [str(p) for p in dd["poses"]]; i = pn.index(pose)
    P = dd["evaluated"][i]; Ptr, R = trunk_ref(dd, i)
    n = np.einsum("vij,vj->vi", R, vrest); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-18)
    return ((P - Ptr) * n).sum(axis=1), P


dn_w, _ = offsets("weights-only", "press_top")
dn_c, _ = offsets("r93", "press_top")
torso = reg == rn.index("torso")
wing = left & torso & (dn_c > 0.02) & (W[:, scl] > 0.10)
print("WING candidates (left torso vertices, scapula weight > 0.10, outward offset from the thorax > 2 cm in r93 press_top): %d" % wing.sum())
ids = np.nonzero(wing)[0]
print("   rest bbox", np.round(rest[ids].min(0), 3), np.round(rest[ids].max(0), 3))
print("   scapula_l weight: min %.2f mean %.2f max %.2f ; trunk weight (spine_02+spine_03) mean %.2f" % (W[ids, scl].min(), W[ids, scl].mean(), W[ids, scl].max(), (W[ids][:, [bones.index('spine_02'), bones.index('spine_03')]]).sum(axis=1).mean()))
print("   outward offset (cm) weights-only: mean %.1f max %.1f ; r93: mean %.1f max %.1f" % (100 * dn_w[ids].mean(), 100 * dn_w[ids].max(), 100 * dn_c[ids].mean(), 100 * dn_c[ids].max()))
# relation between scapula weight and offset
x = W[ids, scl]; y = dn_c[ids]
print("   correlation(scapula weight, offset) = %.2f ; slope %.1f cm per unit weight" % (np.corrcoef(x, y)[0, 1], 100 * np.polyfit(x, y, 1)[0]))
print("\n   offset by pose (cm) - max over the wing set:")
for pose in ("neutral", "press_bottom", "press_top@0.500", "press_top@0.625", "press_top@0.750", "press_top", "press_top_rhythm", "pullup_hang", "pullup_top", "squat_bottom", "pushup_bottom", "row"):
    try:
        a, _ = offsets("weights-only", pose); b, _ = offsets("r93", pose)
        print("   %-18s weights-only max %.1f mean %.1f | r93 max %.1f mean %.1f" % (pose, 100 * a[ids].max(), 100 * a[ids].mean(), 100 * b[ids].max(), 100 * b[ids].mean()))
    except ValueError:
        pass
# ring of vertices around the wing set that are scapula-weighted but in the shoulder/scapula region (legitimate scapular skin)
print("\n   all left torso vertices with scapula weight > 0.10: %d ; of these in wing set %d" % ((left & torso & (W[:, scl] > 0.10)).sum(), wing.sum()))
print("   left SHOULDER-region vertices with scapula weight > 0.10: %d (legitimate scapular skin, not touched)" % (left & (reg == rn.index('shoulder')) & (W[:, scl] > 0.10)).sum())
np.savez(SP + r"\wing_ids.npz", ids=ids)
for v in ids[np.argsort(-dn_c[ids])[:8]]:
    top = np.argsort(-W[v])[:3]
    print("   v%5d rest %s offset %.1f cm | %s" % (v, np.round(rest[v], 3), 100 * dn_c[v], " ".join("%s %.2f" % (bones[b], W[v, b]) for b in top)))
