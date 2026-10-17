"""Native proof: added samples alone preserve R41 at all83 poses; no model save."""
import os,sys,json
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/anatomy_fit')];os.environ['S7_LOCKOUT_HT']='166'
import build_original_review_candidate_r17_blender as r17
import build_original_movement_benchmarks_blender as bench
import build_original_sculpt_corrective_blender as sculpt
import build_functional_shoulder_correction_blender as correction
import original_v1_review_candidate_drives as drives
import original_v1_press_extension as px
import original_v1_shoulder_r4 as r4
from original_review_r43_native import install
source,dest=sys.argv[-2:];z=np.load(source)
res=r17._setup(ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend');body,rig=res['body'],res['runtime']
install(res,np.zeros((7,len(z['rest']),3)),z['sampling_basis']);errors=[]
for s in range(83):
 bench._reset(rig)
 if s<41:px.pose_press_full(res,s/40)
 elif s<82:
  hook=r4._S.get('extend');r4._S['extend']=None
  try:bench.pose_press(res,(s-41)/40,correction)
  finally:r4._S['extend']=hook
 else:sculpt.press_pose(res,130.)
 drives.drive(rig,body);v,f=bench._evaluated(body);p=np.array([tuple(x) for x in v]);base=z['base'][s] if s<82 else z['front_base']
 error=float(np.linalg.norm(p-base,axis=1).max()*1000);errors.append(error)
 if error>.01:raise ValueError(('Baseline interpolation changed native geometry',s,error))
report=dict(sample_count=83,max_baseline_error_mm=max(errors),errors_mm=errors,model_saved=False)
Path(dest).write_text(json.dumps(report,indent=2)+'\n');print('R43_BASELINE_PROOF',json.dumps(report),flush=True)
