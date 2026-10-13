"""Actual paired shoulder details, native LBS/DQ; not accepted biomechanics."""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import original_shoulder_joint_authority as authority
import build_functional_absolute_reach_blender as reach
source=Path(bpy.data.filepath);expected='91ac6b9845a7982e87c7fe0c44b114ee4382c7eb1720d1052ba2bdc29f648e09'
assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
out=Path(sys.argv[sys.argv.index('--')+1]).resolve();out.mkdir(parents=True,exist_ok=True)
body=bpy.data.objects['HGPT_BODY_SHOULDER_REFIT_TRIAL'];rig=bpy.data.objects['HGPT_SHOULDER_JOINT_REFIT_TRIAL']
guide=next(o for o in bpy.data.objects if o.type=='ARMATURE' and len(o.data.bones)==6 and 'scapula_left' in o.data.bones)
record=json.loads((ROOT/authority.RECORD).read_text())
mapping={part+'_'+side:rt+'_'+suffix for side,suffix in [('left','r'),('right','l')] for part,rt in [('clavicle','clavicle'),('scapula','scapula'),('humerus','upperarm')]}
rest={n:rig.matrix_world@rig.data.bones[n].matrix_local for n in mapping.values()}
gs={n:guide.matrix_world@guide.data.bones[n].matrix_local for n in mapping}
reach.pose_absolute(guide,record,160)
for n,t in mapping.items():
    rig.pose.bones[t].matrix=rig.matrix_world.inverted()@(guide.matrix_world@guide.pose.bones[n].matrix)@gs[n].inverted()@rest[t]
    bpy.context.view_layer.update()
modifier=next(m for m in body.modifiers if m.type=='ARMATURE')
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1800;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
camera=scene.camera;camera.data.ortho_scale=1.25
files=[]
for mode,preserve in [('before_linear',False),('after_volume',True)]:
    modifier.use_deform_preserve_volume=preserve;bpy.context.view_layer.update()
    for view,offset in [('front',Vector((0,-5,0))),('rear',Vector((0,5,0)))]:
        target=Vector((0,0,1.52));camera.location=target+offset;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        filename=mode+'_'+view+'.png';scene.render.filepath=str(out/filename);bpy.ops.render.render(write_still=True)
        files.append({'file':filename,'sha256':hashlib.sha256((out/filename).read_bytes()).hexdigest(),'pose':'AUTHORED_160_DEG','view':view,'volume_preservation':preserve})
for arm in (guide,rig):
    for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4)
modifier.use_deform_preserve_volume=True;bpy.context.view_layer.update()
assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
(out/'volume_comparison_images.json').write_text(json.dumps({'source_sha256':expected,'images':files,'scene_saved':False,'deformation_accepted':False,'crop':'shoulder detail; arm tips and legs outside camera; full body retained'},indent=2)+'\n')
