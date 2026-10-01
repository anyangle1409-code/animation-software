"""Milestone capture plan and verified publishing; only actual source PNGs are copied."""
from __future__ import annotations
import json
from pathlib import Path
import re
import shutil
from original_v1_production_control import ROOT,CAND,RC,digest,ensure_finite,evaluate
from collect_original_v1_review_images import verify_source


def load_plan(root=ROOT):
    plan=json.loads((root/'ORIGINAL_V1_VISUAL_BOARD_PLAN.json').read_text(encoding='utf-8-sig'))
    ensure_finite(plan)
    if plan['schema_version']!=1 or plan['production_approved'] is not False or plan['dressed'] is not False:
        raise ValueError('candidate bare milestone protocol required')
    if plan['resolution']!=[900,900,100]:raise ValueError('fixed milestone resolution differs')
    return plan


def views(plan):
    rows=[]
    for view,angles in plan['neutral']['views'].items():
        rows.append({'set':'neutral','pose':'neutral','view':view,'file':f'milestone_neutral_{view}.png',
                     'centre':plan['neutral']['centre'],'scale':plan['neutral']['orthographic_scale'],'angles':angles})
    for region in plan['anatomy']:
        for n,angle in enumerate(region['angles']):
            rows.append({'set':'anatomy','pose':'neutral','region':region['region'],'view':str(n+1),
                         'file':f'milestone_anatomy_{region["region"]}_{n+1}.png','anchors':region['anchors'],
                         'scale':region['orthographic_scale'],'angles':angle})
    for pose in plan['exercise']['poses']:
        for view,angles in plan['exercise']['views'].items():
            rows.append({'set':'exercise','pose':pose,'view':view,'file':f'milestone_{pose}_{view}.png',
                         'centre':plan['exercise']['centre'],'scale':plan['exercise']['orthographic_scale'],'angles':angles})
    return rows


def verify_milestone(directory,source,plan,plan_sha=None):
    expected={x['file']:x for x in views(plan)}
    records=source['images'];names=[x['file'] for x in records]
    if len(names)!=len(set(names)) or set(names)!=set(expected):raise ValueError('milestone view coverage incomplete/duplicated')
    plan_sha=plan_sha or digest(ROOT/'ORIGINAL_V1_VISUAL_BOARD_PLAN.json')
    for record in records:
        capture=record.get('capture',{});row=expected[record['file']]
        if capture.get('protocol')!=plan['protocol']:raise ValueError('milestone capture protocol missing/different')
        if (capture.get('milestone_plan_sha256')!=plan_sha or capture.get('view_id')!=row['file'] or
            capture.get('pose')!=row['pose'] or capture.get('dressed') is not False):
            raise ValueError('milestone capture identity differs')
    return expected


def publish(root,revision):
    if not re.fullmatch(r'r\d+',revision):raise ValueError('numbered candidate revision required')
    out=root/CAND/f'review/milestone_{revision}'
    if out.exists():raise ValueError('milestone review output collision')
    plan=load_plan(root);source_dir=root/RC/f'milestone_{revision}'
    candidate_path=root/CAND/f'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{revision}.json'
    candidate=json.loads(candidate_path.read_text(encoding='utf-8-sig'))
    source_path=source_dir/'render_source_manifest.json'
    source=verify_source(source_path,candidate['candidate_sha256'])
    expected=verify_milestone(source_dir,source,plan,digest(root/'ORIGINAL_V1_VISUAL_BOARD_PLAN.json'))
    evaluate(root,(source_dir/'pose_test_report.json').relative_to(root).as_posix())  # Complete real pose evidence, not a passing-gate assertion.
    rows=[]
    for record in source['images']:
        rows.append({'output':(out/record['file']).relative_to(root).as_posix(),
                     'sha256':record['sha256'],'capture':record['capture'],**expected[record['file']]})
    result={'schema_version':1,'candidate_revision':revision,'candidate_sha256':candidate['candidate_sha256'],
            'candidate_manifest_sha256':digest(candidate_path),'milestone_plan_sha256':digest(root/'ORIGINAL_V1_VISUAL_BOARD_PLAN.json'),
            'source_manifests':[{'path':source_path.relative_to(root).as_posix(),'sha256':digest(source_path)}],
            'owner_review':'pending','blocking':False,'production_approved':False,'files':rows,
            'note':'Actual bare candidate renders; capture evidence is not visual acceptance.'}
    out.mkdir(parents=True)
    for row in rows:shutil.copyfile(source_dir/row['file'],out/row['file'])
    (out/'visual_review_manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    lines=[f'# {revision} milestone review', '', f"Candidate SHA: `{candidate['candidate_sha256']}`",'',
           'EXPERIMENTAL — owner_review: pending — NON-BLOCKING. Continue safe work.','',
           'Bare body evidence. Clothing and final appearance require their own review.','']
    for group in ('neutral','anatomy','exercise'):
        lines+=['## '+group.title(),'']
        for row in rows:
            if row['set']!=group:continue
            label=row.get('region',row['pose'])+' / '+row['view']
            if group=='neutral' or (group=='exercise' and row['view']=='three_quarter'):
                lines += [f'![{label}]({row["file"]})','']
            else:lines += [f'- [{label}]({row["file"]})']
        lines+=['']
    (out/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return out


def capture(revision):
    import shutil
    import subprocess
    import sys
    from original_v1_session_preflight import run,repository_issues,blender_path,power_info,process_info
    from original_v1_production_control import build,read
    control=read(ROOT,'ORIGINAL_V1_PRODUCTION_CONTROL.json')
    branch=run(['git','branch','--show-current']);head=run(['git','rev-parse','HEAD'])
    live=run(['git','ls-remote','--exit-code','origin','refs/heads/'+control['branch']]).split()[0]
    issues=repository_issues(branch,control['branch'],head,live,run(['git','status','--porcelain','--untracked-files=all']))
    build(ROOT)  # Frozen rig, baseline, gates, poses and numeric evidence must verify.
    blender=blender_path()
    if not blender:issues.append('Blender unavailable; set BLENDER_EXE')
    if shutil.disk_usage(ROOT).free<2*1024**3:issues.append('less than 2 GiB free for milestone evidence')
    processes=process_info();power=power_info()
    print(json.dumps({'power':power,'processes':processes,'local_head':head,'live_head':live},indent=2))
    if processes.get('conflicts'):issues.append('conflicting Blender/optimiser processes; inspect PIDs')
    if issues:raise ValueError('; '.join(issues))
    out=ROOT/RC/f'milestone_{revision}'
    if out.exists() or (ROOT/CAND/f'review/milestone_{revision}').exists():raise ValueError('milestone output collision; preserve existing files')
    candidate=ROOT/CAND/f'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{revision}.blend'
    man=read(ROOT,candidate.with_suffix('.json').relative_to(ROOT))
    if man.get('candidate')!=candidate.name or digest(candidate)!=man.get('candidate_sha256'):
        raise ValueError('local milestone candidate hash/name mismatch')
    subprocess.run([str(blender),'--background','--factory-startup',str(candidate),'--python-exit-code','1',
        '--python','scripts/pose_test_original_v1_o4_candidate_blender.py','--',str(out),'','--milestone'],cwd=ROOT,check=True)
    # Never save the Blend, resume partial rendering automatically or promote a candidate.


def main():
    import argparse
    import subprocess
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('revision');ap.add_argument('--capture',action='store_true')
    args=ap.parse_args()
    try:
        if not re.fullmatch(r'r\d+',args.revision):raise ValueError('numbered candidate revision required')
        if args.capture:capture(args.revision)
        out=publish(ROOT,args.revision)
        print('MILESTONE REVIEW READY',out,'owner_review: pending; NON-BLOCKING. Publish evidence and continue safe work.')
        return 0
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as exc:
        print('STOP — '+str(exc));return 2

if __name__=='__main__':raise SystemExit(main())
