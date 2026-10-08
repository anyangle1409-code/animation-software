#!/usr/bin/env python3
"""Captioned c002 review images and before/after sheets (c001 vs c002, a003 vs c002). Pillow only.

Reuses compose_shoulder_review.py helpers unchanged (that script and the c001 review set are not modified). Captions carry
each record's identity and status; every c002 image states the SC closure FAIL. Only c002 singles, pairs and sheets are
written (the a003/c001 singles already live in the c001 review set).

  compose_shoulder_review_c002.py --a003-views D --c001-views D --c002-views D --a003-poses D --c001-poses D --c002-poses D --out DIR
"""
import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compose_shoulder_review as m  # noqa: E402

ROOT = m.ROOT
C2 = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_proposal_c002_ansur_height'
m.LABEL['c002'] = ('AFTER  r95_a003_shoulder_proposal_c002_ansur_height - AUDIT PROPOSAL, NOT CANONICAL - SC CLOSURE FAIL', (255, 150, 120))
FOOTS = {
    'a003': m.FOOT,
    'c001': m.FOOT,
    'c002': ('cyan = clavicle/scapula + outline | yellow SC, white AC, magenta GH | girdle+arm dropped 63.0 mm: LM27 at ANSUR acromial '
             'height (owner policy) | SC 56.2 mm below retained notch | mesh NOT refitted'),
}
SOURCES = dict(m.SOURCES, c002_record=C2 / 'candidate_record.json',
               c002_blend=C2 / 'HGPT_ANATOMICAL_AUDIT_r95_a003_shoulder_proposal_c002_ansur_height.blend')


def cap(png, who, title):
    m.FOOT = FOOTS[who]
    return m.captioned(png, who, title)


def main():
    ap = argparse.ArgumentParser()
    for k in ('a003-views', 'c001-views', 'c002-views', 'a003-poses', 'c001-poses', 'c002-poses', 'out'):
        ap.add_argument('--' + k, required=True)
    o = ap.parse_args()
    out = Path(o.out).resolve()
    if out.exists():
        raise FileExistsError(out)
    vdir = {'a003': o.a003_views, 'c001': o.c001_views, 'c002': o.c002_views}
    pdir = {'a003': o.a003_poses, 'c001': o.c001_poses, 'c002': o.c002_poses}
    views = sorted(p.stem for p in Path(o.c002_views).glob('*.png'))
    poses = sorted(p.stem for p in Path(o.c002_poses).glob('*.png'))
    for who in vdir:
        if sorted(p.stem for p in Path(vdir[who]).glob('*.png')) != views or sorted(p.stem for p in Path(pdir[who]).glob('*.png')) != poses:
            raise SystemExit(f'view/pose sets differ for {who}')
    files, C = {}, {}
    pose_t = '{}: illustrative humerus-subtree rotation about GH, bones only (scapula static; not a movement test)'
    for who in vdir:
        for v in views:
            C[(who, v)] = cap(Path(vdir[who]) / f'{v}.png', who, f'view: {v}')
        for p in poses:
            C[(who, p)] = cap(Path(pdir[who]) / f'{p}.png', who, pose_t.format(p))
    for v in views:
        m.save(C[('c002', v)], out / 'views_c002' / f'{v}.jpg', files)
    for p in poses:
        m.save(C[('c002', p)], out / 'poses_c002' / f'{p}.jpg', files)
    for base in ('c001', 'a003'):
        for v in views + poses:
            m.save(m.pair(C[(base, v)], C[('c002', v)], f'BEFORE {base} (left) vs AFTER c002 (right): {v}'),
                   out / f'before_after_{base}_vs_c002' / f'{v}.jpg', files)
        for side in ('left', 'right'):
            vs = [v for v in views if v.startswith((f'shoulder_{side}', f'axilla_{side}'))]
            ims = [x for v in vs for x in (C[(base, v)], C[('c002', v)])]
            m.save(m.grid(ims, 2, f'BEFORE {base} (left column) vs AFTER c002 (right column): {side} shoulder + axilla'),
                   out / 'sheets' / f'sheet_{base}_vs_c002_shoulder_{side}.jpg', files)
        ims = [x for v in views if v.startswith(('full_', 'upper_')) for x in (C[(base, v)], C[('c002', v)])]
        m.save(m.grid(ims, 2, f'BEFORE {base} (left column) vs AFTER c002 (right column): full and upper body'),
               out / 'sheets' / f'sheet_{base}_vs_c002_body.jpg', files)
        ims = [x for p in poses for x in (C[(base, p)], C[('c002', p)])]
        m.save(m.grid(ims, 2, f'BEFORE {base} (left) vs AFTER c002 (right): illustrative GH poses'),
               out / 'sheets' / f'sheet_{base}_vs_c002_poses.jpg', files)
    rec = json.loads((C2 / 'candidate_record.json').read_text())['candidate']
    manifest = {
        'candidate_id': rec['id'], 'status': rec['status'], 'closure_vs_retained_trunk': rec['closure_vs_retained_trunk']['status'],
        'renderer': 'Blender Workbench via scripts/anatomy_fit/render_shoulder_candidate_review.py (identical cameras for a003, c001, c002)',
        'composer': 'scripts/anatomy_fit/compose_shoulder_review_c002.py (helpers from compose_shoulder_review.py)',
        'sources_sha256': {k: m.sha(p) for k, p in SOURCES.items()},
        'views': views, 'poses': poses,
        'pose_note': 'humerus subtree rotated rigidly about the GH centre; scapula/clavicle static; mesh not skinned to the anatomical master; illustrative only',
        'files_sha256': files,
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
    print(len(files), 'images')


if __name__ == '__main__':
    main()
