#!/usr/bin/env python3
"""Phone filmstrips (1080 px wide) and looping GIFs of the R1 review candidate's exercise sequences (PIL only).

Per benchmark: R1 three-quarter frames (t = 0 .. 1, five frames), R1 side frames, then the a003 vs R1 peak frame
(three-quarter), and the measured worst-frame metrics of both.

  python3 compose_review_candidate_sequences.py --renders DIR --validation JSON --out DIR
"""
import argparse, json, textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
TS = ("0.00", "0.25", "0.50", "0.75", "1.00")


def main():
    ap = argparse.ArgumentParser()
    for a in ("--renders", "--validation", "--out"):
        ap.add_argument(a, required=True)
    o = ap.parse_args()
    val = json.loads(Path(o.validation).read_text())["benchmarks"]
    big, small, tiny = ImageFont.truetype(F, 36), ImageFont.truetype(F, 23), ImageFont.truetype(F, 18)
    r1, a3 = Path(o.renders) / "r1", Path(o.renders) / "a003"
    out = Path(o.out); out.mkdir(parents=True, exist_ok=True)
    for name, v in val.items():
        if not (r1 / f"{name}__t1.00__three_quarter.png").exists():
            continue
        tw = 216
        strip = []
        for view in ("three_quarter", "side"):
            ims = [Image.open(r1 / f"{name}__t{t}__{view}.png").convert("RGB") for t in TS]
            th = int(ims[0].height * tw / ims[0].width)
            strip.append([im.resize((tw, th)) for im in ims])
        pa = Image.open(a3 / f"{name}__t1.00__three_quarter.png").convert("RGB")
        pb = Image.open(r1 / f"{name}__t1.00__three_quarter.png").convert("RGB")
        ph = int(pa.height * 540 / pa.width)
        pa, pb = pa.resize((540, ph)), pb.resize((540, ph))
        aw, bw = v["a003_worst"], v["r1_worst"]
        lines = [f"Worst frame a003 -> R1: collapse {aw['collapse_lt_0_1']} -> {bw['collapse_lt_0_1']}, stretch>2 "
                 f"{aw['stretch_gt_2']} -> {bw['stretch_gt_2']}, self-intersecting pairs {aw['self_intersecting_pairs']} -> {bw['self_intersecting_pairs']}",
                 f"Volume change a003 {v['a003_volume_pct'][0]:+.1f}..{v['a003_volume_pct'][1]:+.1f} %, R1 {v['r1_volume_pct'][0]:+.1f}..{v['r1_volume_pct'][1]:+.1f} %",
                 "R1 end-frame contacts: " + ("; ".join(f"{a}/{b} {n}" for a, b, n in v["r1_end_classes"]) or "none"),
                 "R1 = C5 feet + W3A shoulder helper + K1 knee/elbow keys (drives run per frame); review only, not accepted"]
        wl = [p for L in lines for p in textwrap.wrap(L, 80)]
        H = 130 + sum(s[0].height + 34 for s in strip) + 40 + ph + 24 + 30 * len(wl)
        S = Image.new("RGB", (1080, H), (249, 249, 247)); d = ImageDraw.Draw(S)
        d.text((24, 14), f"ORIGINAL_v1 R1 - {name.replace('_', ' ')}", font=big, fill=(20, 20, 20))
        d.text((24, 66), "review candidate sequence, t = 0 / 0.25 / 0.5 / 0.75 / 1", font=small, fill=(80, 80, 80))
        y = 110
        for label, row in zip(("three-quarter", "side"), strip):
            d.text((24, y), label, font=tiny, fill=(80, 80, 80)); y += 24
            for i, im in enumerate(row):
                S.paste(im, (i * tw, y))
            y += row[0].height + 10
        d.text((24, y + 6), "peak frame: a003 (left) vs R1 (right)", font=small, fill=(20, 20, 20)); y += 40
        S.paste(pa, (0, y)); S.paste(pb, (540, y)); y += ph + 12
        for L in wl:
            d.text((24, y), L, font=small, fill=(20, 20, 20)); y += 30
        S.save(out / f"{name}_sequence.jpg", quality=82)
        frames = [Image.open(r1 / f"{name}__t{t}__three_quarter.png").convert("RGB").resize((360, int(360 * pa.height / 540)))
                  for t in TS]
        loop = frames + frames[-2:0:-1]
        loop[0].save(out / f"{name}.gif", save_all=True, append_images=loop[1:], duration=350, loop=0, optimize=True)
    print("sequences in", out)


if __name__ == "__main__":
    main()
