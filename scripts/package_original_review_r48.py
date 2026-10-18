"""Package native R48 shape-study evidence. No image retouching or model save."""
from pathlib import Path
import json,subprocess,shutil
from PIL import Image,ImageDraw,ImageFont
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
tmp=Path('/tmp/r48-response');now=Path('/tmp/r48-study/R48')
previous=Path('/tmp/r47-previous/tmp/r47-study/R47')
out=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r48_study_20261018'
if out.exists():raise FileExistsError('R48 study folder is immutable')
out.mkdir(parents=True)
native=json.loads((tmp/'native_final.json').read_text())
bench=json.loads((tmp/'benchmarks.json').read_text())
author=json.loads((tmp/'solved.npz.json').read_text())
identity=json.loads(Path('/tmp/r48-study/protected_identity.json').read_text())
tests={p.name:int(p.read_text().strip()) for p in tmp.glob('*_test_exit.txt')}
report=dict(candidate='R48',status='UNSAVED_SHAPE_STUDY_NOT_ACCEPTED',approved=False,model_saved=False,
 native=native,benchmark_passed=bench['passed'],benchmark_regressions=bench['regressions'],
 test_exit_codes=tests,protected_identity=identity,fit=author,
 owner_scope_approved='2026-10-18 19:05 Europe/London',owner_r47_outline_approved=True,
 note='R48 retains exactly the approved R47 skin scope and fits the actual R47 outline with joint-pose safety constraints. Historical outward-fill and proximal-arm line tests remain unchanged; all outcomes are retained. This study cannot be promoted or saved as an accepted model.')
(out/'r48_review.json').write_text(json.dumps(report,indent=2)+'\n')
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
draw.text((10,8),'R47 / R48 — full outline at135.625 degrees',font=font,fill='black')
for row,view in enumerate(('back','three_quarter')):
 for col,(name,folder) in enumerate((('R47',previous),('R48',now))):
  x=col*512;y=48+row*544
  draw.text((x+10,y),name+' '+view.replace('_',' '),font=font,fill='black')
  canvas.paste(picture(folder/f'f025_{view}.png'),(x,y+28))
draw.text((10,1130),'Actual Blender5.2.1 geometry. R48 unsaved shape study; not accepted.',font=small,fill='black')
canvas.save(out/'R47_R48_full_outline.jpg',quality=95)
for side in ('l','r'):
 canvas=Image.new('RGB',(1280,1430),'white');draw=ImageDraw.Draw(canvas)
 draw.text((12,8),'R47 / R48 — exact135.625-degree shoulder views',font=font,fill='black')
 for row,view in enumerate(('back','three_quarter')):
  for col,(name,folder) in enumerate((('R47',previous),('R48',now))):
   x=col*640;y=52+row*664;draw.text((x+12,y),name+' '+view.replace('_',' '),font=font,fill='black')
   canvas.paste(picture(folder/f'{side}_{view}_135.625.png'),(x,y+28))
 draw.text((12,1405),'R48 UNSAVED SHAPE STUDY — all failed checks retained; owner review pending',font=small,fill='black')
 canvas.save(out/f'R47_R48_marked_{side}.jpg',quality=95)
sequence=[0]*8+list(range(41))+[40]*8+list(range(39,0,-1))
for comparison in (False,True):
 frames=Path('/tmp/r48-video-compare' if comparison else '/tmp/r48-video');frames.mkdir(exist_ok=True)
 for index,i in enumerate(sequence):
  canvas=Image.new('RGB',(1024,1100 if comparison else 588),(27,27,27));draw=ImageDraw.Draw(canvas)
  draw.text((12,8),'R47 / R48 matched press' if comparison else 'R48 full press — shape study',font=font,fill='white')
  for row,view in enumerate(('back','three_quarter')):
   if comparison:
    for col,(name,folder) in enumerate((('R47',previous),('R48',now))):
     x=col*512;y=48+row*524;canvas.paste(picture(folder/f'f{i:03d}_{view}.png'),(x,y))
     draw.text((x+10,y+8),name+' '+view.replace('_',' '),font=small,fill='white')
   else:canvas.paste(picture(now/f'f{i:03d}_{view}.png'),(row*512,48))
  draw.text((12,canvas.height-24),f'R48 STUDY — NOT ACCEPTED | t={i/40:.3f}',font=small,fill='white')
  canvas.save(frames/f'{index:03d}.jpg',quality=94)
 name='R47_R48_press_comparison.mp4' if comparison else 'shoulder_press_r48.mp4'
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','12','-i',str(frames/'%03d.jpg'),'-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(out/name)],check=True)
text=f"""# R48 joint-pose surface repair study

Status: UNSAVED_SHAPE_STUDY_NOT_ACCEPTED. Model saved: false.

The owner confirmed R47's actual overall outline on 18 October 2026: “Yes that looks good.” This approves the outline only. R47 remained rejected for folds, intersections and motion regressions.

R48 fits the exact native R47 marked-pose outline from the rear and three-quarter views, in the exact authorized R47 material domain. It starts with the safe immutable R41 zero increment and accepts fitting steps only while the existing affine area/orientation, known-contact, front, posterior crease, motion and source/dense displacement gates remain satisfied. Actual native contact detection and all13 benchmarks still run independently. The fitting time is bounded; a retained partial fit is not a completed shape correction.

Every original response array, including the old R42 profile target and the full posterior coverage mask, is preserved byte-for-byte. New fields separately identify the R48 target and editable coordinates. Three preparation tests pass after detecting the discarded preparation's overwritten target. The new marked-surface test reproduced R47's17 reversed triangles; the new outline test requires the actual R47 outline within1mm. No old assertion, threshold or test is changed or deleted.

All83 native responses passed: {native['passed']}; new contact records: {len(native['contacts'])}.
Back acceleration excess: {native['back_motion_excess_mm']:.6f}mm; unchanged limit0.5mm.
Posterior crease excess: {native['posterior_crease_excess_degrees']:.6f}degrees; unchanged limit2degrees.
13 benchmarks passed: {bench['passed']}; regression records: {len(bench['regressions'])}.
Test exit codes (zero passes): {json.dumps(tests,sort_keys=True)}.
Protected identity: {json.dumps(identity,sort_keys=True)}.

The historical outward-fill and proximal-arm line tests are retained and their failures are reported. They remain historical diagnostics following the owner's explicitly changed inward-outline requirement. R48's1mm actual-outline test is separate. Numerical success does not constitute owner visual approval. This pipeline has no model-save step and cannot promote a candidate to production.

Review R47_R48_full_outline.jpg, R47_R48_marked_l/r.jpg, R47_R48_press_comparison.mp4 and shoulder_press_r48.mp4. These are actual native Blender5.2.1 geometry with identical poses/cameras/lighting. Reference photos and traced outlines remain outside the repository.
"""
(out/'README.md').write_text(text)
(ROOT/'docs/CODEX_ORIGINAL_V1_REVIEW_CANDIDATE_R48_20261018.md').write_text(text)
print('R48_SURFACE_STUDY_PACKAGED',native['passed'],bench['passed'],tests,flush=True)
