"""Build a matched V13e/V15f Stage-B per-digit proof board."""
from __future__ import annotations
import argparse
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
ALLOWED=("index_L","index_R","middle_L","middle_R")

def font(size):
    for p in ("C:/Windows/Fonts/arial.ttf","C:/Windows/Fonts/segoeui.ttf"):
        if Path(p).is_file(): return ImageFont.truetype(p,size)
    return ImageFont.load_default()

ap=argparse.ArgumentParser();ap.add_argument("digit",choices=ALLOWED);args=ap.parse_args()
key=args.digit
src=ROOT/"renders_v15f_stage_b"/key
out=src/f"V15F_V13E_{key.upper()}_PROOF.jpg"
views=(("yneg","Y-"),("ypos","Y+"),("xside","Side"),("oblique","Oblique"))
images={};missing=[]
for version in ("V13e","V15f"):
    for view,_ in views:
        p=src/f"{version}_{key}_{view}.png"
        if not p.is_file():missing.append(p)
        else:images[(version,view)]=Image.open(p).convert("RGB")
if missing:raise SystemExit("Missing renders:\n- "+"\n- ".join(map(str,missing)))

cw=650;ch=650;lh=50;th=78
canvas=Image.new("RGB",(cw*4,th+(ch+lh)*2),(25,25,25))
draw=ImageDraw.Draw(canvas)
draw.text((22,18),f"V15f {key} proof — V13e baseline vs current V15f",font=font(30),fill=(240,240,240))
for row,version in enumerate(("V13e","V15f")):
    for col,(view,title) in enumerate(views):
        im=images[(version,view)];im.thumbnail((cw,ch),Image.Resampling.LANCZOS)
        y0=th+row*(ch+lh);x=col*cw+(cw-im.width)//2;y=y0+(ch-im.height)//2
        canvas.paste(im,(x,y))
        draw.text((col*cw+12,y0+ch+9),f"{version} — {title}",font=font(22),fill=(240,240,240))
out.parent.mkdir(parents=True,exist_ok=True);canvas.save(out,quality=92,subsampling=0)
print(out)
