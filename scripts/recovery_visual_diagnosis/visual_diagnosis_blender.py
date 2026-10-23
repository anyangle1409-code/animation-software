"""Read-only native pose/triangle evidence on exact reconstructed copies. NEVER saves a .blend."""
import hashlib,json,sys,traceback,struct,tempfile,shutil,math
from pathlib import Path
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from triangle_flags import flag_triangles,compare_rows

SELECT={'shoulder_press':{0,6,8},'squat':{0,7,8}}

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def static_signature(rig,body,adapter):
 h=hashlib.sha256();a=np.empty(len(body.data.vertices)*3,dtype=np.float32)
 body.data.vertices.foreach_get('co',a);h.update(a.tobytes())
 loops=np.empty(len(body.data.loops),dtype=np.int32);body.data.loops.foreach_get('vertex_index',loops);h.update(loops.tobytes())
 for field in ('loop_start','loop_total'):
  poly=np.empty(len(body.data.polygons),dtype=np.int32);body.data.polygons.foreach_get(field,poly);h.update(poly.tobytes())
 h.update(json.dumps([(g.index,g.name) for g in body.vertex_groups],separators=(',',':')).encode())
 for k in body.data.shape_keys.key_blocks:
  h.update(k.name.encode());k.data.foreach_get('co',a);h.update(a.tobytes())
 for v in body.data.vertices:
  for g in v.groups:h.update(struct.pack('<IIf',v.index,g.group,g.weight))
 return {'rest_bones':adapter.rest_signature(rig,body),'mesh_keys_weights':h.hexdigest()}

def snapshot_render(V,F,flags,out,stem,roi=None):
 """New display-only scene/mesh from evaluated coordinates. No source geometry edited."""
 source_scene=bpy.context.window.scene
 scene=bpy.data.scenes.new('READONLY_DISPLAY_'+stem)
 meshes=[]
 try:
  bpy.context.window.scene=scene
  mesh=bpy.data.meshes.new('evaluated_snapshot');mesh.from_pydata(V,[],F);mesh.update();meshes.append(mesh)
  ob=bpy.data.objects.new('snapshot_not_a_model',mesh);scene.collection.objects.link(ob)
  for name,color in [('plain',(.62,.63,.65,1)),('stretch_yellow',(1,.72,.03,1)),('collapse_red',(.9,.03,.02,1)),('intersection_purple',(.65,.05,.85,1))]:
   mat=bpy.data.materials.new('diagnostic_'+name);mat.diffuse_color=color;mesh.materials.append(mat)
  codes=np.zeros(len(F),dtype=np.int32)
  for i in flags.get('stretched',[]):codes[i]=1
  for i in flags.get('collapsed',[]):codes[i]=2
  for a,b in flags.get('intersections',[]):codes[a]=codes[b]=3
  scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL'
  scene.display.shading.show_cavity=True;scene.display.shading.show_shadows=True
  scene.render.image_settings.file_format='PNG';scene.render.resolution_x=600;scene.render.resolution_y=850;scene.render.resolution_percentage=100
  scene.world=bpy.data.worlds.new('diagnostic_world');scene.world.color=(.12,.12,.12)
  camera=bpy.data.cameras.new('diagnostic_camera');camera.type='ORTHO';cam=bpy.data.objects.new('diagnostic_camera',camera);scene.collection.objects.link(cam);scene.camera=cam
  # Fixed full-body camera framing across models and samples; hand-only view is explicitly separate.
  centre=Vector((0,0,1.1));scale=2.5
  if roi is not None:centre=Vector(roi);scale=.32
  camera.ortho_scale=scale
  for mode in ('plain','overlay'):
   mesh.polygons.foreach_set('material_index',np.zeros(len(F),dtype=np.int32) if mode=='plain' else codes)
   mesh.update()
   for view,offset in [('front',(0,-5,0)),('back',(0,5,0)),('side',(5,0,0)),('three_quarter',(3.6,-3.6,.6))]:
    cam.location=centre+Vector(offset);cam.rotation_euler=(centre-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(out/(stem+'__'+mode+'__'+view+'.png'));bpy.ops.render.render(write_still=True)
 finally:
  bpy.context.window.scene=source_scene
  for ob in list(scene.objects):bpy.data.objects.remove(ob,do_unlink=True)
  bpy.data.scenes.remove(scene)
  for mesh in meshes:bpy.data.meshes.remove(mesh)

def main():
 source,root,priorpath,out=map(lambda x:Path(x).resolve(),sys.argv[sys.argv.index('--')+1:])
 if out.exists():raise ValueError('Output must be a new empty suffixed folder')
 sys.path[:0]=[str(root/'scripts'),str(root/'scripts/anatomy_fit'),str(Path(__file__).resolve().parents[1]/'recovery_diagnostics')]
 import diagnose_candidates_blender as adapter
 from fixed_measurement_triangles import freeze_evaluated
 import build_original_movement_benchmarks_blender as bench
 import build_functional_shoulder_correction_blender as correction
 import original_v1_review_candidate_drives as drives
 import original_v1_press_extension as px
 digest=sha(source);model=adapter.candidate_name(digest)
 prior=json.loads(priorpath.read_text())
 if prior['source_sha256']!=digest:raise ValueError('Prior measurement source mismatch')
 out.mkdir();copydir=Path(tempfile.mkdtemp(prefix='immutable_model_copy_',dir=out));copy=copydir/source.name;shutil.copy2(source,copy);copy.chmod(0o444)
 if sha(copy)!=digest:raise ValueError('Copy hash mismatch')
 report={'model':model,'source_sha256':digest,'running_blender':bpy.app.version_string,'paths':{},'approved':False,'archive_equivalence':'FAIL / NOT_ESTABLISHED','anatomical_approval':'NOT_GRANTED','overlay_legend':{'yellow':'stretch area ratio>2','red':'collapse area ratio<0.1','purple':'nonadjacent intersecting triangles (priority over red/yellow)'},'scope':'read-only pose/triangle diagnosis; display meshes are evaluated snapshots, not saved models'}
 original_eval=bench._evaluated;original_metric=bench.frame_metrics;original_build=correction.build_corrected_scene
 original_pairs=bench._thumb_finger_pairs;original_collapse=bench._hand_collapse
 # Independent saved display control, rendered before installing diagnostic drives.
 bpy.ops.wm.open_mainfile(filepath=str(copy),use_scripts=False,load_ui=False)
 saved_body=bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
 ev=saved_body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 try:
  me.calc_loop_triangles();savedV=[ev.matrix_world@v.co for v in me.vertices];savedF=[tuple(t.vertices) for t in me.loop_triangles]
 finally:ev.to_mesh_clear()
 snapshot_render(savedV,savedF,{},out,model+'__SAVED_DISPLAY_AS_LOADED')
 report['saved_display_control']='evaluated as loaded, no drive/setup installed; fixed camera matches other full-body views'
 for path in ('shoulder_press','squat','grip'):
  bpy.ops.wm.open_mainfile(filepath=str(copy),use_scripts=False,load_ui=False)
  body=bpy.data.objects[adapter.BODY] if hasattr(adapter,'BODY') else bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
  rig=bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL'];before=static_signature(rig,body,adapter)
  result=adapter.loaded_result(bpy,correction,drives);px.install()
  if 'hgpt_cap_fraction_ramp' in rig or px._PATH['name']!='v4':raise ValueError('Press source setup changed')
  correction.build_corrected_scene=lambda:result
  native_polygons=[]
  def triangles(ob):
   ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
   try:
    me.calc_loop_triangles();native_polygons[:]=[t.polygon_index for t in me.loop_triangles]
    return [tuple(t.vertices) for t in me.loop_triangles]
   finally:ev.to_mesh_clear()
  bench._evaluated,tess=freeze_evaluated(original_eval,triangles)
  entry={'frames':[],'grip_trials':[],'measurement_tessellation':tess};report['paths'][path]=entry
  index=[0]
  def capture(V0,V,F,dom,rest_floor):
   metrics=original_metric(V0,V,F,dom,rest_floor);i=index[0];index[0]+=1
   if i==0 and path=='shoulder_press':snapshot_render(V0,F,{},out,model+'__BENCHMARK_REST_BEFORE_PATH')
   if i in SELECT.get(path,set()):
    areas0=[bench._area(V0,f) for f in F];areas=[bench._area(V,f) for f in F]
    tree=BVHTree.FromPolygons(V,F,all_triangles=True)
    flags=flag_triangles(F,areas0,areas,tree.overlap(tree))
    counts={'collapse_lt_0_1':len(flags['collapsed']),'stretch_gt_2':len(flags['stretched']),'self_intersecting_pairs':len(flags['intersections'])}
    if any(counts[k]!=metrics[k] for k in counts):raise ValueError('Triangle localization does not reproduce native metric counts')
    polygon_ids=native_polygons or list(range(len(F)))
    tri_hash=hashlib.sha256(json.dumps(F,separators=(',',':')).encode()).hexdigest()
    stem=f'{model}__{path}__sample{i:02d}'
    np.savez_compressed(out/(stem+'__geometry.npz'),rest_vertices=np.asarray(V0),posed_vertices=np.asarray(V),triangles=np.asarray(F,dtype=np.int32),source_polygon_ids=np.asarray(polygon_ids,dtype=np.int32),collapsed=np.asarray(flags['collapsed'],dtype=np.int32),stretched=np.asarray(flags['stretched'],dtype=np.int32),intersections=np.asarray(flags['intersections'],dtype=np.int32).reshape(-1,2),dominant_groups=np.asarray(dom))
    details={'sample_index':i,'t':i/(bench.FRAMES-1),'counts':counts,'metrics':metrics,'triangle_indices_sha256':tri_hash,'flags':flags,'geometry_file':stem+'__geometry.npz'}
    (out/(stem+'__triangles.json')).write_text(json.dumps(details,indent=1)+'\n')
    entry['frames'].append({k:v for k,v in details.items() if k!='flags'})
    snapshot_render(V,F,flags,out,stem)
   return metrics
  def track_pairs(ob,s):
   pairs=original_pairs(ob,s)
   entry['grip_trials'].append({'runtime_suffix':s,'thumb_01_euler_rad':list(rig.pose.bones['thumb_01_'+s].rotation_euler),'pairs':pairs,'hand_collapse':'NOT_RUN: pair guard short-circuits' if pairs>bench.THUMB_OPPOSITION['max_pairs'] else 'PENDING'})
   return pairs
  def track_collapse(ob,s):
   n=original_collapse(ob,s);entry['grip_trials'][-1]['hand_collapse']=n;return n
  bench.frame_metrics=capture;bench._thumb_finger_pairs=track_pairs;bench._hand_collapse=track_collapse
  try:
   outcome=bench.run(only=[path],post_pose=lambda r:drives.drive(r['runtime'],r['body']))
   rows=outcome['benchmarks'][path]['frames'];previous=prior['benchmarks'][path]['frames']
   entry['full_native_rows']=rows
   entry['reproduction_differences']=compare_rows(rows,previous)
   entry['all_nine_samples_reproduced']=len(rows)==len(previous)==9 and not entry['reproduction_differences']
   if not entry['all_nine_samples_reproduced']:raise ValueError('Native path differs from recorded baseline; review reproduction_differences')
  except Exception:
   entry['exception']=traceback.format_exc()
   if path!='grip':raise
   entry['grip_exception_expected']='no thumb placement within the pair limit' in entry['exception']
   if not entry['grip_exception_expected']:raise
   # Actual last rejected solver state, before any post_pose corrective update. NOT a passing grip pose.
   V,F=bench._evaluated(body);s=entry['grip_trials'][-1]['runtime_suffix']
   snapshot_render(V,F,{},out,model+'__grip__LAST_REJECTED_TRIAL_NO_POST_POSE',roi=rig.pose.bones['hand_'+s].head)
   entry['last_trial_render_scope']='actual last rejected solver state; not closest/best, not post_pose corrected, not benchmark completion'
  finally:
   bench.frame_metrics=original_metric;bench._thumb_finger_pairs=original_pairs;bench._hand_collapse=original_collapse
   after=static_signature(rig,body,adapter);entry['static_content_unchanged']=before==after
   if not entry['static_content_unchanged']:raise ValueError('In-memory source rest geometry/keys/weights/bones changed')
   if sha(source)!=digest or sha(copy)!=digest:raise ValueError('Source/copy bytes changed')
   report['source_and_copy_unchanged']=True
   (out/'diagnosis.json').write_text(json.dumps(report,indent=2)+'\n')
  print('VISUAL_PATH_RECORDED',model,path,flush=True)
 bench._evaluated=original_eval;correction.build_corrected_scene=original_build
 # Source blend remains read-only and is never uploaded again; reports/renders only.
 print('VISUAL_DIAGNOSIS_COMPLETE',model,flush=True)

if __name__=='__main__':main()
