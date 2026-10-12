"""Native, read-only rest-offset proof against actual source controls.

The pilot is built in a separate temporary scene. Original full-body scene,
skeletal geometry, skin, weights and native file are never changed/saved.
"""
import bpy,json,sys,hashlib
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import original_shoulder_bind_semantics as bind
import original_v1_functional_fullbody as bridge
import build_functional_scapula_bowl_blender as bowl
import build_functional_absolute_reach_blender as reach
SOURCE_HASH='670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56'
source=Path(bpy.data.filepath).resolve()
assert hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_HASH
original=bpy.context.scene
runtime=bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
anatomy=bpy.data.objects['HGPT_ANATOMICAL_MASTER']
body=bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
assert not bridge.validate_blender_bridge(anatomy,runtime,body)['errors']
def rows(m):return [list(row) for row in m]
def original_fingerprint():
    record={'vertices':[list(v.co) for v in body.data.vertices],
      'weights':[[[g.group,g.weight] for g in v.groups] for v in body.data.vertices],
      'modifiers':[[m.name,m.type,m.object.name if m.type=='ARMATURE' and m.object else None,m.show_viewport,m.show_render] for m in body.modifiers],
      'skeletons':{arm.name:{'world':rows(arm.matrix_world),'bones':{b.name:rows(b.matrix_local) for b in arm.data.bones},'pose':{p.name:rows(p.matrix_basis) for p in arm.pose.bones}} for arm in (runtime,anatomy)}}
    return hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest()
before=original_fingerprint()
targets={}
for side,suffix in [('left','r'),('right','l')]:
    for part,rt in [('clavicle','clavicle'),('scapula','scapula'),('humerus','upperarm')]:
        targets[part+'_'+side]=rows(runtime.matrix_world@runtime.data.bones[rt+'_'+suffix].matrix_local)
record_path=ROOT/reach.context.shoulder.RECORD
rec=json.loads(record_path.read_text())
# Existing builder deletes objects in its current scene, so isolate it first.
probe=bpy.data.scenes.new('READ_ONLY_SHOULDER_BIND_PROBE')
bpy.context.window.scene=probe
arm,shapes=bowl.build(rec)
source_rest={b.name:rows(arm.matrix_world@b.matrix_local) for b in arm.data.bones}
offsets={name:bind.bind_offset(source_rest[name],targets[name]) for name in targets}
samples=[]; maximum_error=0; maximum_gap_drift=0
for angle in (None,0,90,160):
    if angle is None:
        for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4)
        bpy.context.view_layer.update()
    else:reach.pose_absolute(arm,rec,angle)
    for name in targets:
        p=arm.matrix_world@arm.pose.bones[name].matrix
        candidate=bind.transfer_world(rows(p),offsets[name])
        # Independent native mathutils oracle, no helper implementation used.
        oracle=p@(arm.matrix_world@arm.data.bones[name].matrix_local).inverted()@Matrix(targets[name])
        error=max(abs(candidate[r][c]-oracle[r][c]) for r in range(4) for c in range(4))
        rest_gap=bind.separation_m(source_rest[name],targets[name])
        gap=bind.separation_m(rows(p),candidate)
        drift=abs(gap-rest_gap)
        maximum_error=max(maximum_error,error);maximum_gap_drift=max(maximum_gap_drift,drift)
        assert error<2e-6,(name,error)
        assert drift<2e-6,(name,drift)
        if angle is None:
            assert max(abs(candidate[r][c]-targets[name][r][c]) for r in range(4) for c in range(4))<2e-6
        samples.append({'sample':'SOURCE_REST' if angle is None else f'AUTHORED_ABSOLUTE_HT_{angle}',
         'source_control':name,'source_pose_world_row_major':rows(p),
         'diagnostic_target_world_row_major':candidate,'native_oracle_max_matrix_error':error,
         'source_control_origin_to_target_origin_mm':gap*1000,
         'retained_rest_gap_mm':rest_gap*1000})
bpy.context.window.scene=original
after=original_fingerprint()
assert before==after,'Original body/weights/modifiers/skeleton/pose changed'
assert hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_HASH
result={'source_commit':'d04100995ca496fd4e095c748179e08b730bcd6e',
 'fullbody_model_sha256':SOURCE_HASH,'shape_record_sha256':hashlib.sha256(record_path.read_bytes()).hexdigest(),
 'native_blender_version':bpy.app.version_string,'original_scene_fingerprint_before':before,
 'original_scene_fingerprint_after':after,'original_scene_and_file_unchanged':before==after,
 'source_authored_curved_shape_meshes':len(shapes),'control_count':len(targets),'native_comparisons':len(samples),
 'formula':'offset=inv(sourceWorldRest)*targetWorldRest; diagnosticTargetWorld=sourceWorldPose*offset',
 'bind_offsets_row_major':offsets,'max_native_matrix_oracle_error':maximum_error,
 'max_retained_gap_drift_m':maximum_gap_drift,'samples':samples,
 'claims':{'rest_preserving_math_proved':True,'anatomical_joint_centre_alignment_proved':False,
 'retarget_installed':False,'body_driven_by_source_skeleton':False,'deformation_fixed':False,
 'production_approved':False,'anatomical_approval':False},
 'finding':'Rest-preserving offsets retain the nonzero origin gaps at every sampled pose. Correct matrix math alone does not align source anatomical joints with the old runtime.',
 'next':'Explicitly distinguish SC/AC/GH and scapula control origins; derive provisional runtime joint frames from the source authority, then refit body/weights in a separate candidate. Never displace anatomical source to old skin.'}
out=Path(sys.argv[sys.argv.index('--')+1]).resolve();out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(result,indent=2)+'\n')
print('NATIVE_BIND_PROOF',len(samples),'comparisons; matrix max',maximum_error,'gap drift',maximum_gap_drift,'original unchanged',before==after)
