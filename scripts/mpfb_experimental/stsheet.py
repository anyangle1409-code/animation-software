"""Standing-pose sheet: per view (front, 3/4, side, back) the reference panel, then each model's standing render,
all scaled to the same figure height.  usage: stsheet.py <out.jpg> <ref.jpg|-> <label>=<anim dir> ..."""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
out, ref = sys.argv[1], sys.argv[2]
models = [a.split("=", 1) for a in sys.argv[3:]]
REFBOX = {"front": (0, 28, 282, 625), "front34": (282, 28, 537, 625), "side": (537, 28, 765, 625), "back": (765, 28, 1028, 625)}
VIEWS = ["front", "front34", "side", "back"]
FH = 560                                           # figure height in the sheet, px
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
except OSError:
    font = ImageFont.load_default()


def bbox_model(im):
    a = np.asarray(im.convert("RGB")).astype(int); R, G, B = a[..., 0], a[..., 1], a[..., 2]
    m = ((0.3 * R + 0.59 * G + 0.11 * B) < 215) & (R > B + 4)      # the tan skin, not the grey backdrop / floor
    rows = np.nonzero(m.sum(1) > 1)[0]; cols = np.nonzero(m.sum(0) > 1)[0]
    pad = 6
    return max(cols.min() - pad, 0), max(rows.min() - pad, 0), min(cols.max() + pad, a.shape[1]), min(rows.max() + pad, a.shape[0])


def bbox_ref(im):
    a = np.asarray(im.convert("RGB")).astype(int)
    m = a.sum(-1) > 150                            # figure (skin, shorts edges, shoes) against the dark backdrop
    rows = np.nonzero(m.sum(1) > 2)[0]; cols = np.nonzero(m.sum(0) > 2)[0]
    return cols.min(), rows.min(), cols.max() + 1, rows.max() + 1


def fit(im, box, label):
    x0, y0, x1, y1 = box
    c = im.crop((x0, y0, x1, y1)); s = FH / (y1 - y0)
    c = c.resize((max(1, int((x1 - x0) * s)), FH), Image.LANCZOS)
    tile = Image.new("RGB", (max(c.width + 40, 300), FH + 60), (24, 24, 26))
    if c.mode == "RGBA":
        tile.paste(c, ((tile.width - c.width) // 2, 50), c)
    else:
        tile.paste(c, ((tile.width - c.width) // 2, 50))
    ImageDraw.Draw(tile).text((10, 12), label, fill=(235, 235, 235), font=font)
    return tile


rows = []
import os
REFDIR = os.path.isdir(ref)
R = Image.open(ref).convert("RGB") if (ref != "-" and not REFDIR) else None
for v in VIEWS:
    tiles = []
    if REFDIR:
        p = Image.open(f"{ref}/images/reference_{ {'front34': 'front_34'}.get(v, v)}.png").convert("RGB"); bx = bbox_ref(p)
        tiles.append(fit(p, bx, f"reference {v}"))
    elif R is not None:
        p = R.crop(REFBOX[v]); bx = bbox_ref(p)
        tiles.append(fit(p, bx, f"reference {v}"))
    for lab, d in models:
        import os
        im = Image.open(f"{d}/stand_{v}_000.png" if os.path.exists(f"{d}/stand_{v}_000.png") else f"{d}/press_{v}_000.png")
        mir = v == "side"                     # face the same way as the photographs
        if mir:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        tiles.append(fit(im, bbox_model(im), f"{lab} {v}" + (" (mirrored)" if mir else "")))
    w = sum(t.width for t in tiles); row = Image.new("RGB", (w, FH + 60), (24, 24, 26)); x = 0
    for t in tiles:
        row.paste(t, (x, 0)); x += t.width
    rows.append(row)
W = max(r.width for r in rows); sheet = Image.new("RGB", (W, sum(r.height for r in rows)), (24, 24, 26)); y = 0
for r in rows:
    sheet.paste(r, (0, y)); y += r.height
sheet.save(out, quality=90); print(out, sheet.size)
