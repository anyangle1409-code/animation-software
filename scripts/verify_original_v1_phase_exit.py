#!/usr/bin/env python3
"""Validate Phase 4–11 exit-record contracts; never approves production or assets.

This verifies explicit check coverage and exact source references. It does not
replace the referenced domain tests or judge anatomy. Phase 12 is a separate gate.
"""
from __future__ import annotations
import argparse
from datetime import datetime
import json
from pathlib import Path
import re
from original_v1_production_control import ROOT,build,digest,ensure_finite
from verify_original_v1_production_promotion import safe_path

REQUIRED_CHECKS={
 '4':['development_zero_failures','no_unresolved_regressions','replay_matches_primary',
      'frozen_rig_baseline_gates','source_lineage_verified','published_review_snapshot','freeze_record_pinned'],
 '5':['anatomy_5A_torso','anatomy_5B_shoulders','anatomy_5C_arms','anatomy_5D_hands',
      'anatomy_5E_pelvis_legs','anatomy_5F_feet','anatomy_5G_head_neck',
      'mesh_weight_audits','deformation_regression_checks','published_review_snapshots'],
 '6':['manifold_surface','normals','degenerate_faces','joint_support','symmetry',
      'topology_weight_audit','deformation_regression_checks'],
 '7':['original_garment_provenance','dressed_deformation','coverage_clearance',
      'bare_dressed_equivalence','published_review_snapshot'],
 '8':['owned_material_sources','stable_presentation_capture','readable_application_views',
      'no_concealed_body_failures','published_review_snapshot'],
 '9':['production_target_zero_failures','continuous_motion_ranges','bilateral_grip_floor_contact',
      'intersection_classification','final_body_clothing_hashes'],
 '10':['real_engine_exercises','smooth_human_motion','canonical_rig_binding','bare_dressed_equivalence',
       'export_round_trip','standalone_runtime_audit'],
 '11':['deterministic_capture','automatic_visual_checks','pose_camera_region_coverage',
       'first_party_reference_policy','coverage_limits_recorded','candidate_runtime_binding']}


def verify_exit(root,phase,packet,candidate_sha):
    phase=str(phase);issues=[]
    if phase=='12':return ['Phase 12 requires the separate controlled production promotion workflow']
    if phase not in REQUIRED_CHECKS:return ['unsupported intermediate phase exit: '+phase]
    if not isinstance(packet,dict):return ['phase exit packet must be an object']
    try:ensure_finite(packet)
    except ValueError as exc:issues.append(str(exc))
    if (packet.get('schema_version')!=1 or str(packet.get('phase'))!=phase or
        packet.get('candidate_sha256')!=candidate_sha or packet.get('status')!='PASS' or
        packet.get('production_approved') is not False):issues.append('phase exit identity/schema/PASS contract differs')
    if not re.fullmatch('[0-9a-f]{64}',str(candidate_sha)):issues.append('invalid expected candidate SHA')
    if not re.fullmatch('[0-9a-f]{40}',str(packet.get('source_git_commit',''))):issues.append('exact source git commit required')
    if not isinstance(packet.get('command'),str) or not packet['command'].strip():issues.append('executed validation command required')
    try:
        stamp=datetime.fromisoformat(packet.get('evidence_timestamp','').replace('Z','+00:00'))
        if stamp.tzinfo is None:raise ValueError('timestamp timezone required')
    except (ValueError,AttributeError,TypeError):issues.append('ISO evidence timestamp with timezone required')
    if packet.get('owner_review') not in ('pending','accepted') or packet.get('blocking') is not False:
        issues.append('routine owner review must remain explicit and non-blocking; acceptance is never inferred')
    if phase in ('10','11') and not re.fullmatch('[0-9a-f]{40}',str(packet.get('target_runtime_commit',''))):
        issues.append('exact target runtime commit required')
    checks=packet.get('checks',[])
    if not isinstance(checks,list) or any(not isinstance(x,dict) for x in checks):return issues+['invalid phase check rows']
    names=[x.get('id') for x in checks]
    if any(not isinstance(x,str) for x in names):return issues+['check IDs must be strings']
    if len(names)!=len(set(names)):issues.append('duplicate phase check IDs')
    missing=set(REQUIRED_CHECKS[phase])-set(names)
    if missing:issues.append('missing phase exit checks: '+', '.join(sorted(missing)))
    for check in checks:
        name=check.get('id','unknown')
        if check.get('passed') is not True:issues.append(name+': failing/unknown check')
        refs=check.get('evidence',[])
        if not isinstance(refs,list) or not refs:issues.append(name+': source evidence required');continue
        for ref in refs:
            try:
                if not isinstance(ref,dict) or not re.fullmatch('[0-9a-f]{64}',str(ref.get('sha256',''))):raise ValueError('path/hash reference required')
                p=safe_path(root,ref['path'])
                if digest(p)!=ref['sha256']:raise ValueError('source evidence hash differs')
            except (OSError,ValueError,KeyError,TypeError) as exc:issues.append(name+': '+str(exc))
    return list(dict.fromkeys(issues))


def make_template(phase,state):
    phase=str(phase)
    if phase not in REQUIRED_CHECKS:raise ValueError('Phase 4–11 templates only; Phase 12 uses the final promotion workflow')
    return {'schema_version':1,'phase':int(phase),'candidate_sha256':state['last_known_candidate_sha256'],
            'status':'INCOMPLETE','production_approved':False,'source_git_commit':None,
            'evidence_timestamp':None,'command':None,'owner_review':'pending','blocking':False,
            **({'target_runtime_commit':None} if phase in ('10','11') else {}),
            'checks':[{'id':name,'passed':None,'evidence':[]} for name in REQUIRED_CHECKS[phase]],
            'source_context':{'candidate':state['current_candidate'],'development_failure_count':state['development_failure_count'],
                'pinned_baseline':state['pinned_baseline']['revision'],'next_action':state['next_action']['action']},
            'note':'Template only; no checks executed. Refresh candidate identity, command/commit/time and actual source hashes after executing every required test. Never turn placeholders into PASS assertions.'}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('packet',type=Path,nargs='?');ap.add_argument('--phase',required=True)
    ap.add_argument('--template',action='store_true',help='Create an INCOMPLETE packet shape, not an exit decision')
    ap.add_argument('--json-out',type=Path);args=ap.parse_args();issues=[]
    try:
        state,_=build(ROOT)
        if args.template:
            if args.packet:raise ValueError('template mode does not consume a gate packet')
            result=make_template(args.phase,state)
            if args.json_out:
                if args.json_out.exists():raise ValueError('template output collision; preserve existing files')
                args.json_out.parent.mkdir(parents=True,exist_ok=True)
                args.json_out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
            print(json.dumps(result,indent=2));print('INCOMPLETE TEMPLATE ONLY — no check passed or phase completed')
            return 0
        if args.packet is None:raise ValueError('packet required unless --template is specified')
        packet=json.loads(args.packet.read_text(encoding='utf-8-sig'))
        issues=verify_exit(ROOT,args.phase,packet,state['last_known_candidate_sha256'])
        if state['incomplete_candidates']:issues.append('newer incomplete candidate work remains')
        if state['candidate_state']=='rejected':issues.append('candidate is rejected')
        phase=int(args.phase)
        if phase==4 and (state['development_failure_count'] or state['unresolved_regressions']):
            issues.append('development blockers or strict regressions remain; freeze is refused')
        if 4<=phase<=11 and state['phases'][str(phase-1)]['state']!='complete':issues.append('preceding phase is incomplete')
    except (OSError,ValueError,KeyError,TypeError) as exc:issues.append(str(exc))
    result={'schema_version':1,'phase':args.phase,'contract_status':'REFUSED' if issues else 'EXIT_RECORD_VERIFIED',
            'production_approved':False,'issues':issues,
            'note':'Source/contract verification only. Run all domain tests; do not infer anatomy quality or owner acceptance. No shared state is modified.'}
    if args.json_out:
        if args.json_out.exists():raise SystemExit('STOP — exit verification output collision')
        args.json_out.parent.mkdir(parents=True,exist_ok=True);args.json_out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2));return 1 if issues else 0

if __name__=='__main__':raise SystemExit(main())
