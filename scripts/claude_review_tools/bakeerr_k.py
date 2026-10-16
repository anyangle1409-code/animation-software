import os
import sys
sys.path.insert(0, "/home/user/p5/scripts"); sys.path.insert(0, "/home/user/p5/scripts/anatomy_fit")
import bpy, numpy as np
import original_v1_review_candidate_drives as drives
blend, npz = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=blend)
import build_functional_shoulder_correction_blender as correction
import build_original_movement_benchmarks_blender as bench
import build_original_sculpt_corrective_blender as s4
import original_v1_press_extension as px
res = correction.build_corrected_scene(); body, rig = res["body"], res["runtime"]
drives.setup(res); px.install(); bench._reset(rig)
s4.press_pose(res, float(os.environ.get("KEY","172.0"))); drives.drive(rig, body)
V, F = bench._evaluated(body); B = np.array([tuple(v) for v in V])
print("S7 values", [(kb.name, round(kb.value, 2)) for kb in body.data.shape_keys.key_blocks if kb.name.startswith("HGPT_S7")])
T = np.load(npz)[os.environ.get("KEY","172.0")]
e = np.linalg.norm(B - T, axis=1)
gh = np.array(tuple(rig.matrix_world @ rig.pose.bones["upperarm_r"].head))
print("err mm: max %.1f p99 %.1f  >5mm %d  >10mm %d" % (e.max() * 1000, np.percentile(e, 99) * 1000, (e > 0.005).sum(), (e > 0.01).sum()))
for i in np.argsort(-e)[:12]:
    sg = 1 if B[i, 0] > 0 else -1
    gh_ = np.array(tuple(rig.matrix_world @ rig.pose.bones["upperarm_" + ("r" if sg > 0 else "l")].head))
    r = (B[i] - gh_) * np.array([sg, 1, 1]) * 100
    print("  v%d err %.1f mm at x(out) %.1f y(back) %.1f z(up) %.1f cm" % (i, e[i] * 1000, *r))
