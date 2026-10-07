#!/usr/bin/env python3
"""Offline integrity/measurement tools. No anatomical fit or motion gate can pass here."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'ORIGINAL_V1_WORK/anatomy'
ATLAS_FILES=['adult_bone_inventory_206.json','adult_bone_blender_aliases_206.json',
             'adult_articulation_inventory.json','joint_landmark_frame_atlas.json',
             'whole_body_movement_atlas.json','anatomy_sources.json']
FUNCTIONAL_TASKS=['squat','split_squat_lunge','hip_hinge','calf_raise_forefoot_loading','curl','row',
                  'shoulder_press','pull_up_hang','push_up_plank','multiplanar_reaching',
                  'loaded_grip_pinch','wrist_supported_loading']


def atlas_hashes():
    return {name:hashlib.sha256((DATA/name).read_bytes()).hexdigest() for name in ATLAS_FILES}


def build_plan():
    aliases=json.loads((DATA/ATLAS_FILES[1]).read_text())['aliases']
    inventory=json.loads((DATA/ATLAS_FILES[2]).read_text())['articulations']
    frames=json.loads((DATA/ATLAS_FILES[3]).read_text())
    movement=json.loads((DATA/ATLAS_FILES[4]).read_text())
    cases={}
    for key,p in movement['profiles'].items():
        members=[j for j in inventory if movement['joint_assignments'][j['id']]['profile_id']==key]
        cases[key]={'test_id':'isolated_'+key,'sides':sorted({j['side'] for j in members}),
                    'joint_ids':[j['id'] for j in members],'sources':p['sources'],
                    'instructions':p['bone_only_tests'],'acceptance_criteria':p['acceptance_criteria'],
                    'stages':['neutral','intermediate','near_source_context_range'],
                    'directions':['outbound','return','reversal'],
                    'plane_context':p['movement_plane_dependence'],
                    'posture_load_context':p['posture_load_dependence'],
                    'rom':p['rom'],'numeric_motion_bounds':None,'execution_status':'NOT_EXECUTED'}
    return {'schema_version':1,'scope':'Prepared local measurement requests; no fitting or solver execution.',
            'atlas_sha256':atlas_hashes(),'expected_bones':{a['anatomical_id']:a['reference_blender_name'] for a in aliases},
            'bone_frames':frames['bone_assignments'],'landmark_recipes':frames['frames'],
            'joint_markers':{j['id']:{'object_name':'HGPT_JOINT_'+j['id'],
                'participants':j['participants'],'role':j['role'],'frame_id':frames['joint_assignments'][j['id']]['frame_id'],
                'centre_recipe':frames['joint_assignments'][j['id']]['centre_recipe'],
                'sources':j['sources'],'fit_status':'UNVERIFIED'} for j in inventory},
            'profile_cases':cases,'functional_cases':[{'test_id':'functional_'+t,'task':t,
                'execution_status':'NOT_EXECUTED','acceptance_status':'UNVERIFIED'} for t in FUNCTIONAL_TASKS],
            'samples':[],'character_accepted':False,
            'sample_fields':['test_id','frame','subframe','side','plane','direction','posture','load','measurement_mode'],
            'policy':['Use explicitly fitted joint-frame marker objects; never infer centres from bone origins.',
                      'Fill animation frames only after local poses/solvers are prepared. This tool never constructs poses.',
                      'Read-only measurements do not establish anatomical fit, contact mechanics or clinical ROM.',
                      'No universal numeric limits; local tolerances and source context require separate review.']}


def point(v):
    if not isinstance(v,(list,tuple)) or len(v)!=3 or not all(type(x) in (int,float) and math.isfinite(x) for x in v):
        raise ValueError('Finite 3-vector required')
    return list(v)


# Blender stores bone/object matrices in single precision; short bones show orthogonality errors of a few 1e-6.
# Real shear or non-uniform scale is orders of magnitude larger.
RIGID_TOLERANCE=1e-5


def rigid_matrix(m,expected_scale=None):
    """Normalised rigid copy of a 4x4 world matrix. With expected_scale (the armature object's uniform world
    scale), each axis must have exactly that length, so pose-bone scale cannot hide inside a rigid transform."""
    if not isinstance(m,list) or len(m)!=4 or any(not isinstance(r,list) or len(r)!=4 for r in m):
        raise ValueError('4x4 matrix required')
    if any(type(v) not in (int,float) or not math.isfinite(v) for r in m for v in r):
        raise ValueError('Nonfinite matrix')
    if any(abs(m[3][i]-[0,0,0,1][i])>1e-8 for i in range(4)): raise ValueError('Invalid affine row')
    cols=[];lengths=[]
    for c in range(3):
        vec=[m[r][c] for r in range(3)];length=math.sqrt(sum(v*v for v in vec))
        if length<=1e-12:raise ValueError('Degenerate matrix axis')
        cols.append([v/length for v in vec]);lengths.append(length)
    # A uniform object scale is allowed (positions are converted separately); non-uniform scale is not rigid.
    if max(lengths)-min(lengths)>RIGID_TOLERANCE*max(lengths):raise ValueError('Non-uniform axis scale is not a rigid rotation')
    if expected_scale is not None and any(abs(l-expected_scale)>RIGID_TOLERANCE*expected_scale for l in lengths):
        raise ValueError('Bone axis scale differs from the armature object scale (pose-bone scale is not rigid)')
    if any(abs(sum(x*y for x,y in zip(cols[a],cols[b])))>RIGID_TOLERANCE for a,b in [(0,1),(0,2),(1,2)]):
        raise ValueError('Sheared axes are not a rigid rotation')
    x,y,z=cols
    det=x[0]*(y[1]*z[2]-y[2]*z[1])-x[1]*(y[0]*z[2]-y[2]*z[0])+x[2]*(y[0]*z[1]-y[1]*z[0])
    if det<1-RIGID_TOLERANCE:raise ValueError('Reflected/improper frame')
    return [[cols[c][r] for c in range(3)]+[m[r][3]] for r in range(3)]+[[0,0,0,1]]


def relative_transform(parent,child,expected_scale=None):
    a,b=rigid_matrix(parent,expected_scale),rigid_matrix(child,expected_scale)
    rotation=[[sum(a[k][i]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    delta=[b[i][3]-a[i][3] for i in range(3)]
    return [rotation[i]+[sum(a[k][i]*delta[k] for k in range(3))] for i in range(3)]+[[0,0,0,1]]


def rotation_difference_degrees(a,b):
    r=relative_transform(a,b)
    return math.degrees(math.acos(max(-1,min(1,(sum(r[i][i] for i in range(3))-1)/2))))


def trajectory_metrics(points,times):
    if len(points)!=len(times) or len(points)<2:raise ValueError('Two or more time/point samples required')
    pts=[point(p) for p in points]
    if any(type(t) not in (int,float) or not math.isfinite(t) for t in times):raise ValueError('Finite times required')
    dt=[b-a for a,b in zip(times,times[1:])]
    if any(t<=0 for t in dt):raise ValueError('Strictly increasing seconds required')
    velocities=[[(b[c]-a[c])/d for c in range(3)] for a,b,d in zip(pts,pts[1:],dt)]
    speeds=[math.sqrt(sum(v*v for v in row)) for row in velocities]
    accelerations=[math.sqrt(sum((2*(b[c]-a[c])/(d1+d2))**2 for c in range(3)))
                   for a,b,d1,d2 in zip(velocities,velocities[1:],dt,dt[1:])]
    return {'speeds_m_per_s':speeds,'acceleration_m_per_s2':accelerations,
            'interpretation':'Finite-difference descriptive metrics; no physiological threshold or pass inferred.'}


def analyze_capture(capture,plan):
    checks={};errors=[]
    def check(key,status,detail):checks[key]={'status':status,'detail':detail}
    current_hashes=atlas_hashes()
    canonical_plan=build_plan()
    contract_keys=['expected_bones','joint_markers','profile_cases','functional_cases','bone_frames','landmark_recipes']
    contract_ok=all(plan.get(key)==canonical_plan[key] for key in contract_keys)
    provenance=capture.get('provenance',{})
    def valid_hash(value):
        return isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)
    before_hash=provenance.get('blend_sha256');after_hash=provenance.get('blend_sha256_after')
    if not contract_ok or provenance.get('atlas_sha256')!=current_hashes or plan.get('atlas_sha256')!=current_hashes:
        check('provenance','FAIL','Capture/plan contract or atlas hashes differ from current reference.')
    elif provenance.get('source_file_unchanged') is False or provenance.get('frame_restored') is False:
        check('provenance','FAIL','Source file changed or original scene frame was not restored.')
    elif valid_hash(before_hash) and valid_hash(after_hash) and before_hash!=after_hash:
        check('provenance','FAIL','Before/after source blend hashes contradict preservation evidence.')
    elif provenance.get('automatic_python_execution_failed') is True:
        check('provenance','UNVERIFIED','Automatic Python/driver execution failed; evaluated motion is incomplete.')
    elif provenance.get('dirty_before_capture') is not False:
        check('provenance','UNVERIFIED','Saved blend hash does not identify unsaved character state.')
    elif not valid_hash(before_hash) or not valid_hash(after_hash):
        check('provenance','UNVERIFIED','Valid before/after source blend hashes required.')
    elif (provenance.get('source_file_unchanged') is not True or
          provenance.get('frame_restored') is not True or
          provenance.get('automatic_python_execution_failed') is not False):
        check('provenance','UNVERIFIED','Explicit source preservation, frame restoration and execution status required.')
    else:check('provenance','PASS','Atlas hashes match; saved source identified. This does not prove fitted geometry.')
    scale=capture.get('metres_per_world_unit')
    unit_ok=capture.get('units')=='metres' and type(scale) in (int,float) and math.isfinite(scale) and scale>0
    consistent=provenance.get('unit_scale_consistent')
    if not unit_ok:check('units','FAIL','Explicit positive metres-per-world-unit conversion required.')
    elif consistent is False:check('units','FAIL','Supplied metres-per-world-unit contradicts the scene unit scale.')
    elif consistent is True:check('units','PASS','Explicit conversion matches the scene unit scale; character physical scale still needs independent confirmation.')
    else:check('units','UNVERIFIED','Scene declares no physical unit; confirm the conversion from character provenance.')
    plan=canonical_plan
    bones=capture.get('rest_bones',{})
    counts=Counter(b.get('anatomical_id') for b in bones.values() if b.get('anatomical_id'))
    expected=plan['expected_bones']
    identity_errors=[k for k,n in counts.items() if n!=1 or k not in expected]
    identity_errors += [name for name,b in bones.items() if b.get('anatomical_id') in expected and name!=expected[b['anatomical_id']]]
    check('identity','FAIL' if identity_errors else 'PASS',identity_errors or 'Unique stable anatomical names; untagged helper controls excluded.')
    present=set(counts)&set(expected);missing=sorted(set(expected)-present)
    check('bone_coverage','FAIL' if missing else 'PASS',{'represented':len(present),'expected':len(expected),'missing':missing})
    lengths={};geometry_errors=[]
    def object_scale(value):
        if value is None:return None
        if type(value) not in (int,float) or not math.isfinite(value) or value<=0:raise ValueError('Invalid armature world scale')
        return float(value)
    try:rest_scale=object_scale(provenance.get('armature_world_scale'))
    except ValueError as e:rest_scale=None;geometry_errors.append('provenance: '+str(e))
    check('bone_scale','PASS' if provenance.get('armature_world_scale_uniform') is True and rest_scale is not None else
          ('FAIL' if provenance.get('armature_world_scale_uniform') is False else 'UNVERIFIED'),
          'Bone axes must equal the uniform armature object scale.' if rest_scale is not None else
          'Capture has no armature world scale: uniform pose-bone scale cannot be excluded.')
    for name,b in bones.items():
        try:
            h,t=point(b['head_world_m']),point(b['tail_world_m']);rigid_matrix(b['matrix_world'],rest_scale)
            length=math.dist(h,t)
            if length<=1e-9:raise ValueError('Zero/unresolved bone length')
            if b.get('anatomical_id') in expected:lengths[b['anatomical_id']]=length
        except (KeyError,TypeError,ValueError,OverflowError) as e:geometry_errors.append(name+': '+str(e))
        cursor=name;seen=set()
        while cursor is not None:
            if cursor in seen:geometry_errors.append(name+': hierarchy cycle');break
            if cursor not in bones:geometry_errors.append(name+': missing parent '+str(cursor));break
            seen.add(cursor);cursor=bones[cursor].get('parent')
    check('geometry_integrity','FAIL' if geometry_errors else ('PASS' if bones else 'UNVERIFIED'),
          geometry_errors or ('Finite nonzero segments, proper unsheared axes, existing parents and no cycles.' if bones else 'No bone geometry supplied.'))
    bilateral={}
    for key,length in lengths.items():
        if key.endswith('_left') and key[:-5]+'_right' in lengths:
            right=lengths[key[:-5]+'_right']
            bilateral[key[:-5]]={'left_m':length,'right_m':right,'relative_difference':abs(length-right)/max(length,right),'status':'UNVERIFIED'}
    check('bilateral_lengths','UNVERIFIED','Differences measured; no universal symmetry tolerance or fit inferred.')
    known_tests={p['test_id'] for p in plan['profile_cases'].values()}|{p['test_id'] for p in plan['functional_cases']}
    centres={};centre_errors=[];pose_errors=[];tracks={};relative_rotations={};context_missing=[];executed=set();pose_count=0
    landmarks={};landmark_errors=[];images=[]
    for index,s in enumerate(capture.get('samples',[])):
        tid=s.get('test_id');time=s.get('time_seconds')
        if tid in known_tests:
            executed.add(tid)
            if any(not s.get(k) for k in ['side','plane','direction','posture','load','measurement_mode']):context_missing.append(index)
        elif tid!='unassigned_current_pose':pose_errors.append(f'Sample {index}: unknown test ID')
        context=[tid]+[s.get(k) for k in ['side','plane','direction','posture','load','measurement_mode']]
        seen_landmarks=set()
        for name,landmark in s.get('landmarks',{}).items():
            try:
                key=landmark.get('landmark_id')
                if not isinstance(key,str) or not key or key in seen_landmarks:raise ValueError('Missing/duplicate landmark ID')
                seen_landmarks.add(key)
                p=point(landmark['position_world_m'])
                landmarks.setdefault(key,[]).append({'sample':index,'object_name':name,'position_m':p,'anatomical_fit':'UNVERIFIED'})
            except (KeyError,TypeError,ValueError) as e:landmark_errors.append(f'{index}/{name}: {e}')
        for image in s.get('evidence_images',[]):
            images.append({'sample':index,'test_id':tid,'attachment':image,'scene_correspondence':'UNVERIFIED'})
        try:sample_scale=object_scale(s.get('armature_world_scale',rest_scale))
        except ValueError as e:sample_scale=None;pose_errors.append(f'{index}: {e}')
        for name,b in s.get('bones',{}).items():
            pose_count+=1
            try:
                point(b['head_world_m']);point(b['tail_world_m']);rigid_matrix(b['matrix_world'],sample_scale)
                parent=b.get('parent')
                if parent is not None:
                    parent_matrix=s['bones'][parent]['matrix_world']
                    relative=relative_transform(parent_matrix,b['matrix_world'],sample_scale)
                else:relative=rigid_matrix(b['matrix_world'],sample_scale)
                relative_rotations.setdefault(name,[]).append({'sample':index,'matrix':relative,'context':context})
            except (KeyError,TypeError,ValueError,OverflowError) as e:pose_errors.append(f'{index}/{name}: {e}')
        sample_centres={}
        for key,marker in s.get('joint_frames',{}).items():
            try:
                if key not in plan['joint_markers']:raise ValueError('Unknown articulation marker')
                matrix=rigid_matrix(marker['matrix_world']);p=[matrix[i][3] for i in range(3)]
                sample_centres[key]=p;centres.setdefault(key,[]).append({'sample':index,'position_m':p})
                group=json.dumps(context,sort_keys=True)
                tracks.setdefault((key,group),[]).append((time,p))
            except (KeyError,TypeError,ValueError,OverflowError) as e:pose_errors.append(f'{index}/{key}: {e}')
        for side in ['left','right']:
            pairs=[('sternoclavicular','acromioclavicular'),('acromioclavicular','glenohumeral'),('talocrural','subtalar_posterior')]
            for a,b in pairs:
                a,b=a+'_'+side,b+'_'+side
                if a in sample_centres and b in sample_centres and math.dist(sample_centres[a],sample_centres[b])<=1e-9:
                    centre_errors.append(f'Sample {index}: {a} and {b} coincide to numerical resolution; distinct anatomical centres required.')
    check('landmark_integrity','FAIL' if landmark_errors else 'PASS' if landmarks else 'UNVERIFIED',landmark_errors or 'Only supplied landmark IDs/coordinates checked; anatomical placement unverified.')
    check('joint_marker_coverage','PASS' if set(centres)==set(plan['joint_markers']) else 'UNVERIFIED',
          {'measured':len(centres),'expected':len(plan['joint_markers']),'missing':sorted(set(plan['joint_markers'])-set(centres))})
    check('distinct_centres','FAIL' if centre_errors else 'UNVERIFIED',centre_errors or 'No exact collision detected in supplied pairs; source-fitted separations still unverified.')
    trajectories=[]
    for (joint,context),rows in tracks.items():
        if len(rows)<2:continue
        try:metrics=trajectory_metrics([r[1] for r in rows],[r[0] for r in rows])
        except (ValueError,TypeError,OverflowError) as e:errors.append(joint+': '+str(e));continue
        trajectories.append({'joint_id':joint,'context':json.loads(context),'metrics':metrics,'status':'UNVERIFIED'})
    check('trajectory_integrity','FAIL' if errors else 'PASS' if trajectories else 'UNVERIFIED',errors or 'No invalid provided time sequence; absent/short tracks do not establish motion.')
    for rows in relative_rotations.values():
        first={}
        for row in rows:
            group=json.dumps(row['context'],sort_keys=True)
            first.setdefault(group,row['matrix'])
            try:row['principal_rotation_from_first_deg']=rotation_difference_degrees(first[group],row['matrix'])
            except (ValueError,TypeError,OverflowError) as e:
                row['principal_rotation_from_first_deg']=None;pose_errors.append(f"{row['sample']}: relative rotation: {e}")
    check('sample_integrity','FAIL' if pose_errors else 'PASS' if pose_count else 'UNVERIFIED',pose_errors or 'Provided transforms structurally valid; omitted pose data is not evidence.')
    check('test_execution','UNVERIFIED',{'sampled_test_ids':sorted(executed),'missing_context_samples':context_missing,
          'note':'Labels are not proof of complete sides, stages, planes or reversal. Inspect local test evidence.'})
    check('anatomical_placement','UNVERIFIED','Requires character landmarks/contact surfaces and reviewed fitting evidence. Bone names/matrices are insufficient.')
    check('joint_operation','UNVERIFIED','Requires sourced relative contact/axis/coupling tests in Blender; raw principal rotations are not clinical JCS angles.')
    return {'schema_version':1,'scope':'Numerical integrity and descriptive measurements only; no Blender gate acceptance.',
            'checks':checks,'bone_lengths_m':lengths,'bilateral_lengths':bilateral,'joint_centres':centres,
            'trajectories':trajectories,'relative_bone_transforms':relative_rotations,
            'landmark_positions':landmarks,'evidence_images':images,
            'overall_status':'FAIL' if any(c['status']=='FAIL' for c in checks.values()) else 'UNVERIFIED',
            'character_accepted':False,'production_approved':False,'completed_tracker_gates':[]}


def sample_with_frame_restore(scene,samples,capture_frame):
    for request in samples:
        frame=request.get('frame')
        if type(frame) is not int or not -1048574<=frame<=1048574:raise ValueError('Explicit supported integer animation frame required')
        subframe=request.get('subframe',0)
        if type(subframe) not in (int,float) or not math.isfinite(subframe) or not 0<=subframe<1:raise ValueError('Finite subframe in [0,1) required')
    initial_frame,initial_subframe=scene.frame_current,scene.frame_subframe
    result=[]
    try:
        for request in samples:
            scene.frame_set(request['frame'],subframe=request.get('subframe',0))
            result.append(capture_frame(request))
    finally:scene.frame_set(initial_frame,subframe=initial_subframe)
    return result


def write_new_json(path,data):
    path=Path(path)
    if path.suffix!='.json':raise ValueError('Audit output must be a new .json file')
    payload=json.dumps(data,indent=2,allow_nan=False)+'\n'
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as stream:stream.write(payload)


def report_markdown(report):
    lines=['# Anatomical Blender measurements','',f"Overall: **{report['overall_status']}**. Character accepted: **No**.",'',
           'This report checks recorded geometry and measures supplied samples. It does not approve anatomical placement or movement.','',
           '| Check | Status | Detail |','|---|---|---|']
    for key,c in report['checks'].items():
        detail=c['detail'] if isinstance(c['detail'],str) else json.dumps(c['detail'])
        lines.append(f"| {key} | {c['status']} | {detail.replace('|','/').replace(chr(10),' ')} |")
    lines+=['','## Bilateral segment measurements','','| Segment | Left (m) | Right (m) | Relative difference | Status |','|---|---|---|---|---|']
    for key,v in report['bilateral_lengths'].items():lines.append(f"| {key} | {v['left_m']:.6g} | {v['right_m']:.6g} | {v['relative_difference']:.6g} | UNVERIFIED |")
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('plan');p.add_argument('--out',required=True)
    p=sub.add_parser('analyze');p.add_argument('capture');p.add_argument('--plan');p.add_argument('--out',required=True);p.add_argument('--markdown')
    args=parser.parse_args()
    if args.mode=='plan':write_new_json(args.out,build_plan());return 0
    cap=json.loads(Path(args.capture).read_text());plan=json.loads(Path(args.plan).read_text()) if args.plan else build_plan()
    result=analyze_capture(cap,plan);write_new_json(args.out,result)
    if args.markdown:
        with Path(args.markdown).open('x',encoding='utf-8') as stream:stream.write(report_markdown(result))
    return 1 if result['overall_status']=='FAIL' else 0

if __name__=='__main__':raise SystemExit(main())
