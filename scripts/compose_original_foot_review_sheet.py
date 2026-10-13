#!/usr/bin/env python3
"""Phone-sized before/after foot review sheets from two render_original_foot_views_blender.py output folders (Pillow).

Each sheet: one view, BEFORE on top and AFTER below (portrait, 1080 px wide, iPhone-friendly), with a title, the view
name, the 10 mm grid / 50 mm bar note and up to six measurement lines taken from the verify JSON.

  python3 compose_original_foot_review_sheet.py --before DIR --after DIR --verify JSON --out DIR [--after-label C2]
"""
import argparse, json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W = 1080


def font(size):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/dejavu/DejaVuSans.ttf'):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser()
    for a in ('--before', '--after', '--verify', '--out'):
        ap.add_argument(a, required=True)
    ap.add_argument('--after-label', default='C2')
    o = ap.parse_args()
    v = json.loads(Path(o.verify).read_text())
    if 'neutral_plusX_foot' in v:                    # skeleton candidate verify report
        a, c = v['neutral_plusX_foot']['parent'], v['neutral_plusX_foot']['candidate']
        lines = [f"Foot length {a['length_mm']:.1f} -> {c['length_mm']:.1f} mm (ANSUR 1.82 m: 279.9 +/- 9.1)",
                 f"Heel to MTP1 {a['heel_to_MTP1_station_mm']:.1f} -> {c['heel_to_MTP1_station_mm']:.1f} mm (ANSUR 207.4 +/- 7.8)",
                 f"Heel behind ankle {a['heel_behind_AJC_mm']:.1f} -> {c['heel_behind_AJC_mm']:.1f} mm (provisional 60)",
                 f"Lowest toe skin {a['lowest_toe_skin_mm']:.1f} -> {c['lowest_toe_skin_mm']:.1f} mm; breadth {c['breadth_mm']:.1f} mm",
                 f"Foot bones changed {v['master_bones_changed']}; stations inside skin {v['containment']['stations'] - len(v['containment']['candidate_outside'])}/{v['containment']['stations']}; {v['verdict']}"]
    else:
        nb, nc = v['neutral']['parent']['plusX'], v['neutral']['candidate']['plusX']
        lines = [f"Foot length {nb['length_mm']:.1f} -> {nc['length_mm']:.1f} mm (unchanged; ANSUR 1.82 m: 279.9 +/- 9.1)",
                 f"Breadth {nb['breadth_mm']:.1f} -> {nc['breadth_mm']:.1f} mm",
                 f"Lowest toe skin {nb['toe_region_min_z_mm']:.1f} -> {nc['toe_region_min_z_mm']:.1f} mm above floor",
                 f"Skeleton/weights/rig unchanged: {all(v['protected_identical'].values())}; stations outside skin: {len(v['containment']['candidate_outside'])}",
                 f"Symmetry max {v['symmetry_max_m'] * 1000:.4f} mm; verdict {v['verdict']}"]
    out = Path(o.out); out.mkdir(parents=True, exist_ok=True)
    f_t, f_s = font(40), font(27)
    made = []
    for p in sorted(Path(o.before).glob('*.png')):
        q = Path(o.after) / p.name
        if not q.exists():
            continue
        ia, ib = (Image.open(x).convert('RGB').resize((W, W)) for x in (p, q))
        head, foot = 110, 40 + 38 * len(lines)
        sheet = Image.new('RGB', (W, head + 2 * W + 60 + foot), (250, 250, 248))
        d = ImageDraw.Draw(sheet)
        d.text((24, 18), f'ORIGINAL_v1 foot - {p.stem}', fill=(20, 20, 30), font=f_t)
        d.text((24, 70), 'orthographic, neutral rest pose; grid 10 mm, bar 50 mm', fill=(80, 80, 90), font=f_s)
        y = head
        for img, lab in ((ia, 'BEFORE (a003 native)'), (ib, f'AFTER ({o.after_label} review candidate, not accepted)')):  # noqa
            sheet.paste(img, (0, y + 30)); d.text((24, y), lab, fill=(150, 40, 30) if 'BEFORE' in lab else (20, 100, 50), font=f_s)
            y += W + 30
        y += 10
        for ln in lines:
            d.text((24, y), ln, fill=(20, 20, 30), font=f_s); y += 38
        dst = out / f'{p.stem}_before_after.jpg'
        sheet.save(dst, quality=86); made.append(dst.name)
    print('sheets', made)


if __name__ == '__main__':
    main()
