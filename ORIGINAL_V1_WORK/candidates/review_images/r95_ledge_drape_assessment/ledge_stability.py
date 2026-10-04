import json
import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
REPO = r"C:\Users\Mark\Documents\animation-software\repo"
d = np.load(SP + r"\r95_full_dump.npz", allow_pickle=True)
rest, reg, tris, E = d["rest"], d["region"], d["tris"], d["edges"]
rn = [str(x) for x in d["region_names"]]
poses = [str(p) for p in d["poses"]]
# zones as vertex sets (same rule as ledge_drape.py)
ups = np.isin(reg, [rn.index("torso"), rn.index("shoulder"), rn.index("neck")])
ledge = ups & (rest[:, 1] > 0.0) & (rest[:, 2] > 1.20) & (rest[:, 2] < 1.46) & (np.abs(rest[:, 0]) < 0.24)
drape = ups & (rest[:, 1] > 0.0) & (rest[:, 2] >= 1.46) & (np.abs(rest[:, 0]) < 0.26)
# 1. self-intersection pairs of press_top / rhythm / hang that touch the zones (exact pair list from the committed r95 evidence)
pl = json.load(open(REPO + r"\ORIGINAL_V1_WORK\candidates\repair_checks\axilla_r95\pushup_pair_list.json"))
print("push-up pair list is for pushup_bottom only; running the exact pair lists for the overhead poses is done by the Blender tool below")
# 2. arc stability: frame-to-frame motion of the zone vertices along each arc relative to the mean step
for arc in ("press_top", "pullup_hang", "press_top_rhythm"):
    fr = [0.0]
    names = ["neutral"]
    for f in ("0.250", "0.375", "0.500", "0.625", "0.750", "0.875"):
        names.append("%s@%s" % (arc, f))
    names.append(arc)
    # use neutral (rest) as the first sample
    P = [d["evaluated"][poses.index(n)] for n in names if n in poses]
    for nm, z in (("ledge", ledge), ("drape", drape)):
        steps = [np.linalg.norm(P[i + 1][z] - P[i][z], axis=1) for i in range(len(P) - 1)]
        mx = [s.max() * 100 for s in steps]
        # smoothness of the sequence: ratio of the largest step to the median step per vertex (jumps would show as large ratios)
        ratio = max((steps[i].max() / max(np.median([s.max() for s in steps]), 1e-9)) for i in range(len(steps)))
        print("%-18s %-6s max vertex step per interval (cm): %s | largest/median step %.2f" % (arc, nm, " ".join("%.1f" % m for m in mx), ratio))
