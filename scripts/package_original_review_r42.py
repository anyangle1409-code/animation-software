"""Package measured R42 evidence and review visuals; never soften failed checks."""
import json
import re
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r42_20261017"
def read(name):
    return json.loads((OUT / name).read_text())
a, b = read("r34_press.json"), read("r42_press.json")
ba, bb = read("r34_benchmarks.json"), read("r42_benchmarks.json")
from original_review_r35_reports import validate_samples
validate_samples(a,b,ba,bb)
invariants = read("identity.json")
regressions = []
for x, y in zip(a["press"], b["press"]):
    for metric in ("pairs", "collapse", "stretch"):
        if y[metric] > x[metric]:
            regressions.append({"path": "press", "t": x["t"], "metric": metric, "r34": x[metric], "r42": y[metric]})
for name in ba["benchmarks"]:
    for x, y in zip(ba["benchmarks"][name]["frames"], bb["benchmarks"][name]["frames"]):
        for metric in ("self_intersecting_pairs", "collapse_lt_0_1", "stretch_gt_2"):
            if y[metric] > x[metric]:
                regressions.append({"path": name, "t": x["t"], "metric": metric, "r34": x[metric], "r42": y[metric]})
# The parent is an additional baseline; R34 comparisons above remain intact.
parent=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017'
pa=json.loads((parent/'r41_press.json').read_text());pb=json.loads((parent/'r41_benchmarks.json').read_text())
validate_samples(pa,b,pb,bb)
for x,y in zip(pa['press'],b['press']):
    for metric in ('pairs','collapse','stretch'):
        if y[metric]>x[metric]:regressions.append({'baseline':'R41','path':'press','t':x['t'],'metric':metric,'r41':x[metric],'r42':y[metric]})
for name in pb['benchmarks']:
    for x,y in zip(pb['benchmarks'][name]['frames'],bb['benchmarks'][name]['frames']):
        for metric in ('self_intersecting_pairs','collapse_lt_0_1','stretch_gt_2'):
            if y[metric]>x[metric]:regressions.append({'baseline':'R41','path':name,'t':x['t'],'metric':metric,'r41':x[metric],'r42':y[metric]})
test_log = (OUT / "front_test.txt").read_text()
from original_review_candidate_checks import acceptance
front_exit = int((OUT / "front_test_exit.txt").read_text().strip())
guard_report = read("r42_guard_recheck.json")
gate = acceptance(invariants, front_exit, test_log, b["press"], regressions, guard_report)
front_pass = gate["checks"]["front_test_process"]
accepted_for_review = gate["passed"]
status = "NUMERIC_CHECKS_PASSED_AWAITING_VISUAL_REVIEW" if accepted_for_review else "REJECTED_NUMERIC_CHECKS"
report = {"candidate": "R42", "approved": False, "status": status,
          "front_test_passed": front_pass, "front_test_exit": front_exit, "acceptance_checks": gate["checks"],
          "guard_violations": guard_report["violations"], "invariants": invariants,
          "regressions": regressions, "r34_fit": a["fit"], "r42_fit": b["fit"]}
from original_review_r41_checks import front_comparison
report['front_comparison_vs_r41']=front_comparison((parent/'front_test.txt').read_text(),test_log)
report['r41_fit']=pa['fit']
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
orientation=read('r42_orientation.json')
orientation_pass=orientation.get('area_safety_passed') is True and len(orientation.get('area_samples',[]))==83 and all(x['passed'] for x in orientation['area_samples']) and orientation.get('sample_count')==82 and len(orientation.get('samples',[]))==82 and orientation.get('passed') is True and all(x['normal_rotations_over_90_degrees']==0 for x in orientation['samples'])
report['acceptance_checks']['final_native_orientation']=orientation_pass
if not orientation_pass:report['status']='REJECTED_NUMERIC_CHECKS'
line_exit=int((OUT/'line_test_exit.txt').read_text())
line_log=(OUT/'line_test.txt').read_text()
line_pass=line_exit==0 and bool(re.search(r'^OK$',line_log,re.M))
report['acceptance_checks']['approved_straight_line']=line_pass
if not line_pass:report['status']='REJECTED_NUMERIC_CHECKS'
for label in ('front_smoothness','r39_line_unchanged','r40_front_unchanged','strain'):
    code=int((OUT/f'{label}_test_exit.txt').read_text())
    log=(OUT/f'{label}_test.txt').read_text()
    passed=code==0 and bool(re.search(r'^OK$',log,re.M))
    report['acceptance_checks'][label]=passed
    if not passed:report['status']='REJECTED_NUMERIC_CHECKS'
profile_exit=int((OUT/'profile_test_exit.txt').read_text())
profile_log=(OUT/'profile_test.txt').read_text()
profile_pass=profile_exit==0 and bool(re.search(r'^OK$',profile_log,re.M))
report['acceptance_checks']['confirmed_owner_junction']=profile_pass
if not profile_pass:report['status']='REJECTED_NUMERIC_CHECKS'
build=read('r42_build.json')
bounded=build.get('bounded_s7_update') is True and build.get('max_s7_update_mm',1e99)<=45. and build.get('sentinels_unchanged') is True and build.get('upper_arm_elbow_exact') is True and build.get('frozen_110_156_166_unchanged') is True
report['acceptance_checks']['bounded_s7_update']=bounded
if not bounded:report['status']='REJECTED_NUMERIC_CHECKS'
# Keep the earlier R38 baseline explicitly, in addition to R34 and immediate parent R41.
old=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r38_20261017'
oldp=json.loads((old/'r38_press.json').read_text());oldb=json.loads((old/'r38_benchmarks.json').read_text())
validate_samples(oldp,b,oldb,bb)
for x,y in zip(oldp['press'],b['press']):
    for metric in ('pairs','collapse','stretch'):
        if y[metric]>x[metric]:report['regressions'].append({'baseline':'R38','path':'press','t':x['t'],'metric':metric,'r38':x[metric],'r42':y[metric]})
for name in oldb['benchmarks']:
    for x,y in zip(oldb['benchmarks'][name]['frames'],bb['benchmarks'][name]['frames']):
        for metric in ('self_intersecting_pairs','collapse_lt_0_1','stretch_gt_2'):
            if y[metric]>x[metric]:report['regressions'].append({'baseline':'R38','path':name,'t':x['t'],'metric':metric,'r38':x[metric],'r42':y[metric]})
old40=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r40_20261017'
p40=json.loads((old40/'r40_press.json').read_text());b40=json.loads((old40/'r40_benchmarks.json').read_text())
validate_samples(p40,b,b40,bb)
for x,y in zip(p40['press'],b['press']):
    for metric in ('pairs','collapse','stretch'):
        if y[metric]>x[metric]:report['regressions'].append({'baseline':'R40','path':'press','t':x['t'],'metric':metric,'before':x[metric],'after':y[metric]})
for name in b40['benchmarks']:
    for x,y in zip(b40['benchmarks'][name]['frames'],bb['benchmarks'][name]['frames']):
        for metric in ('self_intersecting_pairs','collapse_lt_0_1','stretch_gt_2'):
            if y[metric]>x[metric]:report['regressions'].append({'baseline':'R40','path':name,'t':x['t'],'metric':metric,'before':x[metric],'after':y[metric]})
if report['regressions']:report['status']='REJECTED_NUMERIC_CHECKS'
# This new requirement only tightens the existing acceptance gate.
status=report['status']
had_visuals = (OUT / "r41_r42_same_angle_comparison.jpg").exists() and (OUT / "shoulder_press_r42_three_views.mp4").exists()
previous_status = read("r42_review.json").get("status") if (OUT / "r42_review.json").exists() else None
(OUT / "r42_review.json").write_text(json.dumps(report, indent=2) + "\n")
if not had_visuals:
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font = ImageFont.truetype(font_path, 18)
    small = ImageFont.truetype(font_path, 14)
    bg = (28, 28, 30)
    views = ("back", "front", "three_quarter")
    def frame(tag, n, view):
        im = Image.open(f"/tmp/r42-frames/{tag}/f{n:03d}_{view}.png").convert("RGBA")
        base = Image.new("RGBA", im.size, bg + (255,))
        base.alpha_composite(im)
        return base.convert("RGB")
    numbers = (20, 24, 28, 32)
    sheet = Image.new("RGB", (6 * 256, len(numbers) * 294 + 64), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 8), "R41 / R42 - same press times and cameras - REVIEW ONLY", fill="black", font=font)
    draw.text((12, 34), status, fill="black", font=small)
    for row, n in enumerate(numbers):
        for v, view in enumerate(views):
            for k, tag in enumerate(("r41", "r42")):
                x, y = (2 * v + k) * 256, 64 + row * 294
                draw.text((x + 4, y + 2), f"{tag.upper()} {view.replace('_', ' ')} {b['press'][n]['ht']:.1f} deg",
                          fill="black", font=small)
                sheet.paste(frame(tag, n, view).resize((256, 256)), (x, y + 30))
    sheet.save(OUT / "r41_r42_same_angle_comparison.jpg", quality=92)
    video = Path("/tmp/r42-video")
    video.mkdir(exist_ok=True)
    sequence = [0] * 8 + list(range(41)) + [40] * 8 + list(range(39, 0, -1))
    for i, n in enumerate(sequence):
        image = Image.new("RGB", (1536, 576), bg)
        d = ImageDraw.Draw(image)
        for k, view in enumerate(views):
            image.paste(frame("r42", n, view), (k * 512, 0))
            d.text((k * 512 + 12, 10), view.replace("_", " "), fill="white", font=font)
        d.text((12, 520), f"R42 REVIEW ONLY | elevation {b['press'][n]['ht']:.1f} deg | t={n/40:.3f}",
               fill="white", font=font)
        d.text((12, 548), status, fill=(255, 210, 140), font=small)
        image.save(video / f"f{i:04d}.png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", str(video / "f%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-movflags", "+faststart",
                    str(OUT / "shoulder_press_r42_three_views.mp4")], check=True)
elif previous_status != status:
    # Re-label saved review media after stricter reporting checks; preserve the
    # already-rendered geometry instead of spending another Blender render.
    image = Image.open(OUT / "r41_r42_same_angle_comparison.jpg").convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, image.width, 64), fill="white")
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    draw.text((12, 8), "R41 / R42 - same press times and cameras - REVIEW ONLY", fill="black",
              font=ImageFont.truetype(font_path, 18))
    draw.text((12, 34), status, fill="black", font=ImageFont.truetype(font_path, 14))
    image.save(OUT / "r41_r42_same_angle_comparison.jpg", quality=92)
    original_video = OUT / "shoulder_press_r42_three_views.mp4"
    relabeled = Path("/tmp/r42-relabeled.mp4")
    vf = ("drawbox=x=0:y=544:w=1536:h=32:color=0x1c1c1e:t=fill,"
          f"drawtext=fontfile={font_path}:text='{status}':x=12:y=548:fontsize=14:fontcolor=0xffd28c")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(original_video), "-vf", vf,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-movflags", "+faststart",
                    str(relabeled)], check=True)
    original_video.write_bytes(relabeled.read_bytes())

font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
closeups=Path('/tmp/r42-junction')
for side in ('l','r'):
    sheet=Image.new('RGB',(2400,5*640+64),'white');draw=ImageDraw.Draw(sheet)
    draw.text((12,10),f'Arm-to-side junction ({side}): R41 / R42 same cameras - REVIEW ONLY',fill='black',font=font)
    for row,ht in enumerate((120.,130.,135.625,145.,156.)):
        for view_index,view in enumerate(('back','three_quarter')):
            for tag_index,tag in enumerate(('r41','r42')):
                image=Image.open(closeups/tag/f'{side}_{view}_{ht}.png').convert('RGBA')
                base=Image.new('RGBA',image.size,(28,28,30,255));base.alpha_composite(image)
                x,y=(view_index*2+tag_index)*600,64+row*640
                draw.text((x+10,y+4),f'{tag.upper()} {ht:g} deg {view}',fill='black',font=font)
                sheet.paste(base.convert('RGB').resize((600,600)),(x,y+36))
    sheet.save(OUT/f'r41_r42_junction_{side}_closeups.jpg',quality=94)
front=Image.new('RGB',(2400,3*640+64),'white');draw=ImageDraw.Draw(front)
draw.text((12,10),'Bilateral front transition: R41 / R42 same cameras',fill='black',font=font)
for row,ht in enumerate((120.,130.,145.)):
    for side_index,side in enumerate(('l','r')):
        for tag_index,tag in enumerate(('r41','r42')):
            image=Image.open(Path('/tmp/r42-front')/tag/f'{side}_front_{ht}.png').convert('RGBA')
            base=Image.new('RGBA',image.size,(28,28,30,255));base.alpha_composite(image)
            x,y=(side_index*2+tag_index)*600,64+row*640
            draw.text((x+10,y+4),f'{tag.upper()} {side} front {ht:g} deg',fill='black',font=font)
            front.paste(base.convert('RGB').resize((600,600)),(x,y+36))
front.save(OUT/'r41_r42_front_closeups.jpg',quality=94)
doc=f"""# R42: owner-confirmed arm-to-body transition

**{report['status']}. Owner visual review pending.** Parent: immutable R41.

The confirmed contour turns from the newer arm into the torso earlier, without
an extra joint. Only body-side increments of S7 controls120/130/136/145 are
editable. Upper-arm/elbow material coordinates, controls110/156/166, front
anchors, Basis, topology, weights, canonical bones, V-series assets and all
non-S7 keys including HGPT_SHOULDER remain exact. Private references are absent.

R42 has a new45mm final material-vector bound for the confirmed contour
restoration. R41's0.75mm strain-only limit and its tests remain unchanged in R41.
Trial1 broad contour locks stalled near220 marked stretched triangles. Trial2
narrow locks with5mm residual reached187(vsR41:19), rejected before saving.
Trial3 permits tangential skin redistribution inside the same45mm final bound.
No older numerical threshold was loosened. All13 movement benchmarks and the
83 final native area/orientation samples remain gates, alongside R34/R38/R40/R41
counts and the unchanged front, contour and arm-line tests. R41 reproduces eight
failures of the new confirmed-junction shape test before implementation.

Acceptance: {json.dumps(report['acceptance_checks'])}.
Regressions: {len(report['regressions'])}. Front comparison vsR41:
{json.dumps(report['front_comparison_vs_r41'])}. Old target-fit errors and all
failed logs remain in measured evidence. Numerical success is not visual approval.

Reproduction: `.github/workflows/original-review-r42-full.yml`.
The candidate folder contains the immutable blend, tests, JSON, matched R41/R42
images and `shoulder_press_r42_three_views.mp4`. No main merge or force push.
"""
(ROOT/'docs/CODEX_ORIGINAL_V1_REVIEW_CANDIDATE_R42_20261017.md').write_text(doc)
print('R42_REVIEW_FINAL',json.dumps(report),flush=True)

