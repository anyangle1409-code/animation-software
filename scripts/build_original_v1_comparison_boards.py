#!/usr/bin/env python3
"""Embed matched actual render PNGs in labelled SVGs; never synthesizes previews."""
import argparse
import base64
import html
import json
from pathlib import Path
import re
from original_v1_production_control import ROOT,CAND,digest


def board_svg(before_rev,after_rev,before_bytes,after_bytes,before_capture,after_capture,label):
    matched=bool(before_capture) and before_capture==after_capture
    esc=html.escape
    old=base64.b64encode(before_bytes).decode();new=base64.b64encode(after_bytes).decode()
    note='MATCHED CAPTURE SETTINGS' if matched else 'CAPTURE SETTINGS DIFFER — informational side-by-side only'
    text=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="600" viewBox="0 0 1000 600">
<rect width="1000" height="600" fill="#eeeeee"/>
<text x="24" y="28" font-family="sans-serif" font-size="20">{esc(label)} — EXPERIMENTAL / OWNER REVIEW PENDING</text>
<text x="24" y="54" font-family="sans-serif" font-size="16">{esc(before_rev)} (previous)</text>
<text x="524" y="54" font-family="sans-serif" font-size="16">{esc(after_rev)} (new)</text>
<image x="10" y="64" width="480" height="480" href="data:image/png;base64,{old}"/>
<image x="510" y="64" width="480" height="480" href="data:image/png;base64,{new}"/>
<text x="24" y="576" font-family="sans-serif" font-size="16">{esc(note)}</text>
</svg>'''
    return text,matched


def load_review(rev):
    path=ROOT/CAND/f'review/visual_{rev}/visual_review_manifest.json'
    d=json.loads(path.read_text(encoding='utf-8'))
    manifest=ROOT/CAND/f'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{rev}.json'
    if d.get('candidate_sha256')!=json.loads(manifest.read_text(encoding='utf-8-sig'))['candidate_sha256']:
        raise ValueError('review candidate identity mismatch')
    result={}
    for row in d['files']:
        p=(ROOT/row['output']).resolve()
        if not p.is_relative_to((ROOT/CAND/f'review/visual_{rev}').resolve()):raise ValueError('review image outside candidate folder')
        if digest(p)!=row['sha256']:raise ValueError('review image hash mismatch')
        result[p.name]=(p,row)
    return path,d,result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('previous');ap.add_argument('candidate');args=ap.parse_args()
    for r in (args.previous,args.candidate):
        if not re.fullmatch(r'r\d+',r):raise SystemExit('numbered candidate revisions required')
    out=ROOT/CAND/f'review/comparison_{args.previous}_{args.candidate}'
    if out.exists():raise SystemExit('STOP — comparison output collision')
    try:
        apath,a,old=load_review(args.previous);bpath,b,new=load_review(args.candidate)
        names=sorted(old.keys()&new.keys())
        if not names:raise ValueError('no matching actual rendered views')
        rows=[];boards=[]
        for name in names:
            p,x=old[name];q,y=new[name]
            svg,matched=board_svg(args.previous+' / '+a['candidate_sha256'][:12],args.candidate+' / '+b['candidate_sha256'][:12],p.read_bytes(),q.read_bytes(),x.get('capture'),y.get('capture'),name)
            file=Path(name).stem+'.svg';boards.append((file,svg))
            rows.append({'file':file,'previous_png':x['output'],'candidate_png':y['output'],
                         'previous_sha256':x['sha256'],'candidate_sha256':y['sha256'],'capture_settings_match':matched})
        out.mkdir(parents=True)
        for file,svg in boards:(out/file).write_text(svg,encoding='utf-8')
        for row in rows:row['board_sha256']=digest(out/row['file'])
        result={'schema_version':1,'previous_revision':args.previous,'candidate_revision':args.candidate,
                'previous_candidate_sha256':a['candidate_sha256'],'candidate_sha256':b['candidate_sha256'],
                'source_manifests':[{ 'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)} for p in (apath,bpath)],
                'owner_review':'pending','blocking':False,'production_approved':False,'boards':rows,
                'missing_from_previous':sorted(new.keys()-old.keys()),'missing_from_candidate':sorted(old.keys()-new.keys())}
        (out/'comparison_manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print('COMPARISON BOARDS',len(rows),out);return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:print('STOP — '+str(exc));return 2
if __name__=='__main__':raise SystemExit(main())
