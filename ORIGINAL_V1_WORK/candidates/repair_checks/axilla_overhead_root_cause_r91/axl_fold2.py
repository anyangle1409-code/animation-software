import sys
import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
S = {"wonly": np.load(SP + r"\r81_arc_dump.npz", allow_pickle=True), "r91": np.load(SP + r"\r91_full_dump.npz", allow_pickle=True), "r42": np.load(SP + r"\r42_full_dump.npz", allow_pickle=True)}
d = S["r91"]
rest, tris, reg = d["rest"], d["tris"], d["region"]
rn = [str(x) for x in d["region_names"]]
bones = [str(b) for b in d["bones"]]
POSE = sys.argv[1] if len(sys.argv) > 1 else "press_top"


def face_normals(P):
    a, b, c = P[tris[:, 0]], P[tris[:, 1]], P[tris[:, 2]]
    n = np.cross(b - a, c - a)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-18), 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)


# triangle adjacency through shared edges
ed = {}
for t, (a, b, c) in enumerate(tris):
    for u, v in ((a, b), (b, c), (c, a)):
        ed.setdefault((min(u, v), max(u, v)), []).append(t)
pairs = np.array([v for v in ed.values() if len(v) == 2])
keys = [k for k, v in ed.items() if len(v) == 2]
n0, A0 = face_normals(rest)
cos0 = (n0[pairs[:, 0]] * n0[pairs[:, 1]]).sum(axis=1)
UPPER = np.isin(reg, [rn.index(x) for x in ("shoulder", "torso", "neck", "arm")]) & (rest[:, 2] > 1.2)
upper_pair = np.array([UPPER[keys[i][0]] and UPPER[keys[i][1]] for i in range(len(keys))])
cos0 = np.where(upper_pair, cos0, -2.0)
print("pose", POSE, "| rest-smooth adjacent triangle pairs:", int((cos0 > 0.5).sum()), "of", len(pairs))
rows = {}
for name, dd in S.items():
    pn = [str(p) for p in dd["poses"]]
    P = dd["evaluated"][pn.index(POSE)]
    n, A = face_normals(P)
    cs = (n[pairs[:, 0]] * n[pairs[:, 1]]).sum(axis=1)
    rows[name] = (cs, A / A0)
    sm = cos0 > 0.5
    print("%-6s smooth-at-rest pairs with dihedral cos < 0.3: %4d  < 0.0: %4d  < -0.3: %4d | min %.2f | tris with area ratio < 0.35: %d  inverted vs rest(n.n0<0): %d" % (
        name, (cs[sm] < 0.3).sum(), (cs[sm] < 0.0).sum(), (cs[sm] < -0.3).sum(), cs[sm].min(), (A / A0 < 0.35).sum(), ((n * n0).sum(axis=1) < 0).sum()))
cs, ar = rows["r91"]
sm = cos0 > 0.5
worst = np.nonzero(sm)[0][np.argsort(cs[sm])[:40]]
print("\nworst 40 folds in r91 (smooth at rest): location cluster")
mids = np.array([(rest[keys[i][0]] + rest[keys[i][1]]) / 2 for i in worst])
cw = rows["wonly"][0]
for i in worst[:14]:
    a, b = keys[i]
    top = lambda v: bones[int(np.argmax(d["W"][v]))]
    print("  pair %6d rest mid %s region %s cos r91 %.2f wonly %.2f r42 %.2f | %s/%s" % (i, np.round((rest[a] + rest[b]) / 2, 3), rn[reg[a]], cs[i], cw[i], rows["r42"][0][i] if len(rows["r42"][0]) == len(cs) else float("nan"), top(a), top(b)))
print("fold cluster bbox rest min", np.round(mids.min(0), 3), "max", np.round(mids.max(0), 3))
print("regions of worst folds:", {rn[k]: int((np.array([reg[keys[i][0]] for i in worst]) == k).sum()) for k in range(len(rn)) if (np.array([reg[keys[i][0]] for i in worst]) == k).any()})
