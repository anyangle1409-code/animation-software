"""Package native R51 shape-study evidence. No image retouching or model save."""
from pathlib import Path
import json,subprocess,shutil,re
from PIL import Image,ImageDraw,ImageFont
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
tmp=Path('/tmp/r51-response');now=Path('/tmp/r51-study/R51')
previous=Path('/tmp/r47-previous/tmp/r47-study/R47')
out=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r51_study_20261018'
if out.exists():raise FileExistsError('R51 study folder is immutable')
out.mkdir(parents=True)
native=json.loads((tmp/'native_final.json').read_text())
bench=json.loads((tmp/'benchmarks.json').read_text())
author=json.loads((tmp/'solved.npz.json').read_text())
identity=json.loads(Path('/tmp/r51-study/protected_identity.json').read_text())
fit_status=json.loads((tmp/'fit_status.json').read_text())
fit_status['native_validation']='PASSED' if native['passed'] else 'FAILED'
fit_status['retained_state_safety']='NATIVE_CHECKS_PASSED_OWNER_REVIEW_PENDING' if native['passed'] else 'NATIVE_CHECKS_FAILED_UNACCEPTED'
fit_status['shape_repair_complete']=False
(tmp/'fit_status.json').write_text(json.dumps(fit_status,indent=2)+'\n')
fit=dict(fit_status,history=author.get('history',[]))
preflight=json.loads((tmp/'preflight.npz.json').read_text())
tests={p.name:int(p.read_text().strip()) for p in tmp.glob('*_test_exit.txt')}
outline_log=(tmp/'r48_approved_outline_test.txt').read_text()
outline_match=re.search(r'R48_APPROVED_OUTLINE_MAX_ERROR_MM\s+([0-9.eE+-]+)',outline_log)
outline_error=float(outline_match.group(1)) if outline_match else None
report=dict(candidate='R51',status='UNSAVED_SHAPE_STUDY_NOT_ACCEPTED',approved=False,model_saved=False,
 native=native,benchmark_passed=bench['passed'],benchmark_regressions=bench['regressions'],
 test_exit_codes=tests,protected_identity=identity,fit=fit,preflight=preflight,proposal_optimal=False,
 approved_outline_error_mm=outline_error,approved_outline_guard_mm=1.,
 marked_native_reversed_normals=native['samples'][25]['normal_rotations_over_90_degrees'],
 owner_scope_approved='2026-10-18 19:05 Europe/London',owner_r47_outline_approved=True,
 note='R51 starts at the retained unsafe R50 checkpoint of R47 shape. Bounded approximate proposals preserve hard outline/material rows; all exact final gates remain unchanged. Internal search retention and workflow success never mean accepted surface safety, shape completion or owner approval.')
(out/'r51_review.json').write_text(json.dumps(report,indent=2)+'\n')
for path in list(tmp.glob('*.json'))+list(tmp.glob('*test*.txt'))+list(tmp.glob('*.log'))+list(tmp.glob('*exit.txt'))+list(tmp.glob('linear_history.jsonl')):
 shutil.copy2(path,out/path.name)
shutil.copy2(tmp/'solved.npz',out/'solved.npz')
shutil.copy2(now/'native_probe.npz',out/'native_probe.npz')
shutil.copy2(now/'full_press_marked_points.npz',out/'full_press_marked_points.npz')
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
def picture(path):
 im=Image.open(path).convert('RGBA');bg=Image.new('RGBA',im.size,(27,27,27,255));bg.alpha_composite(im);return bg.convert('RGB')
canvas=Image.new('RGB',(1024,1152),'white');draw=ImageDraw.Draw(canvas)
draw.text((10,8),'R47 / R51 — full outline at135.625 degrees',font=font,fill='black')
for row,view in enumerate(('back','three_quarter')):
 for col,(name,folder) in enumerate((('R47',previous),('R51',now))):
  x=col*512;y=48+row*544
  draw.text((x+10,y),name+' '+view.replace('_',' '),font=font,fill='black')
  canvas.paste(picture(folder/f'f025_{view}.png'),(x,y+28))
draw.text((10,1130),'Actual Blender5.2.1 geometry. R51 unsaved shape study; not accepted.',font=small,fill='black')
canvas.save(out/'R47_R51_full_outline.jpg',quality=95)
for side in ('l','r'):
 canvas=Image.new('RGB',(1280,1430),'white');draw=ImageDraw.Draw(canvas)
 draw.text((12,8),'R47 / R51 — exact135.625-degree shoulder views',font=font,fill='black')
 for row,view in enumerate(('back','three_quarter')):
  for col,(name,folder) in enumerate((('R47',previous),('R51',now))):
   x=col*640;y=52+row*664;draw.text((x+12,y),name+' '+view.replace('_',' '),font=font,fill='black')
   canvas.paste(picture(folder/f'{side}_{view}_135.625.png'),(x,y+28))
 draw.text((12,1405),'R51 UNSAVED SHAPE STUDY — all failed checks retained; owner review pending',font=small,fill='black')
 canvas.save(out/f'R47_R51_marked_{side}.jpg',quality=95)
sequence=[0]*8+list(range(41))+[40]*8+list(range(39,0,-1))
for comparison in (False,True):
 frames=Path('/tmp/r51-video-compare' if comparison else '/tmp/r51-video');frames.mkdir(exist_ok=True)
 for index,i in enumerate(sequence):
  canvas=Image.new('RGB',(1024,1100 if comparison else 588),(27,27,27));draw=ImageDraw.Draw(canvas)
  draw.text((12,8),'R47 / R51 matched press' if comparison else 'R51 full press — shape study',font=font,fill='white')
  for row,view in enumerate(('back','three_quarter')):
   if comparison:
    for col,(name,folder) in enumerate((('R47',previous),('R51',now))):
     x=col*512;y=48+row*524;canvas.paste(picture(folder/f'f{i:03d}_{view}.png'),(x,y))
     draw.text((x+10,y+8),name+' '+view.replace('_',' '),font=small,fill='white')
   else:canvas.paste(picture(now/f'f{i:03d}_{view}.png'),(row*512,48))
  draw.text((12,canvas.height-24),f'R51 STUDY — NOT ACCEPTED | t={i/40:.3f}',font=small,fill='white')
  canvas.save(frames/f'{index:03d}.jpg',quality=94)
 name='R47_R51_press_comparison.mp4' if comparison else 'shoulder_press_r51.mp4'
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','12','-i',str(frames/'%03d.jpg'),'-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(out/name)],check=True)
text=f"""# R51 bounded outline-preserving native surface study

Status: UNSAVED_SHAPE_STUDY_NOT_ACCEPTED. Model saved: false. Owner visual review pending.

R47's actual overall outline was approved; its surfaces were rejected. R50 retained
an unsafe outline-preserving checkpoint but produced no native media. Therefore
R47 is the actual rendered comparison for R51. No private image or traced target
enters this build.

R51 replaces repeated full LP optimality solves with a first-party bounded
primal-dual search proposal. Exact hinge-branch presolve preserves the mathematical
objective; independent hard-row projection and original-row reconstruction verify
proposal bounds. Proposals are explicitly NOT certified optimal. The fitter then
requires a lower actual joint-pose repair merit, the actual outline within0.95mm,
and both unchanged45mm displacement caps. All exact final nonlinear and native
safety gates remain identical to R50/R49. No old test or numerical limit changed.
Internal unsafe search retention is not a passed final gate.

See docs/CODEX_ORIGINAL_V1_R51_BUILD_NOTE_20261018.md for failing probes, exact LP
capture, regression tests and the local three-step preflight. CI repeats the
three-step preflight before a bounded15minute main search. Full native checking,
13 benchmarks, all historical tests and actual matched images/video follow even
when the retained search state remains unsafe. There is no model-save step.

Native83-response checks passed: {native['passed']}; new contact records: {len(native['contacts'])}.
Back motion excess: {native['back_motion_excess_mm']:.6f}mm against unchanged0.5mm.
Posterior crease excess: {native['posterior_crease_excess_degrees']:.6f}degrees against unchanged2degrees.
13 benchmarks passed: {bench['passed']}; regression records: {len(bench['regressions'])}.
Actual marked-outline error against approved R47: {outline_error}mm; unchanged guard1mm.
Marked-pose reversed normals: {native['samples'][25]['normal_rotations_over_90_degrees']}.
Test exit codes (zero passes): {json.dumps(tests,sort_keys=True)}.
Search exit and retained checkpoint: {json.dumps(fit_status,sort_keys=True)}.
Protected identity: {json.dumps(identity,sort_keys=True)}.

Historical outward-fill/line tests and full R47 scope tests remain unchanged and
all failures remain recorded. A successful evidence workflow or numerical pass
is not owner visual approval, anatomical correctness or a completed shape repair.
Frozen skeleton, Basis, weights, topology, HGPT_SHOULDER/non-S7 keys, lockout,
anchors and protected elbow/distal arm remain protected.

Review actual R47_R51_full_outline.jpg, R47_R51_marked_l/r.jpg,
R47_R51_press_comparison.mp4 and shoulder_press_r51.mp4. The fitting history,
non-optimal proposal reports, timeout/exit details and native failures are retained.
"""
(out/'README.md').write_text(text)
(ROOT/'docs/CODEX_ORIGINAL_V1_REVIEW_CANDIDATE_R51_20261018.md').write_text(text)
print('R51_SURFACE_STUDY_PACKAGED',native['passed'],bench['passed'],tests,flush=True)

