import sys, os
sys.path.insert(0, "/home/user/p5/scripts"); sys.path.insert(0, "/home/user/p5/scripts/anatomy_fit")
import bpy, numpy as np
import original_v1_review_candidate_drives as drives
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2])
bpy.context.scene["hgpt_press_lockout_ht"] = float(os.environ.get("LOCK_HT", 172))
import build_functional_shoulder_correction_blender as correction
import build_original_movement_benchmarks_blender as bench
import build_original_sculpt_corrective_blender as s4
import original_v1_press_extension as px
res = correction.build_corrected_scene(); body, rig = res["body"], res["runtime"]
drives.setup(res); px.install(); bench._reset(rig)
for kb in body.data.shape_keys.key_blocks[1:]: kb.value = 0.0
V0, F = bench._evaluated(body); R = np.array([tuple(v) for v in V0]); Fa = np.array(F)
key = os.environ["KEY"]; s4.press_pose(res, float(key)); drives.drive(rig, body)
V, _ = bench._evaluated(body); P = np.array([tuple(v) for v in V])
X = np.load(sys.argv[-1])[key]
ar = lambda Y: np.linalg.norm(np.cross(Y[Fa[:, 1]] - Y[Fa[:, 0]], Y[Fa[:, 2]] - Y[Fa[:, 0]]), axis=1) / 2
A0 = ar(R)
for name, Y in (("posed", P), ("target", X)):
    bad = np.where(ar(Y) / np.maximum(A0, 1e-12) < 0.1)[0]
    gi = {g.index: g.name for g in body.vertex_groups}
    for k in bad:
        v = Fa[k][0]; grp = max(body.data.vertices[int(v)].groups, key=lambda e: e.weight)
        print(name, "face", k, "at", (Y[Fa[k]].mean(0) * 100).round(1), "rest-area ratio %.3f" % (ar(Y)[k] / A0[k]), "main bone", gi[grp.group])
