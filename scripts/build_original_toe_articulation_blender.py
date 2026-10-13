"""Separate 95-control toe-articulation experiment, never production retarget."""
import bpy,sys,json,hashlib,math,heapq
from pathlib import Path
from mathutils import Vector,Matrix
INPUT_SHA='6ee29cec4dfd4b2de867f8dbcce4364203bc5f40182deeea72e60e01683438e2'
source=Path(bpy.data.filepath).resolve()
assert hashlib.sha256(source.read_bytes()).hexdigest()==INPUT_SHA
out=Path(sys.argv[sys.argv.index('--')+1]).resolve();out.mkdir(parents=True,exist_ok=True)
original_body=bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
original_rig=bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
anatomy=bpy.data.objects['HGPT_ANATOMICAL_MASTER']
def immutable():
    return {'mesh':[tuple(v.co) for v in original_body.data.vertices],
     'faces':[tuple(p.vertices) for p in original_body.data.polygons],
     'group_names':[g.name for g in original_body.vertex_groups],
     'weights':[[(g.group,g.weight) for g in v.groups] for v in original_body.data.vertices],
     'keys':{k.name:[tuple(v.co) for v in k.data] for k in original_body.data.shape_keys.key_blocks},
     'rigs':{r.name:{'world':[list(x) for x in r.matrix_world],
       'rest':{b.name:[list(x) for x in b.matrix_local] for b in r.data.bones},
       'stations':{b.name:[list(b.head_local),list(b.tail_local),b.length,
         None if b.parent is None else b.parent.name] for b in r.data.bones}}
       for r in (original_rig,anatomy)}}
frozen=immutable()
rig=original_rig.copy();rig.data=original_rig.data.copy();rig.name='HGPT_TOE_SEGMENT_RUNTIME_TRIAL'
bpy.context.scene.collection.objects.link(rig)
body=original_body.copy();body.data=original_body.data.copy();body.name='HGPT_BODY_TOE_SEGMENT_TRIAL'
bpy.context.scene.collection.objects.link(body)
world=body.matrix_world.copy();body.parent=rig;body.matrix_world=world
for m in body.modifiers:
    if m.type=='ARMATURE' and m.object is original_rig:m.object=rig
for k in body.data.shape_keys.key_blocks:
    if k.name!='Basis':k.value=0
for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
def points():
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return [ev.matrix_world@v.co for v in ev.data.vertices]
rest_before=points()
chains={}
for side,suffix in [('left','r'),('right','l')]:
    for digit in range(1,6):
        names=([f'anat_hallux_{part}_phalanx_{side}' for part in ('proximal','distal')]
          if digit==1 else [f'anat_toe{digit}_{part}_phalanx_{side}' for part in ('proximal','middle','distal')])
        chains[(side,digit)]={'suffix':suffix,'references':names,
          'world':[{'head':anatomy.matrix_world@anatomy.data.bones[n].head_local,
                    'tail':anatomy.matrix_world@anatomy.data.bones[n].tail_local} for n in names],
          'controls':[f'trial_toe{digit}_{j+1:02}_{suffix}' for j in range(len(names))]}
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for (side,digit),chain in chains.items():
    previous=rig.data.edit_bones['foot_'+chain['suffix']]
    for name,ref,station in zip(chain['controls'],chain['references'],chain['world']):
        bone=rig.data.edit_bones.new(name)
        bone.head=rig.matrix_world.inverted()@station['head']
        bone.tail=rig.matrix_world.inverted()@station['tail']
        bone.parent=previous;bone.use_connect=False
        bone.align_roll(Vector((0,0,1)))
        previous=bone
bpy.ops.object.mode_set(mode='OBJECT')
for chain in chains.values():
    for name,ref in zip(chain['controls'],chain['references']):
        rig.data.bones[name]['source_anatomical_bone']=ref
        body.vertex_groups.new(name=name)
assert len(rig.data.bones)==95
# Distal toes are five separate connected skin components beyond the authored
# web. Anatomical nearest-ray partition can split one actual toe across rays.
adjacency={v.index:[] for v in body.data.vertices}
for edge in body.data.edges:
    i,j=edge.vertices;adjacency[i].append(j);adjacency[j].append(i)
digit_labels={}
component_sizes={}
for side,sign in [('left',1),('right',-1)]:
    allowed={i for i,p in enumerate(rest_before) if p.x*sign>0 and p.z<.16 and -p.y>.17}
    distal={i for i in allowed if -rest_before[i].y>.220 and rest_before[i].z<.05}
    components=[];unseen=set(distal)
    while unseen:
        seed=min(unseen);stack=[seed];unseen.remove(seed);component=[]
        while stack:
            i=stack.pop();component.append(i)
            for j in adjacency[i]:
                if j in unseen:unseen.remove(j);stack.append(j)
        components.append(component)
    assert len(components)==5,(side,[len(c) for c in components])
    components.sort(key=lambda c:sum(abs(rest_before[i].x) for i in c)/len(c))
    component_sizes[side]=[len(c) for c in components]
    queue=[];best={}
    for digit,component in enumerate(components,1):
        for i in component:
            best[i]=(0.,digit);heapq.heappush(queue,(0.,digit,i))
    while queue:
        distance,digit,i=heapq.heappop(queue)
        if best[i]!=(distance,digit):continue
        for j in adjacency[i]:
            if j not in allowed:continue
            proposal=(distance+(rest_before[i]-rest_before[j]).length,digit)
            if j not in best or proposal<best[j]:
                best[j]=proposal;heapq.heappush(queue,(*proposal,j))
    for i,(_,digit) in best.items():digit_labels[(side,i)]=digit
changes=[]
for v in body.data.vertices:
    weights={body.vertex_groups[g.group].name:g.weight for g in v.groups}
    p=body.matrix_world@v.co
    for side,suffix in [('left','r'),('right','l')]:
        shared='toe_'+suffix;amount=weights.get(shared,0)
        if amount<=0:continue
        def distance(digit):
            chain=chains[(side,digit)];h=chain['world'][0]['head'];t=chain['world'][-1]['tail']
            u=max(0,min(1,(-p.y+h.y)/(-t.y+h.y)))
            return abs(p.x-(h.x+(t.x-h.x)*u))
        digit=digit_labels.get((side,v.index),min(range(1,6),key=distance));chain=chains[(side,digit)]
        stations=[-s['head'].y for s in chain['world']]
        f=-p.y
        root_blend=max(0,min(1,(f-stations[0])/.040))
        root_blend=root_blend*root_blend*(3-2*root_blend)
        fractions=[0.]*len(stations);fractions[0]=1.
        for j in range(1,len(stations)):
            t=max(0,min(1,(f-stations[j]+.004)/.008));t=t*t*(3-2*t)
            for k in range(j):fractions[k]*=1-t
            fractions[j]=t
        body.vertex_groups[shared].remove([v.index])
        foot=body.vertex_groups['foot_'+suffix]
        foot.add([v.index],weights.get('foot_'+suffix,0)+amount*(1-root_blend),'REPLACE')
        for name,fraction in zip(chain['controls'],fractions):
            if fraction*root_blend>0:body.vertex_groups[name].add([v.index],amount*fraction*root_blend,'REPLACE')
        changes.append({'vertex':v.index,'side':side,'digit':digit,'source_amount':amount})
bpy.context.view_layer.update();rest=points()
rest_error=max((p-q).length for p,q in zip(rest_before,rest))
assert rest_error<2e-6,rest_error
assert immutable()==frozen
body['review_only']=True;body['rig_schema']='95_CONTROL_TOE_TRIAL; incompatible with approved67joint claim'
rig['owner_accepted']=False;rig['anatomically_validated']=False
original_body.hide_render=True;original_body.hide_set(True)
original_rig.hide_render=True;original_rig.hide_set(True)
body.hide_render=False;body.hide_set(False);rig.hide_set(False)
candidate=out/'HomeGymPT_ORIGINAL_v1_INDIVIDUAL_TOE_TRIAL.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(candidate))
# Actual posed surface extraction; all candidate mesh positions come from the
# full-body skin evaluated on its separate95-control rig.
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=1800;scene.render.resolution_y=1200
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE'
scene.display.shading.single_color=(.65,.69,.73);scene.display.shading.show_cavity=True
scene.display.shading.background_type='WORLD'
if scene.world is None:scene.world=bpy.data.worlds.new('TOE_TRIAL_WORLD')
scene.world.color=(.045,.055,.075)
for o in scene.objects:o.hide_render=True
cd=bpy.data.cameras.new('INDIVIDUAL_TOE_CAMERA');cd.type='ORTHO';cd.ortho_scale=.42
cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam
faces=[tuple(p.vertices) for p in body.data.polygons]
render_records=[]
def render(tag):
    pts=points();ids={i for i,p in enumerate(rest) if p.x>0 and p.z<.16}
    selected=[f for f in faces if all(i in ids for i in f)]
    indices=sorted({i for face in selected for i in face});mapping={i:j for j,i in enumerate(indices)}
    mesh=bpy.data.meshes.new('DISPLAY_ONLY_'+tag)
    mesh.from_pydata([pts[i] for i in indices],[],[tuple(mapping[i] for i in f) for f in selected])
    ob=bpy.data.objects.new(mesh.name,mesh);scene.collection.objects.link(ob)
    for p in mesh.polygons:p.use_smooth=True
    target=Vector((.095,-.115,.053))
    for view,off in [('side',Vector((3,0,0))),('three_quarter',Vector((3,-3,1.4)))]:
        cam.location=target+off;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(out/(tag+'_'+view+'.png'))
        bpy.ops.render.render(write_still=True)
        render_records.append({'file':tag+'_'+view+'.png','pose':tag,'view':view,'surface_extract_below_m':.16})
    ob.hide_render=True
render('neutral')
for control,tag in [('trial_toe1_01_r','hallux_MTP_only_15deg'),('trial_toe2_02_r','digit2_PIP_only_15deg')]:
    for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
    rig.pose.bones[control].matrix_basis=Matrix.Rotation(math.radians(15),4,'X')
    bpy.context.view_layer.update();render(tag)
for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
assert immutable()==frozen
assert hashlib.sha256(source.read_bytes()).hexdigest()==INPUT_SHA
report={'input_commit':'16d8d50713326e08068d666d82be9eb7c451aa80','input_candidate_sha256':INPUT_SHA,
 'source_original_sha256':'670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56',
 'candidate_file':candidate.name,'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
 'trial_runtime_joint_count':95,'original_runtime_joint_count':67,'new_digit_segments':28,
 'original_body_and_both_original_skeletons_unchanged':True,'trial_geometry_unchanged_from_input':True,
 'redistributed_vertices':len(changes),'neutral_rest_max_vertex_difference_m':rest_error,
 'distal_mesh_component_sizes':component_sizes,'digit_assignment':'five actual distal connected skin components; geodesic propagation into roots',
 'control_source_map':{name:ref for ch in chains.values() for name,ref in zip(ch['controls'],ch['references'])},
 'artist_weight_blend_width_m':.008,'artist_MTP_root_blend_m':.040,'bone_axis_roll_reference':'world +Z; provisional, not functional-axis authority',
 'render_records':render_records,'owner_accepted':False,'anatomical_approval':False,'production_approved':False,
 'limits':['95control trial is NOT the67joint app/GLB schema.',
 'Source toe endpoints remain low-confidence surface-derived reference stations.',
 'Digit assignment uses actual distal connected skin components and geodesic labels; nearest-ray fallback for unlabelled proximal vertices.8mm IP and40mm MTP-root blends are artist trial constraints, not validated muscle/skin mechanics.',
 '15deg samples are implementation probes, not physiological ROM, load, gait or PIP-DIP coupling.',
 'Foot shape and length remain rejected; no28cm shrink or skeleton relocation.']}
report['png_sha256']={r['file']:hashlib.sha256((out/r['file']).read_bytes()).hexdigest() for r in render_records}
(out/'individual_toe_trial.json').write_text(json.dumps(report,indent=2)+'\n')
print('INDIVIDUAL_TOE_TRIAL',len(changes),'vertices redistributed; rest error',rest_error)
