#!/usr/bin/env python3
"""Labelled side-by-side movement clips (animated GIF) and keyframe sheets from render_movement_clips.py frames
(Pillow only). Left panel a003 (baseline), right panel c001 (shoulder audit proposal); identical cameras and frames.

  compose_movement_clips.py --a003 DIR --c001 DIR --out DIR [--right-label TEXT]   (--c001 is the right-panel frames)
"""
import argparse, hashlib, json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
NOTE = 'Phase 9 isolated test, solver-keyed (ST rhythm + clavicle followers); bones only, mesh not skinned; NOT CANONICAL; not a functional/Phase 10 test'


def font(n):
    p = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    return ImageFont.truetype(str(p), n) if p.exists() else ImageFont.load_default()


F, FS = font(14), font(11)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def panel(png, label, col, w=420):
    im = Image.open(png).convert('RGB').resize((w, w))
    out = Image.new('RGB', (w, w + 22), (18, 18, 20))
    out.paste(im, (0, 22)); ImageDraw.Draw(out).text((6, 4), label, fill=col, font=F)
    return out


RIGHT = {'label': 'c001 shoulder audit proposal', 'colour': (120, 220, 235)}


def frame(a_png, c_png, test, view, f):
    a = panel(a_png, 'a003 baseline (audit record)', (230, 200, 120))
    c = panel(c_png, RIGHT['label'], RIGHT['colour'])
    W = a.width * 2 + 6
    s = Image.new('RGB', (W, a.height + 52), (40, 40, 44))
    d = ImageDraw.Draw(s)
    d.text((6, 4), f'{test} | {view} | frame {f}', fill=(255, 255, 255), font=F)
    s.paste(a, (0, 24)); s.paste(c, (a.width + 6, 24))
    d.text((6, a.height + 30), NOTE, fill=(170, 170, 170), font=FS)
    return s


def main():
    ap = argparse.ArgumentParser()
    for k in ('--a003', '--c001', '--out'):
        ap.add_argument(k, required=True)
    ap.add_argument('--right-label', default=RIGHT['label'], help='label of the right panel (directory given by --c001)')
    ap.add_argument('--note', default=None, help='caption note (default: the isolated-test note)')
    o = ap.parse_args()
    RIGHT['label'] = o.right_label
    global NOTE
    if o.note:
        NOTE = o.note
    out = Path(o.out).resolve()
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    ma = json.loads((Path(o.a003) / 'clips_manifest.json').read_text())['tests']
    mc = json.loads((Path(o.c001) / 'clips_manifest.json').read_text())['tests']
    if ma != mc:
        raise SystemExit('frame sets differ between a003 and c001')
    files = {}
    for key, v in mc.items():
        test, view = key.split('/')
        frames = [frame(Path(o.a003) / test / view / f'f{f:05d}.png', Path(o.c001) / test / view / f'f{f:05d}.png', test, view, f) for f in v['frames']]
        g = out / f'{test}__{view}.gif'
        frames[0].save(g, save_all=True, append_images=frames[1:], duration=120, loop=0, optimize=True)
        files[str(g.relative_to(ROOT))] = sha(g)
        n = len(frames); pick = sorted({0, n // 8, n // 4, 3 * n // 8, n // 2 - 1})
        th = [frames[i].resize((frames[i].width // 2, frames[i].height // 2)) for i in pick]
        sheet = Image.new('RGB', (th[0].width, th[0].height * len(th)), (40, 40, 44))
        for i, t in enumerate(th):
            sheet.paste(t, (0, i * t.height))
        p = out / f'{test}__{view}__keyframes.jpg'; sheet.save(p, 'JPEG', quality=84); files[str(p.relative_to(ROOT))] = sha(p)
    (out / 'manifest.json').write_text(json.dumps({'note': NOTE, 'a003_frames': o.a003, 'right_frames': o.c001, 'right_label': RIGHT['label'],
                                                    'renderer': 'scripts/anatomy_fit/render_movement_clips.py',
                                                    'composer': 'scripts/anatomy_fit/compose_movement_clips.py',
                                                    'tests': mc, 'files_sha256': files}, indent=1) + '\n')
    print(len(files), 'files')


if __name__ == '__main__':
    main()
