"""Read-only native response dataset for R40's two-path material solve."""
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
PREFIX='HGPT_S7_DELT_'
KEYS=(110,120,130,136,145)
BASE=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r38_20261017/HGPT_ORIGINAL_V1_REVIEW_R38_CODEX.blend'
OUT=Path('/tmp/r40-response');OUT.mkdir(exist_ok=True)
def coords(kb):
    a=np.empty(len(kb.data)*3);kb.data.foreach_get('co',a);return a.reshape(-1,3)
res=r17._setup(BASE);body,rig=res['body'],res['runtime'];blocks=body.data.shape_keys.key_blocks
basis=coords(blocks[0]);right=basis[:,0]>0
for side in ('l','r'):
    kb=body.shape_key_add(name=f'{PREFIX}{side}_136',from_mix=False)
    kb.data.foreach_set('co',(.6*coords(blocks[f'{PREFIX}{side}_130'])+.4*coords(blocks[f'{PREFIX}{side}_145'])).ravel())
    rig[f'hgpt_s7_angles_{side}']=[110.,120.,130.,136.,145.,156.,166.]
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
from original_review_r40_target import target
from original_review_r40_line import frame,profile,guide
line_normal=np.zeros_like(delta);line_mask=np.zeros(delta.shape[:2],bool)
for k,ht in enumerate(KEYS):
    install(np.zeros_like(delta));bench._reset(rig);sculpt.press_pose(res,float(ht));drives.drive(rig,body)
    p=evaluate();a=matrix()
    bones={side:(np.array(tuple(rig.matrix_world@rig.pose.bones['upperarm_'+side].head)),np.array(tuple(rig.matrix_world@rig.pose.bones['forearm_'+side].head))) for side in ('l','r')}
    change=target(p,faces,bones,basis,.45 if ht==110 else 1.)
    for side,(gh,el) in bones.items():
        axis,n=frame(gh,el,side);d=p-gh;station=d@axis;radius=d@n
        levels=np.arange(-.24,.20001,.002);outline=profile(p,faces,gh,el,side,levels)
        fit=guide(p,faces,gh,el,side)
        local=np.interp(station,levels,outline)
        mask=(radius>local-.012)&(station>=-.14)&(station<=.16)&((np.polyval(fit,station)>local)|(station>=0))&(d[:,1]>-.025)&(p[:,0]*(1 if side=='r' else -1)>0)
        world_normal=n-fit[0]*axis
        covector=np.einsum('nji,j->ni',a,world_normal)
        covector/=np.maximum(np.linalg.norm(covector,axis=1)[:,None],1e-20)
        line_normal[k,mask]=covector[mask];line_mask[k]|=mask
    delta[k]=np.einsum('nij,nj->ni',np.linalg.pinv(a,rcond=1e-4),change)
    delta[k,basis[:,0]==0]=0
data={'rest':neutral,'faces':faces,'delta':delta,'constraint_normal':line_normal,'constraint_mask':line_mask,'constraint_value':(line_normal*delta).sum(2)}
base=[];mats=[];w=[];rows=[]
max_error=0.
for path in ('press','benchmark_press'):
    for i in range(41):
        install(np.zeros_like(delta));pose(path,i/40)
        p=evaluate();a=matrix();c=coefficients()
        if path=="press" and i==25:
            data["marked_gh"]=np.asarray([tuple(rig.matrix_world@rig.pose.bones["upperarm_"+side].head) for side in ("l","r")])
        install(delta);actual=evaluate()
        predicted=p+np.einsum('nij,nj->ni',a,np.einsum('kn,knj->nj',c,delta))
        error=float(np.linalg.norm(predicted-actual,axis=1).max())
        if not all(np.isfinite(x).all() for x in (p,a,c,actual,predicted)) or not np.isfinite(error):
            raise ValueError(('Nonfinite native response',path,i))
        max_error=max(max_error,error)
        rows.append({'path':path,'t':i/40,'linear_error_mm':error*1000})
        base.append(p.astype('float32'));mats.append(a.astype('float32'));w.append(c.astype('float32'))
        print('R40_RESPONSE',path,i,error*1000,flush=True)
data.update(base=np.asarray(base),mat=np.asarray(mats),weight=np.asarray(w))
free=np.linalg.norm(delta,axis=2)>1e-7
adj=[set() for _ in basis]
for e in body.data.edges:
    i,j=e.vertices;adj[i].add(j);adj[j].add(i)
for k in range(len(KEYS)):
    active=set(np.flatnonzero(free[k]))
    for _ in range(2):active|={j for i in active for j in adj[i]}
    free[k,list(active)]=True
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
data.update(free=free,normal=np.asarray(normal))
# Exact130 front quality response, independent of the fixed82 path samples.
install(np.zeros_like(delta));bench._reset(rig);sculpt.press_pose(res,130.);drives.drive(rig,body)
fp=evaluate();fm=matrix();fw=coefficients()
from original_review_r40_front import edge_pairs,angles
fe,ff=edge_pairs(faces);selected=np.zeros(len(fe),bool)
for side in ('l','r'):
 gh=np.array(tuple(rig.matrix_world@rig.pose.bones['upperarm_'+side].head));rel=fp[fe].mean(1)-gh
 selected|=(np.linalg.norm(rel,axis=1)<.115)&(rel[:,0]*(1 if side=='r' else -1)>-.02)&(rel[:,1]<.03)&(rel[:,2]<.025)
ft=faces[ff[selected]];limits=np.maximum(angles(fp,ft)+.1,23.5)
data.update(front_base=fp,front_mat=fm,front_weight=fw,front_triangles=ft,front_limits=limits)
for name,value in data.items():
    if not np.isfinite(value).all():raise ValueError(('Nonfinite response export',name))
np.savez_compressed(OUT/'response.npz',**data)
report={'source':'R38','initial_midkeys':'approved straight arm-to-body line','keys':KEYS,'frozen_keys':[156,166],
        'new_136_key':'exact R38 130-to145 interpolation at fraction0.4',
        'sample_count':len(rows),'max_linear_error_mm':max_error*1000,'samples':rows,
        'modifiers':[{'name':m.name,'type':m.type,'enabled':m.show_viewport} for m in body.modifiers]}
with np.load(ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r38_20261017/probe/r35_contour_surfaces.npz') as reference:
    preserved_error=float(np.linalg.norm(data['base'][25]-reference['all_135.625'],axis=1).max())
report['new_136_baseline_error_mm']=preserved_error*1000
if preserved_error>1e-5:raise RuntimeError(('New control changes parent interpolation',preserved_error))
(OUT/'response.json').write_text(json.dumps(report,indent=2)+'\n')
if max_error>1e-5:raise RuntimeError(('Native response is not sufficiently linear',max_error))

