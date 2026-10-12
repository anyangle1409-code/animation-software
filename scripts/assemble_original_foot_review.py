"""Measured, labelled contact sheets from actual Blender renders."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,sys,numpy as np
out=Path(sys.argv[1]);audit=json.loads((out/'foot_native_audit.json').read_text());candidate=json.loads((out/'foot_contact_candidate_manifest.json').read_text())
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font=ImageFont.truetype(fontpath,28);small=ImageFont.truetype(fontpath,24);big=ImageFont.truetype(fontpath,40)
def save(im,path):
 tmp=path.with_suffix('.tmp');im.save(tmp,format='PNG');tmp.replace(path)
records={r['file']:r for r in candidate['render_records']}
for name in ['before_toe_lift_side.png','after_toe_lift_side.png']:
 im=Image.open(out/name).convert('RGB');d=ImageDraw.Draw(im)
 line=records[name]['floor_line_px'];d.line([tuple(p) for p in line],fill='#75ddff',width=5)
 d.text((55,1030),'Reference floor z = 0 | left toe lift; right foot neutral',font=font,fill='#75ddff')
 save(im,out/(name.removesuffix('.png')+'_labelled.png'))
for view in ('top','side'):
 skin=Image.open(out/('before_neutral_'+view+'.png')).convert('RGB')
 guide=Image.open(out/('reference_guides_'+view+'.png')).convert('RGB')
 a=np.asarray(guide).astype(int);bg=a[0,0]
 mask=(np.max(np.abs(a-bg),axis=2)>10).astype('uint8')*255
 ghost=Image.blend(Image.new('RGB',skin.size,tuple(bg)),skin,.30)
 im=Image.composite(guide,ghost,Image.fromarray(mask));d=ImageDraw.Draw(im)
 line=records['reference_guides_'+view+'.png']['28cm_boundary_px']
 d.line([tuple(p) for p in line],fill='#ff6e78',width=6)
 d.text((45,50),'Red: 28cm skin boundary | gold: unchanged reference controls',font=font,fill='#ffadb3')
 d.text((45,1010),'Reference tip extends 24.16mm beyond proposed boundary',font=font,fill='#ffadb3')
 save(im,out/('FOOT_28CM_BLOCKER_'+view.upper()+'.png'))
def sheet(name,title,subtitle,items):
 im=Image.new('RGB',(1600,230+len(items)//2*630),(19,26,36));d=ImageDraw.Draw(im)
 d.text((25,22),title,font=big,fill='white');d.text((25,78),subtitle,font=font,fill='#e6bd70')
 d.text((25,127),'Actual ORIGINAL_v1 | source skeleton and mesh coordinates preserved',font=small,fill='#b8c9db')
 d.text((25,170),'Separate reversible candidate; no production or anatomical approval',font=small,fill='#b8c9db')
 for i,(file,label,detail) in enumerate(items):
  x=(i%2)*800;y=230+(i//2)*630
  d.text((x+18,y+8),label,font=font,fill='white')
  source=Image.open(out/file).convert('RGB');source.thumbnail((780,500),Image.Resampling.LANCZOS)
  im.paste(source,(x+(800-source.width)//2,y+54))
  d.text((x+18,y+535),detail,font=small,fill='#b8c9db')
 save(im,out/name)
sheet('FOOT_CONTACT_BEFORE_AFTER_PHONE.png','Home Gym PT | foot contact candidate','Foot length remains 30.92cm; 28cm geometry proposal is blocked',[
 ('before_toe_lift_side_labelled.png','BEFORE | toe lift -30 degrees','Forefoot crosses floor by 1.51mm'),
 ('after_toe_lift_side_labelled.png','AFTER | same pose and camera','Floor crossing reduced to <0.001mm'),
 ('before_neutral_top.png','BEFORE | neutral footprint','Length 30.92cm | width 9.67cm'),
 ('after_neutral_top.png','AFTER | neutral footprint','Same footprint; 724 vertices reweighted')])
sheet('FOOT_PROPORTION_BLOCKER_PHONE.png','Home Gym PT | proportion findings','28cm is population-supported; current reference envelope prevents it',[
 ('before_neutral_side.png','ACTUAL ORIGINAL FOOT','Length 30.92cm | stature 1.82m'),
 ('FOOT_28CM_BLOCKER_SIDE.png','28cm TARGET BOUNDARY','Reference points extend 24.16mm beyond'),
 ('before_neutral_top.png','ACTUAL BILATERAL FOOTPRINT','Symmetric length/width in measured mesh'),
 ('FOOT_28CM_BLOCKER_TOP.png','UNCHANGED SOURCE GUIDES','Low-confidence surface-derived stations')])
files=[p for p in out.iterdir() if p.suffix in ('.png','.blend','.json') and '.tmp.' not in p.name and p.name!='review_export_hashes.json']
for p in files:
 if p.suffix=='.png':
  with Image.open(p) as im:im.verify()
(out/'review_export_hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n')
print('FOOT_REVIEW_ASSEMBLED',len(files),'verified artifacts')
