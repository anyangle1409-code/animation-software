"""Package native R47 shape-study evidence. No image retouching or model save."""
from pathlib import Path
import json,subprocess,shutil
from PIL import Image,ImageDraw,ImageFont
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
tmp=Path('/tmp/r47-response');now=Path('/tmp/r47-study/R47')
previous=Path('/tmp/r46-previous/tmp/r46-study/R46')
out=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r47_study_20261018'
if out.exists():raise FileExistsError('R47 study folder is immutable')
out.mkdir(parents=True)
native=json.loads((tmp/'native_final.json').read_text())
bench=json.loads((tmp/'benchmarks.json').read_text())
author=json.loads((tmp/'solved.npz.json').read_text())
identity=json.loads(Path('/tmp/r47-study/protected_identity.json').read_text())
tests={p.name:int(p.read_text().strip()) for p in tmp.glob('*_test_exit.txt')}
report=dict(candidate='R47',status='UNSAVED_SHAPE_STUDY_NOT_ACCEPTED',approved=False,model_saved=False,
 native=native,benchmark_passed=bench['passed'],benchmark_regressions=bench['regressions'],
 test_exit_codes=tests,protected_identity=identity,author=author,
 owner_scope_approved='2026-10-18 19:05 Europe/London',
 note='Owner-approved skin-scope change. Historical outward-fill and proximal-arm line tests remain unchanged; all outcomes are retained. This study cannot be promoted or saved as an accepted model.')
(out/'r47_review.json').write_text(json.dumps(report,indent=2)+'\n')
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
draw.text((10,8),'R46 / R47 — full outline at135.625 degrees',font=font,fill='black')
for row,view in enumerate(('back','three_quarter')):
 for col,(name,folder) in enumerate((('R46',previous),('R47',now))):
  x=col*512;y=48+row*544
  draw.text((x+10,y),name+' '+view.replace('_',' '),font=font,fill='black')
  canvas.paste(picture(folder/f'f025_{view}.png'),(x,y+28))
draw.text((10,1130),'Actual Blender5.2.1 geometry. R47 unsaved shape study; not accepted.',font=small,fill='black')
canvas.save(out/'R46_R47_full_outline.jpg',quality=95)
for side in ('l','r'):
 canvas=Image.new('RGB',(1280,1430),'white');draw=ImageDraw.Draw(canvas)
 draw.text((12,8),'R46 / R47 — exact135.625-degree shoulder views',font=font,fill='black')
 for row,view in enumerate(('back','three_quarter')):
  for col,(name,folder) in enumerate((('R46',previous),('R47',now))):
   x=col*640;y=52+row*664;draw.text((x+12,y),name+' '+view.replace('_',' '),font=font,fill='black')
   canvas.paste(picture(folder/f'{side}_{view}_135.625.png'),(x,y+28))
 draw.text((12,1405),'R47 UNSAVED SHAPE STUDY — all failed checks retained; owner review pending',font=small,fill='black')
 canvas.save(out/f'R46_R47_marked_{side}.jpg',quality=95)
sequence=[0]*8+list(range(41))+[40]*8+list(range(39,0,-1))
for comparison in (False,True):
 frames=Path('/tmp/r47-video-compare' if comparison else '/tmp/r47-video');frames.mkdir(exist_ok=True)
 for index,i in enumerate(sequence):
  canvas=Image.new('RGB',(1024,1100 if comparison else 588),(27,27,27));draw=ImageDraw.Draw(canvas)
  draw.text((12,8),'R46 / R47 matched press' if comparison else 'R47 full press — shape study',font=font,fill='white')
  for row,view in enumerate(('back','three_quarter')):
   if comparison:
    for col,(name,folder) in enumerate((('R46',previous),('R47',now))):
     x=col*512;y=48+row*524;canvas.paste(picture(folder/f'f{i:03d}_{view}.png'),(x,y))
     draw.text((x+10,y+8),name+' '+view.replace('_',' '),font=small,fill='white')
   else:canvas.paste(picture(now/f'f{i:03d}_{view}.png'),(row*512,48))
  draw.text((12,canvas.height-24),f'R47 STUDY — NOT ACCEPTED | t={i/40:.3f}',font=small,fill='white')
  canvas.save(frames/f'{index:03d}.jpg',quality=94)
 name='R46_R47_press_comparison.mp4' if comparison else 'shoulder_press_r47.mp4'
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','12','-i',str(frames/'%03d.jpg'),'-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(out/name)],check=True)
text=f"""# R47 inward arm-root and upper-side shape study

Status: UNSAVED_SHAPE_STUDY_NOT_ACCEPTED. Model saved: false. Owner visual review pending.

The owner approved the cyan whole-outline proposal and broader skin scope on18October at19:05 Europe/London. R47 authors an inward side-cap envelope directly in S7, without a long fit. It starts from immutable R41; R46 is the visual comparison. No reference photo or traced outline is in the repository.

New allowed area: local shoulder-side/proximal upper-arm and upper-flank skin. Skin classified as distal (at least0.16m from the shoulder along the humerus) at ANY original key remains fixed at EVERY source key; fade begins at0.12m.166, fixed anchors, centre seam, skeleton, Basis, weights, topology, HGPT_SHOULDER and all non-S7 keys remain protected. Original source and dense45mm caps stay in force.

The author scope regression first failed on the old locked mask, then passed. A stronger any-angle distal preservation assertion caught0.109mm leakage and passed after the global distal mask was applied. Four own scope tests are required. In-memory protected identity: {json.dumps(identity,sort_keys=True)}.

All83 native responses passed: {native['passed']}; new contact records: {len(native['contacts'])}.
Back acceleration excess: {native['back_motion_excess_mm']:.6f}mm against unchanged0.5mm.
Posterior crease excess: {native['posterior_crease_excess_degrees']:.6f}degrees against unchanged2degrees.
13 benchmarks passed: {bench['passed']}; regression records: {len(bench['regressions'])}.
Test exit codes (zero passes): {json.dumps(tests,sort_keys=True)}.

No existing test was edited. The historical R42 outward-fill and R41 proximal-arm line targets are still executed and retained; their interpretation conflicts with the owner's newly approved inward skin scope. They are not falsely labelled passed. All area/contact/orientation, front, motion, crease and benchmark failures remain visible. This is a shape review study, never a model acceptance or a saved production candidate.

Review R46_R47_full_outline.jpg, R46_R47_marked_l/r.jpg, R46_R47_press_comparison.mp4 and shoulder_press_r47.mp4. These are actual native Blender5.2.1 geometry, same poses/cameras/lighting. No cosmetic image correction is used.
"""
(out/'README.md').write_text(text)
(ROOT/'docs/CODEX_ORIGINAL_V1_REVIEW_CANDIDATE_R47_20261018.md').write_text(text)
print('R47_SHAPE_STUDY_PACKAGED',native['passed'],bench['passed'],tests,flush=True)
