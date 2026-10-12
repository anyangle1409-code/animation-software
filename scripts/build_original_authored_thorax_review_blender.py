"""W2: separate original full-body + authored thorax/shoulder context scene.

Original r95 mesh/weights and both original rigs remain unchanged. c004-authored
curved guides retain their own six controls; no body retarget is installed.
"""
import bpy,sys,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import build_functional_scapula_bowl_blender as bowl
import build_functional_thorax_context_blender as context
import original_v1_functional_fullbody as bridge
source=Path(bpy.data.filepath).resolve()
expected='670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56'
assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
out=Path(sys.argv[sys.argv.index('--')+1]).resolve();out.mkdir(parents=True,exist_ok=True)
original=bpy.context.scene;body=bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
runtime=bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL'];anatomy=bpy.data.objects['HGPT_ANATOMICAL_MASTER']
assert not bridge.validate_blender_bridge(anatomy,runtime,body)['errors']
def fingerprint():
 return hashlib.sha256(json.dumps({'coords':[list(v.co) for v in body.data.vertices],
 'weights':[[[g.group,g.weight] for g in v.groups] for v in body.data.vertices],
 'shape_keys':{k.name:[list(v.co) for v in k.data] for k in body.data.shape_keys.key_blocks},
 'rigs':{a.name:{'world':[list(r) for r in a.matrix_world],
  'rest':{b.name:[list(b.head_local),list(b.tail_local)] for b in a.data.bones},
  'pose':{p.name:[list(r) for r in p.matrix_basis] for p in a.pose.bones}} for a in (runtime,anatomy)}},sort_keys=True).encode()).hexdigest()
before=fingerprint()
record=ROOT/context.shoulder.RECORD;rec=json.loads(record.read_text())
temporary=bpy.data.scenes.new('AUTHORED_GUIDES_BUILD_ISOLATION');bpy.context.window.scene=temporary
arm,shoulders=bowl.build(rec);thorax=context.add_context(rec)
assert len(shoulders)==18 and len(thorax)==25
objects=[arm,*shoulders,*thorax]
for ob in objects:
 original.collection.objects.link(ob)
 for coll in list(ob.users_collection):
  if coll is not original.collection:coll.objects.unlink(ob)
bpy.context.window.scene=original
assert fingerprint()==before
for ob in shoulders+thorax:
 ob['hgpt_review_scope']='SOURCE_AUTHORED_CONTEXT; NOT ANATOMY/CONTACT/BODY DEFORMATION APPROVED'
 ob.hide_render=False
original['hgpt_authored_thorax_review_candidate']='STATIC_CONTEXT_ONLY'
original['hgpt_production_approved']=False
candidate=out/'HomeGymPT_Male_ORIGINAL_v1_AUTHORED_THORAX_REVIEW_ONLY.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(candidate))
# New guide-layer views only; full actual body is visible through diagnostic x-ray.
original.render.engine='BLENDER_WORKBENCH';original.render.resolution_percentage=100
original.render.resolution_x=1600;original.render.resolution_y=2400;original.render.image_settings.file_format='PNG'
sh=original.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_cavity=True;sh.cavity_type='BOTH'
sh.show_xray=True;sh.xray_alpha=.35;sh.background_type='WORLD'
if original.world is None:original.world=bpy.data.worlds.new('AUTHORED_CONTEXT_WORLD')
original.world.color=(.055,.065,.085)
for ob in original.objects:
 if ob.type in ('MESH','CURVE') and ob is not body and ob not in objects:ob.hide_render=True
body.hide_render=False
data=bpy.data.cameras.new('AUTHORED_CONTEXT_CAMERA');data.type='ORTHO'
cam=bpy.data.objects.new(data.name,data);original.collection.objects.link(cam);original.camera=cam
pts=[body.matrix_world@v.co for v in body.data.vertices]
lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
centre,scale=bridge.frame_from_bounds(lo,hi,1.15)
files=[]
for view,offset in {'front':(0,-4,0),'side':(4,0,0),'rear_three_quarter':(3,3,0)}.items():
 target=Vector(centre);data.ortho_scale=scale;cam.location=target+Vector(offset)
 cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
 p=out/('fullbody_authored_context_'+view+'.png');tmp=p.with_name(p.stem+'.tmp.png');original.render.filepath=str(tmp)
 bpy.ops.render.render(write_still=True);assert tmp.read_bytes().endswith(b'\0\0\0\0IEND\xaeB`\x82');tmp.replace(p);files.append(p)
assert fingerprint()==before
assert not bridge.validate_blender_bridge(anatomy,runtime,body)['errors']
assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
report={'source_commit':'edee242f76717957a8f10cf2537961f40ce2fa03','source_sha256':expected,
 'source_shape_record_sha256':hashlib.sha256(record.read_bytes()).hexdigest(),
 'candidate':candidate.name,'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
 'body_vertices':len(body.data.vertices),'original_runtime_bones':len(runtime.data.bones),
 'original_anatomical_bones':len(anatomy.data.bones),'additional_authored_guide_bones':len(arm.data.bones),
 'authored_shoulder_meshes':len(shoulders),'authored_thorax_meshes':len(thorax),
 'original_body_weights_correctives_and_skeletons_unchanged':True,'original_fingerprint':before,
 'body_has_only_original_runtime_driver':True,'source_guides_drive_body':False,
 'purpose':'Actual static full-body reference-layer integration; diagnostic x-ray visibility',
 'assumptions':['Inherited project-authored rib lateral bows9-15cm/tube radius4mm; no bone-surface/contact acceptance',
  'Inherited8mm costal scapula recession/4mm thickness is artist-defined',
  'c004 guide controls preserve their distinct frames; old runtime joint gaps remain unresolved',
  'Original31cm feet and all inherited body anatomy/deformation defects remain'],
 'files_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [candidate,*files]},
 'production_approved':False,'anatomical_approval':False,'motion_approved':False}
(out/'authored_thorax_review_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print('W2_AUTHORED_CONTEXT',len(shoulders)+len(thorax),'authored meshes; actual original body preserved;3native views')
