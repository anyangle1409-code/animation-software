"""R41 bounded S7 strain candidate, with unchanged original guards."""
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
PARENT=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r40_20261017/HGPT_ORIGINAL_V1_REVIEW_R40_CODEX.blend'
OUT=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017'
PREFIX='HGPT_S7_DELT_'
KEYS=(110.,120.,130.,136.,145.,156.,166.)

def coords(kb):
    a=np.empty(len(kb.data)*3)
    kb.data.foreach_get('co',a)
    return a.reshape(-1,3)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build():
    if OUT.exists():
        raise FileExistsError('Existing candidate is immutable; choose a new number')
    res=r17._setup(PARENT);body,rig=res['body'],res['runtime']
    blocks=body.data.shape_keys.key_blocks;rest=coords(blocks[0])
    mirror=int(np.argmin(np.linalg.norm(rest-rest[18633]*[-1,1,1],axis=1)))
    sentinel_ids=[18633,mirror]
    sentinel_before={kb.name:coords(kb)[sentinel_ids].copy() for kb in blocks if kb.name.startswith(PREFIX)}
    s7_before={kb.name:coords(kb).copy() for kb in blocks if kb.name.startswith(PREFIX)}
    frozen={kb.name:coords(kb).copy() for kb in blocks if kb.name.startswith(PREFIX) and kb.name.endswith(('_156','_166'))}
    with np.load('/tmp/r41-response/solved.npz') as z:
        for k,ht in enumerate(KEYS):
            for side in ('l','r'):
                change=z['delta'][k].copy();change[rest[:,0]*(1 if side=='r' else -1)<=0]=0
                kb=blocks[f'{PREFIX}{side}_{int(ht)}']
                kb.data.foreach_set('co',(coords(kb)+change).ravel())
    inverse_log={'method':'native-validated direct material-coordinate solve; no second inverse bake'}
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
    frozen_ok=all(np.array_equal(before,coords(blocks[name])) for name,before in frozen.items())
    from original_review_r41_checks import sentinels_preserved,bounded_s7_update
    bounded_ok,max_update=bounded_s7_update(s7_before,{kb.name:coords(kb) for kb in blocks if kb.name.startswith(PREFIX)},.75)
    sentinel_after={kb.name:coords(kb)[sentinel_ids] for kb in blocks if kb.name.startswith(PREFIX)}
    sentinel_ok=sentinels_preserved(sentinel_before,sentinel_after)
    guard_diagnostic={'bounded_s7_update':bounded_ok,'max_s7_update_mm':max_update,'sentinels_unchanged':sentinel_ok,'smooth_guard':smooth_log,'final_guard':final_log,'frozen_156_166_unchanged':frozen_ok}
    Path('/tmp/r41-response/guard_attempt.json').write_text(json.dumps(guard_diagnostic,indent=2)+'\n')
    if not sentinel_ok:raise RuntimeError('Original guards changed a protected front sentinel: reject before saving')
    if not bounded_ok:
        raise RuntimeError(('R41 S7 update exceeds0.75mm: reject before saving',max_update))
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
    scene=bpy.context.scene;scene['hgpt_review_candidate']='ORIGINAL_V1_REVIEW_R41_CODEX';scene['hgpt_review_candidate_approved']=False
    OUT.mkdir(parents=True)
    model=OUT/'HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(model),copy=True)
    report={'candidate':'R41','approved':False,'status':'EXPERIMENT_NOT_ACCEPTED',
            'owner_scope':'Continue original stretch/crush priorities; preserve R40 line/front fixes; visual review pending',
            'parent_sha256':digest(PARENT),'sha256':digest(model),
            'change':'R40 bounded S7 strain redistribution; all7 existing controls may move at most0.75mm, including156/166; line, front anchors and non-S7 coordinates protected',
            'response':json.loads(Path('/tmp/r41-response/response.json').read_text()),
            'coupled_solver':json.loads(Path('/tmp/r41-response/solved.npz.json').read_text()),
            'frozen_156_166_unchanged':frozen_ok,'end_keys_authored':True,'bounded_s7_update':bounded_ok,'max_s7_update_mm':max_update,'sentinels_unchanged':sentinel_ok,
            'inverse_bake':inverse_log,'smooth_guard':smooth_log,'final_guard':final_log,'guard_samples':list(ts)}
    (OUT/'r41_build.json').write_text(json.dumps(report,indent=2)+'\n')
    print('R41_SAVED',json.dumps({'path':str(model),'sha256':report['sha256']}),flush=True)

if __name__=='__main__':
    {'build':build}[sys.argv[-1]]()


