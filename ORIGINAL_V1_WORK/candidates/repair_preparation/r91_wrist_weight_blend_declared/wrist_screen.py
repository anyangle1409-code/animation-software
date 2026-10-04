import json
import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
REPO = r"C:\Users\Mark\Documents\animation-software\repo"
decl = json.load(open(REPO + r"\ORIGINAL_V1_WORK\candidates\repair_preparation\r91_wrist_weight_blend_declared\wrist_patch_declared_before_edit.json"))
ids = np.array(decl["left_owned_vertex_ids"] + decl["mirror_of_strict_left_vertex_ids"])
p47, p90 = np.load(SP + r"\pl_r47.npz"), np.load(SP + r"\pl_r90.npz")
assert [str(x) for x in p47["bones"]] == [str(x) for x in p90["bones"]]
vg_bones = [str(x) for x in p90["bones"]]            # vertex-group names in the blend (sorted)
W47, W90 = p47["W"], p90["W"]
d = np.load(SP + r"\hd_r90.npz", allow_pickle=True)
dump_bones = [str(b) for b in d["bones"]]
rest, E, reg, mats = d["rest"], d["edges"], d["region"], d["mats"].astype(np.float64)
rn = [str(x) for x in d["region_names"]]
pn = [str(p) for p in d["poses"]]
i = pn.index("pushup_bottom")
# map vertex-group columns to dump deform-bone columns
col = [dump_bones.index(b) if b in dump_bones else -1 for b in vg_bones]
R1 = np.c_[rest, np.ones(len(rest))]
r0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)


def top4(W):
    W = W.copy()
    idx = np.argsort(-W, axis=1)[:, 4:]
    np.put_along_axis(W, idx, 0, axis=1)
    return W / W.sum(1, keepdims=True)


def dumpW(Wvg):
    out = np.zeros((len(rest), len(dump_bones)))
    for j, c in enumerate(col):
        if c >= 0:
            out[:, c] = Wvg[:, j]
    return out


def hand_stats(Wvg):
    Wd = dumpW(Wvg)
    P = np.einsum("vij,vj->vi", np.einsum("vb,bij->vij", Wd, mats[i]), R1)[:, :3]
    r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / r0
    out = {}
    for g in ("hand", "arm", "thumb"):
        k = rn.index(g)
        s = (reg[E[:, 0]] == k) & (reg[E[:, 1]] == k)
        out[g] = (round(float(r[s].min()), 3), round(float(r[s].max()), 3))
    return out


print("r90 weights:", hand_stats(W90))
print("r47 weights:", hand_stats(W47))
for lam in (0.25, 0.5, 0.6, 0.7, 0.75, 1.0):
    W = W90.copy()
    W[ids] = top4((1 - lam) * W90[ids] + lam * W47[ids])
    print("lambda %.2f" % lam, hand_stats(W))
    np.savez(SP + r"\wrist_sol_l%.2f.npz" % lam, vertices=ids, bones=np.array(vg_bones), weights=W[ids])
