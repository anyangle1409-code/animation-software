#!/usr/bin/env python3
"""Verify an independently invoked complete numeric replay; not approval.

Uses the existing Blender pose renderer's metrics-only mode. No poses, geometry,
weights or thresholds are changed. Raw images are not needed for numeric replay.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path, PureWindowsPath
import re
import subprocess
from original_v1_production_control import ROOT,CAND,RC,digest,read,evaluate,verify_full_receipt,build


def verify_replay(root,revision,directory):
    if not re.fullmatch(r'r\d+',revision):raise ValueError('numbered candidate required')
    directory=directory.resolve()
    if not directory.is_relative_to((root/RC).resolve()) or directory.name!=f'freeze_replay_{revision}':
        raise ValueError('fresh candidate replay directory inside repair_checks required')
    primary_receipt=verify_full_receipt(root,revision)
    primary=root/RC/f'full_{revision}_merged_pose_report.json'
    receipt=read(root,primary_receipt['path']);sha=receipt['candidate_sha256']
    source_path=directory/'render_source_manifest.json';source=json.loads(source_path.read_text(encoding='utf-8-sig'))
    replay=directory/'pose_test_report.json'
    if source.get('candidate_sha256')!=sha:raise ValueError('replay candidate identity differs')
    if source.get('render_script_sha256')!=receipt['render_script_sha256']:raise ValueError('replay script identity differs')
    if source.get('pose_report_sha256')!=digest(replay):raise ValueError('replay report hash differs')
    versions={read(root,g['render_source_manifest'])['blender_version'] for g in receipt['groups']}
    if versions!={source.get('blender_version')}:raise ValueError('replay/primary Blender version differs or primary versions are mixed')
    invocation=source.get('capture_arguments',[])
    if (source.get('capture_mode')!='numeric_replay' or len(invocation)!=3 or
        PureWindowsPath(invocation[0]).name!=directory.name or invocation[1]!='' or invocation[2]!='--metrics-only'):
        raise ValueError('replay invocation identity differs; do not relabel primary evidence')
    if source.get('images')!=[]:raise ValueError('numeric replay unexpectedly claims review images')
    evaluate(root,replay.relative_to(root).as_posix())
    rows=json.loads(replay.read_text(encoding='utf-8-sig'))
    original=json.loads(primary.read_text(encoding='utf-8-sig'))
    order=[x['pose'] for x in original];indexed={x['pose']:x for x in rows}
    if [indexed[n] for n in order]!=original:raise ValueError('replay metrics differ from primary; preserve both runs')
    refs=[primary_receipt]+[{'path':p.relative_to(root).as_posix(),'sha256':digest(p)} for p in (primary,source_path,replay)]
    return {'schema_version':1,'gate_id':'original_v1_numeric_replay','status':'PASS',
            'candidate_revision':revision,'candidate_sha256':sha,'pose_count':len(rows),
            'replay_directory':directory.relative_to(root).as_posix(),'source_evidence':refs,
            'production_approved':False,'visual_review_available':False,
            'note':'Identical reported metrics under matching candidate/script/Blender identities. Does not prove production deformation or visual anatomy.'}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('revision');ap.add_argument('--capture',action='store_true')
    ap.add_argument('--json-out',type=Path,required=True);args=ap.parse_args()
    try:
        if args.json_out.exists():raise ValueError('replay verification output collision')
        state,_=build(ROOT)
        if args.revision!=state['current_candidate'] or state['candidate_state']=='rejected':raise ValueError('verified current non-rejected candidate required')
        verify_full_receipt(ROOT,args.revision)  # Refuse missing primary provenance before invoking Blender.
        directory=ROOT/RC/f'freeze_replay_{args.revision}'
        if args.capture:
            from original_v1_milestone_review import capture
            capture(args.revision,mode='numeric_replay')
        result=verify_replay(ROOT,args.revision,directory)
        args.json_out.parent.mkdir(parents=True,exist_ok=True);args.json_out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print('NUMERIC REPLAY VERIFIED — no phase or production approval',args.json_out);return 0
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as exc:
        print('STOP — '+str(exc));return 2

if __name__=='__main__':raise SystemExit(main())
