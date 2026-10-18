"""Build immutable R46 only after native whole-motion and13-benchmark feasibility."""
from pathlib import Path
import sys,os,json,hashlib
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/anatomy_fit')];os.environ['S7_LOCKOUT_HT']='166'
import build_original_review_candidate_r17_blender as r17
import build_original_bake_corrective_blender as bake
import build_original_sculpt_corrective_blender as sculpt
import build_original_movement_benchmarks_blender as bench
import build_functional_shoulder_correction_blender as correction
import original_v1_review_candidate_drives as drives
import original_v1_shoulder_r4 as r4
from original_review_r43_native import install,coords,PREFIX
from original_review_r43_sampling import KEYS
OUT=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r46_20261018'
PARENT=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend'
tmp=Path('/tmp/r46-response')
native=json.loads((tmp/'native_final.json').read_text());benchmarks=json.loads((tmp/'benchmarks_before_save.json').read_text())
if any(int(p.read_text().strip()) for p in tmp.glob('*_test_exit.txt')):raise RuntimeError('Pre-save fixed-scope/area/motion test failed')
if not native['passed'] or not benchmarks['passed']:raise RuntimeError('Native feasibility failed; do not save R46')
if OUT.exists():raise FileExistsError('Choose a new candidate; existing folder is immutable')
z=np.load(tmp/'source.npz');delta=np.load(tmp/'solved.npz')['delta'];res=r17._setup(PARENT);body,rig=res['body'],res['runtime'];blocks=body.data.shape_keys.key_blocks
old={k.name:coords(k).copy() for k in blocks if k.name.startswith(PREFIX)}
info=install(res,delta,z['sampling_basis']);bpy.context.view_layer.update()
before={k.name:coords(k).copy() for k in blocks if k.name.startswith(PREFIX)}
def benchmark_press(t):
 hook=r4._S.get('extend');r4._S['extend']=None
 try:bench.pose_press(res,t,correction)
 finally:r4._S['extend']=hook
adj=[set() for _ in body.data.vertices]
for e in body.data.edges:
 i,j=e.vertices;adj[i].add(j);adj[j].add(i)
old_prefix,old_s4,old_paths=bake.PREFIX,sculpt.PREFIX,bake._EXTRA['paths'];bake.PREFIX=sculpt.PREFIX=PREFIX;bake._EXTRA['paths']=[('benchmark_press',benchmark_press)]
try:
 smooth=bake.smooth_guard(res,adj,ts=tuple(i/40 for i in range(41)));guard=sculpt._guard(res,adj,rounds=10,ts=tuple(i/40 for i in range(41)))
finally:bake.PREFIX,sculpt.PREFIX,bake._EXTRA['paths']=old_prefix,old_s4,old_paths
same=all(np.array_equal(v,coords(blocks[n])) for n,v in before.items())
if not same:raise RuntimeError('Original guards changed the validated geometry; reject before saving')
for k,ht in enumerate(KEYS):
 for side in ('l','r'):
  name=f'{PREFIX}{side}_{int(ht)}'
  if not np.array_equal(coords(blocks[name])[z['frozen_arm'][k]],old[name][z['frozen_arm'][k]]):raise RuntimeError('Original arm/elbow coordinates changed')
  if ht==166 and not np.array_equal(coords(blocks[name]),old[name]):raise RuntimeError('Top control changed')
from original_review_r46_presave import check
presave=check(res,OUT,ROOT)
bench._reset(rig)
for kb in blocks[1:]:kb.value=0
import build_functional_original_attachment_blender as attachment
attachment._remove_previous();bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for side in ('l','r'):
 for name in ('deltoid_helper','shoulder_cap','axilla','hip_crease','muscle_pec','muscle_lat','muscle_trap'):
  helper=f'{name}_{side}'
  if helper in rig.data.edit_bones:rig.data.edit_bones.remove(rig.data.edit_bones[helper])
bpy.ops.object.mode_set(mode='OBJECT')
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();assert sum(b.use_deform for b in rig.data.bones)==67
bpy.context.scene['hgpt_review_candidate']='ORIGINAL_V1_REVIEW_R46_CODEX';bpy.context.scene['hgpt_review_candidate_approved']=False
OUT.mkdir(parents=True);model=OUT/'HGPT_ORIGINAL_V1_REVIEW_R46_CODEX.blend';bpy.ops.wm.save_as_mainfile(filepath=str(model),copy=True)
report=dict(candidate='R46',approved=False,sha256=hashlib.sha256(model.read_bytes()).hexdigest(),parent_sha256=hashlib.sha256(PARENT.read_bytes()).hexdigest(),native=native,benchmarks=benchmarks['passed'],presave=presave,sampling=info,original_guards_changed_validated_geometry=False,smooth_guard=smooth,final_guard=guard)
(OUT/'r46_build.json').write_text(json.dumps(report,indent=2)+'\n');print('R46_SAVED',report['sha256'],flush=True)
