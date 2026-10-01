"""Merge complete candidate-bound evidence; regressions remain experimental evidence.

python scripts/merge_original_v1_repair_group_reports.py <rN> [--prior <rM>]
New full runs require all six render groups, including neutral, from the same
candidate and render-script bytes. Existing historical reports are never rewritten.
Exit 0 means evidence processing completed, not that the candidate passed gates.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from collect_original_v1_review_images import verify_source
from original_v1_production_control import ensure_finite

ROOT=Path(__file__).resolve().parent.parent
CAND=Path('ORIGINAL_V1_WORK/candidates')
RC=CAND/'repair_checks'
# Same pose membership as the existing targeted runner; no stress pose is changed.
GROUP_POSES={
    'shoulder':('press_bottom','press_top','press_top_rhythm','squat_bottom','pullup_hang','pullup_hang_rhythm','pullup_top','pullup_bar'),
    'hand':('curl_peak','press_bottom','press_top','press_top_rhythm','pullup_hang','pullup_hang_rhythm','pullup_top','row','grip','curl_handle','pullup_bar'),
    'hip':('squat_bottom','lunge'),
    'pushup':('pushup_bottom',),
    'row':('row',),
    'neutral':('neutral',),
}


def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def collect_reports(root,revision):
    if not re.fullmatch(r'r\d+',revision):raise ValueError('numbered revision required')
    candidate_manifest=root/CAND/f'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{revision}.json'
    man=json.loads(candidate_manifest.read_text(encoding='utf-8-sig'))
    candidate_sha=man['candidate_sha256']; merged={};owners={};groups=[];script_hash=None
    for group,required in GROUP_POSES.items():
        directory=root/RC/f'{group}_{revision}';report_path=directory/'pose_test_report.json'
        if not report_path.is_file():raise ValueError(f'missing {group} report: {report_path}')
        source_path=directory/'render_source_manifest.json'
        source=verify_source(source_path,candidate_sha)
        if script_hash is None:script_hash=source['render_script_sha256']
        elif source['render_script_sha256']!=script_hash:raise ValueError('mixed render script versions across groups')
        rows=json.loads(report_path.read_text(encoding='utf-8-sig'));ensure_finite(rows)
        if not isinstance(rows,list) or not all(isinstance(x,dict) for x in rows):raise ValueError('pose report must contain rows')
        names=[x['pose'] for x in rows]
        if len(names)!=len(set(names)) or set(names)!=set(required):raise ValueError(f'{group}: incomplete/duplicate group pose coverage')
        for row in rows:
            name=row['pose']
            if name in merged and merged[name]!=row:
                raise ValueError(f'conflicting duplicate pose {name}: {owners[name]} vs {group}')
            merged[name]=row;owners.setdefault(name,group)
        groups.append({'group':group,'pose_report':report_path.relative_to(root).as_posix(),
                       'pose_report_sha256':sha256(report_path),
                       'render_source_manifest':source_path.relative_to(root).as_posix(),
                       'render_source_manifest_sha256':sha256(source_path)})
    baseline=json.loads((root/CAND/'pose_test_report_r2.json').read_text(encoding='utf-8-sig'))
    order=[x['pose'] for x in baseline]
    if set(merged)!=set(order):raise ValueError('full merged report coverage differs from pinned R2')
    receipt={'schema_version':1,'candidate_revision':revision,'candidate_sha256':candidate_sha,
             'candidate_manifest_sha256':sha256(candidate_manifest),'render_script_sha256':script_hash,
             'groups':groups,'pose_count':len(merged),'production_approved':False,
             'purpose':'Complete source-bound merge receipt, not acceptance or baseline promotion.'}
    return [merged[n] for n in order],receipt


def run(args):
    print('>', ' '.join(map(str,args)),flush=True)
    result=subprocess.run([sys.executable,*map(str,args)],cwd=ROOT,capture_output=True,text=True)
    print(result.stdout[-3000:]+result.stderr[-2000:],flush=True)
    return result.returncode


def main():
    ap=argparse.ArgumentParser();ap.add_argument('rev');ap.add_argument('--prior')
    ap.add_argument('--root',type=Path,default=ROOT,help='Repository/evidence root; defaults to this checkout')
    args=ap.parse_args();root=args.root.resolve()
    try:
        rows,receipt=collect_reports(root,args.rev)
        if args.prior and not re.fullmatch(r'r\d+',args.prior):raise ValueError('numbered predecessor required')
        outputs=[root/RC/f'full_{args.rev}_{suffix}' for suffix in (
            'merged_pose_report.json','evidence_manifest.json','deformation_acceptance.md',
            'repair_queue.md','comparison_vs_R2.json')]
        if args.prior:outputs.append(root/RC/f'full_{args.rev}_comparison_vs_{args.prior}.json')
        if any(p.exists() for p in outputs):raise ValueError('full-evidence output collision; preserve existing outputs')
        if args.prior:
            prior=root/RC/f'full_{args.prior}_merged_pose_report.json'
            names=[x['pose'] for x in json.loads(prior.read_text(encoding='utf-8-sig'))]
            if len(names)!=len(set(names)) or set(names)!={x['pose'] for x in rows}:raise ValueError('predecessor has different full pose coverage')
        out=outputs[0];out.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
        receipt['merged_pose_report_sha256']=sha256(out)
        outputs[1].write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
        r2=root/CAND/'pose_test_report_r2.json'
        jobs=[['scripts/evaluate_original_v1_deformation_report.py',out,'--grip-report',out,
               '--profile','development_blocker','--require-group','core_five','--report-only','--markdown-out',outputs[2]],
              ['scripts/build_original_v1_repair_queue.py',out,'--profile','development_blocker',
               '--require-complete-ownership','--markdown-out',outputs[3]],
              ['scripts/compare_original_v1_deformation_reports.py',r2,out,'--baseline-grip-report',r2,
               '--candidate-grip-report',out,'--profile','development_blocker','--report-only','--json-out',outputs[4]]]
        if args.prior:jobs.append(['scripts/compare_original_v1_deformation_reports.py',prior,out,
            '--baseline-grip-report',prior,'--candidate-grip-report',out,'--profile','development_blocker',
            '--report-only','--json-out',outputs[5]])
        for job in jobs:
            code=run(job)
            if code:raise ValueError(f'evidence subprocess failed ({code}): {job[0]}')
        print('FULL EVIDENCE COMPLETE — inspect failures/regressions; no candidate approval inferred')
        return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print('STOP — '+str(exc),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
