"""Compose the FEMALE F11a standing-review sheets (PIL; no geometry).

Sheets: 01 clothed standing (tex), 02 clothed standing (clay), 03 body under the garments (clay, five views + torso),
04 anatomy close-ups: chest, armpits, groin, pelvis, upper thighs - clothed tex / clothed clay / body only.

usage: python3.11 make_f11_sheets.py <render dir> <out dir>
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

D, OUT = Path(sys.argv[1]), Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
BG = (78, 80, 86)


def lab(im, text):
    d = ImageDraw.Draw(im); d.rectangle([0, 0, im.width, 24], fill=(30, 32, 36)); d.text((8, 6), text, fill=(235, 235, 235)); return im


def row(names, labels, h):
    ims = []
    for n, t in zip(names, labels):
        p = D / f"{n}.png"
        im = Image.open(p).convert("RGB") if p.exists() else Image.new("RGB", (h, h), BG)
        ims.append(lab(im.resize((int(im.width * h / im.height), h)), t))
    o = Image.new("RGB", (sum(i.width for i in ims), h), BG); x = 0
    for i in ims:
        o.paste(i, (x, 0)); x += i.width
    return o


def stack(rows, title):
    w = max(r.width for r in rows); o = Image.new("RGB", (w, sum(r.height for r in rows) + 36), BG)
    ImageDraw.Draw(o).text((10, 11), title, fill=(255, 255, 255)); y = 36
    for r in rows:
        o.paste(r, (0, y)); y += r.height
    return o


V = ["front", "back", "left", "right", "q34_front", "q34_rear"]; VL = ["front", "back", "left side", "right side", "3/4 front", "3/4 rear"]
for mode, t in (("tex", "colour"), ("clay", "clay")):
    stack([row([f"stand_{mode}_{v}" for v in V], VL, 860)], f"Female F11a - clothed, natural standing pose ({t})").save(OUT / f"01_clothed_{mode}.jpg", quality=90)
stack([row([f"nude_clay_{v}" for v in V[:5]], VL[:5], 860), row(["nude_clay_torso_front", "nude_clay_torso_back"], ["torso front", "torso back"], 640)],
      "Female F11a - body under the removable bra / shorts (clay)").save(OUT / "02_body_under_garments.jpg", quality=90)
A = ["chest_front", "chest_q34", "armpit_r", "armpit_l", "groin_front", "groin_back", "groin_under", "pelvis_side", "thighs_front"]
AL = ["chest", "chest 3/4", "armpit R", "armpit L", "groin front", "groin back", "groin from below", "pelvis side", "upper thighs"]
stack([row([f"anat_{m}_{a}" for a in A], [f"{m}: {x}" for x in AL], 440) for m in ("tex", "clay", "nude")],
      "Female F11a - chest, armpits, groin, pelvis, upper thighs: clothed (colour), clothed (clay), body only (clay)").save(OUT / "03_anatomy_closeups.jpg", quality=90)
print("SHEETS", sorted(p.name for p in OUT.iterdir()))
