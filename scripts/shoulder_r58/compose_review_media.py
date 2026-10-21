"""Compose R52 | R59 side-by-side review stills and an MP4 from two rendered press sequences (no Blender needed).
  python3 compose_review_media.py <seqdir> <outdir> <frames>
"""
import subprocess
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

seq, out, n = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
CAND = sys.argv[4] if len(sys.argv) > 4 else "R59"
CAND_NAME = sys.argv[5] if len(sys.argv) > 5 else "R59 (smoothed timing)"
out.mkdir(parents=True, exist_ok=True)
tmp = out / "_frames"; tmp.mkdir(exist_ok=True)
B = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
LABELS = (("R52", "R52 (before)"), (CAND, CAND_NAME))
VIEWS = ("rear", "three_quarter")
BG = (28, 28, 30)


def ht(t):
    k = t * t * (3 - 2 * t)
    top = os.environ.get("R70_TOP")
    k0 = 0.625 * 0.625 * (3 - 2 * 0.625)
    if top and k > k0:
        # R70: candidate on the new top-of-press path (r70_press_path.py); left panel R52 stays on Work's path
        u = (k - k0) / (1 - k0); h = u * u * (3 - 2 * u)
        return 70 + 96 * k - (166 - float(top.split(":")[0])) * h
    return 70 + 96 * k


def tile(lab, i, view, size=420):
    a = Image.open(seq / lab / f"f{i:03d}_{view}.png").convert("RGBA")
    b = Image.new("RGBA", a.size, BG + (255,)); b.alpha_composite(a)
    return b.convert("RGB").resize((size, size))


def frame(i, size=420):
    img = Image.new("RGB", (size * 4, size + 70), BG)
    d = ImageDraw.Draw(img)
    x = 0
    for lab, name in LABELS:
        for view in VIEWS:
            img.paste(tile(lab, i, view, size), (x, 40))
            d.text((x + 8, 8), f"{name} - {view.replace('_', ' ')}", fill=(235, 235, 235), font=F)
            x += size
    t = i / n
    d.text((8, size + 44), f"arm elevation {ht(t):.0f} deg   (t = {t:.2f})   review only - not approved", fill=(235, 235, 235), font=B)
    return img


for i in range(n + 1):
    frame(i).save(tmp / f"{i:03d}.png")
for t in (0.5, 0.625, 0.7, 0.8):
    i = round(t * n)
    frame(i).save(out / f"R52_vs_{CAND}_t{t:.3f}_{ht(t):.0f}deg.jpg", quality=90)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "8", "-i", str(tmp / "%03d.png"),
                "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / f"R52_vs_{CAND}_press.mp4")], check=True)
for p in tmp.glob("*.png"):
    p.unlink()
tmp.rmdir()
print("MEDIA_DONE", sorted(p.name for p in out.iterdir()))
