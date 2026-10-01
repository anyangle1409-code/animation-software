#!/usr/bin/env python3
"""Compare original rest-mesh/weight snapshots; evidence, never approval."""
from __future__ import annotations
import argparse
import collections
import json
import math
import re
from pathlib import Path
from original_v1_production_control import digest,ensure_finite


def validate(s):
    ensure_finite(s)
    if s.get('schema_version')!=2:raise ValueError('schema 2 snapshot required; preserve older snapshots and export a new file')
    if s.get('rig_id')!='hgpt_canonical_v4_original':raise ValueError('canonical original rig identity required')
    if not re.fullmatch('[0-9a-f]{64}',s.get('candidate_sha256','')):raise ValueError('invalid snapshot candidate hash')
    if s.get('scene_unit_scale_length')!=1.0:raise ValueError('metre coordinate frame requires scene unit scale 1')
    if s.get('coordinate_space')!='raw mesh local Blender coordinates in metres':raise ValueError('unknown snapshot coordinate frame')
    for key in ('mesh_matrix_world','rig_matrix_world'):
        matrix=s[key]
        if len(matrix)!=4 or any(len(row)!=4 or any(type(x) not in (int,float) for x in row) for row in matrix):raise ValueError('invalid coordinate frame matrix')
    rest=s['rig_rest_bones'];names=[b['name'] for b in rest]
    if len(names)!=63 or len(set(names))!=63:raise ValueError('frozen 63-bone rest snapshot required')
    for bone in rest:
        if bone['parent'] is not None and bone['parent'] not in names:raise ValueError('unknown rig parent')
        if len(bone['head'])!=3 or len(bone['tail'])!=3 or any(type(x) not in (int,float) for x in bone['head']+bone['tail']):raise ValueError('invalid rest bone coordinates')
        if len(bone['matrix'])!=4 or any(len(row)!=4 or any(type(x) not in (int,float) for x in row) for row in bone['matrix']):raise ValueError('invalid rest bone matrix')
        if type(bone['use_deform']) is not bool:raise ValueError('invalid deformation bone flag')
    if not set(s['bone_names']).issubset(names):raise ValueError('unknown bone names in snapshot')
    if any(set(row)-set(s['bone_names']) for row in s['weights']):raise ValueError('unknown bone weights in snapshot')
    v=s['vertices']; w=s['weights']; r=s['regions']
    if not v or len(v)!=len(w) or len(v)!=len(r):raise ValueError('invalid snapshot row counts')
    if any(len(p)!=3 for p in v):raise ValueError('coordinates must have three components')
    for face in s['faces']:
        if len(face)<3 or any(type(i)!=int or not 0<=i<len(v) for i in face):raise ValueError('invalid face index')
    if any(not isinstance(row,dict) or any(not isinstance(x,(int,float)) or x<0 for x in row.values()) for row in w):raise ValueError('invalid raw weights')


def mirrored_bone(b):
    return b[:-2]+'_r' if b.endswith('_l') else b[:-2]+'_l' if b.endswith('_r') else b


def symmetry(s,pairs):
    position=[];weight=[]
    for a,b in pairs:
        if not (0<=a<len(s['vertices']) and 0<=b<len(s['vertices'])):raise ValueError('invalid mirror pair')
        p,q=s['vertices'][a],s['vertices'][b]
        position.append(math.dist([-p[0],p[1],p[2]],q)*1000)
        wa={mirrored_bone(n):x for n,x in s['weights'][a].items()};wb=s['weights'][b]
        weight.append(sum(abs(wa.get(n,0)-wb.get(n,0)) for n in wa.keys()|wb.keys()))
    return {'pair_count':len(pairs),'max_position_error_mm':max(position,default=None),
            'max_weight_L1_delta':max(weight,default=None),'coverage_vertices':len({v for p in pairs for v in p})}


def audit(before,after,policy):
    validate(before);validate(after);ensure_finite(policy)
    if policy.get('before_candidate_sha256')!=before['candidate_sha256'] or policy.get('candidate_sha256')!=after['candidate_sha256']:
        raise ValueError('policy candidate hashes must identify exact before and after sources')
    if (before['coordinate_space']!=after['coordinate_space'] or
        before['mesh_matrix_world']!=after['mesh_matrix_world'] or before['rig_matrix_world']!=after['rig_matrix_world']):
        raise ValueError('coordinate frame changed; local deltas are not comparable')
    if (sorted(before['rig_rest_bones'],key=lambda x:x['name'])!=sorted(after['rig_rest_bones'],key=lambda x:x['name']) or
        set(before['bone_names'])!=set(after['bone_names']) or before['left_x_sign']!=after['left_x_sign']):
        raise ValueError('frozen rig rest/deformation identity changed; preserve snapshots and diagnose')
    tolerance=policy.get('normalization_tolerance',1e-6);maximum=policy.get('max_influences',4)
    if type(tolerance) not in (int,float) or tolerance<0:raise ValueError('invalid normalization tolerance')
    if type(maximum) is not int or maximum<=0:raise ValueError('invalid maximum influence count')
    ids=policy.get('allowed_vertex_ids',[])
    if any(type(i) is not int or not 0<=i<len(after['vertices']) for i in ids) or len(ids)!=len(set(ids)):
        raise ValueError('invalid/duplicate edit policy vertex IDs')
    if not set(policy.get('allowed_bones',[])).issubset(before['bone_names']):raise ValueError('unknown allowed policy bone')
    if not set(policy.get('allowed_regions',[])).issubset(set(before['regions'])|set(after['regions'])):
        raise ValueError('unknown allowed policy region')
    bv,av=before['vertices'],after['vertices']
    topology=len(bv)!=len(av) or before['faces']!=after['faces']
    correspondence=not topology and policy.get('index_correspondence_confirmed') is True
    epsilon=float(policy.get('change_epsilon',1e-8))
    if not math.isfinite(epsilon) or epsilon<0:raise ValueError('invalid change epsilon')
    allowed_regions=set(policy.get('allowed_regions',[]));allowed_ids=set(policy.get('allowed_vertex_ids',[]))
    allowed_bones=set(policy.get('allowed_bones',[]))
    def permitted(i):
        return before['regions'][i] in allowed_regions and after['regions'][i] in allowed_regions and i in allowed_ids
    displacement=[math.dist(p,q)*1000 for p,q in zip(bv,av)] if correspondence else None
    moved=[i for i,x in enumerate(displacement) if x>epsilon*1000] if displacement is not None else None
    mesh={'vertex_count_before':len(bv),'vertex_count_after':len(av),'vertex_count_change':len(av)-len(bv),
          'face_count_before':len(before['faces']),'face_count_after':len(after['faces']),
          'face_count_change':len(after['faces'])-len(before['faces']),'topology_changed':topology,
          'correspondence_status':'CONFIRMED_INDEX' if correspondence else 'CORRESPONDENCE_REQUIRED',
          'vertices_moved':len(moved) if moved is not None else None,
          'max_displacement_mm':max(displacement,default=0) if displacement is not None else None,
          'mean_displacement_mm':sum(displacement)/len(displacement) if displacement is not None else None,
          'mean_moved_displacement_mm':sum(displacement[i] for i in moved)/len(moved) if moved else 0 if moved==[] else None,
          'affected_regions':dict(collections.Counter(after['regions'][i] for i in moved)) if moved is not None else None,
          'unexpected_vertex_ids':[i for i in moved if not permitted(i)] if moved is not None else None,
          'region_label_changes':[i for i,(a,b) in enumerate(zip(before['regions'],after['regions'])) if a!=b] if correspondence else None}
    changed=[];bones=set();max_delta=0;unexpected_bones=set()
    if correspondence:
        for i,(a,b) in enumerate(zip(before['weights'],after['weights'])):
            differences={n:abs(a.get(n,0)-b.get(n,0)) for n in a.keys()|b.keys()}
            rowbones={n for n,d in differences.items() if d>epsilon}
            if rowbones:changed.append(i);bones|=rowbones;unexpected_bones|=(rowbones-allowed_bones)
            max_delta=max(max_delta,max(differences.values(),default=0))
    errors=[abs(sum(w.values())-1) for w in after['weights']]
    influences=[sum(x>epsilon for x in w.values()) for w in after['weights']]
    cross=[];left=after.get('left_x_sign')
    if left not in (-1,1):raise ValueError('snapshot must state rig-derived left_x_sign')
    for i,(p,w) in enumerate(zip(av,after['weights'])):
        side='l' if p[0]*left>epsilon else 'r' if p[0]*left<-epsilon else None
        if side and any(n.endswith('_'+('r' if side=='l' else 'l')) and x>epsilon for n,x in w.items()):cross.append(i)
    pairs=before.get('mirror_pairs',[]) if correspondence else after.get('mirror_pairs',[])
    after_sym=symmetry(after,pairs); before_sym=symmetry(before,before.get('mirror_pairs',[]))
    mesh['symmetry_before']=before_sym;mesh['symmetry_after']=after_sym
    mesh['symmetry_delta_mm']=(after_sym['max_position_error_mm']-before_sym['max_position_error_mm']) if before_sym['max_position_error_mm'] is not None and after_sym['max_position_error_mm'] is not None and correspondence else None
    weights={'comparison_status':'CONFIRMED_INDEX' if correspondence else 'CORRESPONDENCE_REQUIRED',
             'vertices_changed':len(changed) if correspondence else None,'affected_bones':sorted(bones) if correspondence else None,
             'max_weight_delta':max_delta if correspondence else None,'normalization_max_error':max(errors),
             'unnormalized_vertex_ids':[i for i,e in enumerate(errors) if e>policy.get('normalization_tolerance',1e-6)],
             'max_influence_count':max(influences),'over_influence_vertex_ids':[i for i,n in enumerate(influences) if n>policy.get('max_influences',4)],
             'cross_side_vertex_ids':cross,'affected_regions':dict(collections.Counter(after['regions'][i] for i in changed)) if correspondence else None,
             'unexpected_vertex_ids':[i for i in changed if not permitted(i)] if correspondence else None,
             'unexpected_bones':sorted(unexpected_bones) if correspondence else None,'symmetry':after_sym}
    return {'schema_version':2,'before_candidate_sha256':before['candidate_sha256'],
            'candidate_sha256':after['candidate_sha256'],'mesh':mesh,'weights':weights,
            'comparison_identity':'VERIFIED_COORDINATE_FRAMES_AND_FROZEN_RIG_REST',
            'policy_limits':{'change_epsilon':epsilon,'normalization_tolerance':tolerance,'max_influences':maximum},
            'production_approved':False,'purpose':'change evidence only; no approval or gate relaxation'}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('before',type=Path);ap.add_argument('after',type=Path)
    ap.add_argument('--policy',type=Path,required=True);ap.add_argument('--json-out',type=Path,required=True);args=ap.parse_args()
    if args.json_out.exists():raise SystemExit('STOP — audit output already exists')
    try:
        inputs=[json.loads(p.read_text(encoding='utf-8')) for p in (args.before,args.after,args.policy)]
        result=audit(*inputs)
        result['input_hashes']={str(p):digest(p) for p in (args.before,args.after,args.policy)}
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print('CHANGE AUDIT WRITTEN — evidence only',args.json_out);return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:print('STOP — '+str(exc));return 2
if __name__=='__main__':raise SystemExit(main())
