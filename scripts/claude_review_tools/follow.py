# how far upper-arm skin lags the humerus: posed position vs the position it would have if it moved rigidly with the
# upper-arm bone, binned by position along the arm (rest), at several press elevations
import sys, os
sys.path.insert(0, "/home/user/p5/scripts"); sys.path.insert(0, "/home/user/p5/scripts/anatomy_fit")
import bpy, numpy as np
import original_v1_review_candidate_drives as drives
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
import build_functional_shoulder_correction_blender as correction
import build_original_movement_benchmarks_blender as bench
import original_v1_press_extension as px
res = correction.build_corrected_scene(); body, rig = res["body"], res["runtime"]
drives.setup(res); px.install(); bench._reset(rig)
for kb in body.data.shape_keys.key_blocks[1:]: kb.value = 0.0
V0, F = bench._evaluated(body); R = np.array([tuple(v) for v in V0])
W = rig.matrix_world
gi = {g.index: g.name for g in body.vertex_groups}
wu = np.zeros(len(R)); other = {}
for v in body.data.vertices:
    for e in v.groups:
        n = gi[e.group]
        if n == "upperarm_r": wu[v.index] += e.weight
        elif e.weight > 0.05 and n.endswith("_r") and not n.startswith(("forearm", "hand")):
            other[n] = other.get(n, 0) + 1
print("other groups on the right side (vertex counts):", sorted(other.items(), key=lambda x: -x[1])[:10])
b = rig.data.bones["upperarm_r"]
h0 = np.array(tuple(W @ b.head_local)); t0 = np.array(tuple(W @ b.tail_local)); L = np.linalg.norm(t0 - h0); ax0 = (t0 - h0) / L
fr = (R - h0) @ ax0 / L
sel = (wu > 0.05)
band = sel & (fr >= 0.25) & (fr < 0.55)
tot = {}
for i in np.where(band)[0]:
    for e in body.data.vertices[i].groups: tot[gi[e.group]] = tot.get(gi[e.group], 0) + e.weight
print("BAND 25-55% mean weights:", sorted(((k, round(v / band.sum(), 3)) for k, v in tot.items()), key=lambda x: -x[1])[:8])
for t in (0.4, 0.5, 0.65, 0.8, 1.0):
    a = px.pose_press_full(res, t); drives.drive(rig, body)
    if os.environ.get("NOKEYS"):
        for kb in body.data.shape_keys.key_blocks[1:]: kb.value = 0.0
    V, _ = bench._evaluated(body); P = np.array([tuple(v) for v in V])
    pb = rig.pose.bones["upperarm_r"]
    M = np.array(W @ pb.matrix @ b.matrix_local.inverted() @ W.inverted())
    rig_ = (np.c_[R, np.ones(len(R))] @ M.T)[:, :3]
    d = np.linalg.norm(P - rig_, axis=1)
    print("t %.2f ht %.0f elbow %.0f | lag (mm) by position along the upper arm (0 = shoulder joint, 1 = elbow), mean / upperarm weight:" % (t, a["humerothoracic_elevation"], a["elbow_flexion"]))
    for lo in np.arange(-0.1, 0.9, 0.1):
        m = sel & (fr >= lo) & (fr < lo + 0.1)
        if m.sum(): print("   %4.1f-%4.1f  n %4d  lag %5.1f  w_up %.2f" % (lo, lo + 0.1, m.sum(), d[m].mean() * 1000, wu[m].mean()))
