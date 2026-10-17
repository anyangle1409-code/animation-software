"""Compose exact native study renders; no geometry or pixels are retouched."""
import sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
source,dest=map(Path,sys.argv[1:3]);dest.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
for side in ('l','r'):
 sheet=Image.new('RGB',(1600,6*432+64),'white');draw=ImageDraw.Draw(sheet)
 draw.text((12,8),f'R41 / R42 unsaved study — side {side} — NOT ACCEPTED',font=font,fill='black')
 draw.text((12,34),'Same angles, cameras and lighting. All failures retained in the report.',font=font,fill='black')
 for row,angle in enumerate((120.,130.,135.625,145.,156.,166.)):
  for view_index,view in enumerate(('back','three_quarter')):
   for version_index,version in enumerate(('R41','R42_study')):
    x=(2*view_index+version_index)*400;y=64+row*432
    draw.text((x+8,y+3),f'{version.replace("_"," ")} {angle:g} deg {view.replace("_"," ")}',font=small,fill='black')
    im=Image.open(source/version/f'{side}_{view}_{angle}.png').convert('RGBA')
    bg=Image.new('RGBA',im.size,(27,27,27,255));bg.alpha_composite(im)
    sheet.paste(bg.convert('RGB').resize((400,400)),(x,y+30))
 sheet.save(dest/f'R41_R42_all_angles_{side}.jpg',quality=95)
