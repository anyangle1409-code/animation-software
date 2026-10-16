"""Package measured R34 evidence and review visuals; never soften failed checks."""
import json
import re
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r34_20261016"
def read(name):
    return json.loads((OUT / name).read_text())
a, b = read("r33_press.json"), read("r34_press.json")
ba, bb = read("r33_benchmarks.json"), read("r34_benchmarks.json")
invariants = read("identity.json")
regressions = []
for x, y in zip(a["press"], b["press"]):
    for metric in ("pairs", "collapse", "stretch"):
        if y[metric] > x[metric]:
            regressions.append({"path": "press", "t": x["t"], "metric": metric, "r33": x[metric], "r34": y[metric]})
for name in ba["benchmarks"]:
    for x, y in zip(ba["benchmarks"][name]["frames"], bb["benchmarks"][name]["frames"]):
        for metric in ("self_intersecting_pairs", "collapse_lt_0_1", "stretch_gt_2"):
            if y[metric] > x[metric]:
                regressions.append({"path": name, "t": x["t"], "metric": metric, "r33": x[metric], "r34": y[metric]})
test_log = (OUT / "front_test.txt").read_text()
front_pass = bool(re.search(r"^OK$", test_log, re.M))
accepted_for_review = front_pass and all(invariants.values()) and not regressions
status = "NUMERIC_CHECKS_PASSED_AWAITING_VISUAL_REVIEW" if accepted_for_review else "REJECTED_NUMERIC_CHECKS"
report = {"candidate": "R34", "approved": False, "status": status,
          "front_test_passed": front_pass, "invariants": invariants,
          "regressions": regressions, "r33_fit": a["fit"], "r34_fit": b["fit"]}
(OUT / "r34_review.json").write_text(json.dumps(report, indent=2) + "\n")
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
font = ImageFont.truetype(font_path, 18)
small = ImageFont.truetype(font_path, 14)
bg = (28, 28, 30)
views = ("back", "front", "three_quarter")
def frame(tag, n, view):
    im = Image.open(f"/tmp/r34-frames/{tag}/f{n:03d}_{view}.png").convert("RGBA")
    base = Image.new("RGBA", im.size, bg + (255,))
    base.alpha_composite(im)
    return base.convert("RGB")
numbers = (20, 24, 28, 32)
sheet = Image.new("RGB", (6 * 256, len(numbers) * 294 + 64), "white")
draw = ImageDraw.Draw(sheet)
draw.text((12, 8), "R33 / R34 - same press times and cameras - REVIEW ONLY", fill="black", font=font)
draw.text((12, 34), status, fill="black", font=small)
for row, n in enumerate(numbers):
    for v, view in enumerate(views):
        for k, tag in enumerate(("r33", "r34")):
            x, y = (2 * v + k) * 256, 64 + row * 294
            draw.text((x + 4, y + 2), f"{tag.upper()} {view.replace('_', ' ')} {b['press'][n]['ht']:.1f} deg",
                      fill="black", font=small)
            sheet.paste(frame(tag, n, view).resize((256, 256)), (x, y + 30))
sheet.save(OUT / "r33_r34_same_angle_comparison.jpg", quality=92)
video = Path("/tmp/r34-video")
video.mkdir(exist_ok=True)
sequence = [0] * 8 + list(range(41)) + [40] * 8 + list(range(39, 0, -1))
for i, n in enumerate(sequence):
    image = Image.new("RGB", (1536, 576), bg)
    d = ImageDraw.Draw(image)
    for k, view in enumerate(views):
        image.paste(frame("r34", n, view), (k * 512, 0))
        d.text((k * 512 + 12, 10), view.replace("_", " "), fill="white", font=font)
    d.text((12, 520), f"R34 REVIEW ONLY | elevation {b['press'][n]['ht']:.1f} deg | t={n/40:.3f}",
           fill="white", font=font)
    d.text((12, 548), status, fill=(255, 210, 140), font=small)
    image.save(video / f"f{i:04d}.png")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", str(video / "f%04d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-movflags", "+faststart",
                str(OUT / "shoulder_press_r34_three_views.mp4")], check=True)
rows = "\n".join(
    f"| {ht} | {a['fit'][str(float(ht))]['v18633_mm']:.3f} | {b['fit'][str(float(ht))]['v18633_mm']:.3f} |"
    for ht in (120, 145, 156, 166))
details = json.dumps(regressions, indent=2)
doc = f"""# ORIGINAL_v1 R34: bounded front-armpit experiment (16 October 2026)

**{status}. NOT ACCEPTED.** This is a separate candidate, not a production asset.

## Change and rationale

R33's inverse bake matches the front target, but guard cutbacks at full-press t=0.60 and benchmark t=0.55 damage the front patch. Cutbacks can themselves create new intersections and collapsed faces, causing further cutbacks.

R34 starts from R33 and restores inverse-bake detail at 120/145 only inside a symmetric front geodesic patch (full inside 2 cm, smoothly fading to zero at 5 cm). It adds an intermediate S7 key at 130 degrees, with 30 small Taubin fairing passes inside that same patch. Outside the patch the intermediate key initially reproduces the existing 120/145 interpolation exactly.

The original smooth and final guards run on the resulting candidate with 41 samples, containing every old guard sample and every nine-frame benchmark sample. Their source and thresholds are unchanged. An unguarded inverse reference is generated in memory solely as input; it is never saved as a candidate.

No canonical bones, basis mesh, skin weights or non-S7 shape keys are intentionally changed. All HGPT_SHOULDER keys are checked as part of the non-S7 identity comparison.

## Fixed regression goals, established before implementation

- Front sentinel vertex 18633: under 10 mm from the unchanged R33 target at both 120 and 145 degrees.
- Front-patch maximum dihedral at 130 degrees: under 100 degrees (R33 measured 132.393).
- These new tests failed on unchanged R33 with exactly three assertion failures. No pre-existing test or tolerance was changed.
- Numerical comparison uses clean Blender processes for each model/path, avoiding inherited module hooks.

Front test passed: **{front_pass}**.

## Target-fit measurement at the front sentinel

| Elevation | R33 error (mm) | R34 error (mm) |
|---|---:|---:|
{rows}

Full distributions remain in r33_press.json and r34_press.json.

## Preservation checks

{json.dumps(invariants, indent=2)}

The skeleton matrices/parents/deform flags, basis, topology, all weights and every non-S7 key must match R33 exactly.

## Regressions (all retained)

{len(regressions)} increases were measured across the 41-frame full press and all 13 benchmark movements, comparing each actual frame with R33.

```json
{details}
```

A failed front goal, preservation check or any recorded increase rejects the numerical experiment. Visual review is still required even if numerical checks pass. The tests do not establish anatomical correctness or medical approval.

## Review files and reproduction

- r33_r34_same_angle_comparison.jpg: identical 118/132/145/156-degree vicinity press times, back/front/three-quarter views.
- shoulder_press_r34_three_views.mp4: raw skin views along the complete up/down press.
- front_test.txt: unchanged R34 regression test output.
- r34_build.json: exact candidate settings and guard history.
- r33/r34_benchmarks.json: all 13 movement results.
- r34_review.json: status, fit and all numerical regressions.

Build and render commands are recorded in .github/workflows/original-review-front-regression.yml. Python scripts run through pinned Blender 5.2.1. Each measurement/render invocation uses a fresh process.

No owner reference photos are included. No merge or force-push is part of this workflow.
"""
(ROOT / "docs/CODEX_ORIGINAL_V1_REVIEW_CANDIDATE_R34_20261016.md").write_text(doc)
print("R34_REVIEW", json.dumps(report), flush=True)
