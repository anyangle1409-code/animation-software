#!/usr/bin/env python3
"""Phone sheets (1080 px) of the W3 option A shoulder renders: original vs helper at 90/145/160 deg (PIL only).

  python3 compose_shoulder_helper_sheets.py --renders DIR --report JSON --out DIR
"""
import argparse, json, textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def main():
    ap = argparse.ArgumentParser()
    for a in ("--renders", "--report", "--out"):
        ap.add_argument(a, required=True)
    o = ap.parse_args()
    rep = json.loads(Path(o.report).read_text())
    sw = rep["coupled_sweep"]
    b, h = sw["before"]["160"], sw["after"]["160"]
    big, small = ImageFont.truetype(F, 36), ImageFont.truetype(F, 23)
    lines = ["Left: 67-joint original. Right: 69 joints, one half-motion helper per side (in memory only)",
             "Stateless drive: rotation branch closest to the 120 deg reference pose (equals the continuous path)",
             f"160 deg: pairs {b['self_intersecting_face_pairs_in_region']} -> {h['self_intersecting_face_pairs_in_region']}, "
             f"collapse {b['collapse_faces_ratio_lt_0_1']} -> {h['collapse_faces_ratio_lt_0_1']}, volume {b['body_volume_change_pct']:+.1f} -> "
             f"{h['body_volume_change_pct']:+.1f} %, stretch>2 {b['stretched_faces_ratio_gt_2']} -> {h['stretched_faces_ratio_gt_2']} (worse)",
             "Remaining: armpit bulge, posterior axillary web, more stretch. Runtime-contract change; not adopted"]
    wl = [p for L in lines for p in textwrap.wrap(L, 78)]
    out = Path(o.out); out.mkdir(parents=True, exist_ok=True)
    for view in ("front", "rear", "side"):
        H = 140 + 3 * 540 + 30 + 32 * len(wl)
        S = Image.new("RGB", (1080, H), (249, 249, 247)); d = ImageDraw.Draw(S)
        d.text((24, 14), f"W3 option A: shoulder helper ({view} view)", font=big, fill=(20, 20, 20))
        d.text((24, 62), "right shoulder at 90 / 145 / 160 deg coupled elevation", font=small, fill=(80, 80, 80))
        d.text((24, 100), "67-joint original", font=small, fill=(150, 30, 30))
        d.text((564, 100), "helper candidate (not adopted)", font=small, fill=(20, 110, 50))
        for r, a in enumerate((90, 145, 160)):
            for c, t in enumerate(("base", "helper")):
                im = Image.open(Path(o.renders) / f"{t}_{a:03d}_{view}.png").convert("RGB").resize((540, 540))
                S.paste(im, (540 * c, 140 + r * 540))
            d.text((12, 148 + r * 540), f"{a} deg", font=small, fill=(240, 240, 240))
        y = 140 + 3 * 540 + 16
        for L in wl:
            d.text((24, y), L, font=small, fill=(20, 20, 20)); y += 32
        S.save(out / f"helper_reference_{view}_sheet.jpg", quality=84)
    print("sheets in", out)


if __name__ == "__main__":
    main()
