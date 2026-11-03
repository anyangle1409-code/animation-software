"""front-view silhouette widths (fraction of figure height) for the reference panel and model stand renders.
Low-confidence visual evidence: perspective, pose and clothing differ.  usage: stwidths.py <ref.jpg> label=dir ..."""
import sys
import numpy as np
from PIL import Image
LEVELS = [0.86, 0.83, 0.80, 0.77, 0.74, 0.70, 0.66, 0.62, 0.45, 0.40, 0.37, 0.33, 0.28, 0.22, 0.18, 0.12, 0.06]


def runs(row):
    out = []; x = 0
    while x < row.size:
        if row[x]:
            s = x
            while x < row.size and row[x]: x += 1
            if x - s >= 2: out.append((int(s), int(x - 1)))
        else: x += 1
    return out


def widths(mask, top, bot):
    h = bot - top; res = {}
    for f in LEVELS:
        y = int(round(bot - f * h)); r = runs(mask[y])
        res[f] = float((r[-1][1] - r[0][0] + 1) / h) if r else None, [round(float((e - s + 1) / h), 3) for s, e in r]
    return res


ref = np.asarray(Image.open(sys.argv[1]).convert("RGB").crop((0, 28, 282, 625))).astype(int)
R, G, B = ref[..., 0], ref[..., 1], ref[..., 2]
skin = (R > 35) & (R > B + 6) & (R >= G - 2)
fig = ref.sum(-1) > 150
rows = np.nonzero(fig.sum(1) > 2)[0]; top, bot = rows.min(), rows.max()
out = {"reference": widths(skin | (fig & ~skin), top, bot)}
for a in sys.argv[2:]:
    lab, d = a.split("=", 1)
    im = np.asarray(Image.open(f"{d}/stand_front_000.png").convert("RGB")).astype(int)
    R, G, B = im[..., 0], im[..., 1], im[..., 2]
    m = ((0.3 * R + 0.59 * G + 0.11 * B) < 215) & (R > B + 4)
    rows = np.nonzero(m.sum(1) > 1)[0]
    out[lab] = widths(m, rows.min(), rows.max())
labs = list(out)
print("level | " + " | ".join(f"{l:>26s}" for l in labs))
for f in LEVELS:
    cells = []
    for l in labs:
        w, segs = out[l][f]
        cells.append(f"{(w or 0):.3f} " + ",".join(f"{x:.3f}" for x in segs[:4]))
    print(f"{f:.2f}  | " + " | ".join(f"{c:>26s}" for c in cells))
