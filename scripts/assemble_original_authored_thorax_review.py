"""Label actual full-body authored-context renders for phone review."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import sys,json,hashlib
out=Path(sys.argv[1]);fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font=ImageFont.truetype(fontpath,28);small=ImageFont.truetype(fontpath,23)
sheet=Image.new('RGB',(1200,600+3*1880),(19,26,36));d=ImageDraw.Draw(sheet)
for i,line in enumerate([
 'Home Gym PT | ORIGINAL_v1 authored context',
 'Actual original full body | separate static review scene',
 '43 authored meshes: ribs/sternum + curved shoulder guides',
 'Diagnostic x-ray: translucent surfaces overlap in these views',
 'Original skin, weights, shape keys and both rigs unchanged',
 'Authored guides are separate from the 206-control reference',
 'No anatomical, motion, contact or production acceptance',
 'Feet remain 30.92cm; shoulder attachment gaps remain open',
 'Fixed camera scale | 1600 x 2400 individual PNGs']):
 d.text((25,25+55*i),line,font=font if i<2 else small,fill='white' if i<2 else '#b8c9db')
for i,(name,label) in enumerate([
 ('front','FRONT'),('side','SIDE'),('rear_three_quarter','REAR THREE-QUARTER')]):
 p=out/('fullbody_authored_context_'+name+'.png')
 with Image.open(p) as im:im.verify()
 im=Image.open(p).convert('RGB');im.thumbnail((1180,1770),Image.Resampling.LANCZOS)
 y=600+1880*i;d.text((25,y),label,font=font,fill='#e6bd70');sheet.paste(im,((1200-im.width)//2,y+65))
p=out/'AUTHORED_THORAX_FULLBODY_PHONE.png';tmp=p.with_suffix('.tmp')
sheet.save(tmp,format='PNG');tmp.replace(p)
files=[p for p in out.iterdir() if p.suffix in ('.png','.json','.blend') and p.name!='thorax_export_hashes.json']
(out/'thorax_export_hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n')
