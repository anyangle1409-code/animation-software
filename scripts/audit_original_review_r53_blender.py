"""R53 root-cause capture. In-memory ablations only; deliberately no save operation."""
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
from original_review_r53_diagnostics import family,muted_names,geometry_metrics,edge_weight_jumps,relative_rotation_degrees

source,solution,out,mode=sys.argv[-4:]
if mode not in ('r41','r52'):raise ValueError(mode)
out=Path(out)/mode;out.mkdir(parents=True,exist_ok=False)
model=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend'
model_hash=hashlib.sha256(model.read_bytes()).hexdigest()
assert model_hash=='4c44b1fe14aeefd9a976f45baada60b4b81aaaa7cd736a300ca7cede2b0aaf2e'
z=np.load(source);rest=z['rest'];faces=z['faces'];res=r17._setup(model)
body,rig=res['body'],res['runtime'];blocks=body.data.shape_keys.key_blocks

def digest(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def identity():
    return dict(runtime=[(b.name,b.parent.name if b.parent else None,[float(x) for row in b.matrix_local for x in row],tuple(b.head_local),tuple(b.tail_local)) for b in rig.data.bones],
        anatomy=[(b.name,[float(x) for row in b.matrix_local for x in row]) for b in res['anatomy'].data.bones],
        basis=digest(np.array([tuple(v.co) for v in blocks[0].data])),
        polygons=[list(p.vertices) for p in body.data.polygons],groups=[g.name for g in body.vertex_groups],
        weights=[[(g.group,g.weight) for g in v.groups] for v in body.data.vertices],
        protected_keys={k.name:digest(np.array([tuple(v.co) for v in k.data])) for k in blocks if not k.name.startswith('HGPT_S7_DELT_')})
before=identity()
if mode=='r52':install(res,np.load(solution)['dense_delta'])
groups=[g.name for g in body.vertex_groups];weights=np.zeros((len(rest),len(groups)),np.float32)
for v in body.data.vertices:
    for g in v.groups:weights[v.index,g.group]=g.weight
edges=np.array([tuple(e.vertices) for e in body.data.edges],dtype=int)
zone=(abs(rest[:,0])>.07)&(rest[:,2]>1.25)&(rest[:,2]<1.7)
back=(abs(rest[:,0])>.08)&(abs(rest[:,0])<.25)&(rest[:,2]>1.27)&(rest[:,2]<1.49)&(rest[:,1]>.025)
ids=np.flatnonzero(zone);back_ids=np.flatnonzero(back)
np.savez_compressed(out/'rest_weights.npz',rest=rest,faces=faces,edges=edges,weights=weights,shoulder_ids=ids,back_ids=back_ids)
names=[k.name for k in blocks];variants=['no_S'+str(i) for i in range(1,8)]+['all_shoulder_off']
key_geometry={k.name:np.array([tuple(v.co) for v in k.data],dtype=np.float32)[ids] for k in blocks}
np.savez_compressed(out/'key_geometry.npz',**key_geometry)
muted={v:muted_names(names,v) for v in variants}
bone_names=[b.name for b in rig.pose.bones]
parents={b.name:b.parent.name if b.parent else None for b in rig.pose.bones}
snap_frames={0,40,64,80,100,110,128,140,160}
baseline=[];back_motion=[];matrices=[];endpoints=[];activations=[];states=[];ablations={v:[] for v in variants};metrics=[];snap={}
scene=bpy.context.scene
for ob in scene.objects:
    if ob.type in ('MESH','CURVE') and ob is not body:ob.hide_render=True
material=bpy.data.materials.new('R53_DIAGNOSTIC_ONLY');material.diffuse_color=(.72,.55,.45,1)
body.data.materials.clear();body.data.materials.append(material)
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_cavity=True
scene.render.film_transparent=True;scene.render.resolution_x=scene.render.resolution_y=512;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
cd=bpy.data.cameras.new('R53_DIAGNOSTIC');cd.type='ORTHO';cd.ortho_scale=1.15
cam=bpy.data.objects.new('R53_DIAGNOSTIC',cd);scene.collection.objects.link(cam);scene.camera=cam
views=dict(front=(0,-1,.02),rear=(0,1,.02),side=(1,0,.02),three_quarter=(.7,.7,.05))
def render(frame,variant,view):
    d=Vector(views[view]).normalized();cam.location=Vector((0,0,1.45))+d*4
    cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y')
    bpy.context.view_layer.update();scene.render.filepath=str(out/f'{variant}_{frame:03d}_{view}.png');bpy.ops.render.render(write_still=True)
def evaluated():return np.array([tuple(v) for v in bench._evaluated(body)[0]],dtype=np.float32)
for frame in range(161):
    bench._reset(rig);states.append(px.pose_press_full(res,frame/160));drives.drive(rig,body);bpy.context.view_layer.update()
    values={k.name:float(k.value) for k in blocks};activations.append({n:v for n,v in values.items() if abs(v)>1e-10})
    p=evaluated();baseline.append(p[ids]);back_motion.append(p[back_ids])
    bm=np.array([np.array(rig.matrix_world@rig.pose.bones[n].matrix) for n in bone_names]);matrices.append(bm)
    endpoints.append(np.array([[tuple(rig.matrix_world@rig.pose.bones[n].head),tuple(rig.matrix_world@rig.pose.bones[n].tail)] for n in bone_names]))
    metrics.append(dict(frame=frame,baseline=geometry_metrics(rest,p,faces,edges,zone)))
    if frame in snap_frames:snap[f'baseline_{frame:03d}']=p
    # Exact evaluated full clip for each independent family removal; K1/HGPT_SHOULDER stay active.
    for variant in variants:
        for name in muted[variant]:blocks[name].value=0
        bpy.context.view_layer.update();q=evaluated();ablations[variant].append(q[ids]-p[ids])
        metrics[-1][variant]=geometry_metrics(rest,q,faces,edges,zone)
        if frame in snap_frames:snap[f'{variant}_{frame:03d}']=q
        if frame in (80,128) and variant in ('all_shoulder_off','no_S5','no_S7'):
            for view in ('rear','three_quarter'):render(frame,variant,view)
        for name in muted[variant]:blocks[name].value=values[name]
    bpy.context.view_layer.update()
    check=np.array([np.array(rig.matrix_world@rig.pose.bones[n].matrix) for n in bone_names])
    if not np.array_equal(check,bm):raise RuntimeError('Shape ablation changed bone pose')
    # 41 frames in four views, identical cameras in both processes.
    if frame%4==0:
        for view in views:render(frame,'baseline',view)
    if frame%20==0:print('R53_CAPTURE',mode,frame,flush=True)
after=identity();checks={k:before[k]==after[k] for k in before}
if not all(checks.values()):raise RuntimeError(('Protected identity changed',checks))
assert hashlib.sha256(model.read_bytes()).hexdigest()==model_hash
matrices=np.array(matrices);motion={}
for name in bone_names:
    if name.startswith(('clavicle_','scapula_','upperarm_')):
        parent='spine_03' if name.startswith(('clavicle_','scapula_')) else name.replace('upperarm_','scapula_')
        angles=relative_rotation_degrees(matrices[:,bone_names.index(name)],matrices[:,bone_names.index(parent)])
        motion[name]=dict(reference=parent,maximum_change_from_first_deg=float(angles.max()),samples_deg=angles.tolist(),note='Relative rotation magnitude, not clinical ISB decomposition')
jumps=edge_weight_jumps(weights,edges);order=np.argsort(jumps*np.any(zone[edges],axis=1))[-100:][::-1]
modifiers=[dict(name=m.name,type=m.type,show_viewport=m.show_viewport,show_render=m.show_render,**({k:getattr(m,k) for k in ('use_deform_preserve_volume','use_vertex_groups','use_bone_envelopes')} if m.type=='ARMATURE' else {})) for m in body.modifiers]
np.savez_compressed(out/'clip.npz',baseline=np.array(baseline),back_points=np.array(back_motion),bone_matrices=matrices,bone_endpoints=np.array(endpoints),**{v:np.array(a) for v,a in ablations.items()})
np.savez_compressed(out/'snapshots.npz',**snap)
(out/'diagnosis.json').write_text(json.dumps(dict(mode=mode,diagnostic_only=True,model_saved=False,repair_complete=False,approved=False,
    samples=161,protected_identity=checks,model_sha256=model_hash,group_names=groups,bone_names=bone_names,parents=parents,
    modifiers=modifiers,active_keys=activations,muted_names=muted,states=states,relative_bone_motion=motion,
    rest_extent_m=(rest.max(0)-rest.min(0)).tolist(),
    key_relative_to={k.name:k.relative_key.name for k in blocks},
    weight_sum_range=[float(weights.sum(1).min()),float(weights.sum(1).max())],
    highest_weight_jump_edges=[dict(edge=edges[i].tolist(),l1_jump=float(jumps[i])) for i in order],
    metrics=metrics,limitations=['Ablations expose dependencies; they are not repair candidates.','Ratios do not certify absence of intersections or folds.','No acceptance tests edited. Existing R52 failures remain unresolved.','No physical muscle volumes or validated scapula geometry inferred from skin weights.']),indent=2)+'\n')
print('R53_DIAGNOSTIC_COMPLETE',mode,checks,flush=True)
