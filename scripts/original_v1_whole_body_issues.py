#!/usr/bin/env python3
"""Validate and summarize the fail-closed ORIGINAL-v1 anatomy issue ledger."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_LEDGER=ROOT/'ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json'
SEVERITIES=('Critical','High','Medium','Low')
STATES=('Open','In Progress','Pending Review','Fixed','Accepted')
BLOCKING_STATES=('Open','In Progress','Pending Review')
REQUIRED_FIELDS=('id','region','severity','state','candidate','reproduction','evidence_paths',
                 'human_evidence_ids','evidence_gap','defect','acceptance','closure_evidence')


def _strings(value: Any) -> bool:
    return isinstance(value,list) and bool(value) and all(isinstance(x,str) and x.strip() for x in value)


def blocking_issues(ledger: dict[str,Any]) -> list[dict[str,Any]]:
    return [row for row in ledger.get('issues',[]) if isinstance(row,dict)
            and row.get('severity') in ('Critical','High') and row.get('state') in BLOCKING_STATES]


def validate_ledger(ledger: dict[str,Any], root: Path | None=None) -> list[str]:
    errors=[]
    if ledger.get('schema_version')!=1: errors.append('schema_version must be 1')
    if ledger.get('asset')!='HomeGymPT_Male_ORIGINAL_v1': errors.append('asset identity mismatch')
    rows=ledger.get('issues')
    if not isinstance(rows,list) or not rows: return errors+['issues must be a non-empty list']
    human_ids=None
    if root is not None:
        try:
            human=json.loads((root/'ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json').read_text(encoding='utf-8-sig'))
            human_ids={x['id'] for x in human['entries']}
        except (OSError,KeyError,TypeError,json.JSONDecodeError):
            errors.append('human evidence manifest unavailable')
            human_ids=set()
    seen=set()
    for index,row in enumerate(rows):
        if not isinstance(row,dict):
            errors.append(f'issue[{index}]: issue must be an object');continue
        label=str(row.get('id') or f'issue[{index}]')
        for field in REQUIRED_FIELDS:
            if field not in row: errors.append(label+': missing '+field)
        issue_id=row.get('id')
        if not isinstance(issue_id,str) or not re.fullmatch(r'WB-[A-Z]+-\d{3}',issue_id):
            errors.append(label+': invalid stable issue id')
        elif issue_id in seen: errors.append(label+': duplicate issue id')
        else: seen.add(issue_id)
        if row.get('severity') not in SEVERITIES: errors.append(label+': invalid severity')
        if row.get('state') not in STATES: errors.append(label+': invalid state')
        for field in ('region','defect','acceptance'):
            if not isinstance(row.get(field),str) or not row.get(field,'').strip():
                errors.append(label+': '+field+' must be non-empty')
        candidate=row.get('candidate')
        if not isinstance(candidate,dict): errors.append(label+': candidate must be an object')
        else:
            if not re.fullmatch(r'r\d+',str(candidate.get('revision',''))): errors.append(label+': candidate revision invalid')
            if not re.fullmatch(r'[0-9a-f]{64}',str(candidate.get('sha256',''))): errors.append(label+': candidate SHA-256 invalid')
        reproduction=row.get('reproduction')
        if not isinstance(reproduction,dict): errors.append(label+': reproduction must be an object')
        else:
            if not _strings(reproduction.get('poses')): errors.append(label+': reproduction.poses invalid')
            if not _strings(reproduction.get('views')): errors.append(label+': reproduction.views invalid')
            if not isinstance(reproduction.get('description'),str) or not reproduction.get('description','').strip():
                errors.append(label+': reproduction.description invalid')
        evidence_paths=row.get('evidence_paths')
        if not _strings(evidence_paths): errors.append(label+': evidence_paths invalid')
        elif root is not None:
            for path in evidence_paths:
                target=(root/path).resolve()
                if not target.is_relative_to(root.resolve()) or not target.is_file():
                    errors.append(label+': evidence path missing '+path)
        ids=row.get('human_evidence_ids')
        if not isinstance(ids,list) or not all(isinstance(x,str) and x.strip() for x in ids):
            errors.append(label+': human_evidence_ids invalid')
        elif not ids and (not isinstance(row.get('evidence_gap'),str) or not row.get('evidence_gap','').strip()):
            errors.append(label+': empty human_evidence_ids requires evidence_gap')
        elif human_ids is not None:
            for evidence_id in ids:
                if evidence_id not in human_ids: errors.append(label+': unknown human evidence id '+evidence_id)
        closure=row.get('closure_evidence')
        if not isinstance(closure,list) or not all(isinstance(x,str) and x.strip() for x in closure):
            errors.append(label+': closure_evidence must be a string list')
        elif row.get('state') in ('Fixed','Accepted') and not closure:
            errors.append(label+': '+row['state']+' requires closure_evidence')
        elif root is not None:
            for path in closure:
                target=(root/path).resolve()
                if not target.is_relative_to(root.resolve()) or not target.is_file():
                    errors.append(label+': closure evidence path missing '+path)
    return errors


def main() -> int:
    parser=argparse.ArgumentParser();parser.add_argument('ledger',type=Path,nargs='?',default=DEFAULT_LEDGER);args=parser.parse_args()
    try:
        ledger=json.loads(args.ledger.read_text(encoding='utf-8-sig'))
        errors=validate_ledger(ledger,args.ledger.resolve().parent)
    except (OSError,ValueError,TypeError,json.JSONDecodeError) as exc:
        print('ISSUE LEDGER INVALID: '+str(exc));return 2
    if errors:
        print('ISSUE LEDGER INVALID')
        for error in errors: print('- '+error)
        return 2
    blockers=blocking_issues(ledger)
    print(f'ISSUE LEDGER VERIFIED: {len(blockers)} Critical/High blocker(s)')
    for row in blockers: print(f"- {row['id']} [{row['severity']}] {row['state']}: {row['defect']}")
    return 1 if blockers else 0


if __name__=='__main__':raise SystemExit(main())
