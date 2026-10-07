#!/usr/bin/env python3
"""Reference-only anatomy gates. Completeness is checked independently of a rig."""
from collections import Counter
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'ORIGINAL_V1_WORK/anatomy'

# Reviewed named articulation/contact complexes, not a universal human joint count.
# Each line encodes regional anatomical coverage; paired surfaces counted separately.
EXPECTED_FAMILIES = {
    'skull':64, 'ossicles':6, 'tmj':2, 'cervical':33, 'thoracic':36,
    'lumbar':15, 'ribs':44, 'anterior_thorax':44, 'shoulder':8,
    'elbow':4, 'forearm':6, 'wrist':26, 'thumb':6, 'fingers':38,
    'pelvis':9, 'hyoid':4, 'hip':2, 'knee':2, 'patella':2, 'tibiofibular':6,
    'ankle':2, 'hindfoot':4, 'midfoot':32, 'toes':32,
}

def mechanics_profile(j):
    """Reviewed anatomical compatibility, independent of assigned DOF values."""
    n,f=j['id'],j['family']
    if j['role']=='FIXED': return 'fixed'
    if f=='cervical': return 'c0_c1' if n.startswith('atlantooccipital') else 'c1_c2' if n.startswith('atlantoaxial') else 'cervical'
    if f=='pelvis': return 'si' if n.startswith('sacroiliac') else 'pubis' if n=='pubic_symphysis' else 'coccyx'
    if f=='shoulder': return {'sternoclavicular':'sc','acromioclavicular':'ac','scapulothoracic':'st','glenohumeral':'gh'}[n.rsplit('_',1)[0]]
    if f=='forearm': return 'ru_iom' if n.startswith('radioulnar_interosseous') else 'radioulnar'
    if f=='wrist': return 'radiocarpal' if n.startswith('radiocarpal') else 'pisiform' if n.startswith('pisotriquetral') else 'carpal'
    if f=='thumb': return 'thumb_cmc' if n.startswith('cmc') else 'thumb_mcp' if '_mcp_' in n else 'thumb_ip'
    if f=='fingers': return 'metacarpal' if not n.startswith('digit') else n.split('_')[1]
    if f=='tibiofibular': return 'ptf' if n.startswith('proximal') else 'dtf' if n.startswith('distal') else 'tf_iom'
    if f=='hindfoot': return 'subtalar' if n.startswith('subtalar') else 'tcn'
    if f=='midfoot': return 'tmt' if n.startswith(('tmt_','intermetatarsal')) else 'midfoot'
    if f=='toes': return 'sesamoid' if 'sesamoid' in n else 'hallux' if n.startswith('mtp_1_') else 'lesser_mtp' if n.startswith('mtp_') else 'toe_ip'
    return f

def command_group_contract(inventory, profiles):
    """Contact aliases share command ownership; followers retain required functional inputs."""
    groups={}
    for j in inventory['articulations']:
        n,f=j['id'],j['family']; side=j['side']; key=n
        if n.startswith('tmj_'): key='mandible'
        elif n.startswith('atlantooccipital'): key='c0_c1'
        elif n.startswith('atlantoaxial'): key='c1_c2'
        elif n.startswith('disc_'): key=n[5:]
        elif n.startswith(('facet_','uncovertebral_')): key=n.split('_',1)[1].rsplit('_',1)[0]
        elif f=='forearm': key='forearm_'+side
        elif f=='elbow': key='elbow_'+side
        elif f=='ribs': key=next(p for p in j['participants'] if p.startswith('rib_'))
        elif f=='hindfoot': key='hindfoot_'+side
        groups.setdefault(key,[]).append(j)
    result={}
    for key,members in groups.items():
        active=sorted(j['id'] for j in members if j['role']=='ACTIVE')
        owner=active[0] if active else None
        dof=profiles.get(mechanics_profile(next(j for j in members if j['id']==owner)),{}).get('primary_command_dof',0) if owner else 0
        control=None
        if key.startswith('hindfoot_'): dof=1; control='proposed_'+key+'_inversion_eversion'
        dependencies=[]
        if key.startswith('elbow_'): dependencies=['forearm_'+key.split('_',1)[1]]
        if key.startswith('forearm_'): dependencies=['elbow_'+key.split('_',1)[1], 'radiocarpal_'+key.split('_',1)[1]]
        if key.startswith('hindfoot_'): dependencies=['talocrural_'+key.split('_',1)[1]]
        if key.startswith(('sternoclavicular_','acromioclavicular_','scapulothoracic_','glenohumeral_')):
            side=key.rsplit('_',1)[1]
            dependencies=[p+'_'+side for p in ['sternoclavicular','acromioclavicular','scapulothoracic','glenohumeral'] if p+'_'+side!=key]
        result[key]=dict(members=sorted(j['id'] for j in members),owner_joint=owner,owner_control=control,
                         command_dof=dof,coupled_group_ids=dependencies,
                         semantics='Command ownership only; distinct contact transforms remain constrained by their anatomical profiles.',
                         character_validated=False)
    return result

def validate_inventory(data, directory=DATA):
    errors=[]
    def require(ok, message):
        if not ok: errors.append(message)
    bones={b['id'] for b in json.loads((directory/'adult_bone_inventory_206.json').read_text())['bones']}
    sources=json.loads((directory/'anatomy_sources.json').read_text())['sources']
    extra=data.get('additional_structures', {})
    joints=data.get('articulations', [])
    ids=[j.get('id') for j in joints]
    require(len(ids)==len(set(ids)), 'Duplicate articulation IDs')
    require(Counter(j.get('family') for j in joints)==Counter(EXPECTED_FAMILIES), 'Regional articulation coverage differs from reviewed contract')
    seen=set()
    for j in joints:
        name=j.get('id', '?')
        participants=j.get('participants', [])
        require(len(participants)>=2 and len(set(participants))==len(participants), f'{name}: invalid participants')
        require(set(participants)<=bones|set(extra), f'{name}: unknown participant')
        seen.update(set(participants)&bones)
        require(j.get('structural_type') in {'synovial','fibrous','cartilaginous','functional','fused'}, f'{name}: unclassified type')
        require(bool(j.get('subtype')), f'{name}: missing subtype')
        require(j.get('role') in {'ACTIVE','FOLLOWER','FIXED','REFERENCE'}, f'{name}: unclassified mechanics')
        require(j.get('side') in {'left','right','midline'}, f'{name}: invalid side')
        require(j.get('exercise_motion') in {'effectively_zero','moving_constrained'}, f'{name}: unclassified motion')
        require((j.get('role')=='FIXED')==(j.get('exercise_motion')=='effectively_zero'), f'{name}: fixed-motion contradiction')
        refs=j.get('sources', [])
        works={sources[s].get('independent_work_id',s) for s in refs if s in sources}
        require(len(works)>=2 and set(refs)<=set(sources), f'{name}: needs two independent identifiable sources')
        if name.startswith(('proximal_radioulnar','distal_radioulnar')):
            relevant={'OS_SELECTED','SP_PRUJ','ISB_II'} if name.startswith('proximal') else {'SP_DRUJ','DRUJ_FUNCTIONAL','ISB_II'}
            require(len(set(refs)&relevant)>=2 and 'OS_FIBROUS' not in refs, f'{name}: shaft syndesmosis is not synovial RU evidence')
            bindings=j.get('source_bindings',[])
            require({b.get('source') for b in bindings}==set(refs) and all(b.get('supported_claim') and b.get('locator') for b in bindings), f'{name}: missing claim-specific source bindings')
        if j.get('side') in {'left','right'}:
            other='right' if j['side']=='left' else 'left'
            require(name.rsplit('_',1)[0]+'_'+other in ids, f'{name}: missing opposite articulation')
    exemptions=data.get('non_articulating_bones',{})
    require(set(exemptions)=={'hyoid'}, 'Only hyoid may lack bone-to-bone articulation')
    require(seen|set(exemptions)==bones, f'Uncovered bones: {sorted(bones-seen-set(exemptions))}')
    for k,v in extra.items():
        require(v.get('owner_bone') in bones and v.get('counted_in_206') is False, f'{k}: invalid extra structure ownership')
    byid={j.get('id'):j for j in joints}
    for forbidden in ['disc_c1_c2','costotransverse_11_left','costotransverse_12_left']:
        require(forbidden not in byid, f'Anatomically absent joint invented: {forbidden}')
    # Pin rare, easily missed joints; replacing an omission with a spurious extra must fail.
    for s in ['left','right']:
        required={
            'distal_radioulnar':['ulna','radius'], 'pisotriquetral':['pisiform','triquetrum'],
            'hallux_ip':['hallux_proximal_phalanx','hallux_distal_phalanx'],
            'thumb_ip':['thumb_proximal_phalanx','thumb_distal_phalanx'],
            'patellofemoral':['femur','patella'], 'facet_l5_sacrum':['l5','sacrum'],
            'intermetatarsal_4_5':['metatarsal_4','metatarsal_5'],
        }
        for key,bases in required.items():
            expected={b if b in bones else b+'_'+s for b in bases}
            require(set(byid.get(key+'_'+s,{}).get('participants',[]))==expected, f'{key}_{s}: omitted/incorrect articulation')
        rc=byid.get('radiocarpal_'+s,{})
        require('ulna_'+s not in rc.get('participants',[]), f'{s}: direct ulna-carpus contact invented')
        require(byid.get('scapulothoracic_'+s,{}).get('structural_type')=='functional', f'{s}: ST is functional')
    # Ethmoid's thirteen osseous neighbours: detects a deceptively complete skull star.
    neighbours={p for j in joints if 'ethmoid' in j.get('participants',[]) for p in j['participants'] if p!='ethmoid'}
    require(len(neighbours)==13, 'Ethmoid must have thirteen conventional bone neighbours')
    return errors

def _dot(a,b): return sum(x*y for x,y in zip(a,b))
def _cross(a,b): return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
def _unit(v):
    if len(v)!=3 or not all(math.isfinite(x) for x in v): raise ValueError('Finite 3-vector required')
    length=math.sqrt(_dot(v,v))
    if length<=1e-12: raise ValueError('Coincident/collinear landmarks')
    return [x/length for x in v]

def orthonormal_frame(longitudinal, anterior_hint):
    """Generic engineering basis, not a substitute for region-specific ISB JCS."""
    y=_unit(longitudinal)
    hint=_unit(anterior_hint)
    z=_unit(_cross(hint,y))
    x=_unit(_cross(y,z))
    return [x,y,z]

def frame_determinant(frame): return _dot(frame[0],_cross(frame[1],frame[2]))

def validate_frames(atlas, inventory, directory=DATA):
    errors=[]
    sources=json.loads((directory/'anatomy_sources.json').read_text())['sources']
    bones={b['id'] for b in json.loads((directory/'adult_bone_inventory_206.json').read_text())['bones']}
    frames=atlas.get('frames',{})
    assignments=atlas.get('joint_assignments',{})
    if set(assignments)!={j['id'] for j in inventory['articulations']}: errors.append('Missing/extra joint frame assignment')
    if set(atlas.get('bone_assignments',{}))!=bones: errors.append('Missing/extra bone frame assignment')
    for key,f in frames.items():
        if len(set(f.get('landmarks',[])))<3: errors.append(f'{key}: insufficient landmarks')
        if not f.get('origin_recipe') or not f.get('axis_recipe') or not f.get('convention'): errors.append(f'{key}: incomplete semantic frame')
        if len(set(f.get('sources',[])))<2 or not set(f.get('sources',[]))<=set(sources): errors.append(f'{key}: insufficient frame evidence')
        if f.get('character_coordinates') is not None: errors.append(f'{key}: fabricated/pre-gate character coordinates')
    for key,a in assignments.items():
        if a.get('frame_id') not in frames or not a.get('centre_recipe') or not a.get('contact_locator'): errors.append(f'{key}: unresolved frame')
        if a.get('character_fitted') is not False or a.get('joint_centre_m') is not None: errors.append(f'{key}: premature character fit claim')
    for key,a in atlas.get('bone_assignments',{}).items():
        if a.get('frame_id') not in frames: errors.append(f'{key}: unknown bone frame')
    if 'project_adapter' not in atlas.get('conventions',{}): errors.append('Project coordinate adapter decision missing')
    return errors

def validate_movement(atlas, inventory, directory=DATA):
    """Evidence coverage, not a scientific endorsement of numerical limits."""
    errors=[]
    def require(ok, message):
        if not ok: errors.append(message)
    sources=json.loads((directory/'anatomy_sources.json').read_text())['sources']
    frames=json.loads((directory/'joint_landmark_frame_atlas.json').read_text())['joint_assignments']
    joints={j['id']:j for j in inventory['articulations']}
    assignments=atlas.get('joint_assignments',{})
    profiles=atlas.get('profiles',{})
    observations=atlas.get('observations',{})
    expected_groups=command_group_contract(inventory,profiles)
    require(atlas.get('command_groups')==expected_groups,'Command group membership, owner, DOF or dependency differs from anatomical contract')
    owner_dof={g['owner_joint']:g['command_dof'] for g in expected_groups.values() if g['owner_joint']}
    joint_groups={jid:key for key,g in expected_groups.items() for jid in g['members']}
    require(set(assignments)==set(joints), 'Missing/extra movement joint assignment')
    for scope,ids in atlas.get('complex_reference_observations',{}).items():
        for oid in ids:
            require(observations.get(oid,{}).get('measured_scope')==scope, f'{scope}: wrong composite reference')
    for scope,ids in atlas.get('clinical_reference_observations',{}).items():
        for oid in ids:
            o=observations.get(oid,{})
            require(o.get('measured_scope')==scope and o.get('mode')=='clinical_unspecified', f'{scope}: clinical mode/scope mismatch')
    for level,ids in atlas.get('level_reference_observations',{}).items():
        for oid in ids:
            require(oid=='lumbar_lift_'+level and observations.get(oid,{}).get('measured_scope')=='lumbar_segment', f'{level}: other level reference assigned')
    for key,p in profiles.items():
        refs=p.get('sources',[])
        works={sources[s].get('independent_work_id',s) for s in refs if s in sources}
        require(len(works)>=2 and set(refs)<=set(sources), f'{key}: needs two independent evidence works')
        for field in ['axes','measured_channels','coupling','translations_and_instantaneous_centre',
                      'posture_load_dependence','movement_plane_dependence','proposed_blender_representation',
                      'bone_only_tests','acceptance_criteria']:
            require(bool(p.get(field)), f'{key}: missing {field}')
        require(p.get('confidence') in {'contextual_reference','limited_quantitative'}, f'{key}: premature confidence claim')
        require(p.get('character_validated') is False and p.get('production_envelope') is None,
                f'{key}: premature character/production acceptance')
        require(type(p.get('primary_command_dof')) is int and 0<=p['primary_command_dof']<=3, f'{key}: invalid DOF')
        for mode in ['active','passive']:
            r=p.get('rom',{}).get(mode,{})
            require(r.get('status') in {'qualitative','quantitative_contextual','not_independently_defined'}, f'{key}: missing {mode} ROM classification')
            require(bool(r.get('qualification')), f'{key}: unqualified {mode} ROM')
            ids=r.get('observations',[])
            require(set(ids)<=set(observations), f'{key}: unknown ROM observation')
            if r.get('status')=='quantitative_contextual': require(bool(ids), f'{key}: empty quantitative ROM')
            for oid in ids:
                o=observations.get(oid,{})
                require(o.get('measured_scope')==p.get('measured_scope'), f'{key}: composite/other joint ROM misassigned')
                allowed={'active','functional'} if mode=='active' else {'passive','cadaver_passive'}
                require(o.get('mode') in allowed, f'{key}: active/passive evidence mixed')
    for key,a in assignments.items():
        if key not in joints: continue
        j=joints[key];p=profiles.get(a.get('profile_id'),{})
        require(bool(p), f'{key}: unknown mechanics profile')
        require(a.get('profile_id')==mechanics_profile(j), f'{key}: anatomically incompatible mechanics profile')
        for field in ['participants','side','role','variant']:
            require(a.get(field)==j.get(field), f'{key}: {field} differs from articulation inventory')
        require(a.get('anatomy_sources')==j.get('sources'), f'{key}: anatomy-source binding differs from inventory')
        require(a.get('frame_id')==frames[key]['frame_id'], f'{key}: joint-frame mismatch')
        expected=owner_dof.get(key,0)
        require(a.get('independent_command_dof')==expected, f'{key}: follower/contact gains independent actuator')
        require(a.get('coupled_group')==joint_groups[key], f'{key}: contact split from required command group')
        require((a.get('profile_id')=='fixed')==(j['role']=='FIXED'), f'{key}: fixed/moving mechanics contradiction')
        for oid in (a.get('rom_observation_overrides') or {}).get('active',[]):
            o=observations.get(oid,{})
            require(o.get('measured_scope')==p.get('measured_scope') and o.get('mode')=='active', f'{key}: wrong override scope/mode')
            if key.startswith('digit'): require(oid==key.rsplit('_',1)[0]+'_flexion', f'{key}: another digit ROM assigned')
    for key,o in observations.items():
        for field in ['measured_scope','motion','mode','statistic','sources','population','method','posture','load','locator','limitations']:
            require(bool(o.get(field)), f'{key}: missing measurement context {field}')
        require(set(o.get('sources',[]))<=set(sources), f'{key}: unknown measurement source')
        require(o.get('use_as_joint_limit') is False, f'{key}: study statistic used as joint limit')
        require(o.get('mode') in {'active','functional','passive','cadaver_passive','clinical_unspecified'}, f'{key}: unknown examination mode')
        require(o.get('unit') in {'degrees','mm'}, f'{key}: unsupported measurement units')
        vals=o.get('value',{})
        require(bool(vals), f'{key}: absent measurement')
        for field,value in vals.items():
            nums=value if isinstance(value,list) else [value]
            require(all(isinstance(v,(int,float)) and math.isfinite(v) for v in nums), f'{key}: nonfinite measurement')
            if isinstance(value,list): require(len(value)==2 and value[0]<=value[1], f'{key}: invalid interval')
        if o.get('statistic')=='mean_ci95': require('ci95_of_mean' in vals and 'observed_range' not in vals, f'{key}: mean CI mislabeled as population range')
    used={a.get('profile_id') for a in assignments.values()}
    require(used==set(profiles), 'Missing/unused mechanics profile')
    require(all(atlas.get('policy',{}).get(k) is True for k in ['no_universal_rom','no_individual_limits_from_mean_ci','not_available_is_not_zero','active_passive_not_interchangeable','shared_contact_not_independent_actuator']), 'Evidence policy missing')
    return errors

def validate_gaps(matrix, directory=DATA):
    """Recompute static findings from pinned inputs; never inspect or modify Blender."""
    import importlib.util
    root=directory.parent.parent
    path=root/'scripts/build_anatomical_rig_gap_matrix.py'
    spec=importlib.util.spec_from_file_location('gap_builder',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    expected=module.build_matrix(root)
    errors=[]
    for key in expected:
        if matrix.get(key)!=expected[key]: errors.append(f'Gap matrix stale/invalid: {key}')
    return errors

def main():
    data=json.loads((DATA/'adult_articulation_inventory.json').read_text())
    errors=validate_inventory(data)
    result={'gate':2,'scope':'inventory classification; no dynamic acceptance',
        'articulations':len(data['articulations']), 'families':dict(Counter(j['family'] for j in data['articulations'])),
        'unclassified_or_invalid':errors,'passed':not errors}
    frame_path=DATA/'joint_landmark_frame_atlas.json'
    if frame_path.exists():
        atlas=json.loads(frame_path.read_text())
        frame_errors=validate_frames(atlas,data)
        result['gate3']={'semantic_frames':len(atlas['frames']),'joint_assignments':len(atlas['joint_assignments']), 'errors':frame_errors, 'passed':not frame_errors, 'character_fitted':False}
        errors+=frame_errors
    movement_path=DATA/'whole_body_movement_atlas.json'
    if movement_path.exists():
        atlas=json.loads(movement_path.read_text())
        motion_errors=validate_movement(atlas,data)
        result['gate4']={'profiles':len(atlas['profiles']), 'joint_assignments':len(atlas['joint_assignments']),
                         'observations':len(atlas['observations']), 'errors':motion_errors,
                         'passed':not motion_errors, 'scope':'evidence structure/coverage; no dynamic acceptance'}
        errors+=motion_errors
    gap_path=DATA/'current_rig_anatomical_gap_matrix.json'
    if gap_path.exists():
        matrix=json.loads(gap_path.read_text())
        gap_errors=validate_gaps(matrix)
        result['gate5']={'bones':len(matrix['bones']),'joints':len(matrix['joints']),
                         'profiles':len(matrix['profiles']),'errors':gap_errors,'passed':not gap_errors,
                         'scope':'static gap comparison only; local character unverified'}
        errors+=gap_errors
    print(json.dumps(result,indent=2))
    return bool(errors)

if __name__=='__main__': raise SystemExit(main())
