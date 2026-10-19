"""Read-only project scapula-guide/landmark containment. No model save."""
from pathlib import Path
import sys,os,json,hashlib
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/anatomy_fit')];os.environ['S7_LOCKOUT_HT']='166'
import build_original_review_candidate_r17_blender as r17
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
import original_v1_press_extension as px
from original_review_r52_native import install
from original_shoulder_containment_audit import classify_hits,closed_triangle_surface
source,solution,out,mode=sys.argv[-4:];out=Path(out)/mode;out.mkdir(parents=True,exist_ok=False)
if mode not in ('r41','r52'):raise ValueError(mode)
DIRECTIONS=[Vector(v).normalized() for v in ((1,.123,.237),(.137,1,.317),(.213,.391,1))]

def query(point,tree,closed=True):
 point=Vector(point);near=tree.find_nearest(point)
 if near[0] is None:raise RuntimeError('No skin surface')
 rays=[]
 for direction in DIRECTIONS:
  distances=[];travel=0.;complete=False
  for _ in range(128):
   hit,normal,index,distance=tree.ray_cast(point+direction*travel,direction,20.-travel)
   if hit is None:complete=True;break
   if abs(normal.dot(direction))<1e-8:break
   absolute=travel+distance;distances.append(float(absolute));travel=absolute+1e-7
   if travel>=20.:complete=True;break
  rays.append(distances if complete else None)
 result=classify_hits(rays,float(near[3]))
 if not closed:result.update(ray_only_classification=result['classification'],classification='unreliable_open_skin',signed_clearance_mm=None)
 return dict(point_world_m=list(point),**result)

# Native BVH integration check on a known closed cube, before touching model data.
cube=[(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
quad=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
ct=BVHTree.FromPolygons(cube,quad)
for p,status in [((0,0,0),'inside'),((3,0,0),'outside'),((1,0,0),'on_skin')]:
 actual=query(p,ct)['classification']
 if actual!=status:raise RuntimeError(('Native classifier self-test',p,actual,status))
print('NATIVE_CONTAINMENT_CUBE_SELFTEST_PASS',flush=True)
model=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend'
expected='4c44b1fe14aeefd9a976f45baada60b4b81aaaa7cd736a300ca7cede2b0aaf2e'
if hashlib.sha256(model.read_bytes()).hexdigest()!=expected:raise RuntimeError('Wrong baseline')
z=np.load(source);res=r17._setup(model);body,rig=res['body'],res['runtime'];blocks=body.data.shape_keys.key_blocks

def protected():
 digest=lambda a:hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
 def bones(ob):return [(b.name,b.parent.name if b.parent else None,list(b.head_local),list(b.tail_local),b.use_deform,[float(v) for row in b.matrix_local for v in row]) for b in ob.data.bones]
 return dict(runtime_rest=bones(rig),anatomy_rest=bones(res['anatomy']),basis=digest(np.array([tuple(v.co) for v in blocks[0].data])),
  polygons=[list(p.vertices) for p in body.data.polygons],groups=[g.name for g in body.vertex_groups],weights=[[(g.group,g.weight) for g in v.groups] for v in body.data.vertices],
  non_s7={k.name:digest(np.array([tuple(v.co) for v in k.data])) for k in blocks if not k.name.startswith('HGPT_S7_DELT_')})
before=protected()
if mode=='r52':install(res,np.load(solution)['dense_delta']);bpy.context.view_layer.update()
faces=z['faces'];closed=closed_triangle_surface(faces);guides={};landmarks={}
for runtime_side,anatomy_side in (('r','left'),('l','right')):
 ob=res['objects'][f'scapula_{anatomy_side}']
 if ob.get('runtime_control')!=f'scapula_{runtime_side}':raise RuntimeError('Guide side mapping mismatch')
 guides[runtime_side]=ob
 landmarks[runtime_side]={}
 for name in ('AA','TS','AI','GH'):
  oblm=bpy.data.objects.get(f'LM_scapula_{anatomy_side}__{name}')
  if oblm is None:raise RuntimeError('Required named landmark absent: '+name)
  landmarks[runtime_side][name]=oblm.matrix_world.translation.copy()
scene=bpy.context.scene
for ob in scene.objects:
 if ob.type in ('MESH','CURVE') and ob is not body:ob.hide_render=True
mat=bpy.data.materials.new('READ_ONLY_CONTAINMENT_SKIN');mat.diffuse_color=(.72,.55,.45,1);body.data.materials.clear();body.data.materials.append(mat)
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_cavity=True
scene.render.film_transparent=True;scene.render.resolution_x=scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
cd=bpy.data.cameras.new('READ_ONLY_CONTAINMENT_CAMERA');cd.type='ORTHO';cd.ortho_scale=1.05
cam=bpy.data.objects.new('READ_ONLY_CONTAINMENT_CAMERA',cd);scene.collection.objects.link(cam);scene.camera=cam
rows=[];projections={};snapshots={};render_frames=(0,80,128,160);bone_matrices=[]
for i in range(161):
 bench._reset(rig);state=px.pose_press_full(res,i/160);drives.drive(rig,body);p=np.array([tuple(v) for v in bench._evaluated(body)[0]]);tree=BVHTree.FromPolygons(p.tolist(),faces.tolist(),all_triangles=True)
 row=dict(frame=i,t=i/160,press=state,sides={});bone_matrices.append(np.array([tuple(tuple(r) for r in (rig.matrix_world@rig.pose.bones[f'scapula_{s}'].matrix)) for s in ('r','l')]))
 view_data={}
 for side,ob in guides.items():
  verts,polys=bench._evaluated(ob);verts=np.array([tuple(v) for v in verts]);triangles=[]
  for f in polys:
   for j in range(1,len(f)-1):triangles.append([f[0],f[j],f[j+1]])
  tri=np.array(triangles,int);edges=np.unique(np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1),axis=0)
  samples=np.concatenate([verts,verts[tri].mean(1),verts[edges].mean(1)]);records=[query(v,tree,closed) for v in samples]
  delta=rig.matrix_world@rig.pose.bones[f'scapula_{side}'].matrix@rig.data.bones[f'scapula_{side}'].matrix_local.inverted()@rig.matrix_world.inverted()
  lm={name:query(delta@point,tree,closed) for name,point in landmarks[side].items()}
  control={name:query(rig.matrix_world@point,tree,closed) for name,point in (('head',rig.pose.bones[f'scapula_{side}'].head),('tail',rig.pose.bones[f'scapula_{side}'].tail))}
  counts={status:sum(r['classification']==status for r in records) for status in ('inside','outside','on_skin','ambiguous','unreliable_open_skin')}
  row['sides'][side]=dict(guide_object=ob.name,guide_is_provisional=True,sample_counts=counts,guide_vertices=len(verts),guide_samples=records,landmarks=lm,runtime_control_only=control)
  view_data[side]=(verts,edges,records[:len(verts)],lm)
  if i in render_frames:snapshots[f'guide_{side}_{i}']=verts
 if i in render_frames:
  snapshots[f'skin_{i}']=p
  for view,direction in (('back',(0,1,.02)),('three_quarter',(.7,.7,.05))):
   direction=Vector(direction).normalized();cam.location=Vector((0,0,1.48))+direction*4;cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-direction).to_track_quat('-Z','Y');bpy.context.view_layer.update()
   key=f'f{i:03d}_{view}';scene.render.filepath=str(out/(key+'.png'));bpy.ops.render.render(write_still=True)
   def pixel(point):
    uv=world_to_camera_view(scene,cam,Vector(point));return [float(uv.x*640),float((1-uv.y)*640)]
   projections[key]={side:dict(vertices=[pixel(v) for v in vd[0]],edges=vd[1].tolist(),classification=[r['classification'] for r in vd[2]],landmarks={n:dict(pixel=pixel(v['point_world_m']),classification=v['classification']) for n,v in vd[3].items()}) for side,vd in view_data.items()}
 rows.append(row)
 if i%40==0:print('SCAPULA_CONTAINMENT_FRAME',mode,i,flush=True)
after=protected();checks={k:before[k]==after[k] for k in before}
if not all(checks.values()):raise RuntimeError(('Protected data changed',checks))
if hashlib.sha256(model.read_bytes()).hexdigest()!=expected:raise RuntimeError('Stored baseline changed')
report=dict(mode=mode,diagnostic_only=True,model_saved=False,stored_model_modified=False,repair_complete=False,skin_topology_closed=closed,samples=161,protected_identity=checks,projections=projections,rows=rows,
 limitations=['Scapula bowl is an existing project-authored provisional guide, not an independently validated physical bone.','AA/TS/AI/GH are existing project landmarks carried by the unchanged runtime scapula transform.','Guide vertices, triangle centres and edge midpoints are sampled; this is not proof of continuous-volume containment.','Closed topology does not exclude self-intersection. R52 remains an unsafe rejected study.','Ray disagreements are ambiguous and are never reported as contained.'])
(out/'containment.json').write_text(json.dumps(report,indent=2)+'\n');np.savez_compressed(out/'snapshot_geometry.npz',faces=faces,**snapshots);np.savez_compressed(out/'scapula_matrices.npz',matrices=np.array(bone_matrices))
print('SCAPULA_CONTAINMENT_COMPLETE',mode,closed,checks,flush=True)
