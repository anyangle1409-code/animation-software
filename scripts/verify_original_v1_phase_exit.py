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
from original_v1_phase9_production_validation import verify_receipt as verify_phase9_validation_receipt

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


PHASE5_REGION_CHECKS=[
 ('anatomy_5A_torso','5A'),('anatomy_5B_shoulders','5B'),('anatomy_5C_arms','5C'),
 ('anatomy_5D_hands','5D'),('anatomy_5E_pelvis_legs','5E'),('anatomy_5F_feet','5F'),
 ('anatomy_5G_head_neck','5G')]


def verify_phase5_region_receipts(root,checks,candidate_sha):
    """Bind Phase 5 exit to the actual ordered 5A->5G verified regional receipts."""
    issues=[];by_id={x.get('id'):x for x in checks if isinstance(x,dict)}
    control_path=root/'ORIGINAL_V1_PRODUCTION_CONTROL.json'
    if not control_path.is_file():
        return ['Phase 5 requires production-control Phase 4 freeze identity']
    try:
        control=json.loads(control_path.read_text(encoding='utf-8-sig'))
        freeze_sha=((control.get('phase_completion_records') or {}).get('4') or {}).get('candidate_sha256')
        if not re.fullmatch('[0-9a-f]{64}',str(freeze_sha or '')):
            issues.append('recorded Phase 4 freeze candidate SHA missing/invalid')
    except (OSError,ValueError,TypeError,json.JSONDecodeError) as exc:
        return ['Phase 5 production-control identity unreadable: '+str(exc)]

    previous=None;freeze_seen=None;epoch_seen=None
    for check_id,region in PHASE5_REGION_CHECKS:
        check=by_id.get(check_id) or {}
        candidates=[]
        for ref in check.get('evidence',[]) if isinstance(check.get('evidence'),list) else []:
            try:
                p=safe_path(root,ref['path'])
                if p.suffix.lower()!='.json' or digest(p)!=ref.get('sha256'): continue
                data=json.loads(p.read_text(encoding='utf-8-sig'))
                if data.get('contract_status')=='REGION_EVIDENCE_VERIFIED' and data.get('region')==region:
                    candidates.append((p,ref,data))
            except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError):
                continue
        if len(candidates)!=1:
            issues.append(f'{check_id}: exactly one verified {region} regional receipt required')
            previous=None
            continue
        receipt_path,receipt_ref,receipt=candidates[0]
        if (receipt.get('schema_version')!=1 or receipt.get('phase')!=5 or
            receipt.get('phase_complete') is not False or receipt.get('production_approved') is not False or
            receipt.get('issues') not in ([],None)):
            issues.append(f'{check_id}: regional receipt contract differs')
        plan_ref=receipt.get('plan') or {}
        try:
            plan_path=safe_path(root,plan_ref['path'])
            if plan_ref.get('path')!='ORIGINAL_V1_PHASE5_ANATOMY_EXECUTION_PLAN.json' or digest(plan_path)!=plan_ref.get('sha256'):
                issues.append(f'{check_id}: Phase 5 execution-plan identity differs')
        except (OSError,ValueError,KeyError,TypeError):
            issues.append(f'{check_id}: Phase 5 execution-plan identity missing')
        if not re.fullmatch('[0-9a-f]{40}',str(receipt.get('source_git_commit',''))):
            issues.append(f'{check_id}: regional receipt source Git commit missing/invalid')
        rsha=receipt.get('candidate_sha256')
        if not re.fullmatch('[0-9a-f]{64}',str(rsha or '')):
            issues.append(f'{check_id}: regional candidate SHA invalid')
        rr=receipt.get('region_report') or {}
        try:
            report_path=safe_path(root,rr['path'])
            if digest(report_path)!=rr.get('sha256'): raise ValueError('region report hash differs')
            report=json.loads(report_path.read_text(encoding='utf-8-sig'))
            if (report.get('schema_version')!=1 or report.get('phase')!=5 or report.get('region')!=region or
                report.get('status')!='REGION_EVIDENCE_COMPLETE' or report.get('candidate_sha256')!=rsha or
                report.get('phase_complete') is not False or report.get('production_approved') is not False):
                issues.append(f'{check_id}: regional report identity/contract differs')
            rfreeze=report.get('development_freeze_candidate_sha256')
            epoch=(report.get('active_epoch_baseline_revision'),report.get('active_epoch_baseline_candidate_sha256'))
            if not isinstance(epoch[0],str) or not epoch[0] or not re.fullmatch('[0-9a-f]{64}',str(epoch[1] or '')):
                issues.append(f'{check_id}: active epoch baseline identity missing/invalid')
            if rfreeze!=freeze_sha: issues.append(f'{check_id}: Phase 4 freeze SHA differs from production control')
            if freeze_seen is None: freeze_seen=rfreeze
            elif rfreeze!=freeze_seen: issues.append(f'{check_id}: development-freeze identity changed within Phase 5')
            if epoch_seen is None: epoch_seen=epoch
            elif epoch!=epoch_seen: issues.append(f'{check_id}: active epoch baseline changed within Phase 5')
            prev_ref=report.get('previous_region_receipt')
            if previous is None:
                if region=='5A':
                    if prev_ref not in (None,{}): issues.append('anatomy_5A_torso: 5A must not reference a previous region receipt')
                    if report.get('parent_candidate_sha256')!=freeze_sha:
                        issues.append('anatomy_5A_torso: 5A parent must equal recorded Phase 4 freeze candidate')
                elif region!='5A':
                    issues.append(f'{check_id}: preceding verified region receipt unavailable')
            else:
                prev_path,_prev_ref,prev_receipt=previous
                expected_ref={'path':prev_path.relative_to(root.resolve()).as_posix(),'sha256':digest(prev_path)}
                if prev_ref!=expected_ref:
                    issues.append(f'{check_id}: previous-region receipt reference differs from exact prior receipt')
                if report.get('parent_candidate_sha256')!=prev_receipt.get('candidate_sha256'):
                    issues.append(f'{check_id}: parent candidate does not equal prior regional candidate')
        except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
            issues.append(f'{check_id}: regional report invalid: {exc}')
        previous=(receipt_path,receipt_ref,receipt)

    if previous is not None and previous[2].get('candidate_sha256')!=candidate_sha:
        issues.append('Phase 5 exit candidate must equal final 5G regional candidate')
    return list(dict.fromkeys(issues))



def verify_phase9_validation_binding(root,checks,candidate_sha):
    """All five Phase 9 exit checks must bind one identical verified Phase 9 receipt."""
    issues=[];by_id={x.get('id'):x for x in checks if isinstance(x,dict)}
    receipt_keys=[];receipt_data={}
    for check_id in REQUIRED_CHECKS['9']:
        check=by_id.get(check_id) or {}
        matches=[]
        for item in check.get('evidence',[]) if isinstance(check.get('evidence'),list) else []:
            try:
                if not isinstance(item,dict) or not re.fullmatch('[0-9a-f]{64}',str(item.get('sha256',''))):
                    continue
                p=safe_path(root,item['path'])
                if p.suffix.lower()!='.json' or digest(p)!=item['sha256']:
                    continue
                data=json.loads(p.read_text(encoding='utf-8-sig'))
                if (data.get('phase')==9 and data.get('candidate_sha256')==candidate_sha and
                    data.get('contract_status') in ('PHASE9_VALIDATION_VERIFIED','PHASE9_VALIDATION_BLOCKED')):
                    matches.append((p,item,data))
            except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError):
                continue
        if len(matches)!=1:
            issues.append(check_id+': exactly one candidate-bound Phase 9 validation receipt required')
            continue
        p,item,data=matches[0]
        key=(p.resolve().as_posix(),item['sha256'])
        receipt_keys.append(key);receipt_data[key]=(p,data)
    if receipt_keys and len(set(receipt_keys))!=1:
        issues.append('all Phase 9 checks must reference the same Phase 9 validation receipt')
    if len(receipt_keys)==len(REQUIRED_CHECKS['9']) and len(set(receipt_keys))==1:
        _p,data=receipt_data[receipt_keys[0]]
        issues.extend('phase9_validation: '+x for x in verify_phase9_validation_receipt(root,data,candidate_sha))
    return list(dict.fromkeys(issues))

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
    if phase=='5':
        issues += verify_phase5_region_receipts(root,checks,candidate_sha)
    if phase=='9':
        issues += verify_phase9_validation_binding(root,checks,candidate_sha)
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
