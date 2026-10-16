import sys, bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
b = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; rig = b.find_armature(); W = rig.matrix_world
gi = {g.index: g.name for g in b.vertex_groups}
print([n for n in gi.values() if n.endswith("_r") and ("arm" in n or "elbow" in n or "twist" in n)])
el = np.array(tuple(W @ rig.data.bones["forearm_r"].head_local)); gh = np.array(tuple(W @ rig.data.bones["upperarm_r"].head_local)); wr = np.array(tuple(W @ rig.data.bones["forearm_r"].tail_local))
au = (el - gh) / np.linalg.norm(el - gh); af = (wr - el) / np.linalg.norm(wr - el)
print("upper len %.3f fore len %.3f rest elbow angle %.1f" % (np.linalg.norm(el-gh), np.linalg.norm(wr-el), np.degrees(np.arccos(au @ af))))
M = b.matrix_world
P = np.array([tuple(M @ v.co) for v in b.data.vertices])
rel = P - el; t = np.where(rel @ au < 0, rel @ au, rel @ af)
r = np.linalg.norm(rel - np.outer(rel @ au, au), axis=1)
for lo in range(-14, 14, 2):
    m = np.where((t*100 >= lo) & (t*100 < lo+2) & (r < 0.07) & (P[:,0] > 0.15))[0]
    if not len(m): continue
    acc = {}
    for i in m:
        for e in b.data.vertices[int(i)].groups:
            acc[gi[e.group]] = acc.get(gi[e.group], 0) + e.weight / len(m)
    print("%+3d cm n %3d " % (lo, len(m)), {k: round(v, 2) for k, v in sorted(acc.items(), key=lambda kv: -kv[1]) if v > 0.02})
