# local copy of the R61 benchmark gate: same checks, dense from an exported candidate (no source.npz needed)
from pathlib import Path
import sys, json, os
import bpy, numpy as np
ROOT = Path("/home/user/r57src"); sys.path[:0] = ["/home/user/animation-software/scripts/shoulder_r61", str(ROOT/'scripts'), str(ROOT/'scripts/anatomy_fit')]
os.environ['S7_LOCKOUT_HT'] = '166'
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
from claude_r61_native import install
dense_path, dest = sys.argv[-2:]
zd = np.load(dense_path); delta = (zd["dense"] if "dense" in zd.files else zd["dense_delta"]).astype(float)
parent = ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017'
bpy.ops.wm.open_mainfile(filepath=str(parent/'HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend'))
def setup(res): install(res, delta); drives.setup(res)
report = bench.run(setup=setup, post_pose=lambda r: drives.drive(r['runtime'], r['body']))
baseline = json.loads((parent/'r41_benchmarks.json').read_text()); fail = []
for name, b in baseline['benchmarks'].items():
    for old, new in zip(b['frames'], report['benchmarks'][name]['frames']):
        for metric in ('self_intersecting_pairs', 'collapse_lt_0_1', 'stretch_gt_2'):
            if new[metric] > old[metric]: fail.append(dict(path=name, t=new['t'], metric=metric, parent=old[metric], current=new[metric]))
Path(dest).write_text(json.dumps(dict(regressions=fail), indent=1, default=str))
print("BENCH", dense_path, len(fail), json.dumps(fail), flush=True)
