import numpy as np, sys
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
base = np.load(SP + r"\r92_base_dump.npz", allow_pickle=True)
S = {"weights-only": base, "r92": np.load(SP + r"\r92_full_dump.npz", allow_pickle=True), "r93": np.load(SP + r"\r93_full_dump.npz", allow_pickle=True)}
rest, tris = base["rest"], base["tris"]
import json
z = json.load(open(r"C:\Users\Mark\Documents\animation-software\repo\ORIGINAL_V1_WORK\candidates\repair_preparation\r93_clavicle_top_shape_limits_declared\clavicle_top_zone_declared_before_solve.json"))
inS = np.zeros(len(rest), bool); inS[z["left_owned_vertex_ids"]] = True
tm = inS[tris].any(axis=1)
def area(P): return 0.5 * np.linalg.norm(np.cross(P[tris[tm, 1]] - P[tris[tm, 0]], P[tris[tm, 2]] - P[tris[tm, 0]]), axis=1)
A0 = area(rest)
def vn(P):
    n = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]]); v = np.zeros_like(P)
    for k in range(3): np.add.at(v, tris[:, k], n)
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-18)
Pw = None
print("%-14s %-18s | area/rest max  p99 | #>2x | bulge max (cm) | slide mean/max (cm) | zone SI-relevant: none" % ("state", "entry"))
for entry in ("press_top@0.625", "press_top", "press_top_rhythm", "pullup_hang"):
    pw = [str(p) for p in base["poses"]]; Pw = base["evaluated"][pw.index(entry)]
    for name, d in S.items():
        pc = [str(p) for p in d["poses"]]; P = d["evaluated"][pc.index(entry)]
        a = area(P) / A0
        D = P[inS] - Pw[inS]; n = vn(Pw)[inS]; nd = (D * n).sum(axis=1); tg = np.sqrt(np.maximum((D ** 2).sum(axis=1) - nd ** 2, 0))
        print("%-14s %-18s | %.2f %.2f | %2d | %.2f | %.2f %.2f" % (name, entry, a.max(), np.percentile(a, 99), (a > 2).sum(), 100 * nd.max(), 100 * tg.mean(), 100 * tg.max()))
    print()