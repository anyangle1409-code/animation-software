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
OUT=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r39_20261017'
res=r17._setup(OUT/'HGPT_ORIGINAL_V1_REVIEW_R39_CODEX.blend');body,rig=res['body'],res['runtime']
with np.load('/tmp/r39-response/response.npz') as z:
    bases=z['base'];faces=z['faces']
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
        parent=bases[len(rows)][faces];tri=p[faces]
        ref=np.cross(parent[:,1]-parent[:,0],parent[:,2]-parent[:,0])
        now=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
        count=int((((ref*now).sum(1)<0)&(np.linalg.norm(ref,axis=1)>2e-12)).sum())
        rows.append({'path':path,'t':i/40,'normal_rotations_over_90_degrees':count})
report={'reference':'R38 same-pose native surface','sample_count':len(rows),'samples':rows,'passed':not any(x['normal_rotations_over_90_degrees'] for x in rows)}
(OUT/'r39_orientation.json').write_text(json.dumps(report,indent=2)+'\n')
print('R39_FINAL_ORIENTATION',json.dumps(report),flush=True)
