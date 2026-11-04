#!/usr/bin/env python3
"""Contact sheet: one row per model, columns front / side / back / three-quarter.  Needs Pillow only.

  make_comparison_sheet.py <OUTROOT> <out.jpg>               fresh renders of a rebuild (W8, V14, R120 rows)
  make_comparison_sheet.py --archive <repo_root> <out.jpg>   the ARCHIVED reviewer renders in review-assets/body_v2
                                                             (v13s, v14a, v14b) - not freshly rendered
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

VIEWS = [("front", "front"), ("side", "side"), ("back", "back"), ("front34", "three-quarter")]
H = 560


def sheet(rows, out, title):
    tiles = []
    for label, folder, pattern in rows:
        ims = []
        for v, _ in VIEWS:
            p = folder / pattern.format(v=v)
            if not p.exists():
                ims.append(None); continue
            im = Image.open(p).convert("RGB"); w = int(im.width * H / im.height); ims.append(im.resize((w, H)))
        tiles.append((label, ims))
    if not any(any(i is not None for i in ims) for _, ims in tiles):
        print("no renders found - nothing to do"); return 1
    colw = [max((ims[c].width for _, ims in tiles if ims[c] is not None), default=200) for c in range(4)]
    top, left = 70, 190
    W = left + sum(colw); Hh = top + len(tiles) * (H + 8)
    canvas = Image.new("RGB", (W, Hh), (24, 24, 26)); d = ImageDraw.Draw(canvas)
    d.text((12, 8), title, fill=(235, 235, 235))
    x = left
    for c, (_, name) in enumerate(VIEWS):
        d.text((x + 8, 44), name, fill=(200, 200, 120)); x += colw[c]
    for r, (label, ims) in enumerate(tiles):
        y = top + r * (H + 8); d.text((12, y + 10), label, fill=(235, 235, 235)); x = left
        for c, im in enumerate(ims):
            if im is not None:
                canvas.paste(im, (x, y))
            else:
                d.text((x + 8, y + 10), "missing", fill=(200, 90, 90))
            x += colw[c]
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, quality=88)
    print("wrote", out, canvas.size)
    return 0


if __name__ == "__main__":
    if sys.argv[1] == "--archive":
        rb = Path(sys.argv[2]) / "review-assets/body_v2"
        rows = [("v13s  (W8)", rb / "draft_v13s_standing", "skin_stand_{v}.jpg"),
                ("v14a  legs+feet", rb / "draft_v14a_legs", "skin_stand_{v}.jpg"),
                ("v14b  +torso", rb / "draft_v14b_torso", "skin_stand_{v}.jpg")]
        sys.exit(sheet(rows, sys.argv[3], "ARCHIVED reviewer renders (not freshly rendered) - review-assets/body_v2"))
    root = Path(sys.argv[1])
    rows = [("W8 rebuilt", root / "W8/renders", "V2_skin_stand_{v}.png"),
            ("v14b rebuilt", root / "V14", "V2_skin_stand_{v}.png"),
            ("R120 EXPERIMENTAL", root / "R120", "V2_skin_stand_{v}.png")]
    sys.exit(sheet(rows, sys.argv[2], "Fresh renders of this rebuild"))
