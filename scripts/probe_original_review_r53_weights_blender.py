"""Authorised 26-vertex weight-only trial; no saved or approved model."""
from pathlib import Path
import os,sys,json,hashlib
import bpy,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/anatomy_fit')]
os.environ['S7_LOCKOUT_HT']='166'
import build_original_review_candidate_r17_blender as r17
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
import original_v1_press_extension as px
from original_review_r53_weights import install_patch,linear_points
from original_review_r52_native import install
sys.path.insert(0,str(ROOT/'scripts/tests'))
from test_original_review_r48_approved_outline import outline
source,solution,capture,out,mode=sys.argv[-5:]
if mode not in ('r41','r52'):raise ValueError(mode)
out=Path(out)/mode;out.mkdir(parents=True,exist_ok=False)
z=np.load(source);ref=np.load(Path(capture)/mode/'clip.npz');rw=np.load(Path(capture)/mode/'rest_weights.npz')
model=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend'
expected='4c44b1fe14aeefd9a976f45baada60b4b81aaaa7cd736a300ca7cede2b0aaf2e'
assert hashlib.sha256(model.read_bytes()).hexdigest()==expected
res=r17._setup(model);body,rig=res['body'],res['runtime'];blocks=body.data.shape_keys.key_blocks
if mode=='r52':install(res,np.load(solution)['dense_delta'])
def protect():
    h=lambda a:hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
    return dict(runtime_rest=[(b.name,b.parent.name if b.parent else None,np.array(b.matrix_local).tolist(),tuple(b.head_local),tuple(b.tail_local)) for b in rig.data.bones],
        anatomy_rest=[(b.name,np.array(b.matrix_local).tolist()) for b in res['anatomy'].data.bones],
        weights=[[(g.group,g.weight) for g in v.groups] for v in body.data.vertices],
        groups=[g.name for g in body.vertex_groups],polygons=[list(p.vertices) for p in body.data.polygons],
        all_key_geometry={k.name:h(np.array([tuple(v.co) for v in k.data])) for k in blocks})
before=protect()
bench._reset(rig);px.pose_press_full(res,0.);drives.drive(rig,body)
baseline_points=np.array([tuple(v) for v in bench._evaluated(body)[0]])
baseline_error=float(np.linalg.norm(baseline_points[rw['shoulder_ids']]-ref['baseline'][0],axis=1).max()*1000)
assert baseline_error<.001
patch=install_patch(res);after_patch=protect();names=[b.name for b in rig.pose.bones];allowed=set()
assert allowed.issubset(names)

rest_bones={n:np.array(rig.data.bones[n].matrix_local) for n in names}
np.savez_compressed(out/'rest_bones.npz',matrices=np.array([rest_bones[n] for n in names]),body_matrix_world=np.array(body.matrix_world),rig_matrix_world=np.array(rig.matrix_world))
scene=bpy.context.scene
for ob in scene.objects:
    if ob.type in ('MESH','CURVE') and ob is not body:ob.hide_render=True
mat=bpy.data.materials.new('R53_WEIGHT_TRIAL_ONLY');mat.diffuse_color=(.72,.55,.45,1);body.data.materials.clear();body.data.materials.append(mat)
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_cavity=True
scene.render.film_transparent=True;scene.render.resolution_x=scene.render.resolution_y=512;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
cd=bpy.data.cameras.new('R53_PROBE');cd.type='ORTHO';cd.ortho_scale=1.15;cam=bpy.data.objects.new('R53_PROBE',cd);scene.collection.objects.link(cam);scene.camera=cam
views=dict(front=(0,-1,.02),rear=(0,1,.02),side=(1,0,.02),three_quarter=(.7,.7,.05))
points=[];bones=[];rows=[];snap={};outlines={};max_baseline_error=baseline_error;max_nonlat_pose_error=0
for frame in range(161):
    bench._reset(rig);px.pose_press_full(res,frame/160);drives.drive(rig,body);bpy.context.view_layer.update()
    # Reference is the already hash-verified same-pose R52 capture.
    pose=np.array([np.array(rig.matrix_world@rig.pose.bones[n].matrix) for n in names])
    pe=float(abs(pose-ref['bone_matrices'][frame]).max());max_nonlat_pose_error=max(max_nonlat_pose_error,pe)
    if pe!=0:raise RuntimeError('Weight-only trial changed bone poses')
    p=np.array([tuple(v) for v in bench._evaluated(body)[0]],dtype=np.float32)
    points.append(p[rw['back_ids']]);bones.append(pose)
    rows.append(dict(frame=frame,maximum_skin_difference_mm=float(np.linalg.norm(p[rw['shoulder_ids']]-ref['baseline'][frame],axis=1).max()*1000),maximum_back_difference_mm=float(np.linalg.norm(p[rw['back_ids']]-ref['back_points'][frame],axis=1).max()*1000)))
    if frame in (0,80,100,128,160):snap[f'points_{frame:03d}']=p
    if frame==100:
        outlines=dict(baseline_error_mm=float(abs(outline(np.load(Path(capture)/mode/'snapshots.npz')['baseline_100'],z['faces'])-outline(z['r48_profile_target_points'],z['faces'])).max()*1000),probe_error_mm=float(abs(outline(p,z['faces'])-outline(z['r48_profile_target_points'],z['faces'])).max()*1000),guard_mm=1.)
    if frame%4==0:
        for view,direction in views.items():
            d=Vector(direction).normalized();cam.location=Vector((0,0,1.45))+d*4;cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');bpy.context.view_layer.update()
            scene.render.filepath=str(out/f'probe_{frame:03d}_{view}.png');bpy.ops.render.render(write_still=True)
    if frame%40==0:print('R53_WEIGHT_TRIAL_FRAME',mode,frame,flush=True)
# Actual native probes for unchanged historical front/contour tests.
import build_original_sculpt_corrective_blender as sculpt
contour={'rest':z['rest'],'faces':z['faces']}
for ht in (120.,130.,135.625,145.,156.,166.):
    bench._reset(rig);sculpt.press_pose(res,ht);drives.drive(rig,body)
    contour[f'all_{ht}']=np.array([tuple(v) for v in bench._evaluated(body)[0]])
    for side in ('l','r'):
        contour[f'gh_{side}_{ht}']=np.array(tuple(rig.matrix_world@rig.pose.bones['upperarm_'+side].head))
        contour[f'elbow_{side}_{ht}']=np.array(tuple(rig.matrix_world@rig.pose.bones['forearm_'+side].head))
np.savez_compressed(out/'native_probe.npz',**contour)
after=protect();checks={k:before[k]==after[k] for k in before};assert all(v for k,v in checks.items() if k!='weights'),checks
assert after_patch==after,'Data changed during animation'
np.savez_compressed(out/'weight_patch.npz',before=patch.pop('before'),after=patch.pop('after'))
assert hashlib.sha256(model.read_bytes()).hexdigest()==expected
np.savez_compressed(out/'probe.npz',back_points=np.array(points),bone_matrices=np.array(bones),**snap)
(out/'weight_probe.json').write_text(json.dumps(dict(mode=mode,diagnostic_only=True,approved=False,model_saved=False,repair_complete=False,samples=161,bone_names=names,protected_identity=checks,authorised_weight_exception=patch,maximum_baseline_replay_error_mm=max_baseline_error,maximum_nonlat_pose_difference=max_nonlat_pose_error,actual_approved_outline=outlines,rows=rows,
    probe='One synchronous 25% one-ring smoothing pass on authorised26 vertices; global2.5percentage-point cap; no fitting',
    limitations=['Only the authorised26 weights change; original weight identity intentionally fails.','Original bone motion, all key coordinates, topology and other weights remain protected.','Complete safety and benchmarks are separate retained steps, not inferred from this render.']),indent=2)+'\n')
print('R53_WEIGHT_TRIAL_COMPLETE',mode,checks,flush=True)
