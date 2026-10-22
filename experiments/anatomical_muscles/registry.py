"""Bilateral scientific seed expansion and fail-closed binding validation.

L/R mean anatomical sides, NEVER inferred runtime suffixes (F-SIDE-001).
Neighbor membership denotes shared research interaction, not proven contact.
"""
import argparse
import copy
import json
import re
from pathlib import Path
from .kernel import vec, scalar

ROOT=Path(__file__).resolve().parents[2]
SEED=ROOT/'docs/ORIGINAL_V1_MUSCLE_REGISTRY_SEED_20261022.json'
PILOT_REGIONS={'shoulder','scapula','chest','back','pelvis','thigh'}


def expand(seed):
    muscles=[]
    interactions=[]
    for side in ('L','R'):
        for rule in seed['interaction_rules']:
            item=copy.deepcopy(rule)
            item['id']='hgpt.interaction.'+rule['id']+'.'+side
            item['muscle_ids']=['hgpt.muscle.'+x+'.'+side for x in rule['muscle_ids']]
            interactions.append(item)
        for original in seed['muscles']:
            mid='hgpt.muscle.'+original['id']+'.'+side
            related=[x for x in interactions if mid in x['muscle_ids']]
            muscles.append({
                'id':mid,'seed_id':original['id'],'side':side,
                'identity':{'namespace':'hgpt.muscle','anatomical_name':original['id'],
                            'functional_head_id':original['id'],'immutable':True,'deprecated_aliases':[original['id']+'.'+side]},
                'region':original['region'],'depth':original['depth'],
                'pilot':original['region'] in PILOT_REGIONS or original['id'] in {'biceps_brachii_long','triceps_long'},
                'origin':{'description':original['origin_landmark'],'anatomical_landmark_id':None},
                'insertion':{'description':original['insertion_landmark'],'anatomical_landmark_id':None},
                'joints_crossed':original['joints_crossed'],'actions':original['actions'],
                'relationships':{'joint_ids':['hgpt.joint.'+j for j in original['joints_crossed']],
                                 'neighbor_ids':[]},
                'neighbors':sorted({x for rule in related for x in rule['muscle_ids'] if x!=mid}),
                'layer_relations_status':'requires_local_anatomy_review',
                'path':{'mode':'reviewed_bone_local_via_points','wrap_targets':None,'status':'unresolved'},
                'tissue':{'contractile_belly':True,'tendon_lengths_m':None,'rest_volume_m3':None,
                          'note':'Tendon/aponeurosis/fascia routing must be authored separately; no fitted numeric parameters.'},
                'contraction':{'length_driver':'evaluated_attachment_path','activation_driver':'explicit_exercise_rule',
                               'supported_states':['shortening','lengthening','near_isometric','variable'],
                               'activation_independent_of_pose':True},
                'activation':{'mode':'explicit_visual_channel','default':0,'force_claim':False},
                'skin':{'mask':None,'direct_transfer_allowed':original['depth']=='superficial',
                        'rest_relative_only':True},
                'provenance':{'url':original['reference_url'],'confidence':original['anatomy_status'],
                              'license':'reference_only_no_asset_redistribution_reviewed'},
                'binding':None,'status':'semantic_seed_only'})
            muscles[-1]['relationships']['neighbor_ids']=muscles[-1]['neighbors']
    return {'schema_version':1,'experimental_only':True,'PT_MODEL_VERSION':'1.0',
            'coordinate_convention':'SI metres, bone-local anchors, explicit anatomical-side mapping',
            'muscles':muscles,'interactions':interactions}


def validate(data):
    errors=[]
    if data.get('schema_version')!=1 or data.get('experimental_only') is not True or data.get('PT_MODEL_VERSION')!='1.0':
        errors.append('Invalid experiment header')
    muscles=data.get('muscles',[])
    ids=[m.get('id') for m in muscles]
    if not muscles or len(ids)!=len(set(ids)): errors.append('Empty or duplicate muscle IDs')
    idset=set(ids)
    for m in muscles:
        mid=m.get('id','')
        side=m.get('side')
        if side not in ('L','R') or mid!='hgpt.muscle.'+m.get('seed_id','')+'.'+str(side): errors.append(f'{mid}: side identity')
        other='hgpt.muscle.'+m.get('seed_id','')+'.'+('R' if side=='L' else 'L')
        if other not in idset: errors.append(f'{mid}: missing contralateral entry')
        if m.get('identity',{}).get('immutable') is not True: errors.append(f'{mid}: mutable identity')
        if m.get('depth') not in ('deep','intermediate','superficial'): errors.append(f'{mid}: depth')
        if not m.get('joints_crossed'): errors.append(f'{mid}: joint crossings')
        for end in ('origin','insertion'):
            if not m.get(end,{}).get('description'): errors.append(f'{mid}: {end} missing')
        p=m.get('provenance',{})
        if not p.get('url','').startswith('https://') or not p.get('confidence') or not p.get('license'):
            errors.append(f'{mid}: provenance')
        for n in m.get('neighbors',[]):
            if n not in idset or n==mid or not n.endswith('.'+str(side)): errors.append(f'{mid}: invalid neighbor')
        if m.get('contraction',{}).get('activation_independent_of_pose') is not True: errors.append(f'{mid}: contraction coupling')
        if m.get('relationships',{}).get('neighbor_ids')!=m.get('neighbors'): errors.append(f'{mid}: neighbor relationship mismatch')
        if m.get('activation',{}).get('mode')!='explicit_visual_channel': errors.append(f'{mid}: activation mode')
        if m.get('activation',{}).get('force_claim') is not False: errors.append(f'{mid}: force claim')
    ruleids=[]
    for rule in data.get('interactions',[]):
        ruleids.append(rule['id'])
        if not rule.get('muscle_ids') or any(x not in idset for x in rule['muscle_ids']): errors.append('Unresolved interaction')
    if len(ruleids)!=len(set(ruleids)): errors.append('Duplicate interaction IDs')
    return errors


def binding_errors(muscle, bone_ids):
    b=muscle.get('binding')
    if not b: return ['No reviewed binding']
    errors=[]
    anchors=b.get('anchors',[])
    if len(anchors)<2: errors.append('Need origin and insertion anchors')
    for a in anchors:
        if a.get('bone') not in bone_ids: errors.append('Unknown actual rig bone')
        try: vec(a.get('local_m'))
        except (ValueError,TypeError): errors.append('Invalid local coordinates')
    review=b.get('review',{})
    if not review.get('reviewer') or not review.get('evidence'): errors.append('Missing local review evidence')
    if not re.fullmatch('[0-9a-f]{64}',b.get('source_sha256','')): errors.append('Missing source hash')
    if b.get('anatomical_side')!=muscle['side']: errors.append('Unverified anatomical side')
    if b.get('wrap_reviewed') is not True: errors.append('Path wrapping review incomplete')
    try:
        weight=scalar(b.get('direct_skin_weight'),0,1)
        if weight and muscle['depth']!='superficial': errors.append('Deep/intermediate direct skin transfer blocked')
        if weight and not b.get('skin_mask'): errors.append('Missing explicit skin mask')
    except ValueError: errors.append('Invalid direct skin weight')
    return errors


def readiness(data,bone_ids):
    errors=validate(data)
    if errors: raise ValueError(errors)
    return {m['id']:errors for m in data['muscles'] if (errors:=binding_errors(m,set(bone_ids)))}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    data=expand(json.loads(SEED.read_text()))
    errors=validate(data)
    if errors: raise ValueError(errors)
    # Exclusive output: do not replace an authored registry with regenerated seed.
    with args.out.open('x') as f: json.dump(data,f,indent=2); f.write('\n')
    print(json.dumps({'semantic_records':len(data['muscles']),'pilot_records':sum(m['pilot'] for m in data['muscles']),
                      'unresolved_bindings':len(readiness(data,[])),'native_validation':'BLOCKED'}))

if __name__=='__main__': main()
