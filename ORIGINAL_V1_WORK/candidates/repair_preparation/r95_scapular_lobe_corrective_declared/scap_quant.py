import json, sys
import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
REPO = r"C:\Users\Mark\Documents\animation-software\repo"
tags = sys.argv[1:] or ["L0.045", "L0.035"]
S = {"r93": np.load(SP + r"\r93_scap_dump_drv.npz", allow_pickle=True)}
for t in tags:
    S[t] = np.load(SP + r"\sp_%s_dump.npz" % t, allow_pickle=True)
d = S["r93"]
rest, tris, reg, W, E = d["rest"], d["tris"], d["region"], d["W"], d["edges"]
bones = [str(b) for b in d["bones"]]
lz = json.load(open(REPO + r"\ORIGINAL_V1_WORK\candidates\repair_preparation\r95_scapular_lobe_corrective_declared\lobe_limit_zone_declared_before_solve.json"))
zone = np.array(lz["left_owned_vertex_ids"])
mk = json.load(open(REPO + r"\ORIGINAL_V1_WORK\candidates\repair_preparation\r95_scapular_lobe_corrective_declared\scapular_lobe_mask_declared_before_solve.json"))
mask = np.array(mk["left_owned_vertex_ids"])
TRUNK = ("pelvis", "spine_01", "spine_02", "spine_03", "neck", "head")
tcols = [bones.index(b) for b in TRUNK]
R1 = np.c_[rest, np.ones(len(rest))]


def vn(P):
    n = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]]); v = np.zeros_like(P)
    for k in range(3): np.add.at(v, tris[:, k], n)
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-18)


vrest = vn(rest)
r0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
tm = np.isin(tris, mask).any(axis=1)


def area(P): return 0.5 * np.linalg.norm(np.cross(P[tris[tm, 1]] - P[tris[tm, 0]], P[tris[tm, 2]] - P[tris[tm, 0]]), axis=1)


A0 = area(rest)
inm = np.zeros(len(rest), bool); inm[mask] = True
em = inm[E[:, 0]] | inm[E[:, 1]]


def offs(dd, i):
    Wt = dd["W"][:, tcols]; s = Wt.sum(axis=1, keepdims=True); Wn = Wt / np.maximum(s, 1e-9)
    M = np.einsum("vb,bij->vij", Wn, dd["mats"][i][tcols].astype(np.float64)); Ptr = np.einsum("vij,vj->vi", M, R1)[:, :3]
    n = np.einsum("vij,vj->vi", M[:, :3, :3], vrest); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-18)
    return ((dd["evaluated"][i] - Ptr) * n).sum(axis=1)


print("%-26s %-8s | lobe-zone outward offset cm: max p95 median | min over zone | area/rest max (mask tris) | edge ratio min max (mask edges) | boundary step cm" % ("entry", "state"))
for entry in ("press_bottom", "press_top@0.500", "press_top@0.625", "press_top@0.750", "press_top", "press_top_rhythm", "pullup_top", "pullup_hang", "pullup_hang_rhythm"):
    for name, dd in S.items():
        pn = [str(p) for p in dd["poses"]]
        if entry not in pn: continue
        i = pn.index(entry); o = offs(dd, i)[zone]
        P = dd["evaluated"][i]
        er = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / r0
        ar = area(P) / A0
        # displacement relative to r93 on the taper ring (mask minus zone): max movement of ring vertices
        ring = np.setdiff1d(mask, zone)
        step = np.linalg.norm(P[ring] - S["r93"]["evaluated"][[str(p) for p in S["r93"]["poses"]].index(entry)][ring], axis=1).max() * 100 if name != "r93" else 0.0
        print("%-26s %-8s | %5.2f %5.2f %5.2f | %6.2f | %5.2f | %.2f %.2f | %.2f" % (entry, name, 100 * o.max(), 100 * np.percentile(o, 95), 100 * np.median(o), 100 * o.min(), ar.max(), er[em].min(), er[em].max(), step))
    print()
