import sys, bpy
def W(p):
    bpy.ops.wm.open_mainfile(filepath=p); b = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
    gi = {g.index: g.name for g in b.vertex_groups}
    return [{gi[e.group]: e.weight for e in v.groups} for v in b.data.vertices]
a, b = W(sys.argv[-2]), W(sys.argv[-1])
for s in "lr":
    n = f"upperarm_{s}"; d = [(b[i].get(n, 0) - a[i].get(n, 0), i) for i in range(len(a))]
    neg = sorted(x for x in d if x[0] < -1e-3)
    print(s, "dropped", len(neg), "gained>0.05", sum(x[0] > 0.05 for x in d))
    for dv, i in neg[:4]: print("  ", round(dv, 3), {k: round(v, 3) for k, v in a[i].items()}, "->", {k: round(v, 3) for k, v in b[i].items()})
