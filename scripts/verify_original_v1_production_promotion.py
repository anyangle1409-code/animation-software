#!/usr/bin/env python3
"""Fail-closed future Phase 12 eligibility check; never changes approval flags.

A passing packet is evidence for a controlled owner-authorised release operation,
not an optimiser's power to promote. This verifier is not an owner identity service.
"""
from __future__ import annotations
import argparse
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


def verify_packet(root,packet):
    if not isinstance(packet,dict):return ['packet must be an object; owner acceptance and gates are missing']
    issues=[];
    gates=packet.get('gates',{})
    if not isinstance(gates,dict):gates={}
    sha=packet.get('candidate_sha256')
    if packet.get('schema_version')!=1:issues.append('promotion packet schema_version must be 1')
    if not isinstance(sha,str) or not re.fullmatch('[0-9a-f]{64}',sha):issues.append('invalid final candidate SHA-256')
    for name,required_checks in REQUIRED_GATES.items():
        try:
            report=verified_report(root,gates.get(name))
            if report.get('gate_id')!=name or report.get('candidate_sha256')!=sha or report.get('status')!='PASS':
                raise ValueError('gate report is missing, failing or bound to another candidate')
            checks=report.get('checks',[])
            if not isinstance(checks,list) or any(not isinstance(x,dict) for x in checks):raise ValueError('invalid check rows')
            passed={x.get('id') for x in checks if x.get('passed') is True}
            if set(required_checks)-passed:raise ValueError('missing explicit checks: '+', '.join(sorted(set(required_checks)-passed)))
            if any(x.get('passed') is not True for x in checks):raise ValueError('gate includes a failing/unknown check')
            if not report.get('command') or not re.fullmatch('[0-9a-f]{40}',str(report.get('source_git_commit',''))) or not report.get('evidence_timestamp'):
                raise ValueError('gate needs command, source git commit and evidence timestamp')
            # Raw source logs must also be bound; assertions alone are insufficient.
            refs=report.get('source_evidence',[])
            if not refs:raise ValueError('gate lacks underlying source evidence')
            for ref in refs:
                p=safe_path(root,ref['path'])
                if digest(p)!=ref['sha256']:raise ValueError('underlying evidence hash mismatch')
            if name in ('runtime_animation','standalone_release') and report.get('target_runtime_commit')!=packet.get('target_runtime_commit'):
                raise ValueError('runtime/release report targets a different integration commit')
        except (ValueError,OSError,KeyError,TypeError) as exc:issues.append(name+': '+str(exc))
    try:
        owner=verified_report(root,packet.get('owner_acceptance'))
        if owner.get('decision')!='OWNER ACCEPTED' or owner.get('candidate_sha256')!=sha:
            raise ValueError('explicit final OWNER ACCEPTED record for this SHA required')
        if owner.get('actor')!='owner' or not owner.get('decision_source') or not owner.get('evidence_timestamp'):
            raise ValueError('owner decision source and timestamp required; never infer acceptance')
    except (ValueError,OSError,KeyError,TypeError) as exc:issues.append('owner visual acceptance: '+str(exc))
    assets=packet.get('assets',[])
    if not isinstance(assets,list):assets=[]
    if not assets or {a.get('role') for a in assets if isinstance(a,dict)}!={'bare','dressed'}:
        issues.append('final bare/dressed assets required')
    for asset in assets:
        try:
            p=safe_path(root,asset['path'])
            if digest(p)!=asset['sha256'] or asset.get('candidate_sha256')!=sha:raise ValueError('final asset hash/lineage mismatch')
        except (ValueError,OSError,KeyError,TypeError) as exc:issues.append('asset: '+str(exc))
    if not re.fullmatch('[0-9a-f]{40}',str(packet.get('target_runtime_commit',''))):issues.append('exact standalone integration commit required')
    return issues


def main():
    ap=argparse.ArgumentParser();ap.add_argument('packet',type=Path);ap.add_argument('--json-out',type=Path);args=ap.parse_args()
    issues=[]
    try:
        packet=json.loads(args.packet.read_text(encoding='utf-8-sig'));ensure_finite(packet)
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
    result={'schema_version':1,'eligibility':'REFUSED' if issues else 'ALL_REQUIRED_GATES_SATISFIED',
            'production_approved':False,'issues':issues,
            'note':'Eligibility evidence only. No assets, baseline, state or release allowlist is modified.'}
    if args.json_out:
        if args.json_out.exists():raise SystemExit('STOP — promotion receipt output already exists')
        args.json_out.parent.mkdir(parents=True,exist_ok=True);args.json_out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2));return 1 if issues else 0
if __name__=='__main__':raise SystemExit(main())
