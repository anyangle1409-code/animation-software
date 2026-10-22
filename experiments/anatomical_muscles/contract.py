"""Validate and sample reusable exercise-to-muscle movement contracts.

Joint targets, path-length state and visual activation are independent inputs.
The contract is an animation authoring prior, not EMG, force or medical advice.
"""
import math

ROLES={'agonist','antagonist','synergist','stabilizer'}
LENGTH_STATES={'shortening','lengthening','near_isometric','variable'}


def _finite(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)


def _range(value,low=None,high=None):
    if not isinstance(value,list) or len(value)!=2 or not all(_finite(x) for x in value): return False
    return value[0]<=value[1] and (low is None or value[0]>=low) and (high is None or value[1]<=high)


def validate_library(library,muscle_registry):
    errors=[]
    muscles=muscle_registry.get('muscles',[])
    muscle_list=[m.get('id') for m in muscles]
    muscle_ids=set(muscle_list)
    if len(muscle_list)!=len(muscle_ids): errors.append('Duplicate muscle registry IDs')
    if any(not str(x).startswith('hgpt.muscle.') for x in muscle_ids): errors.append('Invalid permanent muscle ID')
    if not muscle_ids: errors.append('Muscle registry is empty')
    semantics=library.get('activation_semantics',{})
    if semantics.get('derive_from_pose') is not False: errors.append('Activation must not derive from pose')
    if semantics.get('meaning')!='visual_relative_estimate_not_emg_force_or_clinical_prescription': errors.append('Activation meaning missing')
    sources={s.get('id') for s in library.get('sources',[]) if s.get('url','').startswith(('https://','docs/'))}
    if not sources: errors.append('Source ledger missing')
    exercises=library.get('exercises',[]); exercise_ids=[]
    if not exercises: errors.append('Exercise library empty')
    for exercise in exercises:
        eid=exercise.get('id',''); exercise_ids.append(eid)
        if not eid.startswith('hgpt.exercise.') or not eid.endswith('.v1'): errors.append(f'{eid}: invalid exercise ID')
        if not exercise.get('instruction'): errors.append(f'{eid}: instruction missing')
        if any(x not in sources for x in exercise.get('source_ids',[])) or not exercise.get('source_ids'): errors.append(f'{eid}: sources unresolved')
        phase_ids=[]
        for phase in exercise.get('phases',[]):
            pid=phase.get('id',''); phase_ids.append(pid)
            if not pid or not phase.get('joint_targets'): errors.append(f'{eid}/{pid}: phase or joints missing')
            joint_ids=[j.get('joint_id') for j in phase.get('joint_targets',[])]
            if len(joint_ids)!=len(set(joint_ids)): errors.append(f'{eid}/{pid}: duplicate joint')
            for joint in phase.get('joint_targets',[]):
                if not joint.get('joint_id','').startswith('hgpt.joint.'): errors.append(f'{eid}/{pid}: invalid joint ID')
                if not _range(joint.get('from_deg')) or not _range(joint.get('to_deg')): errors.append(f'{eid}/{pid}: invalid angle range')
                if joint.get('activation_driver') is not False: errors.append(f'{eid}/{pid}: pose cannot drive activation')
            seen=set()
            for rule in phase.get('muscles',[]):
                mid=rule.get('muscle_id'); seen.add(mid)
                if mid not in muscle_ids: errors.append(f'{eid}/{pid}: unknown muscle {mid}')
                if rule.get('role') not in ROLES: errors.append(f'{eid}/{pid}/{mid}: invalid role')
                if rule.get('length_change') not in LENGTH_STATES: errors.append(f'{eid}/{pid}/{mid}: invalid length state')
                activation=rule.get('activation_estimate',{})
                if activation.get('kind')!='normalized_visual_estimate' or activation.get('source')!='exercise_phase_rule': errors.append(f'{eid}/{pid}/{mid}: invalid activation semantics')
                if not _range(activation.get('range'),0,1): errors.append(f'{eid}/{pid}/{mid}: invalid activation range')
                if rule.get('deformation',{}).get('mode') not in {'path_length_plus_activation','activation_only','stabilization_tone'}: errors.append(f'{eid}/{pid}/{mid}: deformation missing')
                skin=rule.get('skin_response',{})
                if skin.get('mode') not in {'region_mask_capped_blend','no_direct_skin_transfer'}: errors.append(f'{eid}/{pid}/{mid}: skin response missing')
                if skin.get('mode')=='region_mask_capped_blend' and not str(skin.get('mask_id','')).startswith('hgpt.skinmask.'): errors.append(f'{eid}/{pid}/{mid}: skin mask missing')
                if skin.get('mode')=='no_direct_skin_transfer' and skin.get('mask_id') is not None: errors.append(f'{eid}/{pid}/{mid}: unexpected skin mask')
            if len(seen)!=len(phase.get('muscles',[])): errors.append(f'{eid}/{pid}: duplicate muscle')
            stabilizers={r.get('muscle_id') for r in phase.get('muscles',[]) if r.get('role')=='stabilizer'}
            declared=set(phase.get('stabilization',{}).get('muscle_ids',[]))
            if not stabilizers or declared!=stabilizers: errors.append(f'{eid}/{pid}: stabilization mismatch')
        if not phase_ids or len(phase_ids)!=len(set(phase_ids)): errors.append(f'{eid}: phases empty or duplicated')
    if len(exercise_ids)!=len(set(exercise_ids)): errors.append('Duplicate exercise IDs')
    return errors


def sample_phase(exercise,phase_id,progress,activation_scale=1):
    if not _finite(progress) or not 0<=progress<=1: raise ValueError('progress must be within 0..1')
    if not _finite(activation_scale) or not 0<=activation_scale<=1: raise ValueError('activation_scale must be within 0..1')
    try: phase=next(x for x in exercise['phases'] if x['id']==phase_id)
    except (KeyError,StopIteration): raise ValueError('unknown phase')
    joints=[]
    for joint in phase['joint_targets']:
        angle=[joint['from_deg'][i]+progress*(joint['to_deg'][i]-joint['from_deg'][i]) for i in range(2)]
        joints.append({'joint_id':joint['joint_id'],'angle_deg':angle,'coordinate':joint['coordinate']})
    muscles=[]
    for rule in phase['muscles']:
        lo,hi=rule['activation_estimate']['range']
        muscles.append({'muscle_id':rule['muscle_id'],'role':rule['role'],'length_change':rule['length_change'],
                        'visual_activation':activation_scale*((lo+hi)/2),
                        'visual_activation_range':[activation_scale*lo,activation_scale*hi],
                        'deformation':rule['deformation'],'skin_response':rule['skin_response']})
    return {'exercise_id':exercise['id'],'phase_id':phase_id,'progress':progress,
            'joint_targets':joints,'muscles':muscles,
            'activation_source':'explicit_exercise_rule_scaled_by_caller',
            'claims':{'force':False,'emg':False,'clinical_accuracy':False}}
