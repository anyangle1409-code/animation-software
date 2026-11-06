"""Compose the FEMALE standing-review sheets from the rendered views (PIL; no geometry).

usage: python3.11 make_review_sheets.py <render dir> <Option 4 reference .png> <out dir>
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

D, REF, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); OUT.mkdir(parents=True, exist_ok=True)
BG = (78, 80, 86)


def lab(im, text, size=None):
    d = ImageDraw.Draw(im); d.rectangle([0, 0, im.width, 26], fill=(30, 32, 36)); d.text((8, 6), text, fill=(235, 235, 235)); return im


def row(names, labels=None, h=900):
    ims = []
    for i, n in enumerate(names):
        p = D / f"{n}.png"
        im = Image.open(p).convert("RGB") if p.exists() else Image.new("RGB", (560, 900), BG)
        im = im.resize((int(im.width * h / im.height), h)); ims.append(lab(im, labels[i] if labels else n))
    o = Image.new("RGB", (sum(i.width for i in ims), h), BG); x = 0
    for i in ims:
        o.paste(i, (x, 0)); x += i.width
    return o


def stack(rows, title):
    w = max(r.width for r in rows); o = Image.new("RGB", (w, sum(r.height for r in rows) + 40), BG)
    ImageDraw.Draw(o).text((10, 12), title, fill=(255, 255, 255)); y = 40
    for r in rows:
        o.paste(r, (0, y)); y += r.height
    return o


V = ["front", "back", "left", "right", "q34_front", "q34_rear"]
VL = ["front", "back", "left side", "right side", "3/4 front", "3/4 rear"]
for mode in ("tex", "clay"):
    stack([row([f"stand_{mode}_{v}" for v in V], VL)], f"Female F09b - natural standing pose ({'colour from her source albedo' if mode == 'tex' else 'clay, no textures'})").save(OUT / f"01_stand_{mode}.jpg", quality=90)
    stack([row([f"rest_{mode}_source_{v}" for v in V], ["SOURCE " + x for x in VL]), row([f"rest_{mode}_new_{v}" for v in V], ["NEW " + x for x in VL])],
          f"Source (Meshy Pro) vs new model - same A-pose, cameras and lighting ({mode})").save(OUT / f"02_source_vs_new_{mode}.jpg", quality=90)
# reference panels (Option 4 sheet: front, 3/4 front, side, 3/4 back, back)
ref = Image.open(REF).convert("RGB")
boxes = [(5, 63, 250, 680), (256, 63, 494, 680), (499, 63, 708, 680), (713, 63, 935, 680), (941, 63, 1166, 680)]
refs = [lab(ref.crop(b).resize((int((b[2] - b[0]) * 900 / (b[3] - b[1])), 900)), t) for b, t in zip(boxes, ["REFERENCE front", "REFERENCE 3/4 front", "REFERENCE side", "REFERENCE 3/4 back", "REFERENCE back"])]
rr = Image.new("RGB", (sum(i.width for i in refs), 900), BG); x = 0
for i in refs:
    rr.paste(i, (x, 0)); x += i.width
nr = row(["stand_tex_front", "stand_tex_q34_front", "stand_tex_right", "stand_tex_q34_rear", "stand_tex_back"], ["NEW front", "NEW 3/4 front", "NEW side", "NEW 3/4 rear", "NEW back"])
stack([rr, nr], "Selected Option 4 reference (top) vs new model, natural standing pose (bottom); the reference wears shoes").save(OUT / "03_reference_vs_new.jpg", quality=90)
C = ["face_front", "face_q34", "face_side", "shoulders_front", "shoulders_back", "pelvis_front", "pelvis_back"]
H_ = ["hand_r_out", "hand_r_front", "hand_l_out", "hand_l_front", "foot_r", "foot_l"]
for mode in ("tex", "clay"):
    stack([row([f"close_{mode}_{c}" for c in C], C, 600), row([f"close_{mode}_{c}" for c in H_], H_, 600)], f"Close-ups, natural pose ({mode})").save(OUT / f"04_closeups_{mode}.jpg", quality=90)
stack([row(["nude_clay_front", "nude_clay_back", "nude_clay_left", "nude_clay_right", "nude_clay_q34_front"], ["front", "back", "left", "right", "3/4"]),
       row(["nude_clay_torso_front", "nude_clay_torso_back"], ["torso front", "torso back"], 700)],
      "Body under the removable bra / shorts (clay): conservative neutral form, 3 mm inset of the garment shape").save(OUT / "05_body_without_clothing.jpg", quality=90)
stack([row(["wire_front", "wire_back"], ["topology front", "topology back"]), row(["wire_face", "wire_hand_r", "wire_foot_r", "wire_shoulder_r"], ["face", "hand", "foot", "shoulder"], 600)],
      "Topology diagnostics (A-pose, flat shading + wireframe)").save(OUT / "06_topology_diagnostics.jpg", quality=88)
print("SHEETS", sorted(p.name for p in OUT.iterdir()))
