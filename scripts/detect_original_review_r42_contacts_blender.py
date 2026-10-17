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
from original_review_r42_strain import area_safety
source,solution,dest=sys.argv[-3:];z=np.load(source);delta=np.load(solution)['delta'];faces=z['faces'];fs=[set(f) for f in faces]
res=r17._setup(ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend');body,rig=res['body'],res['runtime'];blocks=body.data.shape_keys.key_blocks
def coords(k):
 a=np.empty(len(k.data)*3);k.data.foreach_get('co',a);return a.reshape(-1,3)
rest=coords(blocks[0])
for k,ht in enumerate((110,120,130,136,145,156,166)):
 for side in ('l','r'):
  add=delta[k].copy();add[rest[:,0]*(1 if side=='r' else -1)<=0]=0
  kb=blocks[f'HGPT_S7_DELT_{side}_{ht}'];kb.data.foreach_set('co',(coords(kb)+add).ravel())
body.data.update();bpy.context.view_layer.update()
def pairs(p):
 tree=BVHTree.FromPolygons([Vector(v) for v in p],faces,all_triangles=True)
 return {(a,b) for a,b in tree.overlap(tree) if a<b and not(fs[a]&fs[b])}
contacts=[];samples=[]
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
 base=z['base'][s] if s<82 else z['front_base']
 a=z['mat'][s] if s<82 else z['front_mat'];w=z['weight'][s] if s<82 else z['front_weight']
 predicted=base+np.einsum('nij,nj->ni',a,np.einsum('kn,knj->nj',w,delta))
 error=float(np.linalg.norm(p-predicted,axis=1).max()*1000)
 if error>.01:raise ValueError(('Native affine prediction invalid',s,error))
 before=pairs(base);after=pairs(p);extra=after-before
 contacts.extend(dict(sample=s,a=int(a),b=int(b)) for a,b in sorted(extra))
 row=area_safety(p,base,z['rest'],faces);row.update(sample=s,parent_pairs=len(before),current_pairs=len(after),new_contact_pairs=len(extra),affine_error_mm=error);samples.append(row)
 print('R42_NATIVE_SAMPLE',s,len(extra),row['passed'],error,flush=True)
Path(dest).write_text(json.dumps(dict(contacts=contacts,sample_count=82,front_130=samples[-1],samples=samples),indent=2)+'\n')
print('R42_NATIVE_CONTACTS',len(contacts),flush=True)
