# where does the benchmark shoulder press stretch the skin (area ratio > 2)?  per frame, clustered, rest + posed centroids
from pathlib import Path
import sys, json, os
import bpy, numpy as np
ROOT = Path("/home/user/r57src"); sys.path[:0] = ["/home/user/animation-software/scripts/shoulder_r61", str(ROOT/'scripts'), str(ROOT/'scripts/anatomy_fit')]
os.environ['S7_LOCKOUT_HT'] = '166'
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
from claude_r61_native import install
dense_path, tag = sys.argv[-2:]
zd = np.load(dense_path); delta = (zd["dense"] if "dense" in zd.files else zd["dense_delta"]).astype(float)
parent = ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017'
bpy.ops.wm.open_mainfile(filepath=str(parent/'HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend'))
st = {"i": 0}
def arr(V): return np.array([tuple(v) for v in V])
def setup(res):
    V0, F = bench._evaluated(res["body"]); st["V0"] = arr(V0); st["F"] = np.array(F); install(res, delta); drives.setup(res)
def area(V, F): return 0.5 * np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1)
def post(res):
    drives.drive(res['runtime'], res['body'])
    t = st["i"] / (bench.FRAMES - 1); st["i"] += 1
    if t < 0.49: return
    V, _ = bench._evaluated(res["body"]); V = arr(V); F = st["F"]
    a0 = area(st["V0"], F); r = area(V, F) / np.maximum(a0, 1e-12); r[a0 <= 1e-12] = 1
    bad = np.flatnonzero(r > 2); c0 = st["V0"][F[bad]].mean(1); cp = V[F[bad]].mean(1)
    lab = -np.ones(len(bad), int); k = 0
    for i in np.argsort(-r[bad]):
        if lab[i] >= 0: continue
        m = (np.linalg.norm(c0 - c0[i], axis=1) < 0.04) & (lab < 0); lab[m] = k; k += 1
    cl = sorted([dict(n=int((lab == j).sum()), max_ratio=round(float(r[bad][lab == j].max()), 2), rest=np.round(c0[lab == j].mean(0), 3).tolist(), posed=np.round(cp[lab == j].mean(0), 3).tolist()) for j in range(k)], key=lambda d: -d["n"])
    print("LOC", tag, round(t, 3), len(bad), json.dumps(cl[:5]), flush=True)
bench.run(setup=setup, post_pose=post, only=["shoulder_press"])
