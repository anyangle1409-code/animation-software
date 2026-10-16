"""Package measured R35 evidence and review visuals; never soften failed checks."""
import json
import re
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r35_20261016"
def read(name):
    return json.loads((OUT / name).read_text())
a, b = read("r34_press.json"), read("r35_press.json")
ba, bb = read("r34_benchmarks.json"), read("r35_benchmarks.json")
from original_review_r35_reports import validate_samples
validate_samples(a,b,ba,bb)
invariants = read("identity.json")
regressions = []
for x, y in zip(a["press"], b["press"]):
    for metric in ("pairs", "collapse", "stretch"):
        if y[metric] > x[metric]:
            regressions.append({"path": "press", "t": x["t"], "metric": metric, "r34": x[metric], "r35": y[metric]})
for name in ba["benchmarks"]:
    for x, y in zip(ba["benchmarks"][name]["frames"], bb["benchmarks"][name]["frames"]):
        for metric in ("self_intersecting_pairs", "collapse_lt_0_1", "stretch_gt_2"):
            if y[metric] > x[metric]:
                regressions.append({"path": name, "t": x["t"], "metric": metric, "r34": x[metric], "r35": y[metric]})
test_log = (OUT / "front_test.txt").read_text()
from original_review_candidate_checks import acceptance
front_exit = int((OUT / "front_test_exit.txt").read_text().strip())
guard_report = read("r35_guard_recheck.json")
gate = acceptance(invariants, front_exit, test_log, b["press"], regressions, guard_report)
front_pass = gate["checks"]["front_test_process"]
accepted_for_review = gate["passed"]
status = "NUMERIC_CHECKS_PASSED_AWAITING_VISUAL_REVIEW" if accepted_for_review else "REJECTED_NUMERIC_CHECKS"
report = {"candidate": "R35", "approved": False, "status": status,
          "front_test_passed": front_pass, "front_test_exit": front_exit, "acceptance_checks": gate["checks"],
          "guard_violations": guard_report["violations"], "invariants": invariants,
          "regressions": regressions, "r34_fit": a["fit"], "r35_fit": b["fit"]}
contour_log=(OUT/'contour_test.txt').read_text()
contour_exit=int((OUT/'contour_test_exit.txt').read_text())
contour_pass=contour_exit==0 and bool(re.search(r'^OK$',contour_log,re.M))
report['contour_test_passed']=contour_pass
report['contour_test_exit']=contour_exit
report['acceptance_checks']['new_contour_goals']=contour_pass
if not contour_pass:report['status']='REJECTED_NUMERIC_CHECKS'
# This new requirement only tightens the existing acceptance gate.
status=report['status']
had_visuals = (OUT / "r34_r35_same_angle_comparison.jpg").exists() and (OUT / "shoulder_press_r35_three_views.mp4").exists()
previous_status = read("r35_review.json").get("status") if (OUT / "r35_review.json").exists() else None
(OUT / "r35_review.json").write_text(json.dumps(report, indent=2) + "\n")
if not had_visuals:
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font = ImageFont.truetype(font_path, 18)
    small = ImageFont.truetype(font_path, 14)
    bg = (28, 28, 30)
    views = ("back", "front", "three_quarter")
    def frame(tag, n, view):
        im = Image.open(f"/tmp/r35-frames/{tag}/f{n:03d}_{view}.png").convert("RGBA")
        base = Image.new("RGBA", im.size, bg + (255,))
        base.alpha_composite(im)
        return base.convert("RGB")
    numbers = (20, 24, 28, 32)
    sheet = Image.new("RGB", (6 * 256, len(numbers) * 294 + 64), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 8), "R34 / R35 - same press times and cameras - REVIEW ONLY", fill="black", font=font)
    draw.text((12, 34), status, fill="black", font=small)
    for row, n in enumerate(numbers):
        for v, view in enumerate(views):
            for k, tag in enumerate(("r34", "r35")):
                x, y = (2 * v + k) * 256, 64 + row * 294
                draw.text((x + 4, y + 2), f"{tag.upper()} {view.replace('_', ' ')} {b['press'][n]['ht']:.1f} deg",
                          fill="black", font=small)
                sheet.paste(frame(tag, n, view).resize((256, 256)), (x, y + 30))
    sheet.save(OUT / "r34_r35_same_angle_comparison.jpg", quality=92)
    video = Path("/tmp/r35-video")
    video.mkdir(exist_ok=True)
    sequence = [0] * 8 + list(range(41)) + [40] * 8 + list(range(39, 0, -1))
    for i, n in enumerate(sequence):
        image = Image.new("RGB", (1536, 576), bg)
        d = ImageDraw.Draw(image)
        for k, view in enumerate(views):
            image.paste(frame("r35", n, view), (k * 512, 0))
            d.text((k * 512 + 12, 10), view.replace("_", " "), fill="white", font=font)
        d.text((12, 520), f"R35 REVIEW ONLY | elevation {b['press'][n]['ht']:.1f} deg | t={n/40:.3f}",
               fill="white", font=font)
        d.text((12, 548), status, fill=(255, 210, 140), font=small)
        image.save(video / f"f{i:04d}.png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", str(video / "f%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-movflags", "+faststart",
                    str(OUT / "shoulder_press_r35_three_views.mp4")], check=True)
elif previous_status != status:
    # Re-label saved review media after stricter reporting checks; preserve the
    # already-rendered geometry instead of spending another Blender render.
    image = Image.open(OUT / "r34_r35_same_angle_comparison.jpg").convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, image.width, 64), fill="white")
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    draw.text((12, 8), "R34 / R35 - same press times and cameras - REVIEW ONLY", fill="black",
              font=ImageFont.truetype(font_path, 18))
    draw.text((12, 34), status, fill="black", font=ImageFont.truetype(font_path, 14))
    image.save(OUT / "r34_r35_same_angle_comparison.jpg", quality=92)
    original_video = OUT / "shoulder_press_r35_three_views.mp4"
    relabeled = Path("/tmp/r35-relabeled.mp4")
    vf = ("drawbox=x=0:y=544:w=1536:h=32:color=0x1c1c1e:t=fill,"
          f"drawtext=fontfile={font_path}:text='{status}':x=12:y=548:fontsize=14:fontcolor=0xffd28c")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(original_video), "-vf", vf,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-movflags", "+faststart",
                    str(relabeled)], check=True)
    original_video.write_bytes(relabeled.read_bytes())

font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
closeups=Path('/tmp/r35-junction')
for side in ('l','r'):
    sheet=Image.new('RGB',(2400,5*640+64),'white');draw=ImageDraw.Draw(sheet)
    draw.text((12,10),f'Arm-to-side junction ({side}): R34 / R35 same cameras - REVIEW ONLY',fill='black',font=font)
    for row,ht in enumerate((120.,130.,135.625,145.,156.)):
        for view_index,view in enumerate(('back','three_quarter')):
            for tag_index,tag in enumerate(('r34','r35')):
                image=Image.open(closeups/tag/f'{side}_{view}_{ht}.png').convert('RGBA')
                base=Image.new('RGBA',image.size,(28,28,30,255));base.alpha_composite(image)
                x,y=(view_index*2+tag_index)*600,64+row*640
                draw.text((x+10,y+4),f'{tag.upper()} {ht:g} deg {view}',fill='black',font=font)
                sheet.paste(base.convert('RGB').resize((600,600)),(x,y+36))
    sheet.save(OUT/f'r34_r35_junction_{side}_closeups.jpg',quality=94)
front=Image.new('RGB',(2400,3*640+64),'white');draw=ImageDraw.Draw(front)
draw.text((12,10),'Bilateral front transition: R34 / R35 same cameras',fill='black',font=font)
for row,ht in enumerate((120.,130.,145.)):
    for side_index,side in enumerate(('l','r')):
        for tag_index,tag in enumerate(('r34','r35')):
            image=Image.open(Path('/tmp/r35-front')/tag/f'{side}_front_{ht}.png').convert('RGBA')
            base=Image.new('RGBA',image.size,(28,28,30,255));base.alpha_composite(image)
            x,y=(side_index*2+tag_index)*600,64+row*640
            draw.text((x+10,y+4),f'{tag.upper()} {side} front {ht:g} deg',fill='black',font=font)
            front.paste(base.convert('RGB').resize((600,600)),(x,y+36))
front.save(OUT/'r34_r35_front_closeups.jpg',quality=94)
doc=f"""# ORIGINAL_v1 R35: broader arm-to-side skin transition

**{report['status']}. Owner visual approval: pending.**

The owner approved a broader local skin transition rebuild on 16 October 2026 after rejecting R34's arm-root shelf. The frozen skeleton, skin weights, basis, topology and all non-S7 keys are required to remain identical. No HGPT_SHOULDER key is edited. R34 and all earlier assets are immutable.

R35 uses an anchored thin-plate surface target over a broader shoulder/upper-arm/side patch. The support ellipsoid is 19/20/22 cm; its outer 35% fades to a fixed boundary. A 15mm front-sentinel neighborhood is protected, with a 30mm blend. Position-anchor coefficient is 0.001. Gains are 1 at 120/130/145 degrees, 0.4 at 156 and 0 at 166. Targets are inverse-baked into existing S7 keys; the original guards run unchanged at 41 samples on each of two paths. The exact offsets and guard history are in r35_build.json. No new key family or mesh topology is introduced.

## Tests and measured results

The new rear contour test was fixed before the rebuild. At the owner's exact 135.625-degree frame, both rear outlines must have less than 12.5 degrees of tangent change over adjacent 10mm spans (sampled at 2mm, 15-80mm below GH). R34 fails twice: left 17.5147, right 16.9866. Three-quarter peaks must not worsen from R34 (left 35.407937, right 53.426476 degrees). These outline checks do not measure every visible surface ridge and never substitute for owner review.

The R34 front tests run unchanged on R35; they retain the 10mm front-fit and 100-degree dihedral limits. Every old test remains intact. New reporting tests reject truncated or mismatched frame lists before comparison; this strengthens reporting only. Final guard checks compare against no-S7 at 82 samples; the strict original 2.5% lockout-volume rule and zero pairs/collapses above 95 degrees remain intact. Every actual frame of 13 benchmarks and 41 full-press samples is compared with R34. Any count increase rejects the numerical candidate. Identity compares to R33, whose protected data R34 already exactly matches.

Acceptance checks:

```json
{json.dumps(report['acceptance_checks'],indent=2)}
```

All regressions (including worse results):

```json
{json.dumps(regressions,indent=2)}
```

Front tests: exit {front_exit}; contour tests: exit {contour_exit}. Full logs, fit distributions, benchmark frames and guard measurements accompany the model. A numerically rejected candidate is retained as evidence and never presented as accepted.

## Review and reproduction

- r34_r35_junction_l_closeups.jpg and r34_r35_junction_r_closeups.jpg: exact 120/130/135.625/145/156-degree rear and three-quarter details.
- r34_r35_front_closeups.jpg: bilateral front-boundary inspection.
- r34_r35_same_angle_comparison.jpg: matched full views.
- shoulder_press_r35_three_views.mp4: complete up/down press, raw review skin.
- r35_review.json and r35_build.json: status, all metrics and exact settings.
- probe/r35_contour_surfaces.npz: fresh saved-model geometry for reproducible contour checks.

Workflow: .github/workflows/original-review-r35.yml; pinned Blender 5.2.1. Build: export posed parent; run fair_original_review_r35_targets.py; build_original_review_candidate_r35_blender.py -- build; run unchanged measurements/tests; render both versions in clean Blender processes; package evidence. No owner reference images are stored. No merge or force push.
"""
(ROOT/'docs/CODEX_ORIGINAL_V1_REVIEW_CANDIDATE_R35_20261016.md').write_text(doc)
print('R35_REVIEW_FINAL',json.dumps(report),flush=True)
