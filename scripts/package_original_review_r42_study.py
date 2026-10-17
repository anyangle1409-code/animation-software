"""Label native diagnostic evidence honestly; this does not approve a model."""
import json,sys,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
source=Path(sys.argv[1]);dest=Path(sys.argv[2]);dest.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
def picture(p):
 im=Image.open(p).convert('RGBA');bg=Image.new('RGBA',im.size,(27,27,27,255));bg.alpha_composite(im);return bg.convert('RGB')
for side in ('l','r'):
 canvas=Image.new('RGB',(1280,1400),'white');draw=ImageDraw.Draw(canvas)
 draw.text((12,8),'135.625 degrees — R41 / R42 unsaved contour study',font=font,fill='black')
 for row,view in enumerate(('back','three_quarter')):
  for col,name in enumerate(('R41','R42_study')):
   x=col*640;y=52+row*664;draw.text((x+12,y),name.replace('_',' ')+' — '+view.replace('_',' '),font=font,fill='black')
   canvas.paste(picture(source/name/f'{side}_{view}_135.625.png'),(x,y+28))
 draw.text((12,1380),'Native Blender 5.2.1. Diagnostic only; failed checks remain reported.',font=small,fill='black')
 canvas.save(dest/f'R41_R42_study_{side}.jpg',quality=95)
frames=dest/'video_frames';frames.mkdir(exist_ok=True)
metrics=json.loads((source/'native_study.json').read_text())
for i in range(41):
 canvas=Image.new('RGB',(1536,584),(27,27,27));draw=ImageDraw.Draw(canvas)
 draw.text((12,8),'R42 UNSAVED CONTOUR STUDY — NOT ACCEPTED',font=font,fill='white')
 draw.text((12,38),f'Native press | t={i/40:.3f} | marked stretch: {metrics["marked_stretch"]} (R41: {metrics["parent_marked_stretch"]})',font=small,fill='white')
 for j,view in enumerate(('back','front','three_quarter')):canvas.paste(picture(source/'R42_study'/f'f{i:03d}_{view}.png'),(j*512,72))
 canvas.save(frames/f'{i:03d}.jpg',quality=93)
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','10','-i',str(frames/'%03d.jpg'),'-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(dest/'R42_unsaved_contour_study.mp4')],check=True)
(dest/'native_study.json').write_text(json.dumps(metrics,indent=2)+'\n')
