"""Read-only native response dataset for R37's two-path material solve."""
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
KEYS=(110,120,130,145)
BASE=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r34_20261016/HGPT_ORIGINAL_V1_REVIEW_R34_CODEX.blend'
START=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r36_20261016/HGPT_ORIGINAL_V1_REVIEW_R36_CODEX.blend'
OUT=Path('/tmp/r37-response');OUT.mkdir(exist_ok=True)
def coords(kb):
    a=np.empty(len(kb.data)*3);kb.data.foreach_get('co',a);return a.reshape(-1,3)
bpy.ops.wm.open_mainfile(filepath=str(START))
body=bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
start={k.name:coords(k) for k in body.data.shape_keys.key_blocks if k.name.startswith(PREFIX)}
res=r17._setup(BASE);body,rig=res['body'],res['runtime'];blocks=body.data.shape_keys.key_blocks
basis=coords(blocks[0]);right=basis[:,0]>0
parent={k.name:coords(k) for k in blocks if k.name.startswith(PREFIX)}
for side in ('l','r'):
    name=f'{PREFIX}{side}_110'
    base110=basis+.6*(parent[f'{PREFIX}{side}_120']-basis)
    kb=body.shape_key_add(name=name,from_mix=False);kb.data.foreach_set('co',base110.ravel())
    parent[name]=base110
    start[name]=base110+.6*(start[f'{PREFIX}{side}_120']-parent[f'{PREFIX}{side}_120'])
    rig[f'hgpt_s7_angles_{side}']=[110.,120.,130.,145.,156.,166.]
delta=np.stack([sum(start[f'{PREFIX}{side}_{ht}']-parent[f'{PREFIX}{side}_{ht}'] for side in ('l','r')) for ht in KEYS])
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
data={'rest':neutral,'faces':faces,'delta':delta}
base=[];mats=[];w=[];rows=[]
max_error=0.
for path in ('press','benchmark_press'):
    for i in range(41):
        install(np.zeros_like(delta));pose(path,i/40)
        p=evaluate();a=matrix();c=coefficients()
        install(delta);actual=evaluate()
        predicted=p+np.einsum('nij,nj->ni',a,np.einsum('kn,knj->nj',c,delta))
        error=float(np.linalg.norm(predicted-actual,axis=1).max())
        if not all(np.isfinite(x).all() for x in (p,a,c,actual,predicted)) or not np.isfinite(error):
            raise ValueError(('Nonfinite native response',path,i))
        max_error=max(max_error,error)
        rows.append({'path':path,'t':i/40,'linear_error_mm':error*1000})
        base.append(p.astype('float32'));mats.append(a.astype('float32'));w.append(c.astype('float32'))
        print('R37_RESPONSE',path,i,error*1000,flush=True)
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
    normal.append(material)
data.update(free=free,normal=np.asarray(normal))
for name,value in data.items():
    if not np.isfinite(value).all():raise ValueError(('Nonfinite response export',name))
np.savez_compressed(OUT/'response.npz',**data)
report={'source':'R34','initial_midkeys':'R36','keys':KEYS,'frozen_keys':[156,166],
        'new_110_key':'R34 baseline interpolation; initial new delta follows R36 interpolation',
        'sample_count':len(rows),'max_linear_error_mm':max_error*1000,'samples':rows,
        'modifiers':[{'name':m.name,'type':m.type,'enabled':m.show_viewport} for m in body.modifiers]}
(OUT/'response.json').write_text(json.dumps(report,indent=2)+'\n')
if max_error>1e-5:raise RuntimeError(('Native response is not sufficiently linear',max_error))
