"""Label each armpit close-up with its angle and view, on a dark background, and make one contact sheet per view."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

src, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
NAME = sys.argv[3] if len(sys.argv) > 3 else "R63g"
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 30)
BG = (28, 28, 30)
by_view = {}
for p in sorted(src.glob("armpit_*.png")):
    _, deg, view = p.stem.split("_", 2)
    a = Image.open(p).convert("RGBA"); b = Image.new("RGBA", a.size, BG + (255,)); b.alpha_composite(a)
    im = b.convert("RGB"); d = ImageDraw.Draw(im)
    label = f"{NAME}  {float(deg.replace('deg', '')):.0f} deg  {view.replace('_', ' ')}"
    d.text((16, 14), label, fill=(240, 240, 240), font=F)
    im.save(out / f"{p.stem}.jpg", quality=90)
    by_view.setdefault(view, []).append(im)
for view, ims in by_view.items():
    W = 450
    sheet = Image.new("RGB", (W * len(ims), W), BG)
    for i, im in enumerate(ims):
        sheet.paste(im.resize((W, W)), (i * W, 0))
    sheet.save(out / f"sheet_{view}.jpg", quality=88)
print("LABELLED", len(list(out.glob('*.jpg'))))
