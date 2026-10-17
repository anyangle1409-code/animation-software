"""Compose native before/after motion and preserve every measured failure."""
import sys,json,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];tmp=Path('/tmp/r43-response');now=Path('/tmp/r43-study/R43');previous=Path('/tmp/r42-previous/r42-study')
model=ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r43_20261017/HGPT_ORIGINAL_V1_REVIEW_R43_CODEX.blend'
out=model.parent if model.exists() else ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r43_study_20261017';out.mkdir(parents=True,exist_ok=True)
native=json.loads((tmp/'native_final.json').read_text());bench=json.loads((tmp/'benchmarks_before_save.json').read_text())
tests={p.name:int(p.read_text().strip()) for p in tmp.glob('*_test_exit.txt')}
identity=json.loads((out/'identity.json').read_text()) if (out/'identity.json').exists() else {}
guard=json.loads((out/'r43_guard_recheck.json').read_text()) if (out/'r43_guard_recheck.json').exists() else {}
passed=model.exists() and native['passed'] and bench['passed'] and tests and not any(tests.values()) and identity and all(identity.values()) and guard.get('sample_count')==82 and not guard.get('violations')
report=dict(candidate='R43',approved=False,model_saved=model.exists(),status='NUMERIC_CHECKS_PASSED_AWAITING_VISUAL_REVIEW' if passed else 'REJECTED_NUMERIC_CHECKS',native=native,benchmark_regressions=bench['regressions'],test_exit_codes=tests,identity=identity,original_guard=guard)
(out/'r43_review.json').write_text(json.dumps(report,indent=2)+'\n')
for p in tmp.glob('*_test*txt'):(out/p.name).write_bytes(p.read_bytes())
(out/'native_probe.npz').write_bytes((now/'native_probe.npz').read_bytes())
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
def picture(p):
 im=Image.open(p).convert('RGBA');bg=Image.new('RGBA',im.size,(27,27,27,255));bg.alpha_composite(im);return bg.convert('RGB')
for reference in ('R41','R42_study'):
 for side in ('l','r'):
  canvas=Image.new('RGB',(1280,1430),'white');draw=ImageDraw.Draw(canvas)
  draw.text((12,8),f'{reference.replace("_"," ")} / R43 — exact135.625 degrees',font=font,fill='black')
  for row,view in enumerate(('back','three_quarter')):
   for col,(name,folder) in enumerate(((reference,previous/reference),('R43',now))):
    x=col*640;y=52+row*664;draw.text((x+12,y),name.replace('_',' ')+' — '+view.replace('_',' '),font=font,fill='black')
    canvas.paste(picture(folder/f'{side}_{view}_135.625.png'),(x,y+28))
  draw.text((12,1405),report['status']+' — native Blender5.2.1; owner review pending',font=small,fill='black')
  canvas.save(out/f'{reference}_R43_marked_{side}.jpg',quality=95)
for side in ('l','r'):
 canvas=Image.new('RGB',(1600,2656),'white');draw=ImageDraw.Draw(canvas)
 draw.text((12,8),'R42 / R43 — same angles, cameras and lighting — review only',font=font,fill='black')
 for row,angle in enumerate((120.,130.,135.625,145.,156.,166.)):
  for vi,view in enumerate(('back','three_quarter')):
   for k,(name,folder) in enumerate((('R42',previous/'R42_study'),('R43',now))):
    x=(vi*2+k)*400;y=64+row*432;draw.text((x+8,y+3),f'{name} {angle:g} deg {view.replace("_"," ")}',font=small,fill='black');canvas.paste(picture(folder/f'{side}_{view}_{angle}.png').resize((400,400)),(x,y+30))
 canvas.save(out/f'R42_R43_all_angles_{side}.jpg',quality=95)
sequence=[0]*8+list(range(41))+[40]*8+list(range(39,0,-1))
for comparison in (False,True):
 frames=Path('/tmp/r43-video-compare' if comparison else '/tmp/r43-video');frames.mkdir(exist_ok=True)
 for index,i in enumerate(sequence):
  canvas=Image.new('RGB',(1024,1100 if comparison else 588),(27,27,27));draw=ImageDraw.Draw(canvas)
  draw.text((12,8),'R42 / R43 matched press motion' if comparison else 'R43 full press — back and three-quarter',font=font,fill='white')
  for row,view in enumerate(('back','three_quarter')):
   if comparison:
    for col,(name,folder) in enumerate((('R42',previous/'R42_study'),('R43',now))):
     x=col*512;y=48+row*524;canvas.paste(picture(folder/f'f{i:03d}_{view}.png'),(x,y));draw.text((x+10,y+8),name+' '+view.replace('_',' '),font=small,fill='white')
   else:canvas.paste(picture(now/f'f{i:03d}_{view}.png'),(row*512,48))
  draw.text((12,canvas.height-24),report['status']+f' | t={i/40:.3f}',font=small,fill='white');canvas.save(frames/f'{index:03d}.jpg',quality=94)
 name='R42_R43_press_comparison.mp4' if comparison else 'shoulder_press_r43.mp4'
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','12','-i',str(frames/'%03d.jpg'),'-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(out/name)],check=True)
print('R43_REVIEW',report['status'],str(out),flush=True)
