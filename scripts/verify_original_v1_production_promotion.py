#!/usr/bin/env python3
"""Fail-closed future Phase 12 eligibility check; never changes approval flags.

A passing packet is evidence for a controlled owner-authorised release operation,
not an optimiser's power to promote. This verifier is not an owner identity service.
"""
from __future__ import annotations
import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from original_v1_production_control import ROOT,build,digest,evaluate,ensure_finite

REQUIRED_GATES={
    'provenance':['blank_source_lineage','candidate_operation_history','no_legacy_transfer'],
    'first_party_audit':['all_asset_sources_owned','no_external_content'],
    'development_deformation':['full_required_coverage','zero_failures','regressions_resolved'],
    'production_deformation':['full_required_coverage','zero_failures','continuous_motion'],
    'anatomy':['primary_form','secondary_form','all_regions_reviewed'],
    'topology':['manifold','normals','degenerate_faces','joint_support','symmetry'],
    'clothing':['original_garment_provenance','dressed_deformation','coverage_clearance'],
    'grip_contact':['bilateral_handles','floor_contact','original_measured_frames'],
    'runtime_animation':['real_engine_exercises','smooth_motion','export_round_trip'],
    'automated_qa':['deterministic_capture','visual_checks','coverage_limits'],
    'standalone_release':['runtime_dependency_audit','asset_allowlist','release_audit']}


def safe_path(root,name):
    p=Path(name)
    if p.is_absolute() or '..' in p.parts:raise ValueError('evidence path is outside repository')
    resolved=(root/p).resolve()
    if not resolved.is_relative_to(root.resolve()):raise ValueError('evidence path is outside repository')
    return resolved


def verified_report(root,ref):
    if not isinstance(ref,dict) or not ref.get('path') or not ref.get('sha256'):
        raise ValueError('gate requires a report reference with path and SHA-256')
    p=safe_path(root,ref['path'])
    if digest(p)!=ref['sha256']:raise ValueError('evidence hash mismatch: '+ref['path'])
    result=json.loads(p.read_text(encoding='utf-8-sig'));ensure_finite(result)
    if not isinstance(result,dict):raise ValueError('report must be a JSON object')
    return result


def timestamp(value):
    try:
        stamp=datetime.fromisoformat(value.replace('Z','+00:00'))
        if stamp.tzinfo is None:raise ValueError('timezone missing')
    except (ValueError,AttributeError,TypeError):raise ValueError('ISO evidence timestamp with timezone required')


def evidence_refs(root,refs):
    if not isinstance(refs,list) or not refs:raise ValueError('underlying source evidence required')
    identities=set()
    for ref in refs:
        if not isinstance(ref,dict) or not re.fullmatch('[0-9a-f]{64}',str(ref.get('sha256',''))):
            raise ValueError('source evidence path and SHA-256 required')
        p=safe_path(root,ref['path'])
        if not p.is_file() or digest(p)!=ref['sha256']:raise ValueError('underlying evidence hash mismatch')
        identity=(p.relative_to(root.resolve()).as_posix(),ref['sha256'])
        if identity in identities:raise ValueError('duplicate source evidence references')
        identities.add(identity)
    return identities


def asset_inventory(root,assets,sha):
    if not isinstance(assets,list) or len(assets)!=2 or any(not isinstance(a,dict) for a in assets):
        raise ValueError('exactly two final bare/dressed assets required')
    if {a.get('role') for a in assets}!={'bare','dressed'}:raise ValueError('unique bare/dressed assets required')
    inventory=[]
    for asset in assets:
        if asset.get('candidate_sha256')!=sha or not re.fullmatch('[0-9a-f]{64}',str(asset.get('sha256',''))):
            raise ValueError('final asset hash/lineage mismatch')
        p=safe_path(root,asset['path'])
        if not p.is_file() or digest(p)!=asset['sha256']:raise ValueError('final asset hash/lineage mismatch')
        inventory.append((asset['role'],p.relative_to(root.resolve()).as_posix(),asset['sha256'],sha))
    if inventory[0][1].casefold()==inventory[1][1].casefold():raise ValueError('distinct bare/dressed asset paths required')
    return sorted(inventory)


def make_template(state):
    sha=state['last_known_candidate_sha256']
    assets=[{'role':role,'path':None,'sha256':None,'candidate_sha256':sha} for role in ('bare','dressed')]
    reports={gate:{'gate_id':gate,'candidate_sha256':sha,'status':'INCOMPLETE',
        'checks':[{'id':name,'passed':None,'evidence':[]} for name in checks],
        'command':None,'source_git_commit':None,'evidence_timestamp':None,
        'source_evidence':[],'assets':assets,
        **({'target_runtime_commit':None} if gate in ('runtime_animation','standalone_release') else {})}
        for gate,checks in REQUIRED_GATES.items()}
    return {'schema_version':1,'status':'INCOMPLETE','production_approved':False,
        'candidate_sha256':sha,'target_runtime_commit':None,'assets':assets,
        'gates':{gate:{'path':None,'sha256':None} for gate in REQUIRED_GATES},
        'owner_acceptance':{'path':None,'sha256':None},'gate_report_templates':reports,
        'owner_acceptance_template':{'decision':'pending','actor':None,'candidate_sha256':sha,
            'decision_source':None,'evidence_timestamp':None,'assets':assets},
        'source_context':{'candidate':state['current_candidate'],'development_failure_count':state['development_failure_count']},
        'note':'INCOMPLETE preparation only. No tests executed or owner acceptance inferred. Write actual gate reports and bind their final hashes after all phases pass.'}


def verify_packet(root,packet):
    if not isinstance(packet,dict):return ['packet must be an object; owner acceptance and gates are missing']
    issues=[];
    gates=packet.get('gates',{})
    if not isinstance(gates,dict):gates={}
    sha=packet.get('candidate_sha256')
    if packet.get('schema_version')!=1:issues.append('promotion packet schema_version must be 1')
    if not isinstance(sha,str) or not re.fullmatch('[0-9a-f]{64}',sha):issues.append('invalid final candidate SHA-256')
    inventory=None
    try:inventory=asset_inventory(root,packet.get('assets'),sha)
    except (ValueError,OSError,KeyError,TypeError) as exc:issues.append('assets: '+str(exc))
    for name,required_checks in REQUIRED_GATES.items():
        try:
            report=verified_report(root,gates.get(name))
            if report.get('gate_id')!=name or report.get('candidate_sha256')!=sha or report.get('status')!='PASS':
                raise ValueError('gate report is missing, failing or bound to another candidate')
            checks=report.get('checks',[])
            if not isinstance(checks,list) or any(not isinstance(x,dict) for x in checks):raise ValueError('invalid check rows')
            ids=[x.get('id') for x in checks]
            if any(not isinstance(x,str) or not x.strip() for x in ids):raise ValueError('check IDs must be nonempty strings')
            if len(ids)!=len(set(ids)):raise ValueError('duplicate gate check IDs')
            passed={x.get('id') for x in checks if x.get('passed') is True}
            if set(required_checks)-passed:raise ValueError('missing explicit checks: '+', '.join(sorted(set(required_checks)-passed)))
            if any(x.get('passed') is not True for x in checks):raise ValueError('gate includes a failing/unknown check')
            if not isinstance(report.get('command'),str) or not report['command'].strip() or not re.fullmatch('[0-9a-f]{40}',str(report.get('source_git_commit',''))):
                raise ValueError('gate needs command, source git commit and evidence timestamp')
            timestamp(report.get('evidence_timestamp'))
            # Raw source logs must also be bound; assertions alone are insufficient.
            sources=evidence_refs(root,report.get('source_evidence'))
            for check in checks:
                if not evidence_refs(root,check.get('evidence')).issubset(sources):
                    raise ValueError('check evidence is absent from gate source evidence')
            if asset_inventory(root,report.get('assets'),sha)!=inventory:raise ValueError('gate asset inventory differs from final exports')
            if name in ('runtime_animation','standalone_release') and report.get('target_runtime_commit')!=packet.get('target_runtime_commit'):
                raise ValueError('runtime/release report targets a different integration commit')
        except (ValueError,OSError,KeyError,TypeError) as exc:issues.append(name+': '+str(exc))
    try:
        owner=verified_report(root,packet.get('owner_acceptance'))
        if owner.get('decision')!='OWNER ACCEPTED' or owner.get('candidate_sha256')!=sha:
            raise ValueError('explicit final OWNER ACCEPTED record for this SHA required')
        if owner.get('actor')!='owner' or not owner.get('decision_source') or not owner.get('evidence_timestamp'):
            raise ValueError('owner decision source and timestamp required; never infer acceptance')
        if not isinstance(owner.get('decision_source'),str) or not owner['decision_source'].strip():raise ValueError('owner decision source must be text')
        timestamp(owner.get('evidence_timestamp'))
        if asset_inventory(root,owner.get('assets'),sha)!=inventory:raise ValueError('owner asset inventory differs from final exports')
    except (ValueError,OSError,KeyError,TypeError) as exc:issues.append('owner visual acceptance: '+str(exc))
    if not re.fullmatch('[0-9a-f]{40}',str(packet.get('target_runtime_commit',''))):issues.append('exact standalone integration commit required')
    return issues



def eligibility_receipt(issues,packet_identity,packet):
    return {'schema_version':1,'eligibility':'REFUSED' if issues else 'ALL_REQUIRED_GATES_SATISFIED',
            'production_approved':False,'issues':list(issues),'promotion_packet':packet_identity,
            'candidate_sha256':packet.get('candidate_sha256') if isinstance(packet,dict) else None,
            'target_runtime_commit':packet.get('target_runtime_commit') if isinstance(packet,dict) else None,
            'note':'Eligibility evidence only. No assets, baseline, state or release allowlist is modified.'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('packet',type=Path,nargs='?');ap.add_argument('--json-out',type=Path)
    ap.add_argument('--template',action='store_true',help='Prepare INCOMPLETE packet/report shapes; no checks or promotion');args=ap.parse_args()
    issues=[];packet_identity=None
    try:
        if args.template:
            if args.packet or not args.json_out:raise ValueError('template mode requires --json-out and no packet')
            if args.json_out.exists():raise ValueError('template output already exists')
            state,_=build(ROOT);result=make_template(state)
            args.json_out.parent.mkdir(parents=True,exist_ok=True);args.json_out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
            print('INCOMPLETE promotion template written; no gates executed or approval changed');return 0
        if not args.packet:raise ValueError('packet required unless creating a template')
        packet=json.loads(args.packet.read_text(encoding='utf-8-sig'));ensure_finite(packet)
        packet_identity={'path':args.packet.as_posix(),'sha256':digest(args.packet)}
        if not isinstance(packet,dict):raise ValueError('packet must be a JSON object')
        issues=verify_packet(ROOT,packet)
        state,_=build(ROOT)
        if packet.get('candidate_sha256')!=state['last_known_candidate_sha256']:issues.append('packet is not for latest complete candidate')
        if state['candidate_state']=='rejected':issues.append('candidate is rejected')
        if state['development_failure_count'] or state['unresolved_regressions']:issues.append('development failures or strict R2 regressions remain')
        if state['incomplete_candidates']:issues.append('newer incomplete candidate evidence remains')
        report=next(x['path'] for x in state['latest_evidence'] if x['path'].endswith('_merged_pose_report.json'))
        if evaluate(ROOT,report,'production_target')['failure_count']:issues.append('recomputed production deformation gate fails')
        for n in range(0,12):
            if state['phases'][str(n)]['state']!='complete':issues.append('Phase '+str(n)+' is incomplete')
    except (OSError,ValueError,KeyError,TypeError) as exc:issues.append(str(exc))
    result=eligibility_receipt(issues,packet_identity,locals().get('packet'))
    if args.json_out:
        if args.json_out.exists():raise SystemExit('STOP — promotion receipt output already exists')
        args.json_out.parent.mkdir(parents=True,exist_ok=True);args.json_out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2));return 1 if issues else 0
if __name__=='__main__':raise SystemExit(main())
