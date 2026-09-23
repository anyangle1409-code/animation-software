"""Verify V8 is an isolated, symmetric knee-surface edit from V7."""
from pathlib import Path
import hashlib,json
import numpy as np
from scripts.candidate_quick_check import load_glb,accessor,topology_stats

r=Path(__file__).resolve().parents[1]
prefix='HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_'
source=r/(prefix+'v7_knee_retopology.glb')
target=r/(prefix+'v8_knee_anatomy.glb')
bare=r/(prefix+'v8_knee_anatomy_BARE.glb')
blend=r/(prefix+'v8_knee_anatomy.blend')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source)=='f6346ac4da1508cc15bb16d6406d7cc0cc8c97a92c173d57d2d422bcb9a59d6d'
a,ab=load_glb(source);b,bb=load_glb(target);c,cb=load_glb(bare)
assert a==b and bb==cb
pa=a['meshes'][0]['primitives'][0];pb=b['meshes'][0]['primitives'][0]
for field,index in pa['attributes'].items():
    if field not in ('POSITION','NORMAL'):
        assert np.array_equal(accessor(a,ab,index),accessor(b,bb,pb['attributes'][field])),field
assert np.array_equal(accessor(a,ab,pa['indices']),accessor(b,bb,pb['indices']))
old=accessor(a,ab,pa['attributes']['POSITION']).astype(float)
new=accessor(b,bb,pb['attributes']['POSITION']).astype(float)
delta=new-old
changed=np.flatnonzero(np.linalg.norm(delta,axis=1)>1e-7)
assert len(changed)>0
assert np.all((np.abs(old[changed,0])>.025)&(np.abs(old[changed,0])<.28))
assert np.all((old[changed,1]>.40)&(old[changed,1]<.68))
assert np.linalg.norm(delta,axis=1).max()<.010
left=changed[old[changed,0]>0];right=changed[old[changed,0]<0]
left_sum=float(np.linalg.norm(delta[left],axis=1).sum())
right_sum=float(np.linalg.norm(delta[right],axis=1).sum())
assert abs(left_sum-right_sum)/left_sum<.02
stats=topology_stats(b,bb)
assert stats['triangles']==62961 and stats['degenerate_triangles']==0 and stats['nonmanifold_edges_gt2']==0
seams=json.loads((r/'reports/knee_seam_v5.json').read_text())['knees']
max_gap=0.
for file in (r/'reports/poses_v8_knee_anatomy').glob('*_candidate.json'):
    p=np.asarray(json.loads(file.read_text())['meshes'][0]['positions'])
    for side in seams.values():
        x,y=side['paths'];max_gap=max(max_gap,float(np.linalg.norm(p[x]-p[y],axis=1).max()*1000))
pose_count=len(list((r/'reports/poses_v8_knee_anatomy').glob('*_candidate.json')))
assert pose_count==28 and max_gap<1e-4
report={'v7_sha256_unchanged':sha(source),'protected_glb_fields_unchanged':True,
        'changed_knee_vertices':len(changed),'left_right_changed':[len(left),len(right)],
        'left_right_displacement_sum_mm':[left_sum*1000,right_sum*1000],
        'max_rest_move_mm':float(np.linalg.norm(delta,axis=1).max()*1000),
        'saved_pose_count':pose_count,'max_paired_seam_pose_gap_mm':max_gap,
        'topology':stats,'artifacts':{p.name:sha(p) for p in (target,bare,blend)}}
(r/'reports/final_integrity_v8_knee_anatomy.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
