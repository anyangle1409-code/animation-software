"""Before / after animation frames for phone review: one composite PNG per trajectory frame (review only).

Rows are models, columns are views; every cell comes from movement_trajectory_test_blender.py run with V2_TRAJ_ANIM=1
(fixed orthographic cameras, identical for every model and frame).  When a run also measured the frame (V2_TRAJ_METRICS=1),
the cell caption carries its numbers: skin self-intersections and folds over 90 deg.

usage: python3 anim_compose.py --move press --views front,side,back --out DIR --title "Shoulder press"
                               --model "LABEL=RUN_DIR" --model "LABEL=RUN_DIR" [--loops 2] [--hold 6]
Writes DIR/<move>_<n>.jpg (n from 0; the out-and-back path repeated --loops times, --hold frames at neutral between).
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BG, INK, MUTED, BAND = (244, 246, 245), (27, 36, 34), (92, 106, 102), (226, 232, 229)


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--move", required=True); ap.add_argument("--views", default="front,side,back")
    ap.add_argument("--out", required=True); ap.add_argument("--title", default="")
    ap.add_argument("--model", action="append", required=True, help="LABEL=RUN_DIR")
    ap.add_argument("--loops", type=int, default=2); ap.add_argument("--hold", type=int, default=6)
    ap.add_argument("--stills", default="", help="also write one JPG per view: rows = these trajectory frames "
                    "(e.g. 0,12,24,48 = neutral, intermediate, maximum, return), columns = models")
    ap.add_argument("--still-labels", default="neutral,intermediate,maximum,return to neutral")
    ap.add_argument("--no-video", action="store_true")
    a = ap.parse_args()
    views = a.views.split(","); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    models = []
    for m in a.model:
        label, d = m.split("=", 1); d = Path(d)
        rep = d / "trajectory_report.json"
        frames = json.loads(rep.read_text())["movements"][a.move]["frames"] if rep.exists() else []
        models.append((label, d / "anim", frames))
    nf = len(sorted(models[0][1].glob(f"{a.move}_{views[0]}_*.png")))
    if not nf:
        raise SystemExit(f"no frames for {a.move} in {models[0][1]}")
    cw, ch = Image.open(models[0][1] / f"{a.move}_{views[0]}_000.png").size
    title_h, lab_h, cap_h = 64, 40, 34
    W = cw * len(views); Hh = title_h + len(models) * (lab_h + ch + cap_h)
    W += W % 2; Hh += Hh % 2
    ft, fl, fc, fv = font(FONT_B, 34), font(FONT_B, 24), font(FONT, 20), font(FONT, 18)
    if a.stills:
        rows = [int(x) for x in a.stills.split(",")]; rl = a.still_labels.split(",")
        for v in views:
            lw = 150; Ws = lw + cw * len(models); Hs = title_h + lab_h + len(rows) * (ch + cap_h)
            im = Image.new("RGB", (Ws, Hs), BG); d = ImageDraw.Draw(im)
            d.text((16, 14), f"{a.title or a.move} \u00b7 {v.replace('_', ' ')}", font=ft, fill=INK)
            d.rectangle((0, title_h, Ws, title_h + lab_h), fill=BAND)
            for c, (label, adir, frames) in enumerate(models):
                d.text((lw + c * cw + 10, title_h + 8), label, font=fv, fill=INK)
            y = title_h + lab_h
            for r, i in enumerate(rows):
                d.text((12, y + ch // 2), rl[r] if r < len(rl) else str(i), font=fv, fill=INK)
                d.text((12, y + ch // 2 + 24), f"frame {i + 1}/{nf}", font=fv, fill=MUTED)
                for c, (label, adir, frames) in enumerate(models):
                    im.paste(Image.open(adir / f"{a.move}_{v}_{i:03d}.png").convert("RGB"), (lw + c * cw, y))
                    if frames and i < len(frames) and "self_intersections" in frames[i]:
                        f = frames[i]
                        d.text((lw + c * cw + 10, y + ch + 6), f"self-int. {f['self_intersections']}  folds {f['edges_gt90']}",
                               font=fv, fill=INK)
                y += ch + cap_h
            im.save(out / f"STILLS_{a.move}_{v}.jpg", quality=86)
        print("stills", a.move, views)
    if a.no_video:
        return
    seq = []
    for _ in range(a.loops):
        seq += [0] * a.hold + list(range(nf))
    seq += [0] * a.hold
    for n, i in enumerate(seq):
        im = Image.new("RGB", (W, Hh), BG); d = ImageDraw.Draw(im)
        d.text((16, 14), a.title or a.move, font=ft, fill=INK)
        d.text((W - 16, 22), f"frame {i + 1}/{nf}", font=fc, fill=MUTED, anchor="ra")
        y = title_h
        for label, adir, frames in models:
            d.rectangle((0, y, W, y + lab_h), fill=BAND); d.text((16, y + 8), label, font=fl, fill=INK)
            y += lab_h
            for c, v in enumerate(views):
                cell = Image.open(adir / f"{a.move}_{v}_{i:03d}.png").convert("RGB")
                im.paste(cell, (c * cw, y)); d.text((c * cw + 10, y + 8), v.replace("_", " "), font=fv, fill=MUTED)
            y += ch
            if frames and i < len(frames) and "self_intersections" in frames[i]:
                f = frames[i]
                cap = (f"skin self-intersections {f['self_intersections']}   folds >90° {f['edges_gt90']}"
                       f"   shoulder folds {f.get('shoulder_gt90', 0)}")
                d.text((16, y + 6), cap, font=fc, fill=INK)
            y += cap_h
        im.save(out / f"{a.move}_{n:04d}.jpg", quality=92)
    print("composed", a.move, len(seq), "frames", W, "x", Hh)


if __name__ == "__main__":
    main()
