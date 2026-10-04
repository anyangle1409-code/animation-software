import numpy as np
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
w = np.load(SP + r"\r81_arc_dump.npz", allow_pickle=True); c = np.load(SP + r"\r91_full_dump.npz", allow_pickle=True)
rest, E, reg, W = c["rest"], c["edges"], c["region"], c["W"]; rn = [str(x) for x in c["region_names"]]; bones = [str(b) for b in c["bones"]]
pit = np.load(SP + r"\axl_diag_press_top.npz")["pit"]
i = [str(p) for p in c["poses"]].index("press_top"); j = [str(p) for p in w["poses"]].index("press_top")
Pw, Pc = w["evaluated"][j], c["evaluated"][i]
r0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
rw = np.linalg.norm(Pw[E[:, 0]] - Pw[E[:, 1]], axis=1) / r0
rc = np.linalg.norm(Pc[E[:, 0]] - Pc[E[:, 1]], axis=1) / r0
isp = np.zeros(len(rest), bool); isp[pit] = True
near = np.zeros(len(rest), bool)
for a, b in E:
    if isp[a] or isp[b]: near[a] = near[b] = True
sel = near[E[:, 0]] & near[E[:, 1]]
print("edges touching the pit zone: %d" % sel.sum())
print("   weights-only edge ratio: min %.2f p50 %.2f p95 %.2f max %.2f   |  r91: min %.2f p50 %.2f p95 %.2f max %.2f" % (rw[sel].min(), np.median(rw[sel]), np.percentile(rw[sel], 95), rw[sel].max(), rc[sel].min(), np.median(rc[sel]), np.percentile(rc[sel], 95), rc[sel].max()))
# weight gradient: along edges, change in the 'arm-driven' share (upperarm+scapula+clavicle+forearm) per cm at rest
armb = [k for k, b in enumerate(bones) if b.startswith(("upperarm_l", "scapula_l", "clavicle_l"))]
share = W[:, armb].sum(axis=1)
g = np.abs(share[E[:, 0]] - share[E[:, 1]]) / (r0 * 100)
print("   arm-driven weight share change per cm along those edges: p50 %.3f p95 %.3f max %.3f; elsewhere in the left torso p95 %.3f" % (np.median(g[sel]), np.percentile(g[sel], 95), g[sel].max(), np.percentile(g[(reg[E[:, 0]] == rn.index('torso')) & (rest[E[:, 0], 0] < 0) & ~sel], 95)))
# the stretched edges in the left torso/shoulder transition in weights-only: where, and how the pit vertices relate
st = np.nonzero(((reg[E[:, 0]] == rn.index('torso')) | (reg[E[:, 0]] == rn.index('shoulder'))) & (rest[E[:, 0], 0] < 0) & (rw > 2.5))[0]
print("   weights-only press_top left torso/shoulder edges with ratio > 2.5: %d (r91: %d)" % (len(st), int(((rc[st]) > 2.5).sum())))
mid = np.array([(rest[a] + rest[b]) / 2 for a, b in E[st]])
print("   their rest-mid bbox", np.round(mid.min(0), 3), np.round(mid.max(0), 3), " pit centroid", np.round(rest[pit].mean(0), 3))
dist = np.linalg.norm(mid - rest[pit].mean(0), axis=1)
print("   distance of those stretched edges to the pit centroid: median %.3f m; r91 ratio of the same edges: median %.2f (weights-only median %.2f)" % (np.median(dist), np.median(rc[st]), np.median(rw[st])))