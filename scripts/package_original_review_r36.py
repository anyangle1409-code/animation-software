"""Package measured R36 evidence and review visuals; never soften failed checks."""
import json
import re
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r36_20261016"
def read(name):
    return json.loads((OUT / name).read_text())
a, b = read("r34_press.json"), read("r36_press.json")
ba, bb = read("r34_benchmarks.json"), read("r36_benchmarks.json")
from original_review_r35_reports import validate_samples
validate_samples(a,b,ba,bb)
invariants = read("identity.json")
regressions = []
for x, y in zip(a["press"], b["press"]):
    for metric in ("pairs", "collapse", "stretch"):
        if y[metric] > x[metric]:
            regressions.append({"path": "press", "t": x["t"], "metric": metric, "r34": x[metric], "r36": y[metric]})
for name in ba["benchmarks"]:
    for x, y in zip(ba["benchmarks"][name]["frames"], bb["benchmarks"][name]["frames"]):
        for metric in ("self_intersecting_pairs", "collapse_lt_0_1", "stretch_gt_2"):
            if y[metric] > x[metric]:
                regressions.append({"path": name, "t": x["t"], "metric": metric, "r34": x[metric], "r36": y[metric]})
test_log = (OUT / "front_test.txt").read_text()
from original_review_candidate_checks import acceptance
front_exit = int((OUT / "front_test_exit.txt").read_text().strip())
guard_report = read("r36_guard_recheck.json")
gate = acceptance(invariants, front_exit, test_log, b["press"], regressions, guard_report)
front_pass = gate["checks"]["front_test_process"]
accepted_for_review = gate["passed"]
status = "NUMERIC_CHECKS_PASSED_AWAITING_VISUAL_REVIEW" if accepted_for_review else "REJECTED_NUMERIC_CHECKS"
report = {"candidate": "R36", "approved": False, "status": status,
          "front_test_passed": front_pass, "front_test_exit": front_exit, "acceptance_checks": gate["checks"],
          "guard_violations": guard_report["violations"], "invariants": invariants,
          "regressions": regressions, "r34_fit": a["fit"], "r36_fit": b["fit"]}
contour_log=(OUT/'contour_test.txt').read_text()
contour_exit=int((OUT/'contour_test_exit.txt').read_text())
contour_pass=contour_exit==0 and bool(re.search(r'^OK$',contour_log,re.M))
report['contour_test_passed']=contour_pass
report['contour_test_exit']=contour_exit
report['acceptance_checks']['new_contour_goals']=contour_pass
if not contour_pass:report['status']='REJECTED_NUMERIC_CHECKS'
# This new requirement only tightens the existing acceptance gate.
status=report['status']
had_visuals = (OUT / "r35_r36_same_angle_comparison.jpg").exists() and (OUT / "shoulder_press_r36_three_views.mp4").exists()
previous_status = read("r36_review.json").get("status") if (OUT / "r36_review.json").exists() else None
(OUT / "r36_review.json").write_text(json.dumps(report, indent=2) + "\n")
if not had_visuals:
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font = ImageFont.truetype(font_path, 18)
    small = ImageFont.truetype(font_path, 14)
    bg = (28, 28, 30)
    views = ("back", "front", "three_quarter")
    def frame(tag, n, view):
        im = Image.open(f"/tmp/r36-frames/{tag}/f{n:03d}_{view}.png").convert("RGBA")
        base = Image.new("RGBA", im.size, bg + (255,))
        base.alpha_composite(im)
        return base.convert("RGB")
    numbers = (20, 24, 28, 32)
    sheet = Image.new("RGB", (6 * 256, len(numbers) * 294 + 64), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 8), "R35 / R36 - same press times and cameras - REVIEW ONLY", fill="black", font=font)
    draw.text((12, 34), status, fill="black", font=small)
    for row, n in enumerate(numbers):
        for v, view in enumerate(views):
            for k, tag in enumerate(("r35", "r36")):
                x, y = (2 * v + k) * 256, 64 + row * 294
                draw.text((x + 4, y + 2), f"{tag.upper()} {view.replace('_', ' ')} {b['press'][n]['ht']:.1f} deg",
                          fill="black", font=small)
                sheet.paste(frame(tag, n, view).resize((256, 256)), (x, y + 30))
    sheet.save(OUT / "r35_r36_same_angle_comparison.jpg", quality=92)
    video = Path("/tmp/r36-video")
    video.mkdir(exist_ok=True)
    sequence = [0] * 8 + list(range(41)) + [40] * 8 + list(range(39, 0, -1))
    for i, n in enumerate(sequence):
        image = Image.new("RGB", (1536, 576), bg)
        d = ImageDraw.Draw(image)
        for k, view in enumerate(views):
            image.paste(frame("r36", n, view), (k * 512, 0))
            d.text((k * 512 + 12, 10), view.replace("_", " "), fill="white", font=font)
        d.text((12, 520), f"R36 REVIEW ONLY | elevation {b['press'][n]['ht']:.1f} deg | t={n/40:.3f}",
               fill="white", font=font)
        d.text((12, 548), status, fill=(255, 210, 140), font=small)
        image.save(video / f"f{i:04d}.png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", str(video / "f%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-movflags", "+faststart",
                    str(OUT / "shoulder_press_r36_three_views.mp4")], check=True)
elif previous_status != status:
    # Re-label saved review media after stricter reporting checks; preserve the
    # already-rendered geometry instead of spending another Blender render.
    image = Image.open(OUT / "r35_r36_same_angle_comparison.jpg").convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, image.width, 64), fill="white")
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    draw.text((12, 8), "R35 / R36 - same press times and cameras - REVIEW ONLY", fill="black",
              font=ImageFont.truetype(font_path, 18))
    draw.text((12, 34), status, fill="black", font=ImageFont.truetype(font_path, 14))
    image.save(OUT / "r35_r36_same_angle_comparison.jpg", quality=92)
    original_video = OUT / "shoulder_press_r36_three_views.mp4"
    relabeled = Path("/tmp/r36-relabeled.mp4")
    vf = ("drawbox=x=0:y=544:w=1536:h=32:color=0x1c1c1e:t=fill,"
          f"drawtext=fontfile={font_path}:text='{status}':x=12:y=548:fontsize=14:fontcolor=0xffd28c")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(original_video), "-vf", vf,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-movflags", "+faststart",
                    str(relabeled)], check=True)
    original_video.write_bytes(relabeled.read_bytes())

font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
closeups=Path('/tmp/r36-junction')
for side in ('l','r'):
    sheet=Image.new('RGB',(2400,5*640+64),'white');draw=ImageDraw.Draw(sheet)
    draw.text((12,10),f'Arm-to-side junction ({side}): R35 / R36 same cameras - REVIEW ONLY',fill='black',font=font)
    for row,ht in enumerate((120.,130.,135.625,145.,156.)):
        for view_index,view in enumerate(('back','three_quarter')):
            for tag_index,tag in enumerate(('r35','r36')):
                image=Image.open(closeups/tag/f'{side}_{view}_{ht}.png').convert('RGBA')
                base=Image.new('RGBA',image.size,(28,28,30,255));base.alpha_composite(image)
                x,y=(view_index*2+tag_index)*600,64+row*640
                draw.text((x+10,y+4),f'{tag.upper()} {ht:g} deg {view}',fill='black',font=font)
                sheet.paste(base.convert('RGB').resize((600,600)),(x,y+36))
    sheet.save(OUT/f'r35_r36_junction_{side}_closeups.jpg',quality=94)
front=Image.new('RGB',(2400,3*640+64),'white');draw=ImageDraw.Draw(front)
draw.text((12,10),'Bilateral front transition: R35 / R36 same cameras',fill='black',font=font)
for row,ht in enumerate((120.,130.,145.)):
    for side_index,side in enumerate(('l','r')):
        for tag_index,tag in enumerate(('r35','r36')):
            image=Image.open(Path('/tmp/r36-front')/tag/f'{side}_front_{ht}.png').convert('RGBA')
            base=Image.new('RGBA',image.size,(28,28,30,255));base.alpha_composite(image)
            x,y=(side_index*2+tag_index)*600,64+row*640
            draw.text((x+10,y+4),f'{tag.upper()} {side} front {ht:g} deg',fill='black',font=font)
            front.paste(base.convert('RGB').resize((600,600)),(x,y+36))
front.save(OUT/'r35_r36_front_closeups.jpg',quality=94)
doc=f"""# ORIGINAL_v1 R36: arm-to-side transition with area constraints

**{report['status']}. Owner visual approval pending.**

The owner approved the broader local skin rebuild on 16 October 2026. R35 removed the rear point but expanded many small triangles: at the marked frame the stretch count rose from 81 to 701, so R35 is rejected and preserved. R36 starts from the unchanged R34 model, extends the broader fairing support down the side (vertical radius 28cm versus R35’s 22cm), then redistributes vertices tangentially over that target before inverse baking. R34 is the numerical baseline; R35 is the preceding visual comparison. No R35 geometry is silently replaced.

## Change

Area constraints target at most 1.85 times the neutral triangle area wherever vertices are movable; fixed parts retain their existing area. Existing R34 overstretched triangles are not exempted from the final non-regression test. A lower bound of 0.2 times neutral area prevents crushed triangles. Projection runs 450 Jacobi iterations, snapping to the target triangle surface every five iterations to retain the intended contour. The target generator rejects any face-normal inversion relative to the smooth target or a redistribution slide over 40mm, and records maximum displacement. Nearest-triangle projection is geometric rather than topology-local; final native guards and bilateral visual review remain necessary. This is an authored deformation experiment, not a claim of anatomical correctness. A 2mm posterolateral Gaussian fill (center75mm below GH, vertical sigma16mm, lateral sigma100mm, depth sigma150mm) blends the lower corner; it respects the same front-sentinel protection. Gains remain 1 at 120/130/145 degrees, 0.4 at 156 and zero at 166. The existing 15mm front-sentinel protection and broader support remain unchanged. The native source export records the evaluated neutral surface for area constraints.

Only S7 coordinates change. The same original smooth and final guards run at 41 samples on each of two paths. Protected skeleton, weights, basis, topology and all non-S7 keys are required to match R33 exactly; R34 already matches these. All HGPT_SHOULDER keys remain protected. The R36 build hash, target statistics and guard history are in r36_build.json.

## Tests and measurements

No test or tolerance is weakened. R36 has its own copy of the fixed R35 contour test with identical limits: bilateral rear peak below 12.5 degrees at the marked 135.625-degree frame; three-quarter outline no worse than R34. The unchanged R34 front tests retain the 10mm fit and 100-degree crease limits. The strict original lockout-volume limit remains <2.5%; no pairs or collapses are allowed above 95 degrees. The final saved model is rechecked against no-S7 at 82 samples. Forty-one full-press frames and every actual frame of the same 13 benchmark movements are compared with R34; every increase is retained and rejects the experiment.

```json
{json.dumps(report['acceptance_checks'],indent=2)}
```

All regressions versus R34:

```json
{json.dumps(regressions,indent=2)}
```

Front test exit: {front_exit}. Contour test exit: {contour_exit}. Full logs and distributions accompany the candidate. R34's previously measured, immutable native reports are copied as the baseline, after verifying its saved model hash, avoiding redundant benchmark execution; R36 measurements run in fresh processes with unchanged measurement code.

## Review files and reproduction

- r35_r36_same_angle_comparison.jpg: previous candidate and R36 at matching press times/cameras.
- r35_r36_junction_l_closeups.jpg and r35_r36_junction_r_closeups.jpg: exact 120/130/135.625/145/156-degree details.
- r35_r36_front_closeups.jpg: both front transitions.
- shoulder_press_r36_three_views.mp4: complete raw-skin press.
- r36_review.json: all pass/fail checks, regressions and reference-fit measurements.

Workflow .github/workflows/original-review-r36.yml pins Blender 5.2.1. Run build_original_review_candidate_r36_blender.py -- export; project_original_review_r36_targets.py; then the build mode. It preserves R34/R35 and every production asset. No owner reference photos, third-party assets, merge or force push.
"""
(ROOT/'docs/CODEX_ORIGINAL_V1_REVIEW_CANDIDATE_R36_20261016.md').write_text(doc)
print('R36_REVIEW_FINAL',json.dumps(report),flush=True)
