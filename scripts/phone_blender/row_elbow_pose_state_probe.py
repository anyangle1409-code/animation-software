"""Read-only authored W8 row control geometry; never anatomical approval."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from forearm_pose_state_probe import (W8_SHA256, R57_SHA, digest, verify_r57_root,
    control_record, _valid_control, _finite, _number, _vector, smooth)
import row_pinned_edges as pinned_edges

CONTROLS = ('upperarm', 'forearm', 'hand')
FLAGS = ('collapse_lt_0_1', 'stretch_gt_2', 'self_intersecting_pairs')
LIMITATIONS = (
    'The row is a coupled shoulder/elbow path, not an isolated elbow-flexion test',
    'Authored suffixes are rig labels, not verified anatomical laterality',
    'Bone heads are authored control points, not anatomical joint centres',
    'Included point angles and local rotations are not signed ISB coordinates or anatomical ROM',
    'Whole-body benchmark flags are not elbow-local deformation measurements or tissue-safety evidence',
    'The plain benchmark clears shape keys and does not test driven corrective skin',
    'The path ends flexed and does not test return to neutral',
)


def scope():
    return {'status':'READ_ONLY_AUTHORED_ROW_ELBOW_CONTROLS_ANATOMY_NOT_APPROVED',
            'evidence_kind':'NATIVE_PINNED_MODEL_OBSERVATION','synthetic_test_fixture':False,
            'model':'W8','source_sha256':W8_SHA256,'pinned_r57_source_commit':R57_SHA,
            'source_unchanged':True,'saved_blend':False,'rest_bone_signature_unchanged':True,
            'plain_benchmark_correctives_cleared':True,'anatomical_motion_approved':False,
            'return_to_neutral_tested':False,'limitations':list(LIMITATIONS)}


def authored_targets(t):
    t = _finite(t)
    if not 0.0 <= t <= 1.0:
        raise ValueError('sample parameter outside [0,1]')
    hinge = smooth(min(1.0, 2*t))
    pull = smooth(max(0.0, 2*t-1.0))
    return {'elbow_flexion':100.0*pull,
            'shoulder_flexion_signed':45.0*hinge-85.0*pull}


def included_elbow_angle_deg(controls):
    points = [_vector(controls[n]['head_world_m_not_anatomical_joint_centre'],3)
              for n in CONTROLS]
    a,e,w = points
    vectors = [[_finite(p[i]-e[i]) for i in range(3)] for p in (a,w)]
    unit = []
    for v in vectors:
        length = math.hypot(*v)
        if not math.isfinite(length) or length <= 1e-12:
            raise ValueError('degenerate control chain')
        unit.append([x/length for x in v])
    dot = max(-1.0,min(1.0,sum(x*y for x,y in zip(*unit))))
    return math.degrees(math.acos(dot))


def validate_report(data):
    if not isinstance(data,dict):
        return ['invalid report scope']
    errors=[]
    for key,value in scope().items():
        if key=='limitations':
            if not isinstance(data.get(key),list) or any(x not in data[key] for x in LIMITATIONS):
                errors.append('missing limitations')
        elif type(data.get(key)) is not type(value) or data[key]!=value:
            errors.append('invalid report scope')
    rows=data.get('samples')
    if not isinstance(rows,list) or len(rows)!=9:
        return errors+['nine samples required']
    for i,row in enumerate(rows):
        if not isinstance(row,dict):
            errors.append('invalid sample');continue
        if type(row.get('sample')) is not int or row['sample']!=i:
            errors.append('invalid sample identity')
        t=row.get('t')
        if not _number(t) or not math.isclose(t,i/8,rel_tol=0.,abs_tol=1e-12):
            errors.append('invalid sample parameter')
        targets=row.get('authored_targets_deg_not_anatomical')
        expected=authored_targets(i/8)
        if (not isinstance(targets,dict) or set(targets)!=set(expected)
            or any(not _number(targets[k]) or not math.isclose(targets[k],v,rel_tol=0.,abs_tol=1e-7)
                   for k,v in expected.items())):
            errors.append('authored target mismatch')
        flags=row.get('whole_body_benchmark_flags_not_elbow_local')
        if (not isinstance(flags,dict) or set(flags)!=set(FLAGS)
            or any(type(flags[k]) is not int or flags[k]<0 for k in FLAGS)):
            errors.append('invalid whole-body flags')
        sides=row.get('sides')
        if not isinstance(sides,dict) or set(sides)!={'l','r'}:
            errors.append('both authored suffixes required');continue
        for side in ('l','r'):
            observed=sides[side]
            if not isinstance(observed,dict):
                errors.append('invalid side');continue
            controls=observed.get('controls')
            if not isinstance(controls,dict) or set(controls)!=set(CONTROLS):
                errors.append('invalid controls');continue
            valid=True
            for name in CONTROLS:
                good,consistent=_valid_control(controls[name],'XYZ')
                if not good or not consistent:
                    errors.append('invalid control observation');valid=False
            if not valid:continue
            try:
                angle=included_elbow_angle_deg(controls)
                actual=observed.get('included_control_elbow_angle_deg_not_anatomical')
                if not _number(actual) or not math.isclose(actual,angle,rel_tol=0.,abs_tol=1e-7):
                    errors.append('included geometry mismatch')
            except (KeyError,TypeError,ValueError,OverflowError):
                errors.append('invalid included geometry')
    return errors


def markdown(data):
    errors=validate_report(data)
    if errors:raise ValueError('; '.join(errors))
    lines=['# W8 authored row elbow controls — native read-only evidence','',
           'This coupled shoulder/elbow path does not establish anatomical motion or elbow-local skin quality.','',
           '| Sample | elbow target° | signed shoulder target° | local forearm magnitude l/r° | included control angle l/r° |',
           '|---:|---:|---:|---:|---:|']
    for row in data['samples']:
        sides=row['sides'];target=row['authored_targets_deg_not_anatomical']
        local=[sides[s]['controls']['forearm']['local_delta_angle_deg_not_anatomical'] for s in ('l','r')]
        included=[sides[s]['included_control_elbow_angle_deg_not_anatomical'] for s in ('l','r')]
        lines.append(f"| {row['sample']} | {target['elbow_flexion']:.5f} | {target['shoulder_flexion_signed']:.5f} | {local[0]:.5f}/{local[1]:.5f} | {included[0]:.5f}/{included[1]:.5f} |")
    lines+=['','Whole-body flags below are not elbow-local:','',
            '| Sample | collapsed triangles | stretched triangles | intersecting pairs |','|---:|---:|---:|---:|']
    for row in data['samples']:
        f=row['whole_body_benchmark_flags_not_elbow_local']
        lines.append(f"| {row['sample']} | {f[FLAGS[0]]} | {f[FLAGS[1]]} | {f[FLAGS[2]]} |")
    lines+=['']+[f'- {x}.' for x in data['limitations']]
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source-dir',type=Path,required=True)
    p.add_argument('--r57-root',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    sources=list(args.source_dir.rglob('*.blend'))
    if len(sources)!=1 or digest(sources[0])!=W8_SHA256:
        raise ValueError('Exactly one hash-pinned W8 source required')
    source=sources[0].resolve();root=args.r57_root.resolve();verify_r57_root(root)
    sys.path[:0]=[str(root/'scripts'),str(root/'scripts/anatomy_fit'),
                  str(Path(__file__).resolve().parents[1]/'recovery_diagnostics')]
    import bpy
    import diagnose_candidates_blender as adapter
    import build_original_movement_benchmarks_blender as bench
    import build_functional_shoulder_correction_blender as correction
    import original_v1_review_candidate_drives as drives
    import original_v1_press_extension as press_extension
    if (bench.FRAMES!=9 or bench.ROW['elbow_flexion']!=100.0
        or bench.ROW['shoulder_flexion_start']!=45.0 or bench.ROW['shoulder_extension_end']!=40.0):
        raise ValueError('Frozen row contract changed')
    bpy.context.preferences.filepaths.use_scripts_auto_execute=False
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    body=bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
    rig=bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
    before=adapter.rest_signature(rig,body)
    result=adapter.loaded_result(bpy,correction,drives)
    press_extension.install()
    if 'hgpt_cap_fraction_ramp' in rig or press_extension._PATH['name']!='v4':
        raise ValueError('Pinned benchmark variant changed')
    captures=[]
    edge_reference=[None]
    edge_samples=[]
    source_vertex_count=len(body.data.vertices)
    source_faces=[tuple(poly.vertices) for poly in body.data.polygons]
    def setup_edges(loaded):
        if any(k.value!=0. for k in body.data.shape_keys.key_blocks[1:]):
            raise ValueError('Neutral edge reference has active corrective keys')
        vertices,faces=bench._evaluated(body)
        edge_reference[0]=pinned_edges.reference(vertices,faces,source_vertex_count,source_faces)
    def capture(loaded):
        if any(k.value!=0. for k in body.data.shape_keys.key_blocks[1:]):
            raise ValueError('Plain benchmark unexpectedly activated corrective keys')
        sides={}
        for side in ('l','r'):
            records={n:control_record(loaded['runtime'].pose.bones,rig.matrix_world,f'{n}_{side}') for n in CONTROLS}
            sides[side]={'controls':records,'included_control_elbow_angle_deg_not_anatomical':included_elbow_angle_deg(records)}
        captures.append(sides)
        vertices,faces=bench._evaluated(body)
        edge_samples.append(pinned_edges.snapshot(vertices,faces,edge_reference[0],len(captures)-1))
        print('READ_ONLY_ROW_ELBOW_CAPTURE',len(captures)-1,flush=True)
    original=correction.build_corrected_scene
    correction.build_corrected_scene=lambda:result
    try:outcome=bench.run(only=['bent_over_row'],setup=setup_edges,post_pose=capture)
    finally:correction.build_corrected_scene=original
    frames=outcome.get('benchmarks',{}).get('bent_over_row',{}).get('frames',[])
    if len(frames)!=9 or len(captures)!=9:raise ValueError('Incomplete row observation')
    if digest(source)!=W8_SHA256 or adapter.rest_signature(rig,body)!=before:
        raise ValueError('Protected source/rest data changed')
    data=scope();data['samples']=[]
    for i,(frame,sides) in enumerate(zip(frames,captures)):
        target=authored_targets(i/8)
        angles=frame.get('angles_deg',{})
        if not _number(angles.get('elbow_flexion')) or abs(angles['elbow_flexion']-target['elbow_flexion'])>0.011:
            raise ValueError('Frozen benchmark elbow target mismatch')
        data['samples'].append({'sample':i,'t':i/8,'authored_targets_deg_not_anatomical':target,
            'whole_body_benchmark_flags_not_elbow_local':{k:frame[k] for k in FLAGS},'sides':sides})
    errors=validate_report(data)
    if errors:raise ValueError('Invalid native row evidence: '+'; '.join(errors))
    edge_data=pinned_edges.report(edge_reference[0],edge_samples)
    args.out.mkdir(parents=True,exist_ok=False)
    (args.out/'w8_row_elbow_pose_state.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    (args.out/'w8_row_elbow_pose_state.md').write_text(markdown(data),encoding='utf-8')
    (args.out/'w8_row_pinned_edges.json').write_text(json.dumps(edge_data,indent=2)+'\n',encoding='utf-8')
    (args.out/'w8_row_pinned_edges.md').write_text(pinned_edges.markdown(edge_data),encoding='utf-8')
    print('W8_ROW_ELBOW_POSE_STATE_WRITTEN',len(captures),flush=True)


if __name__=='__main__':main()
