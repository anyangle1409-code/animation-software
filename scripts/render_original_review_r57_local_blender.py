"""R57 actual native R52 vs R57 visual evidence, each in a fresh Blender process.

Use matched body/pose/cameras, no altered model saved. Neither variant is approved.
"""
from pathlib import Path
import sys,os,json,hashlib
import bpy,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/anatomy_fit')]
os.environ['S7_LOCKOUT_HT']='166'
import build_original_review_candidate_r17_blender as r17
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
import original_v1_press_extension as px
from original_review_r52_native import install

source,solution,out,mode=sys.argv[-4:]
if mode not in ('R52_original','R57_local_study'):
    raise ValueError("Unexpected model-study label")
out=Path(out)/mode
out.mkdir(parents=True,exist_ok=False)
model=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend'
expected='4c44b1fe14aeefd9a976f45baada60b4b81aaaa7cd736a300ca7cede2b0aaf2e'
if hashlib.sha256(model.read_bytes()).hexdigest()!=expected:
    raise ValueError("Original Blender model bytes changed")
res=r17._setup(model)
rig,body=res['runtime'],res['body']
keys=body.data.shape_keys.key_blocks
digest=lambda a:hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def protect():
    return dict(
        rest_bones=[(b.name,tuple(b.head_local),tuple(b.tail_local),
                     tuple(float(x) for row in b.matrix_local for x in row))
                    for b in rig.data.bones],
        groups=[g.name for g in body.vertex_groups],
        weights=[[(g.group,g.weight) for g in v.groups] for v in body.data.vertices],
        basis=digest(np.array([tuple(v.co) for v in keys[0].data])),
        non_s7={k.name:digest(np.array([tuple(v.co) for v in k.data]))
                for k in keys if not k.name.startswith('HGPT_S7_DELT_')})
before=protect()
z=np.load(source);candidate=np.load(solution)['dense_delta']
install(res,candidate,z['sampling_basis'])
after=protect()
if before!=after:
    raise RuntimeError("R57 native installer modified protected source components")
scene=bpy.context.scene
for ob in scene.objects:
    if ob.type in ('MESH','CURVE') and ob is not body:
        ob.hide_render=True
material=bpy.data.materials.new('R57_UNSAVED_DIAGNOSTIC_ONLY')
material.diffuse_color=(.72,.55,.45,1)
body.data.materials.clear()
body.data.materials.append(material)
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO'
scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_cavity=True
scene.render.film_transparent=True
scene.render.resolution_x=scene.render.resolution_y=512
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
camera_data=bpy.data.cameras.new('R57_REVIEW')
camera_data.type='ORTHO'
camera_data.ortho_scale=1.15
camera=bpy.data.objects.new('R57_REVIEW',camera_data)
scene.collection.objects.link(camera)
scene.camera=camera
views=dict(front=(0,-1,.02),rear=(0,1,.02),
           side=(1,0,.02),three_quarter=(.7,.7,.05))
rows=[]
for fraction in (0.5,0.625,0.8):
    bench._reset(rig)
    state=px.pose_press_full(res,fraction)
    drives.drive(rig,body)
    bpy.context.view_layer.update()
    for view,direction in views.items():
        direction=Vector(direction).normalized()
        camera.location=Vector((0,0,1.45))+direction*4
        camera.rotation_mode='QUATERNION'
        camera.rotation_quaternion=(-direction).to_track_quat('-Z','Y')
        scene.render.filepath=str(out/('t'+str(fraction).replace('.','_')+'_'+view+'.png'))
        bpy.ops.render.render(write_still=True)
    rows.append(dict(press_fraction=fraction,native_pose_state=str(state),
                     views=list(views)))
(out/'actual_native_visual_evidence.json').write_text(json.dumps(
    dict(status='UNSAVED_R57_VISUAL_STUDY_NOT_APPROVED',mode=mode,
         model_saved=False,protected_identity_passed=before==after,
         elligible_for_owner_review_only=True,poses=rows),indent=2)+chr(10))
if hashlib.sha256(model.read_bytes()).hexdigest()!=expected:
    raise RuntimeError("Immutable Blender model modified")
print('R57_NATIVE_IMAGES_COMPLETE',mode,flush=True)
