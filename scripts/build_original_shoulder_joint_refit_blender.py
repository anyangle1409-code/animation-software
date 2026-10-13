"""Separate actual-body source-joint bind trial; inherited skin is unrefitted."""
import bpy,json,sys,hashlib,math
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import original_shoulder_joint_authority as authority
import build_functional_absolute_reach_blender as reach
SOURCE_HASH='ca8e6824ae54e5778a04409e00d32ae13ac23d9fce95e1f6d8207abbef265ca7'
source=Path(bpy.data.filepath);assert hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_HASH
out=Path(sys.argv[sys.argv.index('--')+1]).resolve();out.mkdir(parents=True,exist_ok=True)
record=json.loads((ROOT/authority.RECORD).read_text());joints=authority.extract(record)['joints']
original=bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE'];old=bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
anatomy=bpy.data.objects['HGPT_ANATOMICAL_MASTER']
def original_fingerprint():
    r={'vertices':[list(v.co) for v in original.data.vertices],
       'weights':[[[g.group,g.weight] for g in v.groups] for v in original.data.vertices],
       'shapes':{k.name:[list(p.co) for p in k.data] for k in original.data.shape_keys.key_blocks},
       'rigs':{a.name:{'world':[list(row) for row in a.matrix_world],
           'bones':{b.name:{'matrix':[list(row) for row in b.matrix_local],'parent':b.parent.name if b.parent else None} for b in a.data.bones},
           'poses':{p.name:[list(row) for row in p.matrix_basis] for p in a.pose.bones}} for a in (old,anatomy)}}
    return hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()
fingerprint=original_fingerprint()
guide=next(o for o in bpy.data.objects if o.type=='ARMATURE' and len(o.data.bones)==6 and 'scapula_left' in o.data.bones)
rig=old.copy();rig.data=old.data.copy();rig.name='HGPT_SHOULDER_JOINT_REFIT_TRIAL';bpy.context.scene.collection.objects.link(rig)
body=original.copy();body.data=original.data.copy();body.name='HGPT_BODY_SHOULDER_REFIT_TRIAL';bpy.context.scene.collection.objects.link(body)
for modifier in body.modifiers:
    if modifier.type=='ARMATURE':modifier.object=rig
body.parent=rig
for p in rig.pose.bones:
    assert len(p.constraints)==0,'Constraint transfer requires explicit review'
    p.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
mapping={}
for side,suffix in [('left','r'),('right','l')]:
    for joint,part,rt in [('SC','clavicle','clavicle'),('AC','scapula','scapula'),('GH','humerus','upperarm')]:
        name=rt+'_'+suffix;bone=rig.data.edit_bones[name]
        centre=Vector([joints[joint+'_'+side]['world_frame_row_major'][r][3] for r in range(3)])
        bone.use_connect=False;bone.head=rig.matrix_world.inverted()@centre
        if joint=='SC':bone.tail=rig.matrix_world.inverted()@Vector(record['bones']['clavicle_'+side]['tail_m'])
        if joint=='AC':bone.tail=rig.matrix_world.inverted()@Vector(record['bones']['humerus_'+side]['head_m'])
        # Upper-arm tail keeps the inherited elbow. New elbow fit is separate.
        mapping[part+'_'+side]=name
bpy.ops.object.mode_set(mode='OBJECT')
rest={name:rig.matrix_world@rig.data.bones[name].matrix_local for name in mapping.values()}
guide_rest={name:guide.matrix_world@guide.data.bones[name].matrix_local for name in mapping}
def evaluated():
    bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return [ev.matrix_world@v.co for v in ev.data.vertices]
neutral=evaluated();baseline=[original.matrix_world@v.co for v in original.data.vertices]
rest_error=max((a-b).length for a,b in zip(neutral,baseline));assert rest_error<2e-6
triangles=[]
body.data.calc_loop_triangles()
for t in body.data.loop_triangles:triangles.append(tuple(t.vertices))
def measures(points):
    flips=0;ratios=[]
    for a,b,c in triangles:
        ref=(neutral[b]-neutral[a]).cross(neutral[c]-neutral[a])
        now=(points[b]-points[a]).cross(points[c]-points[a])
        if ref.length>1e-12:
            ratios.append(now.length/ref.length)
            if ref.dot(now)<0:flips+=1
    return {'world_normal_dot_reversals':flips,'minimum_triangle_area_ratio':min(ratios),
            'maximum_triangle_area_ratio':max(ratios),'finite':all(math.isfinite(x) for p in points for x in p)}
scene=bpy.context.scene
for obj in scene.objects:obj.hide_render=True
body.hide_render=False;body.hide_set(False);rig.hide_set(False);guide.hide_set(False)
scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1200;scene.render.resolution_y=1800;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE'
scene.display.shading.single_color=(.65,.68,.70);scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
scene.display.shading.background_type='WORLD'
if scene.world is None:scene.world=bpy.data.worlds.new('SHOULDER_TRIAL_BACKGROUND')
scene.world.color=(.055,.065,.08)
camera_data=bpy.data.cameras.new('SHOULDER_REFIT_REVIEW_CAMERA');camera_data.type='ORTHO';camera_data.ortho_scale=2.65
camera=bpy.data.objects.new(camera_data.name,camera_data);scene.collection.objects.link(camera);scene.camera=camera
samples=[];images=[]
for angle in (None,0,45,90,135,160,135,90,45,0,None):
    if angle is None:
        for a in (rig,guide):
            for p in a.pose.bones:p.matrix_basis=Matrix.Identity(4)
    else:
        reach.pose_absolute(guide,record,angle)
        for name,target in mapping.items():
            # Parent-first source world motion applied to a distinct target rest.
            rig.pose.bones[target].matrix=rig.matrix_world.inverted()@(guide.matrix_world@guide.pose.bones[name].matrix)@guide_rest[name].inverted()@rest[target]
            bpy.context.view_layer.update()
    pts=evaluated();samples.append({'stage':'REST' if angle is None else angle,**measures(pts)})
    tag='neutral' if angle is None else f'reach_{angle:03d}'
    if tag in ('neutral','reach_090','reach_160') and not any(i['pose']==tag for i in images):
        target=Vector((0,0,1.05))
        for view,offset in [('front',Vector((0,-5,0))),('three_quarter',Vector((3,-5,.25)))]:
            camera.location=target+offset;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
            file=tag+'_'+view+'.png';scene.render.filepath=str(out/file);bpy.ops.render.render(write_still=True)
            images.append({'file':file,'pose':tag,'view':view,'sha256':hashlib.sha256((out/file).read_bytes()).hexdigest()})
assert max((a-b).length for a,b in zip(evaluated(),neutral))<2e-6
assert original_fingerprint()==fingerprint
assert hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_HASH
candidate=out/'HomeGymPT_ORIGINAL_v1_SHOULDER_JOINT_REFIT_TRIAL.blend'
rig['review_only']=True;rig['anatomical_approval']=False;body['review_only']=True
bpy.ops.wm.save_as_mainfile(filepath=str(candidate))
report={'input_commit':'8e050c2dc9798030df584f9a71644945568c3a48',
    'authored_context_commit':'27e2dbf4424b878d8312cf346624e495720bba0a',
    'input_model_sha256':SOURCE_HASH,'original_model_sha256':'670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56',
    'source_record_sha256':hashlib.sha256((ROOT/authority.RECORD).read_bytes()).hexdigest(),
    'candidate_filename':candidate.name,'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
    'body_vertices':len(body.data.vertices),'runtime_count':len(rig.data.bones),'joint_control_map':mapping,
    'neutral_max_difference_m':rest_error,'original_fingerprint_before':fingerprint,'original_fingerprint_after':original_fingerprint(),
    'source_file_unchanged':True,'samples':samples,'images':images,
    'limitations':['Six copied runtime heads now use provisional c004 SC/AC/GH centres; source206 and original67 unchanged.',
    'Inherited weights/skin/correctives are NOT refitted. Upper-arm tails retain old elbow stations; roll inherited, not approved anatomical axes.',
    'World normal dot sign change includes legitimate rigid turning and is not proof of inversion. Area ratios are distortion diagnostics, not physiological pass.',
    '11 stages use inherited artist-authored coupling and shortest-arc humeral directions, not validated ROM, muscle mechanics or loaded exercise.',
    'Original rejected foot geometry remains visible; foot trials are separate.'],
    'anatomical_approval':False,'deformation_accepted':False,'motion_accepted':False,'production_approved':False}
(out/'shoulder_joint_refit_trial.json').write_text(json.dumps(report,indent=2)+'\n')
print('SHOULDER_REFIT_TRIAL',rest_error,report['candidate_sha256'],samples)
