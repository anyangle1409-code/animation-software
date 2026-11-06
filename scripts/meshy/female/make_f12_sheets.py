"""Compose the FEMALE F12 chest / shorts validation sheets, F11a (before) against the F12 candidate (after). PIL.

  01_chest_before_after      chest with and without the bra: front, 3/4, side, sternum
  02_shorts_before_after     body + shorts: front, back, side, from below
  03_body_shorts_separate    shorts only and body only: front, from below
  04_clearance_diagnostic    body coloured by clearance under the garments (red = skin outside the fabric)
  05_chest_sections          sections z 1.20, x 0, x 0.085 (chest_sections_draw.py outputs sec_<prefix>.png)
  06_hip_flexion_check       limited hip-flexion clearance poses (hip_flexion_clearance_f_blender.py renders, hip/)
  07_arm_elevation_check     limited arm-elevation poses (chest_bra_elevation_test_f_blender.py renders, elev/)

usage: python3.11 make_f12_sheets.py <render dir> <out dir> [candidate prefix, default F12d]
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

D, OUT = Path(sys.argv[1]), Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
CAND = sys.argv[3] if len(sys.argv) > 3 else "F12d"
BG = (78, 80, 86); H = 520


def tile(name, text):
    p = D / f"{name}.png"
    im = Image.open(p).convert("RGB") if p.exists() else Image.new("RGB", (H, H), BG)
    im = im.resize((int(im.width * H / im.height), H)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, im.width, 24], fill=(30, 32, 36)); d.text((8, 6), text, fill=(235, 235, 235)); return im


def sheet(views, title, fn):
    rows = []
    for pfx in ("F11a", CAND):
        ims = [tile(f"{pfx}_{v}", f"{pfx}  {lbl}") for v, lbl in views]
        r = Image.new("RGB", (sum(i.width for i in ims), H), BG); x = 0
        for i in ims:
            r.paste(i, (x, 0)); x += i.width
        rows.append(r)
    o = Image.new("RGB", (max(r.width for r in rows), 2 * H + 36), BG)
    ImageDraw.Draw(o).text((10, 11), title + f"   (top: F11a before, bottom: {CAND} candidate)", fill=(255, 255, 255))
    o.paste(rows[0], (0, 36)); o.paste(rows[1], (0, 36 + H)); o.save(OUT / fn, quality=90)


sheet([("chest_bra_front", "bra front"), ("chest_bra_q34", "bra 3/4"), ("chest_bra_side", "bra side"), ("sternum_bra", "bra sternum"),
       ("chest_body_front", "body front"), ("chest_body_q34", "body 3/4"), ("chest_body_side", "body side"), ("sternum_body", "body sternum")],
      "Female chest with and without the sports bra (clay)", "01_chest_before_after.jpg")
sheet([("shorts_front", "front"), ("shorts_back", "back"), ("shorts_side", "side"), ("shorts_under", "from below")],
      "Female shorts on the body (clay)", "02_shorts_before_after.jpg")
sheet([("shorts_only_front", "shorts only front"), ("shorts_only_under", "shorts only below"), ("body_only_front", "body only front"), ("body_only_under", "body only below")],
      "Female body and shorts separately (clay)", "03_body_shorts_separate.jpg")
sheet([("diag_front", "front"), ("diag_chest", "chest"), ("diag_under", "from below")],
      "Clearance under the garments: green >= 1 mm, yellow 0-1 mm, RED skin outside fabric, grey uncovered", "04_clearance_diagnostic.jpg")


def grid(rows, title, fn, h=420):
    ims = [[tile2(p, t, h) for p, t in r] for r in rows]; w = max(sum(i.width for i in r) for r in ims)
    o = Image.new("RGB", (w, h * len(ims) + 36), BG); ImageDraw.Draw(o).text((10, 11), title, fill=(255, 255, 255))
    for k, r in enumerate(ims):
        x = 0
        for i in r:
            o.paste(i, (x, 36 + k * h)); x += i.width
    o.save(OUT / fn, quality=90)


def tile2(p, text, h):
    im = Image.open(p).convert("RGB") if p.exists() else Image.new("RGB", (h, h), BG)
    im = im.resize((int(im.width * h / im.height), h)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, im.width, 24], fill=(30, 32, 36)); d.text((8, 6), text, fill=(235, 235, 235)); return im


grid([[(D / "sec_F11a.png", "F11a sections")], [(D / f"sec_{CAND}.png", f"{CAND} sections")]],
     "Chest sections: z 1.20 / sternum x 0 / breast x 0.085 - white source, orange body, blue bra", "05_chest_sections.jpg", 560)
HP = [("hip0_knee0", "standing"), ("hip45_knee60", "hip 45 / knee 60"), ("hip90_knee90", "hip 90 / knee 90")]
grid([[(D / "hip" / f"{k}_side.png", f"{t} side") for k, t in HP], [(D / "hip" / f"{k}_front_below.png", f"{t} front-below") for k, t in HP]],
     f"{CAND} limited hip-flexion clearance check (structural only; no pelvis tilt, no correctives)", "06_hip_flexion_check.jpg")
EL = (0, 45, 90, 135, 170)
grid([[(D / "elev" / f"elev{e:03d}_{v}.png", f"{e} deg {v}") for e in EL] for v in ("front", "side")],
     f"{CAND} limited arm-elevation check (glenohumeral only; diagnostic)", "07_arm_elevation_check.jpg")
print("SHEETS", sorted(p.name for p in OUT.iterdir()))
