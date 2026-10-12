"""Read-only native foot proportions, candidate gate and movement diagnostics.

No original geometry/weights/bone coordinates saved or edited. Motion runs in a
separate copied scene. A 28cm trial is refused if source reference containment
or anatomical station semantics are unresolved.
"""
import bpy,sys,json,math,hashlib,csv,statistics,re
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import original_foot_candidate_gate as gate
SOURCE_SHA='670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56'
src=Path(bpy.data.filepath).resolve()
assert hashlib.sha256(src.read_bytes()).hexdigest()==SOURCE_SHA
args=sys.argv[sys.argv.index('--')+1:];out=Path(args[0]).resolve();out.mkdir(parents=True,exist_ok=True)
original_scene=bpy.context.scene
body=bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
rig=bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
anatomy=bpy.data.objects['HGPT_ANATOMICAL_MASTER']
def rows(m):return [list(r) for r in m]
def fingerprint():
 return hashlib.sha256(json.dumps({'v':[list(v.co) for v in body.data.vertices],
  'w':[[[g.group,g.weight] for g in v.groups] for v in body.data.vertices],
  'sk':{a.name:{'world':rows(a.matrix_world),'rest':{b.name:rows(b.matrix_local) for b in a.data.bones},'pose':{p.name:rows(p.matrix_basis) for p in a.pose.bones}} for a in (rig,anatomy)}},sort_keys=True).encode()).hexdigest()
before=fingerprint()
pat=re.compile(r'^anat_(talus|calcaneus|navicular|cuboid|.*cuneiform|metatarsal_[1-5]|hallux_.*phalanx|toe[2-5]_.*phalanx)_(left|right)$')
bones={b.name:{'head_m':list(anatomy.matrix_world@b.head_local),'tail_m':list(anatomy.matrix_world@b.tail_local)} for b in anatomy.data.bones if pat.match(b.name)}
assert len(bones)==52,len(bones)
fit=json.loads((ROOT/'ORIGINAL_V1_WORK/anatomy/character_fit_r95_a003.json').read_text())
for name,b in bones.items():
 b['source_semantics']=fit['bones'][name.removeprefix('anat_')]
native=[body.matrix_world@v.co for v in body.data.vertices]
feet={}
for side,sign,suffix in [('left',1,'r'),('right',-1,'l')]:
 ids=[v.index for v in body.data.vertices if v.co.z<.16 and v.co.x*sign>0]
 pts=[native[i] for i in ids]
 heel=max(p.y for p in pts);tip=min(p.y for p in pts)
 refs=[p for name,b in bones.items() if name.endswith('_'+side) for p in (b['head_m'],b['tail_m'])]
 lengths=gate.assess(heel,[-p[1] for p in refs],.280,False)
 toe=rig.data.bones['toe_'+suffix]
 toe_h=rig.matrix_world@toe.head_local;toe_t=rig.matrix_world@toe.tail_local
 station_confidence={name:b['source_semantics']['confidence'] for name,b in bones.items() if name.endswith('_'+side)}
 feet[side]={'runtime_suffix':suffix,'mesh_length_m':heel-tip,'heel_backward_m':heel,
  'toe_tip_forward_m':-tip,'mesh_width_m':max(p.x for p in pts)-min(p.x for p in pts),
  'mesh_z_min_m':min(p.z for p in pts),'mesh_z_max_m':max(p.z for p in pts),
  'candidate_gate':lengths,'foot_vertex_count':len(ids),'runtime_toe_head_world':list(toe_h),
  'runtime_toe_tail_world':list(toe_t),'runtime_toe_tail_beyond_mesh_m':max(0,-toe_t.y+tip),
  'source_reference_confidence':station_confidence,
  'toe_reference_points_beyond_28cm_boundary':[name for name,b in bones.items() if name.endswith('_'+side) and -b['tail_m'][1]>lengths['target_forward_station_m']]}
# Weights on actual original vertices; unchanged by this read-only audit.
sums=[sum(g.weight for g in v.groups) for v in body.data.vertices]
weights={'vertex_count':len(sums),'max_sum_error':max(abs(s-1) for s in sums),
 'minimum_weight':min(g.weight for v in body.data.vertices for g in v.groups),
 'all_finite':all(math.isfinite(g.weight) for v in body.data.vertices for g in v.groups)}
# A private copied scene prevents transient motion from changing original state.
probe=bpy.data.scenes.new('FOOT_MOTION_READ_ONLY_COPY')
rt=rig.copy();rt.data=rig.data.copy();probe.collection.objects.link(rt)
copy=body.copy();probe.collection.objects.link(copy)
world=body.matrix_world.copy();copy.parent=rt if body.parent is rig else body.parent;copy.matrix_world=world
for m in copy.modifiers:
 if m.type=='ARMATURE' and m.object is rig:m.object=rt
bpy.context.window.scene=probe
def reset():
 for p in rt.pose.bones:p.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update()
def vertices():
 ev=copy.evaluated_get(bpy.context.evaluated_depsgraph_get())
 return [ev.matrix_world@v.co for v in ev.data.vertices]
reset();rest=vertices()
motion=[]
for side,sign,suffix in [('left',1,'r'),('right',-1,'l')]:
 ids=[i for i,p in enumerate(rest) if p.z<.16 and p.x*sign>0]
 heel_ids=[i for i in ids if rest[i].y>.005 and rest[i].z<.025]
 for control,angles in [('toe',(-30,-15,0,15,30)),('foot',(-20,-10,0,10,20))]:
  previous=None
  for angle in angles:
   reset();p=rt.pose.bones[control+'_'+suffix];pivot=p.head.copy()
   p.matrix=Matrix.Translation(pivot)@Matrix.Rotation(math.radians(angle),4,'X')@Matrix.Translation(-pivot)@p.matrix
   bpy.context.view_layer.update();points=vertices()
   delta=max((points[i]-rest[i]).length for i in ids)
   step=max((points[i]-previous[i]).length for i in ids) if previous else None
   motion.append({'anatomical_side':side,'control':control,'world_sagittal_angle_deg':angle,
    'diagnostic_context':'unloaded control sweep; no planted-stance/contact solver',
    'foot_floor_min_z_m':min(points[i].z for i in ids),
    'heel_min_z_m':min(points[i].z for i in heel_ids),
    'foot_vertex_peak_displacement_m':delta,'step_displacement_m':step,
    'all_vertices_finite':all(math.isfinite(x) for v in points for x in v)})
   previous=points
reset();returned=vertices();return_error=max((p-q).length for p,q in zip(rest,returned))
# Causality experiment: display-control length alone, fixed origin/direction/roll.
rt.pose.bones['toe_r'].matrix_basis=Matrix.Rotation(.4,4,'X');bpy.context.view_layer.update()
long_tail_pose=vertices()
bpy.context.view_layer.objects.active=rt;rt.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
edit=rt.data.edit_bones['toe_r'];edit.tail=edit.head+(edit.tail-edit.head)*.5
bpy.ops.object.mode_set(mode='OBJECT');bpy.context.view_layer.update()
short_tail_pose=vertices()
tail_effect=max((p-q).length for p,q in zip(long_tail_pose,short_tail_pose))
bpy.context.window.scene=original_scene
assert fingerprint()==before and hashlib.sha256(src.read_bytes()).hexdigest()==SOURCE_SHA
ansur={}
if len(args)>1:
 data=Path(args[1]);records=list(csv.DictReader(data.open(encoding='latin1',newline='')))
 pairs=[(float(r['stature']),float(r['footlength'])) for r in records]
 relevant=[fl for h,fl in pairs if 1810<=h<=1830]
 ansur={'source_url':'https://tools.openlab.psu.edu/publicData/ANSUR_II_MALE_Public.csv',
  'sha256':hashlib.sha256(data.read_bytes()).hexdigest(),'male_n':len(pairs),
  'height_band_mm':[1810,1830],'height_band_n':len(relevant),
  'foot_mean_mm':statistics.mean(relevant),'foot_median_mm':statistics.median(relevant),
  'foot_sd_mm':statistics.stdev(relevant),'foot_range_mm':[min(relevant),max(relevant)],
  'individual_target_inferred':False,'interpretation':'28cm is a population-informed provisional trial, not a mandatory individual bone length.'}
report={'source_commit':'edee242f76717957a8f10cf2537961f40ce2fa03','source_model':str(src.relative_to(ROOT)),
 'source_model_sha256':SOURCE_SHA,'blender_version':bpy.app.version_string,
 'body_height_m':max(p.z for p in native)-min(p.z for p in native),'feet':feet,'anatomical_foot_reference_controls':bones,
 'weights':weights,'motion_samples':motion,'return_to_rest_max_error_m':return_error,
 'toe_control_length_halving_max_vertex_effect_m':tail_effect,'original_scene_fingerprint':before,
 'original_mesh_weights_and_both_skeletons_unchanged':True,'ansur_actual_csv_analysis':ansur,
 '28cm_candidate_created':False,'gate_state':'BLOCKED_REFERENCE_ENVELOPE_AND_SEMANTICS',
 'interpretation':['The visible 30.9157cm length is actual rest mesh geometry, not camera perspective.',
  'The206-bone reference foot was derived from old surface landmarks with low-confidence toe stations; it is not an independent validated anatomical baseline.',
  'The unchanged reference points do not fit inside a28cm heel-preserving surface envelope.',
  'Halving runtime toe display-tail length while preserving origin/axis does not shorten skin; actual causal effect is measured separately.',
  'Free toe/ankle sweeps expose floor crossings; they do not validate planted stance or physiological range.',
  'Source station semantics/compatible landmark targets must be resolved before creating a28cm mesh-only correction.'],
 'production_approved':False,'anatomical_approval':False}
(out/'foot_native_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('FOOT_NATIVE_AUDIT',[(k,v['mesh_length_m'],v['candidate_gate']['reference_protrusion_m']) for k,v in feet.items()],
 'motion samples',len(motion),'tail-only effect',tail_effect,'return',return_error,'original unchanged',fingerprint()==before)
