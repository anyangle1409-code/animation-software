"""Create a separate weights-only candidate and actual before/after diagnostics."""
import bpy,sys,json,hashlib,math
from pathlib import Path
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import original_foot_contact_weights as contact
SOURCE_SHA='670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56'
source=Path(bpy.data.filepath).resolve();assert hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_SHA
out=Path(sys.argv[sys.argv.index('--')+1]).resolve();out.mkdir(parents=True,exist_ok=True)
top_only='--only-top' in sys.argv
body=bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE'];rig=bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
anatomy=bpy.data.objects['HGPT_ANATOMICAL_MASTER'];scene=bpy.context.scene
def skeletal_record():
 return {r.name:{'world':[list(v) for v in r.matrix_world],'bones':{b.name:[list(b.head_local),list(b.tail_local),[list(row) for row in b.matrix_local]] for b in r.data.bones}} for r in (rig,anatomy)}
sk_before=skeletal_record();coords_before=[tuple(v.co) for v in body.data.vertices]
old_weights=[{body.vertex_groups[g.group].name:g.weight for g in v.groups} for v in body.data.vertices]
original_pose={p.name:p.matrix_basis.copy() for p in rig.pose.bones}
def reset():
 for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update()
def verts():
 e=body.evaluated_get(bpy.context.evaluated_depsgraph_get());return [e.matrix_world@v.co for v in e.data.vertices]
def pose(control,suffix,angle):
 reset();p=rig.pose.bones[control+'_'+suffix];h=p.head.copy()
 p.matrix=Matrix.Translation(h)@Matrix.Rotation(math.radians(angle),4,'X')@Matrix.Translation(-h)@p.matrix
 bpy.context.view_layer.update()
reset();rest=verts();foot_ids={s:[i for i,p in enumerate(rest) if p.z<.16 and p.x*sign>0] for s,sign in [('left',1),('right',-1)]}
def sample(side,control,angle):
 suffix='r' if side=='left' else 'l';pose(control,suffix,angle);points=verts();ids=foot_ids[side]
 return {'side':side,'control':control,'angle_deg':angle,'min_foot_z_m':min(points[i].z for i in ids),
  'max_displacement_m':max((points[i]-rest[i]).length for i in ids),
  'all_finite':all(math.isfinite(x) for p in points for x in p)}
def sweeps():return [sample(side,control,angle) for side in ('left','right') for control,angles in [('toe',(-30,-15,0,15,30)),('foot',(-20,-10,0,10,20))] for angle in angles]
before=sweeps();reset()
# Save immutable baseline footage for toe lift before modifying any weight.
scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_percentage=100
scene.render.resolution_x=2000;scene.render.resolution_y=1200;scene.render.image_settings.file_format='PNG'
sh=scene.display.shading;sh.light='STUDIO';sh.color_type='SINGLE';sh.single_color=(.66,.69,.72)
sh.show_cavity=True;sh.cavity_type='BOTH';sh.show_shadows=True;sh.background_type='WORLD'
if scene.world is None:scene.world=bpy.data.worlds.new('FOOT_REVIEW_WORLD')
scene.world.color=(.055,.065,.085)
for o in scene.objects:
 if o.type in ('MESH','CURVE','ARMATURE','EMPTY') and o is not body:o.hide_render=True
body.hide_render=False
cd=bpy.data.cameras.new('FOOT_REVIEW_CAMERA');cd.type='ORTHO';cd.ortho_scale=.39
cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam
render_records=[]
def render(name,view):
 target=Vector((0,-.114,.061));off=Vector({'side':(4,0,0),'front':(0,-4,0),'top':(0,0,4)}[view])
 cam.location=target+off;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
 cd.ortho_scale=.55 if view=='top' else .39
 # Isolate the feet optically in superior views; no mesh cut or shape edit.
 cd.clip_start=3.901 if view=='top' else .01
 bpy.context.view_layer.update()
 path=out/(name+'.png');tmp=out/(name+'.tmp.png');scene.render.filepath=str(tmp)
 if not top_only or view=='top':
  bpy.ops.render.render(write_still=True);assert tmp.read_bytes().endswith(b'\0\0\0\0IEND\xaeB`\x82');tmp.replace(path)
 def project(p):
  q=world_to_camera_view(scene,cam,Vector(p));return [q.x*2000,(1-q.y)*1200]
 boundary=-.24026338264346125
 render_records.append({'file':path.name,'view':view,'ortho_scale_m':cd.ortho_scale,
  'camera_matrix_world':[list(r) for r in cam.matrix_world],
  'camera_near_clip_m':cd.clip_start,'feet_isolated_by_near_clip':view=='top',
  'floor_line_px':[project((0,-.35,0)),project((0,.1,0))],
  '28cm_boundary_px':[project((-.17,boundary,-.02)),project((.17,boundary,.16))]})
for view in ('side','front','top'):render('before_neutral_'+view,view)
pose('toe','r',-30);render('before_toe_lift_side','side');render('before_toe_lift_top','top');reset()
changed=[];maximum_sum_change=0
for v,old in zip(body.data.vertices,old_weights):
 if v.co.z>=.16:continue
 for suffix in ('l','r'):
  toe='toe_'+suffix;foot='foot_'+suffix
  if old.get(toe,0)<=0:continue
  origin=rig.matrix_world@rig.data.bones[toe].head_local
  world=body.matrix_world@v.co
  new=contact.redistribute(old,toe,foot,-world.y,-origin.y,.03)
  if abs(new.get(toe,0)-old.get(toe,0))<1e-12:continue
  maximum_sum_change=max(maximum_sum_change,abs(sum(new.values())-sum(old.values())))
  body.vertex_groups[toe].add([v.index],new[toe],'REPLACE')
  body.vertex_groups[foot].add([v.index],new[foot],'REPLACE')
  changed.append({'vertex':v.index,'toe_control':toe,'old':old,'new':new})
bpy.context.view_layer.update();after=sweeps();reset();after_rest=verts()
rest_error=max((p-q).length for p,q in zip(rest,after_rest))
assert coords_before==[tuple(v.co) for v in body.data.vertices]
assert skeletal_record()==sk_before
assert maximum_sum_change<1e-12 and rest_error<2e-6
for r in after:
 assert r['all_finite']
 if r['control']=='toe' and r['angle_deg']<=0:assert r['min_foot_z_m']>-2e-6,r
scene['hgpt_foot_contact_candidate']='WEIGHTS_ONLY_v1; NOT28cm; review required'
scene['hgpt_production_approved']=False
candidate=out/'HomeGymPT_Male_ORIGINAL_v1_FOOT_CONTACT_WEIGHTS_CANDIDATE.blend'
# Candidate includes actual original full-body geometry/rig; source native file untouched.
for p in rig.pose.bones:p.matrix_basis=original_pose[p.name]
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(candidate));reset()
for view in ('side','front','top'):render('after_neutral_'+view,view)
pose('toe','r',-30);render('after_toe_lift_side','side');render('after_toe_lift_top','top');reset()
# Native reference guides for the proportion blocker, not anatomical surfaces.
audit=json.loads((out/'foot_native_audit.json').read_text())
guides=[];body.hide_render=True;sh.single_color=(.92,.72,.22)
for name,b in audit['anatomical_foot_reference_controls'].items():
 c=bpy.data.curves.new('REVIEW_'+name,'CURVE');c.dimensions='3D';c.bevel_depth=.0011;c.bevel_resolution=2
 s=c.splines.new('POLY');s.points.add(1);s.points[0].co=(*b['head_m'],1);s.points[1].co=(*b['tail_m'],1)
 ob=bpy.data.objects.new(c.name,c);scene.collection.objects.link(ob);guides.append(ob)
for view in ('side','top'):render('reference_guides_'+view,view)
assert skeletal_record()==sk_before and hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_SHA
report={'source_commit':'edee242f76717957a8f10cf2537961f40ce2fa03','source_sha256':SOURCE_SHA,
 'candidate':candidate.name,'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
 'correction_scope':'ONLY toe-to-foot influence redistribution proximal to shared toe pivot; 3cm artist-defined transition',
 'changed_vertex_count':len(changed),'weight_changes':changed,'max_weight_sum_change':maximum_sum_change,
 'max_evaluated_rest_vertex_difference_m':rest_error,'native_mesh_vertices_unchanged':True,
 'both_skeleton_geometry_unchanged':True,'body_height_and_neutral_footprint_unchanged':True,
 'foot_length_still_m':audit['feet']['left']['mesh_length_m'],'28cm_geometry_correction':False,
 'before_motion':before,'after_motion':after,'render_records':render_records,
 'original_model_file_unchanged':True,'production_approved':False,'owner_acceptance_required':True,
 'limits':['This fixes sampled shared-control toe-extension floor crossings only, not individual anatomical toe mechanics.',
 'Toe flexion and free ankle sweeps still need a stance/contact solver; no grounded gait acceptance.',
 'Proportion correction remains blocked by the source reference envelope and station semantics.']}
(out/'foot_contact_candidate_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print('CONTACT_CANDIDATE',len(changed),'changed vertices; rest error',rest_error,'before/after toe extension floors',
 [(b['side'],b['angle_deg'],b['min_foot_z_m'],a['min_foot_z_m']) for b,a in zip(before,after) if b['control']=='toe' and b['angle_deg']<0])
