#!/usr/bin/env python3
"""Read-only recovery instructions for an already-created experimental candidate.

Never reruns an optimiser, writes evidence, deletes collisions or approves a model.
Check LIVE branch, frozen inputs and laptop environment before executing instructions.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
from merge_original_v1_repair_group_reports import CAND, RC, GROUP_POSES, ROOT, sha256, collect_reports
from collect_original_v1_review_images import verify_source
from original_v1_production_control import ensure_finite, build


def verify_group(directory,group,candidate_sha,script_sha):
    source=verify_source(directory/'render_source_manifest.json',candidate_sha)
    if source['render_script_sha256']!=script_sha:raise ValueError('group uses a different render script version')
    rows=json.loads((directory/'pose_test_report.json').read_text(encoding='utf-8-sig'));ensure_finite(rows)
    names=[x['pose'] for x in rows]
    if len(names)!=len(set(names)) or set(names)!=set(GROUP_POSES[group]):raise ValueError('group pose coverage differs')


def inspect(root,revision):
    if not re.fullmatch('r[0-9]+',revision):raise ValueError('numbered revision required')
    root=root.resolve();candidate=root/CAND/f'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{revision}.blend'
    manifest=candidate.with_suffix('.json');man=json.loads(manifest.read_text(encoding='utf-8-sig'))
    if man.get('candidate')!=candidate.name or sha256(candidate)!=man.get('candidate_sha256'):
        raise ValueError('local candidate hash/name differs from manifest')
    parent_name=man.get('source_candidate','')
    match=re.fullmatch(r'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_(r[0-9]+)\.blend',parent_name)
    if not match:raise ValueError('numbered parent manifest required; reconcile lineage before recovery')
    parent=match.group(1)
    parent_manifest=json.loads((root/CAND/Path(parent_name).with_suffix('.json')).read_text(encoding='utf-8-sig'))
    if parent_manifest.get('candidate_sha256')!=man.get('source_sha256'):raise ValueError('parent candidate hash differs')
    solution_name=man.get('solution','')
    if not solution_name or Path(solution_name).name!=solution_name:raise ValueError('invalid solution filename')
    solution=root/CAND/'weight_solutions'/solution_name
    if sha256(solution)!=man.get('solution_sha256'):raise ValueError('local solution hash differs from manifest')
    rc=root/RC
    existing=sorted(p.name for p in rc.glob(f'full_{revision}_*'))
    if existing:raise ValueError('existing full outputs require reconciliation; preserve: '+', '.join(existing))
    script_sha=sha256(ROOT/'scripts/pose_test_original_v1_o4_candidate_blender.py')
    missing=[];verified=[];commands=[]
    for group in GROUP_POSES:
        directory=rc/f'{group}_{revision}'
        if directory.exists():
            try:verify_group(directory,group,man['candidate_sha256'],script_sha)
            except (OSError,ValueError,KeyError,TypeError) as exc:
                raise ValueError(f'unfinished/conflicting group {group}: {exc}; preserve folder, use a new evidence label after reconciliation') from exc
            verified.append(group)
        else:
            missing.append(group)
            if group!='neutral':commands.append(f'RUN_ORIGINAL_V1_REPAIR_CHECK.bat {group} "{candidate.relative_to(root)}" {group}_{revision} --report-only')
            else:commands.append(f'"%BLENDER_EXE%" --background --factory-startup "{candidate.relative_to(root)}" --python-exit-code 1 --python scripts/pose_test_original_v1_o4_candidate_blender.py -- "{directory.relative_to(root)}" neutral')
    if not missing:
        collect_reports(root,revision)  # Also verify overlapping metrics before offering merge.
        commands.append(f'python scripts/merge_original_v1_repair_group_reports.py {revision} --prior {parent}')
    return {'schema_version':1,'state':'COLLECT MISSING EVIDENCE' if missing else 'MERGE VERIFIED GROUPS',
            'candidate':revision,'candidate_sha256':man['candidate_sha256'],'parent':parent,
            'verified_groups':verified,'missing_groups':missing,'commands':commands,
            'production_approved':False,'read_only':True,
            'environment_authorized':False,
            'next':'Reinspect after collection; merge only when all six groups verify. Then complete comparisons, trial summary, review and shared status using the r30 runner tail.'}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('revision');args=ap.parse_args()
    try:
        status,ledger=build(ROOT)  # Verify frozen inputs and shared evidence before instructions.
        entry=next((x for x in ledger['candidates'] if x['revision']==args.revision),None)
        if entry and entry['state']=='rejected':raise ValueError('candidate is rejected; do not build on this state')
        report=inspect(ROOT,args.revision)
        print(json.dumps(report,indent=2))
        print('READ-ONLY INSTRUCTIONS — verify LIVE branch/frozen inputs and laptop environment before executing. Set BLENDER_EXE for neutral capture.')
        return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print('STOP — '+str(exc),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
