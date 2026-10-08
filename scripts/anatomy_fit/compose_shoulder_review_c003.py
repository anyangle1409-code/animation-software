#!/usr/bin/env python3
"""c003 review evidence: captioned c003 singles and four-way a003 / c001 / c002 / c003 comparisons on identical cameras
(Pillow only; helpers from compose_shoulder_review.py, which is not modified).

  compose_shoulder_review_c003.py --views a003=D,c001=D,c002=D,c003=D --poses a003=D,c001=D,c002=D,c003=D --out DIR
"""
import argparse, json, sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compose_shoulder_review as m  # noqa: E402

ROOT = m.ROOT
C3 = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c003_ansur_coupled'
ORDER = ('a003', 'c001', 'c002', 'c003')
m.LABEL['c002'] = ('c002 ANSUR-height shoulder-only drop - AUDIT, NOT CANONICAL - SC CLOSURE FAIL', (255, 150, 120))
m.LABEL['c003'] = ('c003 coupled upper-thorax + shoulder (ANSUR) - AUDIT PROPOSAL, NOT CANONICAL, NOT ACCEPTED', (140, 235, 140))
m.LABEL['a003'] = ('a003 baseline (audit record; NOT canonical)', (230, 200, 120))
m.LABEL['c001'] = ('c001 reconciled girdle on a003 notch - AUDIT, NOT CANONICAL', (120, 220, 235))
FOOTS = {
    'a003': 'yellow SC, white AC, magenta GH | cyan clavicle/scapula | mesh NOT refitted',
    'c001': 'girdle reconciled to sources; shoulder 63 mm above ANSUR acromial height (known defect) | mesh NOT refitted',
    'c002': 'girdle dropped 63.0 mm; SC 56.2 mm below the retained a003 notch (closure FAIL) | mesh NOT refitted',
    'c003': 'sternum -24.7 z / +14.7 posterior; ribs 1-10 follow; IJ 1494.5, acromion 1497.7 (ANSUR); clavicle 1.1 deg | mesh NOT refitted',
}


def cap(png, who, title):
    m.FOOT = FOOTS[who]
    return m.captioned(png, who, title)


def parse(s):
    return dict(x.split('=', 1) for x in s.split(','))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--views', required=True); ap.add_argument('--poses', required=True); ap.add_argument('--out', required=True)
    o = ap.parse_args()
    out = Path(o.out).resolve()
    if out.exists():
        raise FileExistsError(out)
    vd, pd = parse(o.views), parse(o.poses)
    views = sorted(p.stem for p in Path(vd['c003']).glob('*.png'))
    poses = sorted(p.stem for p in Path(pd['c003']).glob('*.png'))
    for w in ORDER:
        if sorted(p.stem for p in Path(vd[w]).glob('*.png')) != views or sorted(p.stem for p in Path(pd[w]).glob('*.png')) != poses:
            raise SystemExit(f'view/pose sets differ for {w}')
    files, Cp = {}, {}
    pose_t = '{}: illustrative humerus-subtree rotation about GH, bones only (scapula static; not a movement test)'
    for w in ORDER:
        for v in views:
            Cp[(w, v)] = cap(Path(vd[w]) / f'{v}.png', w, f'view: {v}')
        for p in poses:
            Cp[(w, p)] = cap(Path(pd[w]) / f'{p}.png', w, pose_t.format(p))
    for v in views:
        m.save(Cp[('c003', v)], out / 'views_c003' / f'{v}.jpg', files)
    for p in poses:
        m.save(Cp[('c003', p)], out / 'poses_c003' / f'{p}.jpg', files)
    for v in views + poses:
        m.save(m.grid([Cp[(w, v)] for w in ORDER], 4, f'a003 | c001 | c002 | c003 : {v}', tile_w=380), out / 'four_way' / f'{v}.jpg', files)
    groups = {'body': [v for v in views if v.startswith(('full_', 'upper_'))],
              'shoulder_left': [v for v in views if v.startswith(('shoulder_left', 'axilla_left'))],
              'shoulder_right': [v for v in views if v.startswith(('shoulder_right', 'axilla_right'))],
              'overhead': [v for v in views if v.endswith('overhead')], 'poses': poses}
    for g, vs in groups.items():
        ims = [Cp[(w, v)] for v in vs for w in ORDER]
        m.save(m.grid(ims, 4, f'Columns a003 | c001 | c002 | c003 - {g} (identical cameras; all AUDIT, NOT CANONICAL)', tile_w=360),
               out / 'sheets' / f'sheet_four_way_{g}.jpg', files)
        m.save(m.grid([Cp[('c003', v)] for v in vs], 3 if len(vs) > 4 else 2, f'c003 {g} (AUDIT PROPOSAL - NOT CANONICAL)'),
               out / 'sheets' / f'sheet_c003_{g}.jpg', files)
    rec = json.loads((C3 / 'candidate_record.json').read_text())['candidate']
    manifest = {'candidate_id': rec['id'], 'status': rec['status'], 'acceptance_summary': rec['acceptance_checks']['summary'],
                'renderer': 'scripts/anatomy_fit/render_shoulder_candidate_review.py (identical cameras for a003, c001, c002, c003)',
                'composer': 'scripts/anatomy_fit/compose_shoulder_review_c003.py',
                'sources_sha256': dict({k: m.sha(p) for k, p in m.SOURCES.items()},
                                       c002_record=m.sha(ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_proposal_c002_ansur_height/candidate_record.json'),
                                       c003_record=m.sha(C3 / 'candidate_record.json'),
                                       c003_blend=m.sha(C3 / 'HGPT_ANATOMICAL_AUDIT_r95_a003_shoulder_thorax_c003_ansur_coupled.blend')),
                'views': views, 'poses': poses, 'files_sha256': files}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
    print(len(files), 'images')


if __name__ == '__main__':
    main()
