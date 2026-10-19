"""161 actual full-press poses on R41 and R52; no model save."""
from pathlib import Path
import sys,os,json
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/anatomy_fit')];os.environ['S7_LOCKOUT_HT']='166'
import build_original_review_candidate_r17_blender as r17
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
import original_v1_press_extension as px
from original_review_r52_native import install
from original_review_r52_temporal import oscillation
source,solution,dest=sys.argv[-3:]
with np.load(source) as z:rest=z['rest']
dense=np.load(solution)['dense_delta'];res=r17._setup(ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend');body,rig=res['body'],res['runtime']
back=(abs(rest[:,0])>.08)&(abs(rest[:,0])<.25)&(rest[:,2]>1.27)&(rest[:,2]<1.49)&(rest[:,1]>.025)
def collect():
 values=[]
 for i in range(161):
  bench._reset(rig);px.pose_press_full(res,i/160);drives.drive(rig,body);p=np.array([tuple(v) for v in bench._evaluated(body)[0]])
  values.append(p[back])
  if i%40==0:print('R52_DENSE_NATIVE_FRAME',i,flush=True)
 return np.array(values)
baseline=collect();install(res,dense);bpy.context.view_layer.update();current=collect()
before=np.linalg.norm(np.diff(baseline,n=2,axis=0),axis=2);after=np.linalg.norm(np.diff(current,n=2,axis=0),axis=2);excess=float((after-before).max()*1000)
normalized=excess*16.;step=oscillation(dense)
early=np.array([px.press_state(i/160)[0]<110. for i in range(161)]);outward=(current-baseline)[:,:,0]*np.sign(rest[back,0])[None];early_outward=float(np.maximum(outward[early],0).max()*1000)
report=dict(samples=161,actual_native=True,extra_frame_acceleration_mm=excess,original40_step_equivalent_excess_mm=normalized,guard_original_grid_mm=.5,early_outward_increment_mm=early_outward,early_outward_guard_mm=.05,oscillation=step,passed=bool(normalized<=.5 and step['passed'] and early_outward<=.05),model_saved=False,approved=False,
 note='New stricter temporal coverage; original41-pose test remains unchanged. Normalization uses squared frame-interval ratio(160/40)^2.')
Path(dest).write_text(json.dumps(report,indent=2)+'\n');np.savez_compressed(str(dest)+'.points.npz',baseline=baseline,current=current,back_vertex_ids=np.flatnonzero(back));print('R52_DENSE_NATIVE_RESULT',json.dumps(report),flush=True)
