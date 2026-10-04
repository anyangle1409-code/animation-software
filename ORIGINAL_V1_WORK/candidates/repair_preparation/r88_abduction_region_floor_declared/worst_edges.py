import json
import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
dw = np.load(SP + r"\r81_arc_dump.npz", allow_pickle=True)   # weights-only (no keys)
dk = np.load(SP + r"\r87_dump.npz", allow_pickle=True)        # r87 incl. both corrective key pairs
rest, E, reg = dk["rest"], dk["edges"], dk["region"]
rn = [str(x) for x in dk["region_names"]]
bones = [str(b) for b in dk["bones"]]
W = dk["W"]
r0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
zone = np.zeros(len(rest), bool)
z = json.load(open(r"C:\Users\Mark\Documents\animation-software\repo\ORIGINAL_V1_WORK\candidates\repair_preparation\r81_dilated_weight_smoothing_declared\weight_smoothing_zone_declared_before_edit.json"))
zone[z["left_owned_vertex_ids"]] = True
zone[z["mirror_of_strict_left_vertex_ids"]] = True
cm = json.load(open(r"C:\Users\Mark\Documents\animation-software\repo\ORIGINAL_V1_WORK\candidates\repair_preparation\r86_flexion_corrective_declared\flexion_corrective_mask_declared_before_solve.json"))
mask = np.zeros(len(rest), bool)
mask[cm["left_owned_vertex_ids"]] = True
mask[cm["mirror_of_strict_left_vertex_ids"]] = True


def ratios(d, name):
    pn = [str(p) for p in d["poses"]]
    i = pn.index(name)
    ev = d["evaluated"][i]
    return np.linalg.norm(ev[E[:, 0]] - ev[E[:, 1]], axis=1) / r0, d["theta"][i], d["lam"][i]


def topw(v):
    o = np.argsort(-W[v])[:3]
    return " ".join("%s %.2f" % (bones[b], W[v, b]) for b in o)


for pose, region in (("press_top", "arm"), ("pullup_top", "torso"), ("press_top_rhythm", "arm")):
    k = rn.index(region)
    sel = (reg[E[:, 0]] == k) & (reg[E[:, 1]] == k)
    rw, th, lam = ratios(dw, pose)
    rk, _, _ = ratios(dk, pose)
    print("=== %s / %s  theta %.1f lam %.3f   weights-only min %.3f   r87 min %.3f" % (pose, region, th[0], lam[0], rw[sel].min(), rk[sel].min()))
    ids = np.nonzero(sel)[0][np.argsort(rk[sel])[:8]]
    for e in ids:
        a, b = E[e]
        print("  edge %6d r87 %.3f wonly %.3f  mid %s  zone %s/%s mask %s/%s | A: %s | B: %s" % (e, rk[e], rw[e], np.round((rest[a] + rest[b]) / 2, 3), zone[a], zone[b], mask[a], mask[b], topw(a), topw(b)))
