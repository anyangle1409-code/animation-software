"""Read-only native family ablation and skeleton/skin evidence. Never save a blend."""
from pathlib import Path
import sys,os,json,hashlib
import bpy,numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/anatomy_fit')]
os.environ['S7_LOCKOUT_HT']='166'
import build_original_review_candidate_r17_blender as r17
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
import original_v1_press_extension as px
from original_arm_back_audit import MODES,muted_names
from original_review_r52_native import install
source,solution,out,mode=sys.argv[-4:];out=Path(out)/mode;out.mkdir(parents=True,exist_ok=False)
if mode not in MODES:raise ValueError(mode)
model=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend'
model_hash=hashlib.sha256(model.read_bytes()).hexdigest()
if model_hash!='4c44b1fe14aeefd9a976f45baada60b4b81aaaa7cd736a300ca7cede2b0aaf2e':raise RuntimeError('R41 hash mismatch')
z=np.load(source);rest=z['rest'];res=r17._setup(model);body,rig=res['body'],res['runtime'];blocks=body.data.shape_keys.key_blocks

def protected():
 digest=lambda x:hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
 return dict(bones=[(b.name,b.parent.name if b.parent else None,b.use_deform,[float(v) for row in b.matrix_local for v in row]) for b in rig.data.bones],
  basis=digest(np.array([tuple(v.co) for v in blocks[0].data])),topology=digest(z['faces']),
  actual_polygons=[list(p.vertices) for p in body.data.polygons],
  groups=[g.name for g in body.vertex_groups],weights=[[(g.group,g.weight) for g in v.groups] for v in body.data.vertices],
  non_s7={k.name:digest(np.array([tuple(v.co) for v in k.data])) for k in blocks if not k.name.startswith('HGPT_S7_DELT_')})
before=protected()
if mode=='r52':install(res,np.load(solution)['dense_delta']);bpy.context.view_layer.update()
mute=muted_names(mode,[k.name for k in blocks])
if mode.startswith('r41_no_') and not mute:raise RuntimeError('Requested family absent; diagnostic would be meaningless')
bone_names=[b.name for b in rig.pose.bones]
back=(abs(rest[:,0])>.08)&(abs(rest[:,0])<.25)&(rest[:,2]>1.27)&(rest[:,2]<1.49)&(rest[:,1]>.025)
frames=(64,80,100,128,160);snapshots={'rest':rest,'faces':z['faces']};points=[];bones=[];matrices=[];states=[];activations=[];projections={}
scene=bpy.context.scene
for ob in scene.objects:
 if ob.type in ('MESH','CURVE') and ob is not body:ob.hide_render=True
material=bpy.data.materials.new('READ_ONLY_ABLATION');material.diffuse_color=(.72,.55,.45,1)
body.data.materials.clear();body.data.materials.append(material)
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_cavity=True
scene.render.film_transparent=True;scene.render.resolution_x=scene.render.resolution_y=512;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
cd=bpy.data.cameras.new('READ_ONLY_AUDIT_CAMERA');cd.type='ORTHO';cd.ortho_scale=1.15
cam=bpy.data.objects.new('READ_ONLY_AUDIT_CAMERA',cd);scene.collection.objects.link(cam);scene.camera=cam
selected=[n for n in bone_names if n.startswith(('spine_','clavicle_','scapula_','upperarm_','forearm_'))]
for i in range(161):
 bench._reset(rig);state=px.pose_press_full(res,i/160);drives.drive(rig,body)
 active={k.name:float(k.value) for k in blocks if k.name.startswith(('HGPT_S5_BAKE_','HGPT_S7_DELT_')) and abs(k.value)>1e-10}
 for name in mute:blocks[name].value=0.
 bpy.context.view_layer.update();p=np.array([tuple(v) for v in bench._evaluated(body)[0]])
 points.append(p[back]);states.append(state);activations.append(active)
 bone_positions=np.array([[tuple(rig.matrix_world@rig.pose.bones[n].head),tuple(rig.matrix_world@rig.pose.bones[n].tail)] for n in bone_names]);bones.append(bone_positions)
 matrices.append(np.array([tuple(tuple(row) for row in (rig.matrix_world@rig.pose.bones[n].matrix)) for n in bone_names]))
 if i in frames:
  snapshots[f'points_{i:03d}']=p
  for view,direction in [('back',(0,1,.02)),('three_quarter',(.7,.7,.05))]:
   d=Vector(direction).normalized();cam.location=Vector((0,0,1.45))+d*4;cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');bpy.context.view_layer.update()
   scene.render.filepath=str(out/f'f{i:03d}_{view}.png');bpy.ops.render.render(write_still=True)
   overlay={}
   for n in selected:
    ends=[]
    for pworld in bone_positions[bone_names.index(n)]:
     uv=world_to_camera_view(scene,cam,Vector(pworld));ends.append([float(uv.x*512),float((1-uv.y)*512)])
    overlay[n]=ends
   projections[f'f{i:03d}_{view}']=overlay
 if i%40==0:print('READ_ONLY_ABLATION_FRAME',mode,i,flush=True)
after=protected();checks={k:before[k]==after[k] for k in before}
if not all(checks.values()):raise RuntimeError(('Protected geometry changed',checks))
if hashlib.sha256(model.read_bytes()).hexdigest()!=model_hash:raise RuntimeError('Saved model changed')
np.savez_compressed(out/'motion.npz',back_points=np.array(points),bone_endpoints=np.array(bones),bone_matrices=np.array(matrices),back_vertex_ids=np.flatnonzero(back))
np.savez_compressed(out/'snapshots.npz',**snapshots)
(out/'state.json').write_text(json.dumps(dict(mode=mode,diagnostic_only=True,model_saved=False,model_modified=False,accepted=False,samples=161,bone_names=bone_names,muted_names=mute,protected_identity=checks,press_states=states,activations_before_ablation=activations,projections=projections,model_sha256=model_hash),indent=2)+'\n')
print('READ_ONLY_ABLATION_COMPLETE',mode,checks,flush=True)
