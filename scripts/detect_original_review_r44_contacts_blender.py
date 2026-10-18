"""Actual unsaved native R41+delta BVH, affine and area checks at all83poses."""
import os,sys,json
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/anatomy_fit')]
os.environ['S7_LOCKOUT_HT']='166'
import build_original_review_candidate_r17_blender as r17
import build_original_movement_benchmarks_blender as bench
import build_original_sculpt_corrective_blender as sculpt
import build_functional_shoulder_correction_blender as correction
import original_v1_review_candidate_drives as drives
import original_v1_press_extension as px
import original_v1_shoulder_r4 as r4
from original_review_r41_strain import area_safety
source,solution,dest=sys.argv[-3:];z=np.load(source);delta=np.load(solution)['delta'];faces=z['faces'];fs=[set(f) for f in faces]
res=r17._setup(ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend');body,rig=res['body'],res['runtime'];blocks=body.data.shape_keys.key_blocks
from original_review_r43_native import install
install(res,delta,z['sampling_basis']);bpy.context.view_layer.update()
def pairs(p):
 tree=BVHTree.FromPolygons([Vector(v) for v in p],faces,all_triangles=True)
 return {(a,b) for a,b in tree.overlap(tree) if a<b and not(fs[a]&fs[b])}
contacts=[];samples=[];current=[]
for s in range(83):
 bench._reset(rig)
 if s<41:px.pose_press_full(res,s/40)
 elif s<82:
  hook=r4._S.get('extend');r4._S['extend']=None
  try:bench.pose_press(res,(s-41)/40,correction)
  finally:r4._S['extend']=hook
 else:sculpt.press_pose(res,130.)
 drives.drive(rig,body);pp,ff=bench._evaluated(body);p=np.array([tuple(v) for v in pp])
 if not np.array_equal(ff,faces):raise ValueError('Native response topology differs')
 current.append(p)
 base=z['base'][s] if s<82 else z['front_base']
 a=z['mat'][s] if s<82 else z['front_mat'];w=z['weight'][s] if s<82 else z['front_weight']
 predicted=base+np.einsum('nij,nj->ni',a,np.einsum('kn,knj->nj',w,delta))
 error=float(np.linalg.norm(p-predicted,axis=1).max()*1000)
 if error>.01:raise ValueError(('Native affine prediction invalid',s,error))
 before=pairs(base);after=pairs(p);extra=after-before
 contacts.extend(dict(sample=s,a=int(a),b=int(b)) for a,b in sorted(extra))
 row=area_safety(p,base,z['rest'],faces)
 a=base[faces];b=p[faces];cr0=np.cross(a[:,1]-a[:,0],a[:,2]-a[:,0]);cr1=np.cross(b[:,1]-b[:,0],b[:,2]-b[:,0])
 reversed_count=int((((cr0*cr1).sum(1)<0)&(np.linalg.norm(cr0,axis=1)>2e-12)).sum())
 row['passed']=row['passed'] and reversed_count==0
 row.update(sample=s,parent_pairs=len(before),current_pairs=len(after),new_contact_pairs=len(extra),affine_error_mm=error,normal_rotations_over_90_degrees=reversed_count);samples.append(row)
 print('R44_NATIVE_SAMPLE',s,len(extra),row['passed'],error,flush=True)
from original_review_r41_front import edge_pairs,angles
rest=z['rest'];back=(abs(rest[:,0])>.08)&(abs(rest[:,0])<.25)&(rest[:,2]>1.27)&(rest[:,2]<1.49)&(rest[:,1]>.025)
acc=np.linalg.norm(np.diff(np.array(current[:41])[:,back],n=2,axis=0),axis=2)
old=np.linalg.norm(np.diff(z['base'][:41,back],n=2,axis=0),axis=2)
motion_excess=float((acc-old).max()*1000)
e,ff=edge_pairs(faces);r=rest[e].mean(1);mask=(abs(r[:,0])>.08)&(abs(r[:,0])<.35)&(r[:,1]>.025)&(r[:,2]>1.20)&(r[:,2]<1.51)&z['free'].any(0)[e].any(1);ft=faces[ff[mask]]
rear=max(float((angles(current[s],ft)-angles(z['base'][s],ft)).max()) for s in range(82))
report=dict(contacts=contacts,sample_count=82,front_130=samples[-1],samples=samples,back_motion_excess_mm=motion_excess,posterior_crease_excess_degrees=rear)
report['passed']=not contacts and all(r['passed'] for r in samples) and motion_excess<=.5 and rear<=2.
Path(dest).write_text(json.dumps(report,indent=2)+'\n')
print('R44_NATIVE_FEASIBILITY',len(contacts),motion_excess,rear,report['passed'],flush=True)
