"""Owner-approved R35 S7 junction rebuild, with unchanged original guards."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/anatomy_fit')]
os.environ['S7_LOCKOUT_HT']='166'
import bpy
import numpy as np
import build_original_review_candidate_r17_blender as r17
import build_original_bake_corrective_blender as bake
import build_original_sculpt_corrective_blender as sculpt
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
import original_v1_shoulder_r4 as r4
PARENT=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r34_20261016/HGPT_ORIGINAL_V1_REVIEW_R34_CODEX.blend'
OUT=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r35_20261016'
PREFIX='HGPT_S7_DELT_'
KEYS=(120.,130.,145.,156.,166.)

def coords(kb):
    a=np.empty(len(kb.data)*3)
    kb.data.foreach_get('co',a)
    return a.reshape(-1,3)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def export():
    res=r17._setup(PARENT);body,rig=res['body'],res['runtime']
    data={'rest':coords(body.data.shape_keys.key_blocks[0])}
    for ht in (*KEYS,135.625):
        bench._reset(rig);sculpt.press_pose(res,ht);drives.drive(rig,body)
        vertices,faces=bench._evaluated(body)
        data[f'all_{ht}']=np.array([tuple(v) for v in vertices]);data['faces']=np.asarray(faces)
        for side in ('l','r'):
            data[f'gh_{side}_{ht}']=np.array(tuple(rig.matrix_world@rig.pose.bones['upperarm_'+side].head))
    np.savez_compressed('/tmp/r35-source.npz',**data)

def build():
    if OUT.exists():
        raise FileExistsError('Existing candidate is immutable; choose a new number')
    OUT.mkdir(parents=True)
    res=r17._setup(PARENT);body,rig=res['body'],res['runtime']
    blocks=body.data.shape_keys.key_blocks;rest=coords(blocks[0])
    names={g.index:g.name for g in body.vertex_groups}
    deform={b.name for b in rig.data.bones if b.use_deform}
    inverse_log={}
    with np.load('/tmp/r35-target-deltas.npz') as z:
        for ht in KEYS:
            bench._reset(rig);sculpt.press_pose(res,ht);drives.drive(rig,body)
            offset=z[str(ht)];active=np.flatnonzero(np.linalg.norm(offset,axis=1)>1e-12)
            mats={name:np.array((rig.pose.bones[name].matrix@rig.data.bones[name].matrix_local.inverted()).to_3x3()) for name in deform}
            dr=np.zeros_like(rest)
            for i in active:
                a=sum(g.weight*mats[names[g.group]] for g in body.data.vertices[i].groups if names[g.group] in deform and g.weight>0)
                u,sv,vt=np.linalg.svd(a)
                dr[i]=vt.T@np.diag(sv/(sv*sv+bake.DAMP**2))@u.T@offset[i]
            for side in ('l','r'):
                change=dr.copy();change[rest[:,0]*(1 if side=='r' else -1)<=0]=0
                kb=blocks[f'{PREFIX}{side}_{int(ht)}']
                kb.data.foreach_set('co',(coords(kb)+change).reshape(-1))
            inverse_log[str(ht)]={'max_rest_delta_mm':float(np.linalg.norm(dr,axis=1).max()*1000)}
    adj=[set() for _ in rest]
    for e in body.data.edges:
        i,j=e.vertices;adj[i].add(j);adj[j].add(i)
    def benchmark_press(t):
        hook=r4._S.get('extend');r4._S['extend']=None
        try:
            bench.pose_press(res,t,__import__('build_functional_shoulder_correction_blender'))
        finally:
            r4._S['extend']=hook
    old_prefix,old_s4,old_paths=bake.PREFIX,sculpt.PREFIX,bake._EXTRA['paths']
    bake.PREFIX=sculpt.PREFIX=PREFIX;bake._EXTRA['paths']=[('benchmark_press',benchmark_press)]
    ts=tuple(i/40 for i in range(41))
    try:
        smooth_log=bake.smooth_guard(res,adj,ts=ts)
        final_log=sculpt._guard(res,adj,rounds=10,ts=ts)
    finally:
        bake.PREFIX,sculpt.PREFIX,bake._EXTRA['paths']=old_prefix,old_s4,old_paths
    bench._reset(rig)
    for kb in blocks[1:]:kb.value=0
    import build_functional_original_attachment_blender as attachment
    attachment._remove_previous()
    bpy.context.view_layer.objects.active=rig;rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for side in ('l','r'):
        for name in ('deltoid_helper','shoulder_cap','axilla','hip_crease','muscle_pec','muscle_lat','muscle_trap'):
            helper=f'{name}_{side}'
            if helper in rig.data.edit_bones:rig.data.edit_bones.remove(rig.data.edit_bones[helper])
    bpy.ops.object.mode_set(mode='OBJECT')
    for pb in rig.pose.bones:pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    assert sum(b.use_deform for b in rig.data.bones)==67
    scene=bpy.context.scene;scene['hgpt_review_candidate']='ORIGINAL_V1_REVIEW_R35_CODEX';scene['hgpt_review_candidate_approved']=False
    model=OUT/'HGPT_ORIGINAL_V1_REVIEW_R35_CODEX.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(model),copy=True)
    report={'candidate':'R35','approved':False,'status':'EXPERIMENT_NOT_ACCEPTED',
            'owner_scope_approved':'2026-10-16: broader local skin transition rebuild',
            'parent_sha256':digest(PARENT),'sha256':digest(model),
            'change':'broader anchored thin-plate S7 junction target at 120/130/145, 40% at 156, unchanged target at 166',
            'targets':json.loads(Path('/tmp/r35-target-deltas.npz.json').read_text()),
            'inverse_bake':inverse_log,'smooth_guard':smooth_log,'final_guard':final_log,'guard_samples':list(ts)}
    (OUT/'r35_build.json').write_text(json.dumps(report,indent=2)+'\n')
    print('R35_SAVED',json.dumps({'path':str(model),'sha256':report['sha256']}),flush=True)

if __name__=='__main__':
    {'export':export,'build':build}[sys.argv[-1]]()
