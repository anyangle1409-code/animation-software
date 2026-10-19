"""Actual R51/R52 native evidence, no model save or image retouching."""
from pathlib import Path
import json,subprocess,shutil,re
from PIL import Image,ImageDraw,ImageFont
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
tmp=Path('/tmp/r52-response');now=Path('/tmp/r52-study/R52');previous=Path('/tmp/r51-previous/tmp/r51-study/R51')
out=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r52_study_20261019'
if out.exists():raise FileExistsError('R52 study folder is immutable')
out.mkdir(parents=True)
native=json.loads((tmp/'native_final.json').read_text());bench=json.loads((tmp/'benchmarks.json').read_text());fit=json.loads((tmp/'solved.npz.json').read_text());dense=json.loads((tmp/'dense_motion.json').read_text());identity=json.loads(Path('/tmp/r52-study/protected_identity.json').read_text());tests={p.name:int(p.read_text().strip()) for p in tmp.glob('*_test_exit.txt')}
report=dict(candidate='R52',status='UNSAVED_TEMPORAL_STUDY_NOT_ACCEPTED',model_saved=False,approved=False,shape_repair_complete=False,fit=fit,native=native,dense_temporal=dense,benchmarks=bench,protected_identity=identity,test_exit_codes=tests,legacy_projection_tests=['r47_authorized_scope','r43_motion','r43_back_surface','r48_marked_surface','r48_approved_outline'],note='Independent dense native geometry is the actual study. Original seven-control tests are retained unchanged on the source-knot projection and explicitly cannot certify that geometry. Additional direct-native tests enforce the original numerical limits. No save/promotion step exists.')
(out/'r52_review.json').write_text(json.dumps(report,indent=2)+'\n')
for f in list(tmp.glob('*.json'))+list(tmp.glob('*.log'))+list(tmp.glob('*test*.txt'))+list(tmp.glob('*exit.txt')):shutil.copy2(f,out/f.name)
for name in ('solved.npz',):shutil.copy2(tmp/name,out/name)
for name in ('native_probe.npz','full_press_marked_points.npz'):shutil.copy2(now/name,out/name)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
def picture(path):
 im=Image.open(path).convert('RGBA');bg=Image.new('RGBA',im.size,(27,27,27,255));bg.alpha_composite(im);return bg.convert('RGB')
canvas=Image.new('RGB',(1024,1152),'white');draw=ImageDraw.Draw(canvas)
draw.text((10,8),'R51 / R52 — full outline at135.625 degrees',font=font,fill='black')
for row,view in enumerate(('back','three_quarter')):
 for col,(name,folder) in enumerate((('R51',previous),('R52',now))):
  x=col*512;y=48+row*544
  draw.text((x+10,y),name+' '+view.replace('_',' '),font=font,fill='black')
  canvas.paste(picture(folder/f'f025_{view}.png'),(x,y+28))
draw.text((10,1130),'Actual Blender5.2.1 geometry. R52 unsaved shape study; not accepted.',font=small,fill='black')
canvas.save(out/'R51_R52_full_outline.jpg',quality=95)
for side in ('l','r'):
 canvas=Image.new('RGB',(1280,1430),'white');draw=ImageDraw.Draw(canvas)
 draw.text((12,8),'R51 / R52 — exact135.625-degree shoulder views',font=font,fill='black')
 for row,view in enumerate(('back','three_quarter')):
  for col,(name,folder) in enumerate((('R51',previous),('R52',now))):
   x=col*640;y=52+row*664;draw.text((x+12,y),name+' '+view.replace('_',' '),font=font,fill='black')
   canvas.paste(picture(folder/f'{side}_{view}_135.625.png'),(x,y+28))
 draw.text((12,1405),'R52 UNSAVED SHAPE STUDY — all failed checks retained; owner review pending',font=small,fill='black')
 canvas.save(out/f'R51_R52_marked_{side}.jpg',quality=95)
sequence=[0]*8+list(range(41))+[40]*8+list(range(39,0,-1))
for comparison in (False,True):
 frames=Path('/tmp/r52-video-compare' if comparison else '/tmp/r52-video');frames.mkdir(exist_ok=True)
 for index,i in enumerate(sequence):
  canvas=Image.new('RGB',(1024,1100 if comparison else 588),(27,27,27));draw=ImageDraw.Draw(canvas)
  draw.text((12,8),'R51 / R52 matched press' if comparison else 'R52 full press — shape study',font=font,fill='white')
  for row,view in enumerate(('back','three_quarter')):
   if comparison:
    for col,(name,folder) in enumerate((('R51',previous),('R52',now))):
     x=col*512;y=48+row*524;canvas.paste(picture(folder/f'f{i:03d}_{view}.png'),(x,y))
     draw.text((x+10,y+8),name+' '+view.replace('_',' '),font=small,fill='white')
   else:canvas.paste(picture(now/f'f{i:03d}_{view}.png'),(row*512,48))
  draw.text((12,canvas.height-24),f'R52 STUDY — NOT ACCEPTED | t={i/40:.3f}',font=small,fill='white')
  canvas.save(frames/f'{index:03d}.jpg',quality=94)
 name='R51_R52_press_comparison.mp4' if comparison else 'shoulder_press_r52.mp4'
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','12','-i',str(frames/'%03d.jpg'),'-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(out/name)],check=True)

# Preserve the actual approved-outline reference as a separately identified panel.
approved=Path('/tmp/r47-previous/tmp/r47-study/R47')
canvas=Image.new('RGB',(1536,1152),'white');draw=ImageDraw.Draw(canvas);draw.text((10,8),'Approved R47 outline / R51 / R52 — actual135.625-degree pose',font=font,fill='black')
for row,view in enumerate(('back','three_quarter')):
 for col,(name,folder) in enumerate((('R47 outline reference',approved),('R51',previous),('R52',now))):
  x=col*512;y=48+row*544;draw.text((x+10,y),name+' '+view.replace('_',' '),font=small,fill='black');canvas.paste(picture(folder/f'f025_{view}.png'),(x,y+28))
draw.text((10,1130),'Actual native geometry. R52 unsaved; surface/motion checks and owner review remain separate.',font=small,fill='black');canvas.save(out/'R47_R51_R52_outline_reference.jpg',quality=95)
text=f"""# R52 independent temporal surface study

Owner approved this study19October2026 07:59 Europe/London. Status UNSAVED_TEMPORAL_STUDY_NOT_ACCEPTED. No model saved or promoted. R47 outline approval does not approve its surface or R52.

The independent integer-degree increments retain the original material union, original per-source masks, zero95/110/166, anchors/distal arm and45mm caps. Matrix-free finite-iteration motion constraints, adjacent-control constraints and spatial/temporal regularization are a study, not proof of convergence or repair. Actual outline is checked independently before retaining progress. The local-envelope projection attempts to keep interior skin inside the existing R51 marked boundary while its active support vertices are pinned; exact measured outline error independently determines checkpoint retention. All actual native failures remain recorded.

Original83 native response checks passed: {native['passed']}. New contact records: {len(native['contacts'])}. Original native motion excess: {native['back_motion_excess_mm']:.6f}mm (guard0.5). Posterior crease excess: {native['posterior_crease_excess_degrees']:.6f}degrees (guard2).
Additional161-pose native motion check: {json.dumps(dense,sort_keys=True)}.
13 original benchmarks passed: {bench['passed']}; regression records: {len(bench['regressions'])}.
Protected identity: {json.dumps(identity,sort_keys=True)}.
Tests, all failures retained: {json.dumps(tests,sort_keys=True)}.
Fitter final status (not model acceptance): {json.dumps({k:v for k,v in fit.items() if k!='history'},sort_keys=True)}.

Original R47 scope, R43 motion/crease and R48 marked-normal/outline tests run unchanged on the source-knot projection, labeled legacy diagnostics. They cannot express independent intermediate controls. Additional actual-native tests apply the same original limits to actual R52 positions; all five historical contour/front tests use actual native R52 probes. No previous test is weakened, replaced or deleted. R52 has no Blender model-save step even if every numerical check passes.

Actual R51_R52_full_outline.jpg, R51_R52_marked_l/r.jpg, R51_R52_press_comparison.mp4 and shoulder_press_r52.mp4 are native evidence. R47_R51_R52_outline_reference.jpg keeps the approved outline visible. No reference photo or trace enters the repo. All protected assets remain frozen. Required visual review and any unresolved folds, intersections, stretch or movement prevent calling this a completed repair.
"""
(out/'README.md').write_text(text);(ROOT/'docs/CODEX_ORIGINAL_V1_REVIEW_CANDIDATE_R52_20261019.md').write_text(text);print('R52_ACTUAL_STUDY_PACKAGED',native['passed'],dense['passed'],bench['passed'],flush=True)
