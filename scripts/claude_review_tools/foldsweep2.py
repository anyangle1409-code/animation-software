# sharp new folds near the right arm root along the press (evaluated, all keys driven); optional npz targets at key angles
import sys, os
sys.path.insert(0, "/home/user/p5/scripts"); sys.path.insert(0, "/home/user/p5/scripts/anatomy_fit")
import bpy, numpy as np
from collections import defaultdict
import original_v1_review_candidate_drives as drives
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
import build_functional_shoulder_correction_blender as correction
import build_original_movement_benchmarks_blender as bench
import build_original_sculpt_corrective_blender as s4
import original_v1_press_extension as px
res = correction.build_corrected_scene(); body, rig = res["body"], res["runtime"]
drives.setup(res); px.install(); bench._reset(rig)
vals = {kb.name: kb.value for kb in body.data.shape_keys.key_blocks}
for kb in body.data.shape_keys.key_blocks[1:]: kb.value = 0.0
V0, F = bench._evaluated(body); R = np.array([tuple(v) for v in V0]); Fa = np.array(F)
ef = defaultdict(list)
for k, f in enumerate(F):
    for i in range(3): ef[tuple(sorted((f[i], f[(i + 1) % 3])))].append(k)
E = np.array([k for k, v in ef.items() if len(v) == 2]); FF = np.array([ef[tuple(e)] for e in E])
def fn(Y):
    n = np.cross(Y[Fa[:, 1]] - Y[Fa[:, 0]], Y[Fa[:, 2]] - Y[Fa[:, 0]]); return n / np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-15)
def dih(Y):
    n = fn(Y); return np.degrees(np.arccos(np.clip((n[FF[:, 0]] * n[FF[:, 1]]).sum(1), -1, 1)))
dR = dih(R)
TH = float(os.environ.get("TH", 30))
for ht in [float(x) for x in os.environ.get("HTS", "120,130,139,145,151,156").split(",")]:
    s4.press_pose(res, ht); drives.drive(rig, body)
    V, _ = bench._evaluated(body); P = np.array([tuple(v) for v in V])
    gh = np.array(tuple(rig.matrix_world @ rig.pose.bones["upperarm_r"].head))
    dP = dih(P); mid = (P[E[:, 0]] + P[E[:, 1]]) / 2; rel = mid - gh
    near = np.linalg.norm(rel, axis=1) < 0.18
    sel = near & (dP > TH) & (dP - dR > 15)
    back = sel & (rel[:, 1] > 0)
    c = (rel[back].mean(0) * 100).round(1) if back.any() else None
    s7 = {kb.name: round(kb.value, 2) for kb in body.data.shape_keys.key_blocks if kb.name.startswith("HGPT_S7_DELT_r") and kb.value > 0.01}
    print("HT %5.1f folds>%d near %3d behind %3d max %.0f centre %s s7 %s" % (ht, TH, sel.sum(), back.sum(), dP[near].max(), c, s7), flush=True)
    for i in np.argsort(-dP * near)[:8]: print("   edge %.0f deg at (out %.1f, back %.1f, up %.1f) cm rest %.0f" % (dP[i], *(rel[i] * np.array([1,1,1]) * 100), dR[i]))
    if os.environ.get("NOKEYS"):
        pass
