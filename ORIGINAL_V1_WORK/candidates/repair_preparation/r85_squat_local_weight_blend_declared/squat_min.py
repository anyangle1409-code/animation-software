import json
import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
d = np.load(SP + r"\r81_arc_dump.npz", allow_pickle=True)
rest, E, reg, ev, poses = d["rest"], d["edges"], d["region"], d["evaluated"], d["poses"]
rn = [str(x) for x in d["region_names"]]
z = json.load(open(r"C:\Users\Mark\Documents\animation-software\repo\ORIGINAL_V1_WORK\candidates\repair_preparation\r81_dilated_weight_smoothing_declared\weight_smoothing_zone_declared_before_edit.json"))
zone = np.zeros(len(rest), bool)
zone[z["left_owned_vertex_ids"]] = True
zone[z["mirror_of_strict_left_vertex_ids"]] = True
print("poses", sorted(set(map(str, poses))))
idx = [i for i, p in enumerate(poses) if str(p).startswith("squat_bottom")]
print("squat entries", idx, d["lam"][idx[-1]] if idx else "")
i = idx[-1]
r0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
r1 = np.linalg.norm(ev[i][E[:, 0]] - ev[i][E[:, 1]], axis=1) / r0
for name in ("arm", "shoulder"):
    k = rn.index(name)
    sel = (reg[E[:, 0]] == k) & (reg[E[:, 1]] == k)
    order = np.argsort(r1[sel])[:8]
    ids = np.nonzero(sel)[0][order]
    print(name, "min", r1[ids[0]])
    for e in ids:
        a, b = E[e]
        print("  edge", e, "ratio %.3f" % r1[e], "rest mid", np.round((rest[a] + rest[b]) / 2, 3), "in zone", bool(zone[a]), bool(zone[b]))
