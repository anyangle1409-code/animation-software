"""Native, unsaved contour-study evidence. Never creates a candidate blend."""
from pathlib import Path
import sys,os,json
import bpy,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/anatomy_fit')]
os.environ['S7_LOCKOUT_HT']='166'
import build_original_review_candidate_r17_blender as r17
import build_original_movement_benchmarks_blender as bench
import build_original_sculpt_corrective_blender as sculpt
import original_v1_review_candidate_drives as drives
import original_v1_press_extension as px
from original_review_r41_strain import area_safety
from original_review_r42_line import profile,guide
args=sys.argv[sys.argv.index('--')+1:];source,solution,out=map(Path,args[:3]);model=Path(args[3]) if len(args)>3 else None
out.mkdir(parents=True,exist_ok=True)
z=np.load(source);delta=np.load(solution)['delta'];faces=z['faces']
parent=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend'
res=r17._setup(model or parent);body,rig=res['body'],res['runtime'];blocks=body.data.shape_keys.key_blocks
from original_review_r43_native import install as install_native
def install(active):
 if model is None:install_native(res,delta,z['sampling_basis']);bpy.context.view_layer.update()
def points():return np.asarray([tuple(v) for v in bench._evaluated(body)[0]])
scene=bpy.context.scene
for ob in scene.objects:
 if ob.type in ('MESH','CURVE') and ob is not body:ob.hide_render=True
mat=bpy.data.materials.new('R44_UNSAVED_STUDY');mat.diffuse_color=(.72,.55,.45,1)
body.data.materials.clear();body.data.materials.append(mat)
scene.render.engine='BLENDER_WORKBENCH';sh=scene.display.shading
sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_cavity=True
scene.render.film_transparent=True;scene.render.resolution_x=scene.render.resolution_y=640
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
cd=bpy.data.cameras.new('R44_STUDY_CAMERA');cd.type='ORTHO'
cam=bpy.data.objects.new('R44_STUDY_CAMERA',cd);scene.collection.objects.link(cam);scene.camera=cam
def render(path,target,direction,scale):
 d=Vector(direction).normalized();cd.ortho_scale=scale;cam.location=Vector(target)+d*4
 cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y')
 scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
report={'status':'UNSAVED_CONTOUR_STUDY_NOT_ACCEPTED','model_saved':model is not None,'samples':[]}
ref=np.load(ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r38_20261017/probe/r35_contour_surfaces.npz')
for name,active in [('R44',True)]:
 install(active);folder=out/name;folder.mkdir(exist_ok=True)
 snapshots={'rest':z['rest'],'faces':faces}
 for ht in (120.,130.,135.625,145.,156.,166.):
  bench._reset(rig);sculpt.press_pose(res,ht);drives.drive(rig,body)
  snapshots[f'all_{ht}']=points()
  for side in ('l','r'):
   snapshots[f'gh_{side}_{ht}']=np.array(tuple(rig.matrix_world@rig.pose.bones['upperarm_'+side].head))
   snapshots[f'elbow_{side}_{ht}']=np.array(tuple(rig.matrix_world@rig.pose.bones['forearm_'+side].head))
  if ht==135.625:
   p=points();vals={}
   for side in ('l','r'):
    gh=ref[f'gh_{side}_135.625'];el=ref[f'elbow_{side}_135.625'];levels=np.array([-.12,-.10,-.08,-.06])
    line=guide(ref['all_135.625'],faces,gh,el,side);vals[side]=((profile(p,faces,gh,el,side,levels)-np.polyval(line,levels))*1000).tolist()
   report[name+'_profile_mm']=vals
  for side in ('l','r'):
   sign=1 if side=='r' else -1;gh=rig.matrix_world@rig.pose.bones['upperarm_'+side].head
   target=gh+Vector((sign*.03,.01,-.03))
   render(folder/f'{side}_back_{ht}.png',target,(0,1,.02),.42)
   render(folder/f'{side}_three_quarter_{ht}.png',target,(sign*.7,.7,.05),.42)
 np.savez_compressed(folder/'native_probe.npz',**snapshots)
 if active:
  scene.render.resolution_x=scene.render.resolution_y=512
  for i in range(41):
   bench._reset(rig);px.pose_press_full(res,i/40);drives.drive(rig,body);p=points()
   row=area_safety(p,z['base'][i],z['rest'],faces)
   predicted=z['base'][i]+np.einsum('nij,nj->ni',z['mat'][i],np.einsum('kn,knj->nj',z['weight'][i],delta))
   row['native_affine_error_mm']=float(np.linalg.norm(p-predicted,axis=1).max()*1000)
   report['samples'].append(row)
   for view,d in [('back',(0,1,.02)),('front',(0,-1,.02)),('three_quarter',(.7,.7,.05))]:
    render(folder/f'f{i:03d}_{view}.png',(0,0,1.45),d,1.15)
report['marked_stretch']=report['samples'][25]['current']['stretch']
report['parent_marked_stretch']=report['samples'][25]['parent']['stretch']
report['press_area_safety_passed']=all(r['passed'] for r in report['samples'])
(out/'native_study.json').write_text(json.dumps(report,indent=2)+'\n')
print('R44_UNSAVED_STUDY',report['marked_stretch'],report['parent_marked_stretch'],flush=True)
