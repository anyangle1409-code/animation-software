"""Package measured R37 evidence and review visuals; never soften failed checks."""
import json
import re
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r37_20261016"
def read(name):
    return json.loads((OUT / name).read_text())
a, b = read("r34_press.json"), read("r37_press.json")
ba, bb = read("r34_benchmarks.json"), read("r37_benchmarks.json")
from original_review_r35_reports import validate_samples
validate_samples(a,b,ba,bb)
invariants = read("identity.json")
regressions = []
for x, y in zip(a["press"], b["press"]):
    for metric in ("pairs", "collapse", "stretch"):
        if y[metric] > x[metric]:
            regressions.append({"path": "press", "t": x["t"], "metric": metric, "r34": x[metric], "r37": y[metric]})
for name in ba["benchmarks"]:
    for x, y in zip(ba["benchmarks"][name]["frames"], bb["benchmarks"][name]["frames"]):
        for metric in ("self_intersecting_pairs", "collapse_lt_0_1", "stretch_gt_2"):
            if y[metric] > x[metric]:
                regressions.append({"path": name, "t": x["t"], "metric": metric, "r34": x[metric], "r37": y[metric]})
test_log = (OUT / "front_test.txt").read_text()
from original_review_candidate_checks import acceptance
front_exit = int((OUT / "front_test_exit.txt").read_text().strip())
guard_report = read("r37_guard_recheck.json")
gate = acceptance(invariants, front_exit, test_log, b["press"], regressions, guard_report)
front_pass = gate["checks"]["front_test_process"]
accepted_for_review = gate["passed"]
status = "NUMERIC_CHECKS_PASSED_AWAITING_VISUAL_REVIEW" if accepted_for_review else "REJECTED_NUMERIC_CHECKS"
report = {"candidate": "R37", "approved": False, "status": status,
          "front_test_passed": front_pass, "front_test_exit": front_exit, "acceptance_checks": gate["checks"],
          "guard_violations": guard_report["violations"], "invariants": invariants,
          "regressions": regressions, "r34_fit": a["fit"], "r37_fit": b["fit"]}
contour_log=(OUT/'contour_test.txt').read_text()
contour_exit=int((OUT/'contour_test_exit.txt').read_text())
contour_pass=contour_exit==0 and bool(re.search(r'^OK$',contour_log,re.M))
report['contour_test_passed']=contour_pass
report['contour_test_exit']=contour_exit
report['acceptance_checks']['new_contour_goals']=contour_pass
if not contour_pass:report['status']='REJECTED_NUMERIC_CHECKS'
# This new requirement only tightens the existing acceptance gate.
status=report['status']
had_visuals = (OUT / "r36_r37_same_angle_comparison.jpg").exists() and (OUT / "shoulder_press_r37_three_views.mp4").exists()
previous_status = read("r37_review.json").get("status") if (OUT / "r37_review.json").exists() else None
(OUT / "r37_review.json").write_text(json.dumps(report, indent=2) + "\n")
if not had_visuals:
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font = ImageFont.truetype(font_path, 18)
    small = ImageFont.truetype(font_path, 14)
    bg = (28, 28, 30)
    views = ("back", "front", "three_quarter")
    def frame(tag, n, view):
        im = Image.open(f"/tmp/r37-frames/{tag}/f{n:03d}_{view}.png").convert("RGBA")
        base = Image.new("RGBA", im.size, bg + (255,))
        base.alpha_composite(im)
        return base.convert("RGB")
    numbers = (20, 24, 28, 32)
    sheet = Image.new("RGB", (6 * 256, len(numbers) * 294 + 64), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 8), "R36 / R37 - same press times and cameras - REVIEW ONLY", fill="black", font=font)
    draw.text((12, 34), status, fill="black", font=small)
    for row, n in enumerate(numbers):
        for v, view in enumerate(views):
            for k, tag in enumerate(("r36", "r37")):
                x, y = (2 * v + k) * 256, 64 + row * 294
                draw.text((x + 4, y + 2), f"{tag.upper()} {view.replace('_', ' ')} {b['press'][n]['ht']:.1f} deg",
                          fill="black", font=small)
                sheet.paste(frame(tag, n, view).resize((256, 256)), (x, y + 30))
    sheet.save(OUT / "r36_r37_same_angle_comparison.jpg", quality=92)
    video = Path("/tmp/r37-video")
    video.mkdir(exist_ok=True)
    sequence = [0] * 8 + list(range(41)) + [40] * 8 + list(range(39, 0, -1))
    for i, n in enumerate(sequence):
        image = Image.new("RGB", (1536, 576), bg)
        d = ImageDraw.Draw(image)
        for k, view in enumerate(views):
            image.paste(frame("r37", n, view), (k * 512, 0))
            d.text((k * 512 + 12, 10), view.replace("_", " "), fill="white", font=font)
        d.text((12, 520), f"R37 REVIEW ONLY | elevation {b['press'][n]['ht']:.1f} deg | t={n/40:.3f}",
               fill="white", font=font)
        d.text((12, 548), status, fill=(255, 210, 140), font=small)
        image.save(video / f"f{i:04d}.png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", str(video / "f%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-movflags", "+faststart",
                    str(OUT / "shoulder_press_r37_three_views.mp4")], check=True)
elif previous_status != status:
    # Re-label saved review media after stricter reporting checks; preserve the
    # already-rendered geometry instead of spending another Blender render.
    image = Image.open(OUT / "r36_r37_same_angle_comparison.jpg").convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, image.width, 64), fill="white")
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    draw.text((12, 8), "R36 / R37 - same press times and cameras - REVIEW ONLY", fill="black",
              font=ImageFont.truetype(font_path, 18))
    draw.text((12, 34), status, fill="black", font=ImageFont.truetype(font_path, 14))
    image.save(OUT / "r36_r37_same_angle_comparison.jpg", quality=92)
    original_video = OUT / "shoulder_press_r37_three_views.mp4"
    relabeled = Path("/tmp/r37-relabeled.mp4")
    vf = ("drawbox=x=0:y=544:w=1536:h=32:color=0x1c1c1e:t=fill,"
          f"drawtext=fontfile={font_path}:text='{status}':x=12:y=548:fontsize=14:fontcolor=0xffd28c")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(original_video), "-vf", vf,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-movflags", "+faststart",
                    str(relabeled)], check=True)
    original_video.write_bytes(relabeled.read_bytes())

font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
closeups=Path('/tmp/r37-junction')
for side in ('l','r'):
    sheet=Image.new('RGB',(2400,5*640+64),'white');draw=ImageDraw.Draw(sheet)
    draw.text((12,10),f'Arm-to-side junction ({side}): R36 / R37 same cameras - REVIEW ONLY',fill='black',font=font)
    for row,ht in enumerate((120.,130.,135.625,145.,156.)):
        for view_index,view in enumerate(('back','three_quarter')):
            for tag_index,tag in enumerate(('r36','r37')):
                image=Image.open(closeups/tag/f'{side}_{view}_{ht}.png').convert('RGBA')
                base=Image.new('RGBA',image.size,(28,28,30,255));base.alpha_composite(image)
                x,y=(view_index*2+tag_index)*600,64+row*640
                draw.text((x+10,y+4),f'{tag.upper()} {ht:g} deg {view}',fill='black',font=font)
                sheet.paste(base.convert('RGB').resize((600,600)),(x,y+36))
    sheet.save(OUT/f'r36_r37_junction_{side}_closeups.jpg',quality=94)
front=Image.new('RGB',(2400,3*640+64),'white');draw=ImageDraw.Draw(front)
draw.text((12,10),'Bilateral front transition: R36 / R37 same cameras',fill='black',font=font)
for row,ht in enumerate((120.,130.,145.)):
    for side_index,side in enumerate(('l','r')):
        for tag_index,tag in enumerate(('r36','r37')):
            image=Image.open(Path('/tmp/r37-front')/tag/f'{side}_front_{ht}.png').convert('RGBA')
            base=Image.new('RGBA',image.size,(28,28,30,255));base.alpha_composite(image)
            x,y=(side_index*2+tag_index)*600,64+row*640
            draw.text((x+10,y+4),f'{tag.upper()} {side} front {ht:g} deg',fill='black',font=font)
            front.paste(base.convert('RGB').resize((600,600)),(x,y+36))
front.save(OUT/'r36_r37_front_closeups.jpg',quality=94)
doc=f"""# ORIGINAL_v1 R37: coupled skin-transition constraints

**{report['status']}. Owner visual approval pending.**

R36 softened the marked arm-to-side point and reduced full-press stretch at 135.625 degrees from81 to11, but failed17 comparisons elsewhere. A benchmark collision at t=0.975 caused the original guard to change the156/166-degree keys, raising lockout stretch80→111. R36 is preserved as rejected. Single-key full-press area constraints did not cover the second press path or transitions.

R37 starts from immutable R34. It takes R36's120/130/145 mid-press skin shape, introduces a110-degree S7 key whose base exactly interpolates R34, and solves material-coordinate adjustments across41 samples of each press path. Native skin-response matrices are checked against Blender evaluation before optimization (maximum allowed error0.01mm). Adjustments follow each key's local skin tangent and stay within15mm of the initial mid shape. The156/166-degree keys remain exactly R34's; if either original guard changes them, no model is saved. The original guards and every existing tolerance are unchanged.

## Measured checks

```json
{json.dumps(report['acceptance_checks'],indent=2)}
```

Front test exit: {front_exit}. Contour test exit: {contour_exit}. Regressions versus R34: **{len(regressions)}**; all are retained in r37_review.json. Any increase rejects the numerical candidate. The fixed contour requirements remain bilateral rear peak<12.5degrees at135.625 and three-quarter no worse than R34. Front fit<10mm, crease<100degrees, original strict lockout volume<2.5%, zero intersections/collapses above95degrees, and82 final guard comparisons remain intact. All41 full-press samples and actual frames of13 movements are compared. No test was weakened or deleted.

The skeleton, basis, topology, weights and every non-S7 coordinate (including HGPT_SHOULDER keys) must exactly match R33/R34. R34 baseline reports are copied after verifying its model hash. R37 is measured in fresh native processes. Linear response, solver history, exact settings, frozen-key verification and guard histories are in r37_build.json.

## Review files and reproduction

r36_r37_same_angle_comparison.jpg and bilateral junction/front closeups compare the preceding candidate at identical poses/cameras. shoulder_press_r37_three_views.mp4 is the full raw-skin press. Files are under codex_review_r37_20261016. Owner reference images stay out of the repo.

Workflow .github/workflows/original-review-r37.yml uses pinned Blender5.2.1: export_original_review_r37_blender.py → solve_original_review_r37.py → build_original_review_candidate_r37_blender.py -- build → unchanged native measurements/guards/front test → fixed contour test → renders/package. No production assets, merge or force push.
"""
(ROOT/'docs/CODEX_ORIGINAL_V1_REVIEW_CANDIDATE_R37_20261016.md').write_text(doc)
print('R37_REVIEW_FINAL',json.dumps(report),flush=True)
