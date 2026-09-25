"""Build one matched V13e/V15f left-ring proof board."""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "renders_v15f_ring_proof"
OUT = SRC / "V15F_V13E_RING_L_PROOF.jpg"
VIEWS = [
    ("yneg", "Y- close-up"),
    ("ypos", "Y+ close-up"),
    ("xpos", "Side close-up"),
    ("oblique", "Oblique close-up"),
]

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
    for key, _ in VIEWS:
        path = SRC / f"{version}_ring_L_{key}.png"
        if not path.is_file():
            missing.append(path)
        else:
            images[(version, key)] = Image.open(path).convert("RGB")
if missing:
    raise SystemExit("Missing ring proof renders:\n- " + "\n- ".join(map(str, missing)))

cell_w = 720
cell_h = 720
label_h = 54
title_h = 82
canvas = Image.new("RGB", (cell_w * len(VIEWS), title_h + (cell_h + label_h) * 2), (25, 25, 25))
draw = ImageDraw.Draw(canvas)
draw.text((24, 20), "V15f left-ring proof — V13e baseline vs current V15f", font=font(32), fill=(240,240,240))

for row, version in enumerate(("V13e", "V15f")):
    for col, (key, title) in enumerate(VIEWS):
        im = images[(version, key)]
        im.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
        x = col * cell_w + (cell_w - im.width) // 2
        y0 = title_h + row * (cell_h + label_h)
        y = y0 + (cell_h - im.height) // 2
        canvas.paste(im, (x, y))
        label = f"{version} — {title}"
        draw.text((col * cell_w + 14, y0 + cell_h + 10), label, font=font(24), fill=(240,240,240))

OUT.parent.mkdir(parents=True, exist_ok=True)
canvas.save(OUT, quality=92, subsampling=0)
print(OUT)
