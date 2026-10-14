#!/usr/bin/env python3
"""Phone sheets (1080 px wide) from render_original_skeleton_xray_blender.py output (PIL only).

  python3 compose_skeleton_xray_sheets.py --renders DIR --out DIR
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
LEGEND = ["Skin 22 % opaque.  Bones = the 67-joint rig the skin is weighted to:",
          "red scapula, yellow clavicle, orange upper arm, green forearm/hand, blue spine, grey legs;",
          "ivory = rib/sternum/clavicle/scapula guides.  Magenta = arm pivot (upper-arm head);",
          "cyan (rest only) = anatomical glenohumeral centre landmark.  Diagnostic, nothing approved."]
NAMES = {"today": "today's rig (scapula driven in bone-local axes)", "isb": "anatomical-frame scapula + weight taper",
         "r4": "R4: anatomical scapula on the thorax, lowered pivot, new shoulder weights"}


def grid(title, sub, cols, rows, cells, out, lines):
    big, sm = ImageFont.truetype(F, 34), ImageFont.truetype(F, 22)
    tw = 1080 // len(cols)
    ims = [[Image.open(c).convert("RGB") for c in r] for r in cells]
    th = int(ims[0][0].height * tw / ims[0][0].width)
    H = 130 + len(rows) * (th + 30) + 20 + 30 * len(lines)
    S = Image.new("RGB", (1080, H), (249, 249, 247)); d = ImageDraw.Draw(S)
    d.text((20, 12), title, font=big, fill=(20, 20, 20)); d.text((20, 58), sub, font=sm, fill=(80, 80, 80))
    for j, c in enumerate(cols):
        d.text((j * tw + 10, 96), c, font=sm, fill=(20, 20, 20))
    y = 130
    for i, r in enumerate(ims):
        d.text((10, y), rows[i], font=sm, fill=(60, 60, 60)); y += 28
        for j, im in enumerate(r):
            S.paste(im.resize((tw, th)), (j * tw, y))
        y += th + 2
    y += 14
    for L in lines:
        d.text((20, y), L, font=sm, fill=(20, 20, 20)); y += 30
    S.save(out, quality=84)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--renders", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--configs", default="today,isb")
    o = ap.parse_args(); R, out = Path(o.renders), Path(o.out); out.mkdir(parents=True, exist_ok=True)
    cfgs = o.configs.split(",")
    poses = sorted({p.name.split("_")[1] for p in R.glob("*_ht*_front.png")})
    for cfg in cfgs:
        grid(f"Skeleton under the skin: {cfg}", NAMES[cfg], ["front", "side", "rear"],
             [f"coupled elevation {int(p[2:])} deg" for p in poses],
             [[R / f"{cfg}_{p}_{v}.png" for v in ("front", "side", "rear")] for p in poses], out / f"xray_fullbody_{cfg}.jpg", LEGEND)
    for view in ("front", "rear", "side"):
        grid(f"Shoulder skeleton, {view} view", " vs ".join(NAMES[c].split(":")[0] for c in cfgs),
             [NAMES[c].split(" (")[0].split(":")[0] for c in cfgs], [f"coupled elevation {int(p[2:])} deg" for p in poses],
             [[R / f"{c}_{p}_shoulder_{view}.png" for c in cfgs] for p in poses], out / f"xray_shoulder_{view}.jpg", LEGEND)
    print("sheets in", out)


if __name__ == "__main__":
    main()
