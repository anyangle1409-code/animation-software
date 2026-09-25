"""Build one V13e/V15f Stage-A ring/pinky comparison board."""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "renders_v15f_stage_a"
OUT = SRC / "V15F_V13E_STAGE_A_RING_PINKY_PROOF.jpg"
DIGITS = (
    ("ring_L", "Ring L"),
    ("ring_R", "Ring R"),
    ("pinky_L", "Pinky L"),
    ("pinky_R", "Pinky R"),
)
VIEWS = ("yneg", "oblique")

def font(size):
    for path in (
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ):
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

images = {}
missing = []
for version in ("V13e", "V15f"):
    for key, _ in DIGITS:
        for view in VIEWS:
            path = SRC / f"{version}_{key}_{view}.png"
            if not path.is_file():
                missing.append(path)
            else:
                images[(version, key, view)] = Image.open(path).convert("RGB")
if missing:
    raise SystemExit("Missing Stage-A renders:\n- " + "\n- ".join(map(str, missing)))

cell_w = 560
cell_h = 560
label_h = 46
title_h = 76
rows = 4
cols = 4
canvas = Image.new("RGB", (cell_w * cols, title_h + (cell_h + label_h) * rows), (25,25,25))
draw = ImageDraw.Draw(canvas)
draw.text((22,18), "V15f Stage A — V13e vs V15f ring/pinky proof", font=font(30), fill=(240,240,240))

# Two rows per version: Y- then oblique.
row_specs = [
    ("V13e", "yneg", "V13e Y-"),
    ("V15f", "yneg", "V15f Y-"),
    ("V13e", "oblique", "V13e oblique"),
    ("V15f", "oblique", "V15f oblique"),
]
for row, (version, view, row_label) in enumerate(row_specs):
    for col, (key, title) in enumerate(DIGITS):
        im = images[(version, key, view)]
        im.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
        y0 = title_h + row * (cell_h + label_h)
        x = col * cell_w + (cell_w - im.width)//2
        y = y0 + (cell_h - im.height)//2
        canvas.paste(im, (x,y))
        draw.text(
            (col*cell_w+12, y0+cell_h+8),
            f"{title} — {row_label}",
            font=font(21),
            fill=(240,240,240),
        )

OUT.parent.mkdir(parents=True, exist_ok=True)
canvas.save(OUT, quality=92, subsampling=0)
print(OUT)
