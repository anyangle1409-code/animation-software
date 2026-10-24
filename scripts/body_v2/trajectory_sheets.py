#!/usr/bin/env python3
"""Phone review sheets from movement_trajectory_test_blender.py frame renders: one portrait sheet per movement with the
sampled frames as rows and front / side / back as columns, labelled with the frame's key numbers.  Plain Python + PIL.

usage: python3 trajectory_sheets.py <trajectory out dir> [label]
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

d = Path(sys.argv[1]); label = sys.argv[2] if len(sys.argv) > 2 else d.name
idx = json.loads((d / "frames_index.json").read_text()); rep = json.loads((d / "trajectory_report.json").read_text())
for mv, frames in idx["frames"].items():
    rows = []
    for fi in frames:
        ims = [Image.open(d / f"frame_{mv}_{fi:02d}_{v}.png").convert("RGB") for v in ("front", "side", "back")]
        w, h = ims[0].size
        row = Image.new("RGB", (w * 3, h))
        for k, im in enumerate(ims):
            row.paste(im, (k * w, 0))
        m = rep["movements"][mv]["frames"][fi]
        pose = ", ".join(f"{k.split('_')[0]} {m[k]}" for k in m if k.endswith(("_deg", "depth")) and k != "u")
        txt = (f"{label} | {mv} frame {fi}/{idx['frames_per_trajectory'] - 1} | {pose}\n"
               f"folds>90 {m['edges_gt90']}  crumple>35 {m['edges_gt35']}  self-isect {m['self_intersections']}  "
               f"asym p95 {m['asymmetry_p95_mm']} mm")
        ImageDraw.Draw(row).multiline_text((8, 8), txt, fill=(255, 255, 0))
        rows.append(row)
    sheet = Image.new("RGB", (rows[0].width, sum(r.height for r in rows)))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y)); y += r.height
    sheet = sheet.resize((1170, int(sheet.height * 1170 / sheet.width)))
    sheet.save(d / f"sheet_{mv}.jpg", quality=80)
    print("SHEET", d / f"sheet_{mv}.jpg")
