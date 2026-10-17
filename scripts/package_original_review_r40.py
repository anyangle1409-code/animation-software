"""Package measured R40 evidence and review visuals; never soften failed checks."""
import json
import re
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r40_20261017"
def read(name):
    return json.loads((OUT / name).read_text())
a, b = read("r34_press.json"), read("r40_press.json")
ba, bb = read("r34_benchmarks.json"), read("r40_benchmarks.json")
from original_review_r35_reports import validate_samples
validate_samples(a,b,ba,bb)
invariants = read("identity.json")
regressions = []
for x, y in zip(a["press"], b["press"]):
    for metric in ("pairs", "collapse", "stretch"):
        if y[metric] > x[metric]:
            regressions.append({"path": "press", "t": x["t"], "metric": metric, "r34": x[metric], "r40": y[metric]})
for name in ba["benchmarks"]:
    for x, y in zip(ba["benchmarks"][name]["frames"], bb["benchmarks"][name]["frames"]):
        for metric in ("self_intersecting_pairs", "collapse_lt_0_1", "stretch_gt_2"):
            if y[metric] > x[metric]:
                regressions.append({"path": name, "t": x["t"], "metric": metric, "r34": x[metric], "r40": y[metric]})
# The parent is an additional baseline; R34 comparisons above remain intact.
parent=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r38_20261017'
pa=json.loads((parent/'r38_press.json').read_text());pb=json.loads((parent/'r38_benchmarks.json').read_text())
validate_samples(pa,b,pb,bb)
for x,y in zip(pa['press'],b['press']):
    for metric in ('pairs','collapse','stretch'):
        if y[metric]>x[metric]:regressions.append({'baseline':'R38','path':'press','t':x['t'],'metric':metric,'r38':x[metric],'r40':y[metric]})
for name in pb['benchmarks']:
    for x,y in zip(pb['benchmarks'][name]['frames'],bb['benchmarks'][name]['frames']):
        for metric in ('self_intersecting_pairs','collapse_lt_0_1','stretch_gt_2'):
            if y[metric]>x[metric]:regressions.append({'baseline':'R38','path':name,'t':x['t'],'metric':metric,'r38':x[metric],'r40':y[metric]})
test_log = (OUT / "front_test.txt").read_text()
from original_review_candidate_checks import acceptance
front_exit = int((OUT / "front_test_exit.txt").read_text().strip())
guard_report = read("r40_guard_recheck.json")
gate = acceptance(invariants, front_exit, test_log, b["press"], regressions, guard_report)
front_pass = gate["checks"]["front_test_process"]
accepted_for_review = gate["passed"]
status = "NUMERIC_CHECKS_PASSED_AWAITING_VISUAL_REVIEW" if accepted_for_review else "REJECTED_NUMERIC_CHECKS"
report = {"candidate": "R40", "approved": False, "status": status,
          "front_test_passed": front_pass, "front_test_exit": front_exit, "acceptance_checks": gate["checks"],
          "guard_violations": guard_report["violations"], "invariants": invariants,
          "regressions": regressions, "r34_fit": a["fit"], "r40_fit": b["fit"]}
from original_review_r40_checks import front_comparison
report['front_comparison_vs_r38']=front_comparison((parent/'front_test.txt').read_text(),test_log)
report['r38_fit']=pa['fit']
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
orientation=read('r40_orientation.json')
orientation_pass=orientation.get('sample_count')==82 and len(orientation.get('samples',[]))==82 and orientation.get('passed') is True and all(x['normal_rotations_over_90_degrees']==0 for x in orientation['samples'])
report['acceptance_checks']['final_native_orientation']=orientation_pass
if not orientation_pass:report['status']='REJECTED_NUMERIC_CHECKS'
line_exit=int((OUT/'line_test_exit.txt').read_text())
line_log=(OUT/'line_test.txt').read_text()
line_pass=line_exit==0 and bool(re.search(r'^OK$',line_log,re.M))
report['acceptance_checks']['approved_straight_line']=line_pass
if not line_pass:report['status']='REJECTED_NUMERIC_CHECKS'
for label in ('front_smoothness','r39_line_unchanged'):
    code=int((OUT/f'{label}_test_exit.txt').read_text())
    log=(OUT/f'{label}_test.txt').read_text()
    passed=code==0 and bool(re.search(r'^OK$',log,re.M))
    report['acceptance_checks'][label]=passed
    if not passed:report['status']='REJECTED_NUMERIC_CHECKS'
# This new requirement only tightens the existing acceptance gate.
status=report['status']
had_visuals = (OUT / "r38_r40_same_angle_comparison.jpg").exists() and (OUT / "shoulder_press_r40_three_views.mp4").exists()
previous_status = read("r40_review.json").get("status") if (OUT / "r40_review.json").exists() else None
(OUT / "r40_review.json").write_text(json.dumps(report, indent=2) + "\n")
if not had_visuals:
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font = ImageFont.truetype(font_path, 18)
    small = ImageFont.truetype(font_path, 14)
    bg = (28, 28, 30)
    views = ("back", "front", "three_quarter")
    def frame(tag, n, view):
        im = Image.open(f"/tmp/r40-frames/{tag}/f{n:03d}_{view}.png").convert("RGBA")
        base = Image.new("RGBA", im.size, bg + (255,))
        base.alpha_composite(im)
        return base.convert("RGB")
    numbers = (20, 24, 28, 32)
    sheet = Image.new("RGB", (6 * 256, len(numbers) * 294 + 64), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 8), "R38 / R40 - same press times and cameras - REVIEW ONLY", fill="black", font=font)
    draw.text((12, 34), status, fill="black", font=small)
    for row, n in enumerate(numbers):
        for v, view in enumerate(views):
            for k, tag in enumerate(("r38", "r40")):
                x, y = (2 * v + k) * 256, 64 + row * 294
                draw.text((x + 4, y + 2), f"{tag.upper()} {view.replace('_', ' ')} {b['press'][n]['ht']:.1f} deg",
                          fill="black", font=small)
                sheet.paste(frame(tag, n, view).resize((256, 256)), (x, y + 30))
    sheet.save(OUT / "r38_r40_same_angle_comparison.jpg", quality=92)
    video = Path("/tmp/r40-video")
    video.mkdir(exist_ok=True)
    sequence = [0] * 8 + list(range(41)) + [40] * 8 + list(range(39, 0, -1))
    for i, n in enumerate(sequence):
        image = Image.new("RGB", (1536, 576), bg)
        d = ImageDraw.Draw(image)
        for k, view in enumerate(views):
            image.paste(frame("r40", n, view), (k * 512, 0))
            d.text((k * 512 + 12, 10), view.replace("_", " "), fill="white", font=font)
        d.text((12, 520), f"R40 REVIEW ONLY | elevation {b['press'][n]['ht']:.1f} deg | t={n/40:.3f}",
               fill="white", font=font)
        d.text((12, 548), status, fill=(255, 210, 140), font=small)
        image.save(video / f"f{i:04d}.png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", str(video / "f%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-movflags", "+faststart",
                    str(OUT / "shoulder_press_r40_three_views.mp4")], check=True)
elif previous_status != status:
    # Re-label saved review media after stricter reporting checks; preserve the
    # already-rendered geometry instead of spending another Blender render.
    image = Image.open(OUT / "r38_r40_same_angle_comparison.jpg").convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, image.width, 64), fill="white")
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    draw.text((12, 8), "R38 / R40 - same press times and cameras - REVIEW ONLY", fill="black",
              font=ImageFont.truetype(font_path, 18))
    draw.text((12, 34), status, fill="black", font=ImageFont.truetype(font_path, 14))
    image.save(OUT / "r38_r40_same_angle_comparison.jpg", quality=92)
    original_video = OUT / "shoulder_press_r40_three_views.mp4"
    relabeled = Path("/tmp/r40-relabeled.mp4")
    vf = ("drawbox=x=0:y=544:w=1536:h=32:color=0x1c1c1e:t=fill,"
          f"drawtext=fontfile={font_path}:text='{status}':x=12:y=548:fontsize=14:fontcolor=0xffd28c")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(original_video), "-vf", vf,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-movflags", "+faststart",
                    str(relabeled)], check=True)
    original_video.write_bytes(relabeled.read_bytes())

font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
closeups=Path('/tmp/r40-junction')
for side in ('l','r'):
    sheet=Image.new('RGB',(2400,5*640+64),'white');draw=ImageDraw.Draw(sheet)
    draw.text((12,10),f'Arm-to-side junction ({side}): R38 / R40 same cameras - REVIEW ONLY',fill='black',font=font)
    for row,ht in enumerate((120.,130.,135.625,145.,156.)):
        for view_index,view in enumerate(('back','three_quarter')):
            for tag_index,tag in enumerate(('r38','r40')):
                image=Image.open(closeups/tag/f'{side}_{view}_{ht}.png').convert('RGBA')
                base=Image.new('RGBA',image.size,(28,28,30,255));base.alpha_composite(image)
                x,y=(view_index*2+tag_index)*600,64+row*640
                draw.text((x+10,y+4),f'{tag.upper()} {ht:g} deg {view}',fill='black',font=font)
                sheet.paste(base.convert('RGB').resize((600,600)),(x,y+36))
    sheet.save(OUT/f'r38_r40_junction_{side}_closeups.jpg',quality=94)
front=Image.new('RGB',(2400,3*640+64),'white');draw=ImageDraw.Draw(front)
draw.text((12,10),'Bilateral front transition: R38 / R40 same cameras',fill='black',font=font)
for row,ht in enumerate((120.,130.,145.)):
    for side_index,side in enumerate(('l','r')):
        for tag_index,tag in enumerate(('r38','r40')):
            image=Image.open(Path('/tmp/r40-front')/tag/f'{side}_front_{ht}.png').convert('RGBA')
            base=Image.new('RGBA',image.size,(28,28,30,255));base.alpha_composite(image)
            x,y=(side_index*2+tag_index)*600,64+row*640
            draw.text((x+10,y+4),f'{tag.upper()} {side} front {ht:g} deg',fill='black',font=font)
            front.paste(base.convert('RGB').resize((600,600)),(x,y+36))
front.save(OUT/'r38_r40_front_closeups.jpg',quality=94)
doc=f"""# ORIGINAL_v1 R40: approved straight arm-to-body line

**{report['status']}. Owner visual review pending.**

Owner approval:17October cyan straight guide continuing the upper-arm outline into the body without the inward bend. ImmutableR38 parent. The new test holds the final saved silhouette within2mm of the fixedR38 arm-edge line at stations0..160mm from the shoulder and prevents an inward bodyjoin deficit>2mm at-140..0mm. R38 reproduces four expected bilateral failures,17.5mm nearshoulder and up to26.4mm towardbody. This author-approved contour goal is not an anatomical/clinical validation.

Only S7 coordinates at110/120/130/136/145degrees are authored. The new136control exactly interpolatesR38(.6key130+.4key145) before correction; native owner-frame baseline preservation<0.01mm is required. Raw target continues the humerus-aligned skin edge into the torso, with35mm cap and a localized protectedfront taper8..26mm. Coupled material-area/orientation redistribution uses82native poses. Outer-line normal components are fixed; final safety can cut back tangential changes without erasing the line. Endkeys156/166 stay identicalR38/R34 or no model is saved. The original Blender guards are unchanged.

Front changes versusR38:{json.dumps(report['front_comparison_vs_r38'])}. Whole-surface fit to the oldR33target is retained forR34/R38/R40 in the report.

Acceptance checks:{json.dumps(report['acceptance_checks'])}. Regressions againstR34/R38:{len(report['regressions'])}. All original front, contour, R38mark, guard, strictlockoutvolume, preservation and final82pose orientation checks run unchanged. No test was weakened or deleted. Canonical skeleton, basis, topology, weights and every non-S7 coordinate includingHGPT_SHOULDER remain identical. Owner photos are excluded. Counts are compared at all41pressframes and actualframes of13benchmarks. Any increase or failed new line goal rejects numerical status.

Evidence lives in codex_review_r40_20261017: matchedR38/R40 rear/front/threequarter press images, exact135.625bilateral closeups, shoulder_press_r40_three_views.mp4, full JSON metrics and test logs. The new line is checked on the guarded saved model, not just the target. Topstretch and two crushed benchmarktriangles remain open unless actual reports demonstrate improvement. All regressions and oldR33 target-fit errors are retained in r40_review.json; inspect the renders even if numerical checks pass.

Reproduction:.github/workflows/original-review-r40.yml with pinnedBlender5.2.1 exports native response, solves, builds the isolated candidate, measures/tests in fresh processes and renders/packages both versions. No production assets, merge or force push. See docs/superpowers/plans/2026-10-17-r40-approved-arm-line.md for the execution ledger.
"""
(ROOT/'docs/CODEX_ORIGINAL_V1_REVIEW_CANDIDATE_R40_20261017.md').write_text(doc)
print('R40_REVIEW_FINAL',json.dumps(report),flush=True)
