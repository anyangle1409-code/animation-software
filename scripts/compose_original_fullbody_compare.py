#!/usr/bin/env python3
"""Phone sheets (1080 px wide) comparing full-body renders of two ORIGINAL_v1 candidates view by view (PIL only).

  python3 compose_original_fullbody_compare.py --left DIR --right DIR --left-label A --right-label B --out DIR
         [--title T] [--line TEXT ...]
"""
import argparse, textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def main():
    ap = argparse.ArgumentParser()
    for a in ('--left', '--right', '--left-label', '--right-label', '--out'):
        ap.add_argument(a, required=True)
    ap.add_argument('--title', default='ORIGINAL_v1 full body')
    ap.add_argument('--line', action='append', default=[])
    ap.add_argument('--subtitle', default='same camera and scale; bar 0.5 m')
    o = ap.parse_args()
    big, small = ImageFont.truetype(FONT, 38), ImageFont.truetype(FONT, 24)
    out = Path(o.out); out.mkdir(parents=True, exist_ok=True)
    for f in sorted(Path(o.left).glob('*.png')):
        g = Path(o.right) / f.name
        if not g.exists():
            continue
        a, b = (Image.open(p).convert('RGB') for p in (f, g))
        tw = 540; th = int(a.height * tw / a.width)
        a, b = a.resize((tw, th)), b.resize((tw, th))
        lines = [part for L in o.line for part in textwrap.wrap(L, 76)]
        head, foot = 150, 30 + 34 * len(lines)
        sheet = Image.new('RGB', (1080, head + th + foot), (249, 249, 247)); d = ImageDraw.Draw(sheet)
        d.text((24, 14), o.title, font=big, fill=(20, 20, 20))
        d.text((24, 64), f'view: {f.stem}; {o.subtitle}', font=small, fill=(80, 80, 80))
        d.text((24, 106), o.left_label, font=small, fill=(150, 30, 30))
        d.text((564, 106), o.right_label, font=small, fill=(20, 110, 50))
        sheet.paste(a, (0, head)); sheet.paste(b, (540, head))
        y = head + th + 14
        for L in lines:
            d.text((24, y), L, font=small, fill=(20, 20, 20)); y += 34
        sheet.save(out / f'{f.stem}_compare.jpg', quality=84)
    print('sheets in', out)


if __name__ == '__main__':
    main()
