"""Read-only native response dataset for R42's two-path material solve."""
from pathlib import Path
import json,sys,os
import bpy
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/anatomy_fit')]
os.environ['S7_LOCKOUT_HT']='166'
import build_original_review_candidate_r17_blender as r17
import build_original_sculpt_corrective_blender as sculpt
import build_original_movement_benchmarks_blender as bench
import build_functional_shoulder_correction_blender as correction
import original_v1_review_candidate_drives as drives
import original_v1_press_extension as px
import original_v1_shoulder_r4 as r4
from original_review_r42_front import edge_pairs,angles
PREFIX='HGPT_S7_DELT_'
KEYS=(110,120,130,136,145,156,166)
BASE=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend'
OUT=Path('/tmp/r42-response');OUT.mkdir(exist_ok=True)
def coords(kb):
    a=np.empty(len(kb.data)*3);kb.data.foreach_get('co',a);return a.reshape(-1,3)
res=r17._setup(BASE);body,rig=res['body'],res['runtime'];blocks=body.data.shape_keys.key_blocks
basis=coords(blocks[0]);right=basis[:,0]>0
parent={k.name:coords(k) for k in blocks if k.name.startswith(PREFIX)}
delta=np.zeros((len(KEYS),len(basis),3))
def install(d):
    for k,ht in enumerate(KEYS):
        for side in ('l','r'):
            name=f'{PREFIX}{side}_{ht}'
            add=d[k].copy();add[~right if side=='r' else right]=0
            blocks[name].data.foreach_set('co',(parent[name]+add).ravel())
    body.data.update();bpy.context.view_layer.update()
install(np.zeros_like(delta))
for kb in blocks[1:]:kb.value=0
bench._reset(rig);v0,faces=bench._evaluated(body)
neutral=np.array([tuple(v) for v in v0]);faces=np.asarray(faces)
names={g.index:g.name for g in body.vertex_groups}
bone_names=[b.name for b in rig.data.bones if b.use_deform]
indices={n:i for i,n in enumerate(bone_names)}
weights=np.zeros((len(basis),len(bone_names)))
for v in body.data.vertices:
    for g in v.groups:
        if names[g.group] in indices:weights[v.index,indices[names[g.group]]]=g.weight
weights/=np.maximum(weights.sum(1)[:,None],1e-20)
def matrix():
    palette=[]
    for name in bone_names:
        m=rig.matrix_world@rig.pose.bones[name].matrix@rig.data.bones[name].matrix_local.inverted()@rig.matrix_world.inverted()@body.matrix_world
        palette.append(np.array(m.to_3x3()))
    return (weights@np.asarray(palette).reshape(-1,9)).reshape(-1,3,3)
def evaluate():
    v,_=bench._evaluated(body);return np.array([tuple(x) for x in v])
def pose(path,t):
    bench._reset(rig)
    if path=='press':px.pose_press_full(res,t)
    else:
        hook=r4._S.get('extend');r4._S['extend']=None
        try:bench.pose_press(res,t,correction)
        finally:r4._S['extend']=hook
    drives.drive(rig,body)
def coefficients():
    return np.array([np.where(right,blocks[f'{PREFIX}r_{ht}'].value,blocks[f'{PREFIX}l_{ht}'].value) for ht in KEYS])
from original_review_r41_strain import eligible_vertices
from original_review_r42_line import frame,profile,guide
line_normal=np.zeros_like(delta);line_mask=np.zeros(delta.shape[:2],bool)
key_base=[];key_mat=[];key_bones=[];key_coeff=[]
for k,ht in enumerate(KEYS):
    install(np.zeros_like(delta));bench._reset(rig);sculpt.press_pose(res,float(ht));drives.drive(rig,body)
    p=evaluate();a=matrix()
    bones={side:(np.array(tuple(rig.matrix_world@rig.pose.bones['upperarm_'+side].head)),np.array(tuple(rig.matrix_world@rig.pose.bones['forearm_'+side].head))) for side in ('l','r')}
    key_base.append(p);key_mat.append(a);key_coeff.append(coefficients());key_bones.append([[gh.tolist(),el.tolist()] for gh,el in bones.values()])
    change=np.zeros_like(p)
    for side,(gh,el) in bones.items():
        axis,n=frame(gh,el,side);d=p-gh;station=d@axis;radius=d@n
        levels=np.arange(-.24,.20001,.002);outline=profile(p,faces,gh,el,side,levels)
        fit=guide(p,faces,gh,el,side)
        local=np.interp(station,levels,outline)
        mask=(radius>local-.012)&(station>=0.)&(station<=.16)&(d[:,1]>-.025)&(p[:,0]*(1 if side=='r' else -1)>0)
        world_normal=n-fit[0]*axis
        covector=np.einsum('nji,j->ni',a,world_normal)
        covector/=np.maximum(np.linalg.norm(covector,axis=1)[:,None],1e-20)
        line_normal[k,mask]=covector[mask];line_mask[k]|=mask
    delta[k]=np.einsum('nij,nj->ni',np.linalg.pinv(a,rcond=1e-4),change)
    delta[k,basis[:,0]==0]=0
data={'rest':neutral,'faces':faces,'delta':delta,'constraint_normal':line_normal,'constraint_mask':line_mask,'constraint_value':(line_normal*delta).sum(2)}
base=[];mats=[];w=[];rows=[]
region=(abs(basis[:,0])>.08)&(abs(basis[:,0])<.35)&(basis[:,2]>1.20)&(basis[:,2]<1.51)
mirror=int(np.argmin(np.linalg.norm(basis-basis[18633]*np.array([-1,1,1]),axis=1)))
validation_delta=np.asarray([.0001*np.sin(np.arange(len(basis))[:,None]*.11+k+np.arange(3)) for k in range(len(KEYS))])
validation_delta[:,~region]=0;validation_delta[:,[18633,mirror]]=0
max_error=0.
for path in ('press','benchmark_press'):
    for i in range(41):
        install(np.zeros_like(delta));pose(path,i/40)
        p=evaluate();a=matrix();c=coefficients()
        if path=="press" and i==25:
            data["marked_gh"]=np.asarray([tuple(rig.matrix_world@rig.pose.bones["upperarm_"+side].head) for side in ("l","r")])
        install(validation_delta);actual=evaluate()
        predicted=p+np.einsum('nij,nj->ni',a,np.einsum('kn,knj->nj',c,validation_delta))
        error=float(np.linalg.norm(predicted-actual,axis=1).max())
        if not all(np.isfinite(x).all() for x in (p,a,c,actual,predicted)) or not np.isfinite(error):
            raise ValueError(('Nonfinite native response',path,i))
        max_error=max(max_error,error)
        rows.append({'path':path,'t':i/40,'linear_error_mm':error*1000})
        base.append(p.astype('float32'));mats.append(a.astype('float32'));w.append(c.astype('float32'))
        print('R42_RESPONSE',path,i,error*1000,flush=True)
data.update(base=np.asarray(base),mat=np.asarray(mats),weight=np.asarray(w))
free=np.zeros(delta.shape[:2],bool)
tri=neutral[faces];a0=.5*np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)
face_region=region[faces].any(1)
for sample,p in enumerate(data['base']):
    tri=p[faces];ar=.5*np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)
    ratio=ar/np.maximum(a0,1e-20)
    ids=np.flatnonzero(((ratio>1.8)|(ratio<.18))&face_region&(a0>1e-12))
    vv=np.unique(faces[ids])
    for k in range(len(KEYS)):
        free[k,vv]|=data['weight'][sample,k,vv]>.001
adj=[set() for _ in basis]
for e in body.data.edges:
    i,j=e.vertices;adj[i].add(j);adj[j].add(i)
for k in range(len(KEYS)):
    active=set(np.flatnonzero(free[k]))
    for _ in range(2):active|={j for i in active for j in adj[i]}
    free[k,list(active)]=True
    free[k,~region]=False
mirror=int(np.argmin(np.linalg.norm(basis-basis[18633]*np.array([-1,1,1]),axis=1)))
free[:,[18633,mirror]]=False
free[:,basis[:,0]==0]=False
line_mask&=free
data["constraint_mask"]=line_mask
normal=[]
for ht in KEYS:
    install(np.zeros_like(delta));bench._reset(rig);sculpt.press_pose(res,float(ht));drives.drive(rig,body)
    a=matrix();install(delta);p=evaluate()
    fn=np.cross(p[faces[:,1]]-p[faces[:,0]],p[faces[:,2]]-p[faces[:,0]])
    n=np.zeros_like(p)
    for v in range(3):np.add.at(n,faces[:,v],fn)
    n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-20)
    material=np.einsum('nji,nj->ni',a,n)
    material/=np.maximum(np.linalg.norm(material,axis=1)[:,None],1e-20)
    k=KEYS.index(ht)
    material[line_mask[k]]=line_normal[k,line_mask[k]]
    normal.append(material)
# New owner scope: change only the proximal body-side junction; keep the
# upper-arm and elbow material vertices, and both156/166 controls exact.
frozen_arm=np.zeros_like(free)
from original_review_r42_line import frame as arm_frame
for k in range(len(KEYS)):
    local=np.zeros(len(basis),bool)
    for side_index,side in enumerate(('l','r')):
        gh,el=np.array(key_bones[k][side_index]);axis,nn=arm_frame(gh,el,side)
        rel=key_base[k]-gh;station=rel@axis;radial=rel@nn
        same=key_base[k][:,0]*(1 if side=='r' else -1)>0
        frozen_arm[k]|=same&(station>=0.)
        local|=same&(station>-.36)&(station<0.)&(radial>-.03)&(rel[:,1]>-.065)
    free[k]=region&local if k in (1,2,3,4) else False
free[:,[18633,mirror]]=False;free[:,basis[:,0]==0]=False
line_mask&=free;data['constraint_mask']=line_mask
data.update(free=free,normal=np.asarray(normal),frozen_arm=frozen_arm,
            key_base=np.asarray(key_base),key_mat=np.asarray(key_mat),key_bones=np.asarray(key_bones),key_weight=np.asarray(key_coeff))
# Exact130 front quality response, independent of the fixed82 path samples.
install(np.zeros_like(delta));bench._reset(rig);sculpt.press_pose(res,130.);drives.drive(rig,body)
fp=evaluate();fm=matrix();fw=coefficients()
fe,ff=edge_pairs(faces);selected=np.zeros(len(fe),bool)
for side in ('l','r'):
 gh=np.array(tuple(rig.matrix_world@rig.pose.bones['upperarm_'+side].head));rel=fp[fe].mean(1)-gh
 selected|=(np.linalg.norm(rel,axis=1)<.115)&(rel[:,0]*(1 if side=='r' else -1)>-.02)&(rel[:,1]<.03)&(rel[:,2]<.025)
ft=faces[ff[selected]];limits=np.maximum(angles(fp,ft)+.1,23.5)
install(validation_delta);front_actual=evaluate();front_predicted=fp+np.einsum('nij,nj->ni',fm,np.einsum('kn,knj->nj',fw,validation_delta))
front_error=float(np.linalg.norm(front_actual-front_predicted,axis=1).max())
if front_error>1e-5:raise RuntimeError(('Front response linearity failed',front_error))
data.update(strain_mode=np.array(1),max_delta_mm=np.array(.70),front_base=fp,front_mat=fm,front_weight=fw,front_triangles=ft,front_limits=limits)
for name,value in data.items():
    if not np.isfinite(value).all():raise ValueError(('Nonfinite response export',name))
np.savez_compressed(OUT/'response.npz',**data)
report={'source':'R41','initial_midkeys':'zero increment; bounded strain optimization','keys':KEYS,'frozen_keys':[110,156,166],'maximum_saved_update_mm':60.,
        'new_136_key':'inherited unchanged as baseline from R40',
        'front_linear_error_mm':front_error*1000,'free_vertices_per_key':free.sum(1).tolist(),'line_vertices_per_key':line_mask.sum(1).tolist(),'sample_count':len(rows),'max_linear_error_mm':max_error*1000,'samples':rows,
        'modifiers':[{'name':m.name,'type':m.type,'enabled':m.show_viewport} for m in body.modifiers]}
with np.load(ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/probe/r35_contour_surfaces.npz') as reference:
    preserved_error=float(np.linalg.norm(data['base'][25]-reference['all_135.625'],axis=1).max())
report['parent_baseline_error_mm']=preserved_error*1000
if preserved_error>1e-5:raise RuntimeError(('R42 untouched parent baseline mismatch',preserved_error))
(OUT/'response.json').write_text(json.dumps(report,indent=2)+'\n')
if max_error>1e-5:raise RuntimeError(('Native response is not sufficiently linear',max_error))

