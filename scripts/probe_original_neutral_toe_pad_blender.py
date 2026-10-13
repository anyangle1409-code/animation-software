"""Actual original mesh trial: downward plantar expansion, review only.

Run on pinned r95/a003. Saves a separate candidate; never saves over input.
Rendering uses a disclosed left-foot surface extract for unobstructed views.
"""
import bpy, sys, json, hashlib, math
from pathlib import Path
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).parent))
from original_neutral_toe_pad_trial import expand_plantar

SOURCE_SHA='670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56'
source=Path(bpy.data.filepath)
assert hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_SHA
out=Path(sys.argv[sys.argv.index('--')+1]).resolve()
out.mkdir(parents=True,exist_ok=True)
body=bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
rig=bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
anatomy=bpy.data.objects['HGPT_ANATOMICAL_MASTER']
def rigs():
    return {r.name:{'world':[list(v) for v in r.matrix_world],
      'rest':{b.name:[list(v) for v in b.matrix_local] for b in r.data.bones}}
      for r in (rig,anatomy)}
before_rigs=rigs()
weights=[[(g.group,g.weight) for g in v.groups] for v in body.data.vertices]
original_pose={p.name:p.matrix_basis.copy() for p in rig.pose.bones}
keys=body.data.shape_keys.key_blocks
original_key_values={k.name:k.value for k in keys}
for k in keys:
    if k.name!='Basis':k.value=0
for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
original=[v.co.copy() for v in body.data.vertices]
world=[body.matrix_world@p for p in original]
faces=[tuple(p.vertices) for p in body.data.polygons]
tree=BVHTree.FromPolygons(world,faces)
def stats(points):
    result={}
    for side,sign in [('left',1),('right',-1)]:
        foot=[p for p in points if p.z<.16 and p.x*sign>0]
        distal=[p for p in foot if -p.y>.245]
        result[side]={'length_mm':1000*(max(p.y for p in foot)-min(p.y for p in foot)),
         'width_mm':1000*(max(p.x for p in foot)-min(p.x for p in foot)),
         'distal_min_z_mm':1000*min(p.z for p in distal),
         'min_z_mm':1000*min(p.z for p in foot)}
    return result
before=stats(world)
toe_centres=[]
for b in anatomy.data.bones:
    if b.name.endswith('_left') and ('distal_phalanx' in b.name) and any(s in b.name for s in ('hallux_','toe2_','toe3_','toe4_','toe5_')):
        toe_centres.append(anatomy.matrix_world@b.tail_local)
toe_centres.sort(key=lambda p:p.x)
assert len(toe_centres)==5
delta={}
missed=0
for i,p in enumerate(world):
    f=-p.y
    if p.z>=.022 or p.z<0 or f<=.185 or p.z>=.16:continue
    hit=tree.ray_cast(Vector((p.x,p.y,-.002)),Vector((0,0,1)),.2)[0]
    if hit is None or hit.z>=.0215 or hit.z<0:
        missed+=1
        continue
    blend=min(1,max(0,(f-.185)/.025))
    blend=blend*blend*(3-2*blend)
    # Narrow contact pads rather than flattening the entire underside. Widths
    # and rounded-tip taper are explicitly artist trial constraints.
    nearest=min(range(5),key=lambda j:abs(abs(p.x)-toe_centres[j].x))
    centre=toe_centres[nearest]
    half_width=[.011,.008,.0075,.007,.006][nearest]
    radius=max(0,(abs(abs(p.x)-centre.x)-.0015)/(half_width-.0015))
    lateral=max(0,1-radius*radius)**2
    tip_taper=min(1,max(0,(-centre.y+.001-f)/.004))
    blend*=lateral*tip_taper
    z=expand_plantar(float(p.z),float(hit.z),blend=blend)
    z=max(0,min(p.z,z))
    if p.z-z>1e-8:delta[i]=body.matrix_world.inverted().to_3x3()@Vector((0,0,z-p.z))
# Same per-vertex delta on Basis and every inherited corrective preserves all
# existing relative corrective deltas, but does not validate posed corrections.
for k in keys:
    for i,d in delta.items():k.data[i].co+=d
for i,d in delta.items():body.data.vertices[i].co+=d
bpy.context.view_layer.update()
after_world=[body.matrix_world@v.co for v in body.data.vertices]
after=stats(after_world)
assert rigs()==before_rigs
assert weights==[[(g.group,g.weight) for g in v.groups] for v in body.data.vertices]
assert all(abs(p.x-q.x)<1e-8 and abs(p.y-q.y)<1e-8 for p,q in zip(world,after_world))
assert all(q.z<=p.z+1e-8 for p,q in zip(world,after_world))
assert len(body.data.vertices)==17946
assert before['left']['length_mm']==after['left']['length_mm']
assert before['right']['length_mm']==after['right']['length_mm']
# Check source toe stations against vertical skin intersections. This is a
# geometric ray bracket only; reference points are not verified bone surfaces.
def bracket(points):
    t=BVHTree.FromPolygons(points,faces)
    result=[]
    for b in anatomy.data.bones:
        if not any(s in b.name for s in ('hallux_','toe2_','toe3_','toe4_','toe5_')):continue
        for endpoint,p in [('head',anatomy.matrix_world@b.head_local),('tail',anatomy.matrix_world@b.tail_local)]:
            low=t.ray_cast(Vector((p.x,p.y,-.002)),Vector((0,0,1)),.2)[0]
            high=t.ray_cast(Vector((p.x,p.y,.15)),Vector((0,0,-1)),.2)[0]
            inside=bool(low and high and low.z-1e-6<=p.z<=high.z+1e-6)
            result.append({'bone':b.name,'endpoint':endpoint,'station_m':list(p),
             'vertical_skin_bracket':inside,'plantar_m':None if low is None else low.z,
             'dorsal_m':None if high is None else high.z})
    return result
brackets_before,brackets_after=bracket(world),bracket(after_world)
assert all(not a['vertical_skin_bracket'] or b['vertical_skin_bracket']
           for a,b in zip(brackets_before,brackets_after))
scene=bpy.context.scene
scene['hgpt_review_scope']='NEUTRAL_PLANTAR_PAD_TRIAL; NOT shape/length/anatomy accepted'
scene['hgpt_production_approved']=False
candidate=out/'HomeGymPT_ORIGINAL_v1_NEUTRAL_TOE_PAD_TRIAL.blend'
for p in rig.pose.bones:p.matrix_basis=original_pose[p.name]
for k in keys:k.value=original_key_values[k.name]
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(candidate))
# Render actual source/candidate left-foot surfaces, with explicit surface crop.
scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=1800;scene.render.resolution_y=1200
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.display.shading.light='STUDIO'
scene.display.shading.color_type='SINGLE'
scene.display.shading.single_color=(.65,.69,.73)
scene.display.shading.show_cavity=True
scene.display.shading.background_type='WORLD'
if scene.world is None:scene.world=bpy.data.worlds.new('PAD_TRIAL_WORLD')
scene.world.color=(.045,.055,.075)
for o in scene.objects:o.hide_render=True
cd=bpy.data.cameras.new('PAD_TRIAL_CAMERA');cd.type='ORTHO';cd.ortho_scale=.42
cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam
cam.hide_render=False
render_records=[]
for tag,points in [('before',world),('after',after_world)]:
    ids={i for i,p in enumerate(points) if p.x>0 and p.z<.16}
    used=[f for f in faces if all(i in ids for i in f)]
    indices=sorted({i for f in used for i in f});mapping={i:j for j,i in enumerate(indices)}
    mesh=bpy.data.meshes.new('DISPLAY_ONLY_LEFT_FOOT_'+tag)
    mesh.from_pydata([points[i] for i in indices],[],[tuple(mapping[i] for i in f) for f in used])
    ob=bpy.data.objects.new(mesh.name,mesh);scene.collection.objects.link(ob)
    for p in mesh.polygons:p.use_smooth=True
    target=Vector((.095,-.115,.053))
    for view,off in [('side',Vector((3,0,0))),('three_quarter',Vector((3,-3,1.4))),('top',Vector((0,0,3)))]:
        cam.location=target+off
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
        cd.clip_start=.01
        scene.render.filepath=str(out/(tag+'_'+view+'.png'))
        bpy.ops.render.render(write_still=True)
        render_records.append({'file':tag+'_'+view+'.png','view':view,'scale_m':cd.ortho_scale,
          'surface_extract_only':True,'crop_z_m':.16,'anatomical_side':'left'})
    ob.hide_render=True
report={'source_branch':'codex/original-foot-proportions-candidate-20261012',
 'source_commit':'27e2dbf4424b878d8312cf346624e495720bba0a','source_filename':source.name,
 'source_sha256':SOURCE_SHA,'blender_version':bpy.app.version_string,
 'before':before,'after':after,'changed_vertices':len(delta),
 'maximum_downward_change_mm':1000*max(-d.z for d in delta.values()),'ray_misses':missed,
 'mesh_xy_weights_both_skeletons_unchanged':True,'inherited_relative_corrective_deltas_preserved':True,
 'source_toe_station_brackets_before':brackets_before,'source_toe_station_brackets_after':brackets_after,
 'candidate_file':candidate.name,'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
 'render_records':render_records,'production_approved':False,'owner_accepted':False,
 'limits':['22mm dorsal anchor and 25mm transition are artist trial constraints, not approved anatomy.',
 'No foot shortening or tubular silhouette/root topology rebuild.',
 'Toe endpoints are low-confidence surface-derived reference stations, not verified bone volumes.',
 'Render surface is a left-foot extract below160mm for visibility; full candidate body remains intact.',
 'Motion/contact under load and face inversion still require verification; trial must not be promoted.']}
report['png_sha256']={r['file']:hashlib.sha256((out/r['file']).read_bytes()).hexdigest() for r in render_records}
(out/'neutral_toe_pad_trial.json').write_text(json.dumps(report,indent=2)+'\n')
assert hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_SHA
print('PAD_TRIAL_RESULT',json.dumps({'before':before,'after':after,'changed':len(delta)}))
