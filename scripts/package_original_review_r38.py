"""Package measured R38 evidence and review visuals; never soften failed checks."""
import json
import re
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r38_20261017"
def read(name):
    return json.loads((OUT / name).read_text())
a, b = read("r34_press.json"), read("r38_press.json")
ba, bb = read("r34_benchmarks.json"), read("r38_benchmarks.json")
from original_review_r35_reports import validate_samples
validate_samples(a,b,ba,bb)
invariants = read("identity.json")
regressions = []
for x, y in zip(a["press"], b["press"]):
    for metric in ("pairs", "collapse", "stretch"):
        if y[metric] > x[metric]:
            regressions.append({"path": "press", "t": x["t"], "metric": metric, "r34": x[metric], "r38": y[metric]})
for name in ba["benchmarks"]:
    for x, y in zip(ba["benchmarks"][name]["frames"], bb["benchmarks"][name]["frames"]):
        for metric in ("self_intersecting_pairs", "collapse_lt_0_1", "stretch_gt_2"):
            if y[metric] > x[metric]:
                regressions.append({"path": name, "t": x["t"], "metric": metric, "r34": x[metric], "r38": y[metric]})
# The parent is an additional baseline; R34 comparisons above remain intact.
parent=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r37_20261016'
pa=json.loads((parent/'r37_press.json').read_text());pb=json.loads((parent/'r37_benchmarks.json').read_text())
validate_samples(pa,b,pb,bb)
for x,y in zip(pa['press'],b['press']):
    for metric in ('pairs','collapse','stretch'):
        if y[metric]>x[metric]:regressions.append({'baseline':'R37','path':'press','t':x['t'],'metric':metric,'r37':x[metric],'r38':y[metric]})
for name in pb['benchmarks']:
    for x,y in zip(pb['benchmarks'][name]['frames'],bb['benchmarks'][name]['frames']):
        for metric in ('self_intersecting_pairs','collapse_lt_0_1','stretch_gt_2'):
            if y[metric]>x[metric]:regressions.append({'baseline':'R37','path':name,'t':x['t'],'metric':metric,'r37':x[metric],'r38':y[metric]})
test_log = (OUT / "front_test.txt").read_text()
from original_review_candidate_checks import acceptance
front_exit = int((OUT / "front_test_exit.txt").read_text().strip())
guard_report = read("r38_guard_recheck.json")
gate = acceptance(invariants, front_exit, test_log, b["press"], regressions, guard_report)
front_pass = gate["checks"]["front_test_process"]
accepted_for_review = gate["passed"]
status = "NUMERIC_CHECKS_PASSED_AWAITING_VISUAL_REVIEW" if accepted_for_review else "REJECTED_NUMERIC_CHECKS"
report = {"candidate": "R38", "approved": False, "status": status,
          "front_test_passed": front_pass, "front_test_exit": front_exit, "acceptance_checks": gate["checks"],
          "guard_violations": guard_report["violations"], "invariants": invariants,
          "regressions": regressions, "r34_fit": a["fit"], "r38_fit": b["fit"]}
contour_log=(OUT/'contour_test.txt').read_text()
contour_exit=int((OUT/'contour_test_exit.txt').read_text())
contour_pass=contour_exit==0 and bool(re.search(r'^OK$',contour_log,re.M))
report['contour_test_passed']=contour_pass
report['contour_test_exit']=contour_exit
report['acceptance_checks']['new_contour_goals']=contour_pass
if not contour_pass:report['status']='REJECTED_NUMERIC_CHECKS'
marks_exit=int((OUT/'marks_test_exit.txt').read_text())
marks_log=(OUT/'marks_test.txt').read_text()
marks_pass=marks_exit==0 and bool(re.search(r'^OK$',marks_log,re.M))
report['acceptance_checks']['new_owner_mark_goals']=marks_pass
if not marks_pass:report['status']='REJECTED_NUMERIC_CHECKS'
orientation=read('r38_orientation.json')
orientation_pass=orientation.get('sample_count')==82 and len(orientation.get('samples',[]))==82 and orientation.get('passed') is True and all(x['normal_rotations_over_90_degrees']==0 for x in orientation['samples'])
report['acceptance_checks']['final_native_orientation']=orientation_pass
if not orientation_pass:report['status']='REJECTED_NUMERIC_CHECKS'
# This new requirement only tightens the existing acceptance gate.
status=report['status']
had_visuals = (OUT / "r37_r38_same_angle_comparison.jpg").exists() and (OUT / "shoulder_press_r38_three_views.mp4").exists()
previous_status = read("r38_review.json").get("status") if (OUT / "r38_review.json").exists() else None
(OUT / "r38_review.json").write_text(json.dumps(report, indent=2) + "\n")
if not had_visuals:
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font = ImageFont.truetype(font_path, 18)
    small = ImageFont.truetype(font_path, 14)
    bg = (28, 28, 30)
    views = ("back", "front", "three_quarter")
    def frame(tag, n, view):
        im = Image.open(f"/tmp/r38-frames/{tag}/f{n:03d}_{view}.png").convert("RGBA")
        base = Image.new("RGBA", im.size, bg + (255,))
        base.alpha_composite(im)
        return base.convert("RGB")
    numbers = (20, 24, 28, 32)
    sheet = Image.new("RGB", (6 * 256, len(numbers) * 294 + 64), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 8), "R37 / R38 - same press times and cameras - REVIEW ONLY", fill="black", font=font)
    draw.text((12, 34), status, fill="black", font=small)
    for row, n in enumerate(numbers):
        for v, view in enumerate(views):
            for k, tag in enumerate(("r37", "r38")):
                x, y = (2 * v + k) * 256, 64 + row * 294
                draw.text((x + 4, y + 2), f"{tag.upper()} {view.replace('_', ' ')} {b['press'][n]['ht']:.1f} deg",
                          fill="black", font=small)
                sheet.paste(frame(tag, n, view).resize((256, 256)), (x, y + 30))
    sheet.save(OUT / "r37_r38_same_angle_comparison.jpg", quality=92)
    video = Path("/tmp/r38-video")
    video.mkdir(exist_ok=True)
    sequence = [0] * 8 + list(range(41)) + [40] * 8 + list(range(39, 0, -1))
    for i, n in enumerate(sequence):
        image = Image.new("RGB", (1536, 576), bg)
        d = ImageDraw.Draw(image)
        for k, view in enumerate(views):
            image.paste(frame("r38", n, view), (k * 512, 0))
            d.text((k * 512 + 12, 10), view.replace("_", " "), fill="white", font=font)
        d.text((12, 520), f"R38 REVIEW ONLY | elevation {b['press'][n]['ht']:.1f} deg | t={n/40:.3f}",
               fill="white", font=font)
        d.text((12, 548), status, fill=(255, 210, 140), font=small)
        image.save(video / f"f{i:04d}.png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", str(video / "f%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-movflags", "+faststart",
                    str(OUT / "shoulder_press_r38_three_views.mp4")], check=True)
elif previous_status != status:
    # Re-label saved review media after stricter reporting checks; preserve the
    # already-rendered geometry instead of spending another Blender render.
    image = Image.open(OUT / "r37_r38_same_angle_comparison.jpg").convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, image.width, 64), fill="white")
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    draw.text((12, 8), "R37 / R38 - same press times and cameras - REVIEW ONLY", fill="black",
              font=ImageFont.truetype(font_path, 18))
    draw.text((12, 34), status, fill="black", font=ImageFont.truetype(font_path, 14))
    image.save(OUT / "r37_r38_same_angle_comparison.jpg", quality=92)
    original_video = OUT / "shoulder_press_r38_three_views.mp4"
    relabeled = Path("/tmp/r38-relabeled.mp4")
    vf = ("drawbox=x=0:y=544:w=1536:h=32:color=0x1c1c1e:t=fill,"
          f"drawtext=fontfile={font_path}:text='{status}':x=12:y=548:fontsize=14:fontcolor=0xffd28c")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(original_video), "-vf", vf,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-movflags", "+faststart",
                    str(relabeled)], check=True)
    original_video.write_bytes(relabeled.read_bytes())

font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
closeups=Path('/tmp/r38-junction')
for side in ('l','r'):
    sheet=Image.new('RGB',(2400,5*640+64),'white');draw=ImageDraw.Draw(sheet)
    draw.text((12,10),f'Arm-to-side junction ({side}): R37 / R38 same cameras - REVIEW ONLY',fill='black',font=font)
    for row,ht in enumerate((120.,130.,135.625,145.,156.)):
        for view_index,view in enumerate(('back','three_quarter')):
            for tag_index,tag in enumerate(('r37','r38')):
                image=Image.open(closeups/tag/f'{side}_{view}_{ht}.png').convert('RGBA')
                base=Image.new('RGBA',image.size,(28,28,30,255));base.alpha_composite(image)
                x,y=(view_index*2+tag_index)*600,64+row*640
                draw.text((x+10,y+4),f'{tag.upper()} {ht:g} deg {view}',fill='black',font=font)
                sheet.paste(base.convert('RGB').resize((600,600)),(x,y+36))
    sheet.save(OUT/f'r37_r38_junction_{side}_closeups.jpg',quality=94)
front=Image.new('RGB',(2400,3*640+64),'white');draw=ImageDraw.Draw(front)
draw.text((12,10),'Bilateral front transition: R37 / R38 same cameras',fill='black',font=font)
for row,ht in enumerate((120.,130.,145.)):
    for side_index,side in enumerate(('l','r')):
        for tag_index,tag in enumerate(('r37','r38')):
            image=Image.open(Path('/tmp/r38-front')/tag/f'{side}_front_{ht}.png').convert('RGBA')
            base=Image.new('RGBA',image.size,(28,28,30,255));base.alpha_composite(image)
            x,y=(side_index*2+tag_index)*600,64+row*640
            draw.text((x+10,y+4),f'{tag.upper()} {side} front {ht:g} deg',fill='black',font=font)
            front.paste(base.convert('RGB').resize((600,600)),(x,y+36))
front.save(OUT/'r37_r38_front_closeups.jpg',quality=94)
doc=f"""# ORIGINAL_v1 R38: the two remaining owner marks

**{report['status']}. Owner visual approval pending.**

Parent: immutable R37. Owner feedback 17 October: remaining joint-like lobe at (77%,69%) in three-quarter and excess rear bow at (73%,32%), on the exact135.625-degree comparison. Private reference image is excluded.

R38 only changes existing S7 skin coordinates at110/120/130/145. The rear target blends the broad contour toward its anchored chord, capped at12mm; the posterior target blends a local quadratic surface capped at6mm. The front sentinel has a broad spatial protection fade. The raw target is scaled to45%, followed by coupled material-coordinate redistribution over both41-sample press paths. A local target attenuation safety stage then discards unsafe portions. A smooth0.75mm posterior blend through the lower junction preserves three-quarter continuity, followed by another safety pass. Final safety requires no extra stretch/collapse counts and no normal reversals versus the parent same-pose surface; it does not establish anatomical correctness. Endkeys156/166 remain exactly R37/R34. The original native guards are unchanged and must leave those endkeys untouched.

The local response trial increases the short rear corner peaks from R37 left9.0535/right10.0042 to approximately11.37/11.73degrees, while reducing the broader bow. This tradeoff must be checked again on the final saved model and visually reviewed. Both remain below the unchanged12.5degree goal.

All prior R34 front tests and R37 contour tests run unchanged. Two additional owner-mark goals require rear broad-bow RMS<7.5mm (R37 left9.5747/right9.6932mm) and local posterior quadratic-fit residual p95<2mm (R37 left2.7149/right2.7158mm), both at135.625degrees. These are local shape diagnostics, not substitutes for the owner's visual review. R37 reproduces all four expected failing side-goals before the change. A synthetic reversed triangle reproduced the unsigned-area blind spot and the new signed-area check passes after the correction. No prior test/tolerance was weakened or deleted.

Native checks: {json.dumps(report['acceptance_checks'])}. Regressions retained: {len(report['regressions'])}. Full measurements and logs are alongside the model. Numerical comparisons include R34 and R37 at every actual measured frame of the full press and13 benchmarks; every increase rejects the candidate.

Comparison files show R37/R38 at identical cameras and press times. The video is shoulder_press_r38_three_views.mp4. Bilateral native closeups include the exact135.625degree owner frame and front120/130/145degrees. The full-press top remains R37/R34; existing top stretch and crushed shoulder-press benchmark triangles are not claimed resolved by this local change. Broader fit to the old R33 target may worsen and is fully retained in r38_review.json.

Frozen canonical skeleton, basis, weights, topology and every non-S7 coordinate including HGPT_SHOULDER remain identical to R33/R34/R37. Workflow original-review-r38.yml uses pinned Blender5.2.1. No production assets, merge or force push.
"""
(ROOT/'docs/CODEX_ORIGINAL_V1_REVIEW_CANDIDATE_R38_20261017.md').write_text(doc)
print('R38_REVIEW_FINAL',json.dumps(report),flush=True)
