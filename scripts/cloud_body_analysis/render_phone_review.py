"""Read-only phone review sheets from immutable Blender diagnostic PNG archives.

No Blender, model editing, recomputation, smoothing of geometry or anatomical approval.
Renders are already archived from read-only Blender run 39937882229.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

from PIL import Image, ImageDraw, ImageFont, ImageOps

VISUAL_SHA256 = {
    "W8": "3be4322ba67da8b3827c96c0afdb58ffa8adb998cf8d1814aab0978a9e68d63e",
    "V14": "5f11a9441cf5bb1d29ba3fae72c945f59c9109a26023cea15508d3310cb774e0",
    "R120": "cf26902334a90cb3928821d797fcc88e27340a7837911a0e080b6973b5017a2f",
}
MODELS = ("W8", "V14", "R120")
REVIEWS = {
    "shoulder_press": {"samples": ("00", "06", "08"),
                       "labels": ("Start", "75% press", "Top"), "view": "back"},
    "squat": {"samples": ("00", "07", "08"),
              "labels": ("Start", "Near-bottom", "Final"), "view": "side"},
}
BACKGROUND = "#f4f6fa"
PANEL_WIDTH, PANEL_HEIGHT = 360, 510

def typeface(px):
    # System fonts on GitHub Actions runners, with portable fallback.
    for name in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(name, px)
        except OSError:
            pass
    return ImageFont.load_default()

class PinnedEvidence:
    def __init__(self, model, path):
        self.model = model
        self.path = Path(path)
        self.archive = None
        if self.path.is_file():
            with self.path.open("rb") as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            if actual != VISUAL_SHA256[model]:
                raise ValueError(f"{model}: expected diagnostic ZIP SHA256 does not match")
            self.archive = zipfile.ZipFile(self.path)
            self.source = {"kind": "pinned_ZIP", "sha256_verified": actual}
        elif self.path.is_dir():
            # Directory inputs are for synthetic tests/manual inspection only.
            self.source = {"kind": "extracted_directory_UNVERIFIED", "sha256_verified": None}
        else:
            raise FileNotFoundError(self.path)

    def read(self, name):
        relative = f"visual_evidence_new/{self.model}__{name}.png"
        return self.archive.read(relative) if self.archive else (self.path / relative).read_bytes()

    def close(self):
        if self.archive:
            self.archive.close()

def read_png(data):
    with Image.open(io.BytesIO(data)) as original:
        if original.format != "PNG":
            raise ValueError("Expected a PNG from stored Blender renders")
        original.load()
        if original.width < 120 or original.height < 120:
            raise ValueError("Diagnostic image too small")
        return original.convert("RGB")

def review_sheet(sources, movement, outdir, *, crop=False):
    setup = REVIEWS[movement]
    # Draw contact sheets from exact saved photos. Never silently substitute missing views.
    unit_w, unit_h = PANEL_WIDTH, PANEL_HEIGHT
    gap, header, footer, label_h = 13, 76, 76, 29
    width = 3 * unit_w + 4 * gap
    height = header + 3 * (unit_h + label_h + gap) + footer
    image = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(image)
    view = setup["view"]
    title = ("SHOULDER PRESS" if movement == "shoulder_press" else "SQUAT")
    draw.text((gap, 10), f"HOME GYM PT  /  {title}", font=typeface(24), fill="#20385a")
    draw.text((gap, 44), f"Preserved diagnostic overlays  •  {view} view  •  W8 / V14 / R120",
              font=typeface(15), fill="#56657a")
    manifest = {"movement": movement, "camera": view, "cropped_upper_torso": crop,
                "image_provenance": "existing Blender diagnosis run 39937882229",
                "diagnostic_only": True, "anatomical_approval": "NOT_GRANTED",
                "input_sources": {model: sources[model].source for model in MODELS},
                "panels": []}
    for row, model in enumerate(MODELS):
        for col, (sample, label) in enumerate(zip(setup["samples"], setup["labels"])):
            kind = f"{movement}__sample{sample}__overlay__{view}"
            original_bytes = sources[model].read(kind)
            panel = read_png(original_bytes)
            full_size = panel.size
            if crop:
                # Fixed normalized crop covers neck/scapula/axilla area, not hands.
                # Keep the original PNG in the pinned archive for wider context.
                x0 = round(panel.width * .18)
                x1 = round(panel.width * .82)
                y0 = round(panel.height * .16)
                y1 = round(panel.height * .57)
                panel = panel.crop((x0, y0, x1, y1))
            panel = ImageOps.contain(panel, (unit_w, unit_h), Image.Resampling.LANCZOS)
            x = gap + col * (unit_w + gap)
            y = header + row * (unit_h + label_h + gap)
            draw.rounded_rectangle((x, y, x + unit_w, y + unit_h + label_h),
                                   radius=6, fill="#ffffff", outline="#ced6e4", width=2)
            draw.text((x + 9, y + 5), f"{model}   •   {label}", font=typeface(17),
                      fill="#20385a")
            image.paste(panel, (x + (unit_w - panel.width) // 2,
                                y + label_h + (unit_h - panel.height) // 2))
            manifest["panels"].append({
                "model": model, "sample": int(sample), "label": label,
                "png_archive_member": f"visual_evidence_new/{model}__{kind}.png",
                "source_png_sha256": hashlib.sha256(original_bytes).hexdigest(),
                "original_dimensions": full_size,
            })
    draw.text((gap, height - footer + 12),
              "Diagnostic overlays only — NOT a repaired or anatomically approved model.",
              font=typeface(15), fill="#943341")
    draw.text((gap, height - footer + 40),
              "Preserved source images; original .blend model files were NOT modified.",
              font=typeface(14), fill="#56657a")
    suffix = "_upper_torso" if crop else "_full_body"
    output = outdir / f"phone_review_{movement}_{view}{suffix}.jpg"
    image.save(output, format="JPEG", quality=88, optimize=True)
    manifest["contact_sheet_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
    return output, manifest

def produce(paths, outdir):
    sources = {model: PinnedEvidence(model, paths[model]) for model in MODELS}
    try:
        outdir.mkdir(parents=True, exist_ok=True)
        manifest = {"status": "READ_ONLY_PHONE_REVIEW_NOT_ANATOMICAL_APPROVAL",
                    "source_run": 39937882229, "sheets": []}
        for movement in REVIEWS:
            modes = (False, True) if movement == "shoulder_press" else (False,)
            for crop in modes:
                outfile, details = review_sheet(sources, movement, outdir, crop=crop)
                manifest["sheets"].append({"filename": outfile.name, **details})
        (outdir / "phone_review_manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return manifest
    finally:
        for src in sources.values():
            src.close()

def main():
    p = argparse.ArgumentParser()
    for model in MODELS:
        p.add_argument("--" + model.lower(), type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    report = produce({m: getattr(args, m.lower()) for m in MODELS}, args.out)
    for sheet in report["sheets"]:
        print("READ_ONLY_PHONE_VISUAL", sheet["filename"], sheet["contact_sheet_sha256"])

if __name__ == "__main__":
    main()
