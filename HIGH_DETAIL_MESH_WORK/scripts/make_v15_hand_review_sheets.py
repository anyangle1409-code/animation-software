"""Build matched V13e/V15 hand review boards from identical pose/camera renders."""
from __future__ import annotations
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]

def font():
    for path in ("C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(path, 28)
        except OSError:
            pass
    return ImageFont.load_default()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="v15a_deep_hand_rebuild")
    ap.add_argument("--candidate-label", default="V15a")
    ap.add_argument("--baseline-label", default="V13e")
    args = ap.parse_args()
    r = ROOT / f"renders_{args.version}"
    fnt = font()
    sets = {
        f"{args.candidate_label.upper()}_{args.baseline_label.upper()}_OPEN_HAND_COMPARISON.jpg": [
            ("Open palm", "open_hand_review", "hand"),
            ("Back", "open_hand_review", "hand_back"),
            ("Thumb-index web", "open_hand_review", "hand_web"),
        ],
        f"{args.candidate_label.upper()}_{args.baseline_label.upper()}_CLOSED_FIST_COMPARISON.jpg": [
            ("Palm", "closed_fist_review", "hand"),
            ("Back", "closed_fist_review", "hand_back"),
            ("Side", "closed_fist_review", "hand_side"),
        ],
        f"{args.candidate_label.upper()}_{args.baseline_label.upper()}_EXERCISE_HAND_COMPARISON.jpg": [
            ("Curl grip", "dumbbell_bicep_curl_bottom", "hand"),
            ("Push-up contact", "push_up_bottom", "hand"),
            ("Pull-up grip", "pull_up_peak", "hand"),
        ],
    }
    for name, views in sets.items():
        required = []
        for _, pose, view in views:
            for kind in ("baseline", "candidate"):
                required.append(r / f"{pose}_{kind}_{view}.png")
        missing = [str(p) for p in required if not p.is_file()]
        if missing:
            raise SystemExit("Missing matched render(s):\n- " + "\n- ".join(missing))

        w, h = 550, 600
        image = Image.new("RGB", (w * len(views), h * 2 + 82), (23, 27, 32))
        draw = ImageDraw.Draw(image)
        for col, (title, pose, view) in enumerate(views):
            draw.text((col * w + 14, 7), title, fill=(245, 245, 245), font=fnt)
            for row, kind in enumerate(("baseline", "candidate")):
                source = r / f"{pose}_{kind}_{view}.png"
                with Image.open(source) as im:
                    image.paste(
                        im.convert("RGB").resize((w, h), Image.Resampling.LANCZOS),
                        (col * w, 42 + row * h),
                    )
                label = args.baseline_label if row == 0 else args.candidate_label
                draw.text(
                    (col * w + 12, 46 + row * h),
                    label, fill=(255, 255, 255), font=fnt,
                    stroke_width=2, stroke_fill=(0, 0, 0),
                )
        out = r / name
        image.save(out, quality=92, subsampling=0)
        print(out)

if __name__ == "__main__":
    main()
