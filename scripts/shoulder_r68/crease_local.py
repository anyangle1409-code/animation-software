# local copy of the gate's posterior-crease measure: dihedral angles of the rear shoulder edges at all 82 gate poses
# (main press 0-40 on the current path, Work's benchmark press 41-81), saved per sample for comparison between candidates
import os, sys, json
from pathlib import Path
import bpy, numpy as np
ROOT = Path("/home/user/r57src"); sys.path[:0] = ["/home/user/animation-software/scripts/shoulder_r61", str(ROOT/'scripts'), str(ROOT/'scripts/anatomy_fit')]
os.environ['S7_LOCKOUT_HT'] = '166'
import build_original_review_candidate_r17_blender as r17
import build_original_movement_benchmarks_blender as bench
import build_functional_shoulder_correction_blender as correction
import original_v1_review_candidate_drives as drives
import original_v1_press_extension as px
import original_v1_shoulder_r4 as r4
from original_review_r41_front import edge_pairs, angles
from claude_r61_native import install
dense_path, dest = sys.argv[-2:]
zd = np.load(dense_path); delta = (zd["dense"] if "dense" in zd.files else zd["dense_delta"]).astype(float)
res = r17._setup(ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend'); body, rig = res['body'], res['runtime']
install(res, delta); bpy.context.view_layer.update()
_, F = bench._evaluated(body); faces = np.array(F)
rest = np.array([tuple(v.co) for v in body.data.vertices])
e, ff = edge_pairs(faces); r = rest[e].mean(1)
mask = (abs(r[:, 0]) > .08) & (abs(r[:, 0]) < .35) & (r[:, 1] > .025) & (r[:, 2] > 1.20) & (r[:, 2] < 1.51)
ft = faces[ff[mask]]
out = []
for s in range(82):
    bench._reset(rig)
    if s < 41: px.pose_press_full(res, s / 40)
    else:
        hook = r4._S.get('extend'); r4._S['extend'] = None
        try: bench.pose_press(res, (s - 41) / 40, correction)
        finally: r4._S['extend'] = hook
    drives.drive(rig, body); pp, _ = bench._evaluated(body); p = np.array([tuple(v) for v in pp])
    out.append(angles(p, ft))
np.savez_compressed(dest, ang=np.array(out), edges=e[mask], rest_mid=r[mask])
print("CREASE_DONE", flush=True)
