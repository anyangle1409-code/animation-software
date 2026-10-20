"""Run all13 unchanged benchmarks on unsaved R52 before model creation."""
# Claude R61 copy of Work's validate_original_review_r52_benchmarks_blender.py (pinned R57 commit 025d5f28). ONLY change: it uses claude_r61_native.install,
# which allows the 166 deg S7 control (owner decision, 20 Oct). All checks and thresholds are unchanged.
from pathlib import Path
import sys,json,os
import bpy,numpy as np
ROOT=Path(os.environ['R57ROOT']).resolve();sys.path[:0]=[str(Path(__file__).resolve().parent),str(ROOT/'scripts'),str(ROOT/'scripts/anatomy_fit')]
os.environ['S7_LOCKOUT_HT']='166'
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
from claude_r61_native import install
source,solution,dest=sys.argv[-3:];z={k:v for k,v in np.load(source).items()};delta=np.load(solution)['dense_delta']
parent=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017'
bpy.ops.wm.open_mainfile(filepath=str(parent/'HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend'))
def setup(res):install(res,delta,z['sampling_basis']);drives.setup(res)
report=bench.run(setup=setup,post_pose=lambda r:drives.drive(r['runtime'],r['body']))
baseline=json.loads((parent/'r41_benchmarks.json').read_text());fail=[]
for name,b in baseline['benchmarks'].items():
 for old,new in zip(b['frames'],report['benchmarks'][name]['frames']):
  for metric in ('self_intersecting_pairs','collapse_lt_0_1','stretch_gt_2'):
   if new[metric]>old[metric]:fail.append(dict(path=name,t=new['t'],metric=metric,parent=old[metric],current=new[metric]))
Path(dest).write_text(json.dumps(dict(report=report,regressions=fail,passed=len(report['benchmarks'])==13 and not fail),indent=2,default=str)+'\n')
print('R52_UNSAVED_13_BENCHMARKS',len(fail),flush=True)


