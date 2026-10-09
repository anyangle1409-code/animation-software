#!/usr/bin/env python3
"""Sagittal coordinate diagram (NOT a Blender render): c004 spine vs the rejected P003 re-partition and the P002 bottom-up
chain, with rib heads, the P1 S1 centre and the ANSUR 1.82 m heights. Every mark is drawn from committed coordinates.

  plot_spine_sagittal_diagnostic.py --p002 JSON --p003 RECORD --closure JSON --out PNG
"""
import argparse, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
C004 = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json'
CHAIN = ['l5', 'l4', 'l3', 'l2', 'l1'] + [f't{i}' for i in range(12, 0, -1)] + ['c7', 'c6', 'c5', 'c4', 'c3', 'c2']


def main():
    ap = argparse.ArgumentParser()
    for a in ('--p002', '--p003', '--closure', '--out'):
        ap.add_argument(a, required=True)
    o = ap.parse_args()
    c4 = json.loads(C004.read_text())['bones']; p3 = json.loads(Path(o.p003).read_text())['bones']
    p2 = json.loads(Path(o.p002).read_text()); cl = json.loads(Path(o.closure).read_text())['detail']
    W, H = 1100, 1400; z0, z1 = 1000.0, 1700.0; y0 = -120.0; sc = (H - 120) / (z1 - z0)
    img = Image.new('RGB', (W, H), (247, 247, 244)); d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18); fs = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
    except OSError:
        f = fs = ImageFont.load_default()

    def P(y_mm, z_mm):      # anterior (-Y) to the LEFT of the picture, posterior to the right
        return (60 + (y_mm - y0) * sc, H - 60 - (z_mm - z0) * sc)
    for z in range(1000, 1701, 50):
        d.line([P(y0, z), P(y0 + (W - 120) / sc, z)], fill=(225, 225, 220)); d.text((8, P(0, z)[1] - 8), str(z), fill=(110, 110, 110), font=fs)
    for y in range(-100, 260, 50):
        d.line([P(y, z0), P(y, z1)], fill=(232, 232, 228)); d.text((P(y, z0)[0] - 14, H - 50), str(y), fill=(110, 110, 110), font=fs)
    d.text((60, H - 30), 'Y mm (anterior <-  -> posterior)      Z mm above floor      sagittal plane X = 0', fill=(60, 60, 60), font=fs)

    def sticks(B, col, w):
        for n in CHAIN:
            h, t = B[n]['head_m'], B[n]['tail_m']
            d.line([P(1000 * h[1], 1000 * h[2]), P(1000 * t[1], 1000 * t[2])], fill=col, width=w)
            for e in (h, t):
                x, y = P(1000 * e[1], 1000 * e[2]); d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=col)
    sticks(c4, (40, 90, 170), 9)
    sticks(p3, (215, 120, 30), 4)
    key = 'ansur_closed|specimen_shape|reinhold_segmental'
    pts = [(n, v['rebuilt_yz_mm']) for n, v in p2['detail'][key]['levels'].items()]
    for (_, a), (_, b) in zip(pts, pts[1:]):
        d.line([P(*a), P(*b)], fill=(40, 150, 90), width=3)
    for n, a in pts:
        x, y = P(*a); d.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(40, 150, 90), width=2)
    for i in range(1, 13):
        h = c4[f'rib_{i:02d}_left']['head_m']; x, y = P(1000 * h[1], 1000 * h[2])
        d.rectangle([x - 5, y - 5, x + 5, y + 5], outline=(150, 40, 40), width=2); d.text((x + 8, y - 8), f'r{i}', fill=(150, 40, 40), font=fs)
    s1 = p2['P1_S1_yz_mm']; x, y = P(*s1); d.polygon([(x, y - 9), (x - 8, y + 6), (x + 8, y + 6)], fill=(40, 150, 90))
    d.text((x - 120, y + 4), 'P1 S1 centre', fill=(40, 150, 90), font=fs)
    for label, z, col in [('ANSUR suprasternale 1494.5', cl['IJ_height']['ANSUR_182']['prediction_mm'], (120, 60, 160)),
                          ('ANSUR tenth rib 1166.8', cl['rib10_height']['ANSUR_182']['prediction_mm'], (120, 60, 160)),
                          ('ANSUR cervicale 1575.2', cl['C7_height']['ANSUR_cervicale_mm'], (120, 60, 160))]:
        d.line([P(-110, z), P(-30, z)], fill=col, width=2); d.text((P(-110, z)[0], P(-110, z)[1] - 20), label, fill=col, font=fs)
    ij = cl['IJ_height']['record_ij_skin_mm']; d.line([P(-60, ij), P(-20, ij)], fill=(40, 90, 170), width=3)
    d.text((P(-60, ij)[0], P(-60, ij)[1] - 20), 'c004 IJ skin', fill=(40, 90, 170), font=fs)
    leg = [((40, 90, 170), 'c004 vertebral sticks (zero disc gaps)'), ((215, 120, 30), 'P003 re-partition on the c004 curve (REJECTED: rib levels)'),
           ((40, 150, 90), 'P002 bottom-up chain from P1 S1 (ANSUR-closed, specimen tilt shape)'), ((150, 40, 40), 'c004 rib heads (left)')]
    for i, (c, t) in enumerate(leg):
        d.rectangle([W - 560, 60 + 28 * i, W - 540, 76 + 28 * i], fill=c); d.text((W - 532, 58 + 28 * i), t, fill=(40, 40, 40), font=fs)
    d.text((20, 18), 'Spine sagittal diagnostic (coordinate diagram, not a render)', fill=(20, 20, 20), font=f)
    img.save(o.out, quality=92)
    print(o.out)


if __name__ == '__main__':
    main()
