"""Package native R49 shape-study evidence. No image retouching or model save."""
from pathlib import Path
import json,subprocess,shutil,re
from PIL import Image,ImageDraw,ImageFont
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
tmp=Path('/tmp/r49-response');now=Path('/tmp/r49-study/R49')
previous=Path('/tmp/r47-previous/tmp/r47-study/R47')
out=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r49_study_20261018'
if out.exists():raise FileExistsError('R49 study folder is immutable')
out.mkdir(parents=True)
native=json.loads((tmp/'native_final.json').read_text())
bench=json.loads((tmp/'benchmarks.json').read_text())
author=json.loads((tmp/'solved.npz.json').read_text())
identity=json.loads(Path('/tmp/r49-study/protected_identity.json').read_text())
tests={p.name:int(p.read_text().strip()) for p in tmp.glob('*_test_exit.txt')}
outline_log=(tmp/'r48_approved_outline_test.txt').read_text()
outline_match=re.search(r'R48_APPROVED_OUTLINE_MAX_ERROR_MM\s+([0-9.eE+-]+)',outline_log)
outline_error=float(outline_match.group(1)) if outline_match else None
report=dict(candidate='R49',status='UNSAVED_SHAPE_STUDY_NOT_ACCEPTED',approved=False,model_saved=False,
 native=native,benchmark_passed=bench['passed'],benchmark_regressions=bench['regressions'],
 test_exit_codes=tests,protected_identity=identity,fit=author,
 approved_outline_error_mm=outline_error,approved_outline_guard_mm=1.,
 marked_native_reversed_normals=native['samples'][25]['normal_rotations_over_90_degrees'],
 owner_scope_approved='2026-10-18 19:05 Europe/London',owner_r47_outline_approved=True,
 note='R49 retains exactly the approved R47 skin scope and fits the actual R47 outline with joint-pose safety constraints. Historical outward-fill and proximal-arm line tests remain unchanged; all outcomes are retained. This study cannot be promoted or saved as an accepted model.')
(out/'r49_review.json').write_text(json.dumps(report,indent=2)+'\n')
for path in list(tmp.glob('*.json'))+list(tmp.glob('*test*.txt')):
 shutil.copy2(path,out/path.name)
shutil.copy2(tmp/'solved.npz',out/'solved.npz')
shutil.copy2(now/'native_probe.npz',out/'native_probe.npz')
shutil.copy2(now/'full_press_marked_points.npz',out/'full_press_marked_points.npz')
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
def picture(path):
 im=Image.open(path).convert('RGBA');bg=Image.new('RGBA',im.size,(27,27,27,255));bg.alpha_composite(im);return bg.convert('RGB')
canvas=Image.new('RGB',(1024,1152),'white');draw=ImageDraw.Draw(canvas)
draw.text((10,8),'R47 / R49 — full outline at135.625 degrees',font=font,fill='black')
for row,view in enumerate(('back','three_quarter')):
 for col,(name,folder) in enumerate((('R47',previous),('R49',now))):
  x=col*512;y=48+row*544
  draw.text((x+10,y),name+' '+view.replace('_',' '),font=font,fill='black')
  canvas.paste(picture(folder/f'f025_{view}.png'),(x,y+28))
draw.text((10,1130),'Actual Blender5.2.1 geometry. R49 unsaved shape study; not accepted.',font=small,fill='black')
canvas.save(out/'R47_R49_full_outline.jpg',quality=95)
for side in ('l','r'):
 canvas=Image.new('RGB',(1280,1430),'white');draw=ImageDraw.Draw(canvas)
 draw.text((12,8),'R47 / R49 — exact135.625-degree shoulder views',font=font,fill='black')
 for row,view in enumerate(('back','three_quarter')):
  for col,(name,folder) in enumerate((('R47',previous),('R49',now))):
   x=col*640;y=52+row*664;draw.text((x+12,y),name+' '+view.replace('_',' '),font=font,fill='black')
   canvas.paste(picture(folder/f'{side}_{view}_135.625.png'),(x,y+28))
 draw.text((12,1405),'R49 UNSAVED SHAPE STUDY — all failed checks retained; owner review pending',font=small,fill='black')
 canvas.save(out/f'R47_R49_marked_{side}.jpg',quality=95)
sequence=[0]*8+list(range(41))+[40]*8+list(range(39,0,-1))
for comparison in (False,True):
 frames=Path('/tmp/r49-video-compare' if comparison else '/tmp/r49-video');frames.mkdir(exist_ok=True)
 for index,i in enumerate(sequence):
  canvas=Image.new('RGB',(1024,1100 if comparison else 588),(27,27,27));draw=ImageDraw.Draw(canvas)
  draw.text((12,8),'R47 / R49 matched press' if comparison else 'R49 full press — shape study',font=font,fill='white')
  for row,view in enumerate(('back','three_quarter')):
   if comparison:
    for col,(name,folder) in enumerate((('R47',previous),('R49',now))):
     x=col*512;y=48+row*524;canvas.paste(picture(folder/f'f{i:03d}_{view}.png'),(x,y))
     draw.text((x+10,y+8),name+' '+view.replace('_',' '),font=small,fill='white')
   else:canvas.paste(picture(now/f'f{i:03d}_{view}.png'),(row*512,48))
  draw.text((12,canvas.height-24),f'R49 STUDY — NOT ACCEPTED | t={i/40:.3f}',font=small,fill='white')
  canvas.save(frames/f'{index:03d}.jpg',quality=94)
 name='R47_R49_press_comparison.mp4' if comparison else 'shoulder_press_r49.mp4'
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','12','-i',str(frames/'%03d.jpg'),'-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(out/name)],check=True)
text=f"""# R49 bounded-refinement surface repair study

Status: UNSAVED_SHAPE_STUDY_NOT_ACCEPTED. Model saved: false. Owner visual review pending.

The owner approved R47's actual overall outline, while its surface and motion remained rejected. R48 timed out before accepting a first step and produced no native media. Therefore R47 is the actual visual comparison for R49.

R49 retains the exact target, editable material domain, all parent response arrays and complete posterior coverage. It bounds predictive refinement, retains learned cone directions and restores the existing minimum-L1 proposal preference. All actual nonlinear gates and numerical safety limits remain identical to R48; a structural test checks this. No old test was edited or deleted. Read docs/CODEX_ORIGINAL_V1_R49_BUILD_NOTE_20261018.md for the reproduced bottleneck, failed probes and local preflight evidence.

The three-step local preflight accepted three steps in44.2seconds and improved actual outline error by1.723454mm, with motion excess0.452526mm and posterior-crease excess1.872746degrees. This was preliminary affine evidence; the shape was still unresolved. CI repeats the preflight before the main bounded fit.

Native83-response checks passed: {native['passed']}; new contact records: {len(native['contacts'])}.
Back motion excess: {native['back_motion_excess_mm']:.6f}mm against unchanged0.5mm.
Posterior crease excess: {native['posterior_crease_excess_degrees']:.6f}degrees against unchanged2degrees.
13 benchmarks passed: {bench['passed']}; regression records: {len(bench['regressions'])}.
Test exit codes (zero passes): {json.dumps(tests,sort_keys=True)}.
Actual marked-outline error against approved R47: {outline_error}mm; unchanged guard1mm.
Fit status and retained checkpoint: {json.dumps(json.loads((tmp/'fit_status.json').read_text()),sort_keys=True)}.
Protected identity: {json.dumps(identity,sort_keys=True)}.

The actual-R47 outline test retains its1mm guard. The five historical contour/front tests and full R47 scope test remain unchanged and their failures are retained. Numerical passes do not constitute visual approval, nor do they complete the shape request if the outline guard fails. No model-save step exists. Frozen skeleton, weights, Basis, topology,166, anchors, elbow/distal arm, HGPT_SHOULDER and non-S7 keys remain protected.

Review actual native R47_R49_full_outline.jpg, R47_R49_marked_l/r.jpg, R47_R49_press_comparison.mp4 and shoulder_press_r49.mp4. No private photo, trace or cosmetic correction enters these outputs.
"""
(out/'README.md').write_text(text)
(ROOT/'docs/CODEX_ORIGINAL_V1_REVIEW_CANDIDATE_R49_20261018.md').write_text(text)
print('R49_SURFACE_STUDY_PACKAGED',native['passed'],bench['passed'],tests,flush=True)
