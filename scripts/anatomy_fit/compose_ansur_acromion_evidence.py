#!/usr/bin/env python3
"""Captioned evidence for the ANSUR acromion correspondence audit (Pillow only): labelled close-ups, a chart of the
clavicle elevation each mapping needs, a contact sheet and a sha256 manifest.

  compose_ansur_acromion_evidence.py --renders DIR --out DIR
"""
import argparse, hashlib, json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/shoulder_ansur_acromion_correspondence_v1.json'
TITLE = 'ANSUR ACROMION CORRESPONDENCE AUDIT - NOT CANONICAL - NO c003 (absolute ANSUR height infeasible with SC closed)'
LEGEND = ('cyan c001 girdle | red ball LM25 exterior acromial angle | orange LM27 lateral distal extent | green/blue: border crossing of '
          'clavicle-axis / lateral line | magenta plane ANSUR acromial 1497.7 mm | yellow plane a003 notch | RED ghost: least-departure pose '
          'for absolute height (clavicle -6.9 deg) | GREEN ghost: within-subject relation (clavicle 1.1 deg)')


def font(n):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',):
        if Path(p).exists():
            return ImageFont.truetype(p, n)
    return ImageFont.load_default()


F, FS = font(15), font(11)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def wrap(d, text, x, y, width, f, fill):
    line = ''
    for w in text.split(' '):
        t = (line + ' ' + w).strip()
        if d.textlength(t, font=f) > width:
            d.text((x, y), line, fill=fill, font=f); y += f.size + 3; line = w
        else:
            line = t
    d.text((x, y), line, fill=fill, font=f)
    return y + f.size + 3


def caption(png, view):
    im = Image.open(png).convert('RGB')
    head, foot = 48, 62
    out = Image.new('RGB', (im.width, im.height + head + foot), (18, 18, 20))
    out.paste(im, (0, head)); d = ImageDraw.Draw(out)
    wrap(d, TITLE, 8, 4, im.width - 16, FS, (255, 150, 120))
    d.text((8, 28), f'view: {view}  (world: bony thorax pitch, IJ at a003 bony IJ)', fill=(235, 235, 235), font=F)
    wrap(d, LEGEND, 8, head + im.height + 4, im.width - 16, FS, (180, 180, 180))
    return out


def chart(A):
    rows = []
    for k, v in A['feasibility'].items():
        for t, short in (('absolute_ANSUR_acromial_height', 'absolute 1497.7'), ('ANSUR_within_subject_IJ_plus_3.1', 'within-subject')):
            s = v[t]['clavicle_and_scapula_min_chi2']
            rows.append((k.replace('_deg__', ' | ').replace('living_ANSUR_implied', 'living pitch').replace('bony_specimen', 'bony pitch'), short,
                         s['clavicle_elevation_deg'], s['max_abs_z']))
    W, rowh, left = 1500, 26, 760
    H = 120 + rowh * len(rows) + 60
    im = Image.new('RGB', (W, H), (250, 250, 248)); d = ImageDraw.Draw(im)
    d.text((16, 10), 'Clavicle elevation required with SC closed on the a003 notch (scapular angles free, least joint departure)', fill=(20, 20, 20), font=F)
    d.text((16, 32), 'Source: Matsumura male standing 8 +/- 4 deg (band = mean +/- 2 SD, labelled screening line, not a published range). Bars: red = |z| > 2 on some angle.', fill=(60, 60, 60), font=FS)
    x0, x1, lo, hi = left, W - 40, -16.0, 18.0
    X = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
    top = 70
    d.rectangle([X(0), top, X(16), top + rowh * len(rows)], fill=(220, 238, 220))
    d.line([X(8), top, X(8), top + rowh * len(rows)], fill=(40, 140, 40), width=2)
    for tick in range(-16, 19, 4):
        d.line([X(tick), top + rowh * len(rows), X(tick), top + rowh * len(rows) + 6], fill=(60, 60, 60))
        d.text((X(tick) - 8, top + rowh * len(rows) + 8), f'{tick}', fill=(40, 40, 40), font=FS)
    d.line([X(0), top, X(0), top + rowh * len(rows)], fill=(80, 80, 80))
    for i, (name, t, e, mz) in enumerate(rows):
        y = top + i * rowh
        d.text((16, y + 6), f'{name}  [{t}]', fill=(20, 20, 20), font=FS)
        col = (200, 50, 40) if mz > 2 else (40, 140, 60)
        d.rectangle([min(X(0), X(e)), y + 5, max(X(0), X(e)), y + rowh - 5], fill=col)
        lab = f'{e:+.1f} deg (max|z| {mz:.2f})'
        d.text((X(e) + 6 if e >= 0 else X(e) - d.textlength(lab, font=FS) - 6, y + 6), lab, fill=(20, 20, 20), font=FS)
    d.text((16, H - 30), 'deg clavicle elevation (thorax frame)', fill=(40, 40, 40), font=FS)
    return im


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--renders', required=True); ap.add_argument('--out', required=True)
    o = ap.parse_args()
    out = Path(o.out).resolve()
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    A = json.loads(AUDIT.read_text())
    files, caps = {}, {}
    for png in sorted(Path(o.renders).glob('*.png')):
        caps[png.stem] = caption(png, png.stem)
        p = out / f'{png.stem}.jpg'; caps[png.stem].save(p, 'JPEG', quality=84); files[str(p.relative_to(ROOT))] = sha(p)
    p = out / 'chart_required_clavicle_elevation.png'; chart(A).save(p); files[str(p.relative_to(ROOT))] = sha(p)
    order = ['left_front', 'left_side', 'left_rear', 'left_overhead', 'right_front', 'right_side', 'right_rear', 'right_overhead']
    tw = 450
    th = [caps[k].resize((tw, round(caps[k].height * tw / caps[k].width))) for k in order]
    sheet = Image.new('RGB', (4 * tw, 2 * th[0].height + 30), (40, 40, 44))
    ImageDraw.Draw(sheet).text((8, 6), TITLE, fill=(255, 255, 255), font=F)
    for i, t in enumerate(th):
        sheet.paste(t, ((i % 4) * tw, 30 + (i // 4) * t.height))
    p = out / 'sheet_shoulders_both_sides.jpg'; sheet.save(p, 'JPEG', quality=84); files[str(p.relative_to(ROOT))] = sha(p)
    (out / 'manifest.json').write_text(json.dumps({
        'audit': str(AUDIT.relative_to(ROOT)), 'audit_sha256': sha(AUDIT), 'status': A['status'],
        'renderer': 'scripts/anatomy_fit/render_ansur_acromion_evidence.py (geometry: python3; render: Blender Workbench on the c001 audit blend, read-only)',
        'composer': 'scripts/anatomy_fit/compose_ansur_acromion_evidence.py',
        'c001_blend_sha256': sha(ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_proposal_c001/HGPT_ANATOMICAL_AUDIT_r95_a003_shoulder_proposal_c001.blend'),
        'files_sha256': files}, indent=1) + '\n')
    print(len(files), 'files')


if __name__ == '__main__':
    main()
