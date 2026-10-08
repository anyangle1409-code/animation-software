#!/usr/bin/env python3
"""Caption the shoulder-stage review renders and build before/after contact sheets (Pillow only, no bpy).

Inputs are the raw PNG directories written by render_shoulder_candidate_review.py for a003 and for the candidate with
identical cameras. Every output image carries the record identity and status in its caption, so no sheet can be read as
a canonical or accepted skeleton. Outputs are JPEG to keep the repository small; manifest.json lists sha256 of every file
and of the source blends/records.

  compose_shoulder_review.py --a003-views D --c001-views D --a003-poses D --c001-poses D --out REVIEW_DIR
"""
import argparse, hashlib, json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
CAND_DIR = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_proposal_c001'
SOURCES = {
    'a003_record': ROOT / 'ORIGINAL_V1_WORK/anatomy/character_fit_r95_a003.json',
    'a003_blend': ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend',
    'c001_record': CAND_DIR / 'candidate_record.json',
    'c001_blend': CAND_DIR / 'HGPT_ANATOMICAL_AUDIT_r95_a003_shoulder_proposal_c001.blend',
    'shoulder_solution': ROOT / 'ORIGINAL_V1_WORK/anatomy/canonical_shoulder_girdle_solution_182_v1.json',
}
LABEL = {
    'a003': ('BEFORE  r95_a003 (audit reference record; NOT canonical)', (230, 200, 120)),
    'c001': ('AFTER  r95_a003_shoulder_proposal_c001 - AUDIT PROPOSAL, NOT CANONICAL, NOT ACCEPTED', (120, 220, 235)),
}
FOOT = ('cyan = clavicle/scapula + scapula outline | yellow SC, white AC, magenta GH | body X-ray, mesh NOT refitted | '
        'shoulder height vs trunk OPEN (bony pitch 7.04 deg, IJ at a003)')
MAXW = 900


def font(size):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


F, FS = font(15), font(12)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def captioned(png, who, title):
    im = Image.open(png).convert('RGB')
    if im.width > MAXW:
        im = im.resize((MAXW, round(im.height * MAXW / im.width)), Image.LANCZOS)
    head, foot = 46, 20
    out = Image.new('RGB', (im.width, im.height + head + foot), (18, 18, 20))
    out.paste(im, (0, head))
    d = ImageDraw.Draw(out)
    text, col = LABEL[who]
    d.text((8, 4), text, fill=col, font=F)
    d.text((8, 25), title, fill=(235, 235, 235), font=F)
    d.text((8, head + im.height + 3), FOOT, fill=(170, 170, 170), font=FS)
    return out


def pair(a, b, title):
    w, h = a.width + b.width + 6, max(a.height, b.height) + 26
    s = Image.new('RGB', (w, h), (40, 40, 44))
    ImageDraw.Draw(s).text((8, 5), title, fill=(255, 255, 255), font=F)
    s.paste(a, (0, 26)); s.paste(b, (a.width + 6, 26))
    return s


def grid(ims, cols, title, tile_w=420):
    th = [im.resize((tile_w, round(im.height * tile_w / im.width)), Image.LANCZOS) for im in ims]
    rows = [th[i:i + cols] for i in range(0, len(th), cols)]
    hs = [max(t.height for t in r) for r in rows]
    s = Image.new('RGB', (cols * (tile_w + 4), sum(hs) + 4 * len(rows) + 30), (40, 40, 44))
    ImageDraw.Draw(s).text((8, 6), title, fill=(255, 255, 255), font=F)
    y = 30
    for r, rh in zip(rows, hs):
        for i, t in enumerate(r):
            s.paste(t, (i * (tile_w + 4), y))
        y += rh + 4
    return s


def save(im, p, files):
    p.parent.mkdir(parents=True, exist_ok=True)
    im.save(p, 'JPEG', quality=82, optimize=True)
    files[str(p.relative_to(ROOT))] = sha(p)


def main():
    ap = argparse.ArgumentParser()
    for k in ('a003-views', 'c001-views', 'a003-poses', 'c001-poses', 'out'):
        ap.add_argument('--' + k, required=True)
    o = ap.parse_args()
    out = Path(o.out).resolve()
    if out.exists():
        raise FileExistsError(out)
    files, cap = {}, {}
    views = sorted(p.stem for p in Path(o.c001_views).glob('*.png'))
    if views != sorted(p.stem for p in Path(o.a003_views).glob('*.png')):
        raise SystemExit('view sets differ between a003 and candidate')
    poses = sorted(p.stem for p in Path(o.c001_poses).glob('*.png'))
    for who, vd, pd in (('a003', o.a003_views, o.a003_poses), ('c001', o.c001_views, o.c001_poses)):
        for v in views:
            cap[(who, v)] = captioned(Path(vd) / f'{v}.png', who, f'view: {v}')
            save(cap[(who, v)], out / f'views_{who}' / f'{v}.jpg', files)
        for p in poses:
            t = f'{p}: illustrative humerus-subtree rotation about GH, bones only (scapula static; not a movement test)'
            cap[(who, p)] = captioned(Path(pd) / f'{p}.png', who, t)
            save(cap[(who, p)], out / f'poses_{who}' / f'{p}.jpg', files)
    for v in views + poses:
        save(pair(cap[('a003', v)], cap[('c001', v)], f'BEFORE (left) vs AFTER (right): {v}'), out / 'before_after' / f'{v}.jpg', files)
    groups = {
        'sheet_full_body_c001': [v for v in views if v.startswith('full_')],
        'sheet_upper_body_c001': [v for v in views if v.startswith('upper_')],
        'sheet_shoulder_left_c001': [v for v in views if v.endswith('left') or '_left_' in v],
        'sheet_shoulder_right_c001': [v for v in views if v.endswith('right') or '_right_' in v],
        'sheet_poses_c001': poses,
    }
    groups['sheet_shoulder_left_c001'] = [v for v in views if v.startswith(('shoulder_left', 'axilla_left'))]
    groups['sheet_shoulder_right_c001'] = [v for v in views if v.startswith(('shoulder_right', 'axilla_right'))]
    for name, vs in groups.items():
        save(grid([cap[('c001', v)] for v in vs], 3 if len(vs) > 4 else 2, f'{name}  (AUDIT PROPOSAL - NOT CANONICAL)'), out / 'sheets' / f'{name}.jpg', files)
    for side in ('left', 'right'):
        vs = [v for v in views if v.startswith((f'shoulder_{side}', f'axilla_{side}'))]
        ims = [x for v in vs for x in (cap[('a003', v)], cap[('c001', v)])]
        save(grid(ims, 2, f'BEFORE a003 (left column) vs AFTER c001 (right column): {side} shoulder + axilla'), out / 'sheets' / f'sheet_before_after_shoulder_{side}.jpg', files)
    ims = [x for p in poses for x in (cap[('a003', p)], cap[('c001', p)])]
    save(grid(ims, 2, 'BEFORE a003 (left) vs AFTER c001 (right): illustrative GH poses'), out / 'sheets' / 'sheet_before_after_poses.jpg', files)
    manifest = {
        'candidate_id': 'r95_a003_shoulder_proposal_c001', 'status': 'AUDIT_PROPOSAL_NOT_CANONICAL_NOT_ACCEPTED',
        'renderer': 'Blender Workbench via scripts/anatomy_fit/render_shoulder_candidate_review.py (identical cameras for both records)',
        'composer': 'scripts/anatomy_fit/compose_shoulder_review.py',
        'sources_sha256': {k: sha(p) for k, p in SOURCES.items()},
        'views': views, 'poses': poses,
        'pose_note': 'humerus subtree rotated rigidly about the GH centre; scapula/clavicle static (no scapulohumeral rhythm); mesh not skinned to the anatomical master; illustrative only',
        'files_sha256': files,
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
    print(len(files), 'images')


if __name__ == '__main__':
    main()
