"""Fresh-process orientation diagnostic on the final saved model, both paths."""
from pathlib import Path
import sys,json,os
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/anatomy_fit')]
os.environ['S7_LOCKOUT_HT']='166'
import build_original_review_candidate_r17_blender as r17
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
import original_v1_press_extension as px
import original_v1_shoulder_r4 as r4
import build_functional_shoulder_correction_blender as correction
OUT=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017'
res=r17._setup(OUT/'HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend');body,rig=res['body'],res['runtime']
with np.load('/tmp/r41-response/response.npz') as z:
    bases=z['base'];faces=z['faces'];front_base=z['front_base'];rest=z['rest']
from original_review_r41_strain import area_safety
area_rows=[]
rows=[]
for path in ('press','benchmark_press'):
    for i in range(41):
        bench._reset(rig)
        if path=='press':px.pose_press_full(res,i/40)
        else:
            hook=r4._S.get('extend');r4._S['extend']=None
            try:bench.pose_press(res,i/40,correction)
            finally:r4._S['extend']=hook
        drives.drive(rig,body)
        points,actual_faces=bench._evaluated(body);p=np.array([tuple(v) for v in points])
        if not np.array_equal(actual_faces,faces):raise ValueError('Final orientation topology mismatch')
        if not np.isfinite(p).all():raise ValueError('Nonfinite final geometry')
        area_rows.append(area_safety(p,bases[len(rows)],rest,faces))
        parent=bases[len(rows)][faces];tri=p[faces]
        ref=np.cross(parent[:,1]-parent[:,0],parent[:,2]-parent[:,0])
        now=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
        count=int((((ref*now).sum(1)<0)&(np.linalg.norm(ref,axis=1)>2e-12)).sum())
        rows.append({'path':path,'t':i/40,'normal_rotations_over_90_degrees':count})
import build_original_sculpt_corrective_blender as sculpt
bench._reset(rig);sculpt.press_pose(res,130.);drives.drive(rig,body)
points,_=bench._evaluated(body);p=np.array([tuple(v) for v in points]);tri=p[faces];parent=front_base[faces]
area_rows.append(area_safety(p,front_base,rest,faces))
ref=np.cross(parent[:,1]-parent[:,0],parent[:,2]-parent[:,0]);now=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
front_count=int((((ref*now).sum(1)<0)&(np.linalg.norm(ref,axis=1)>2e-12)).sum())
report={'reference':'R40 same-pose native surface','sample_count':len(rows),'samples':rows,'front_130_normal_rotations':front_count,'passed':front_count==0 and not any(x['normal_rotations_over_90_degrees'] for x in rows)}
report['area_samples']=area_rows
report['area_safety_passed']=len(area_rows)==83 and all(x['passed'] for x in area_rows)
report['passed']=report['passed'] and report['area_safety_passed']
(OUT/'r41_orientation.json').write_text(json.dumps(report,indent=2)+'\n')
print('R41_FINAL_ORIENTATION',json.dumps(report),flush=True)
