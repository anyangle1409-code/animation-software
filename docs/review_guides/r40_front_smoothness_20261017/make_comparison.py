"""Assemble unaltered native renders; annotate after pasting so labels stay visible."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import sys
before,after,out,side=sys.argv[1:5]
before=Path(before);after=Path(after);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',24);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
views=['back','three_quarter'];angle='135.625';tags=[before.name.upper(),after.name.upper()]
sheet=Image.new('RGB',(1200,1400),'white')
for row,view in enumerate(views):
 for col,root in enumerate([before,after]):
  im=Image.open(root/f'{side}_{view}_{angle}.png').convert('RGBA');bg=Image.new('RGBA',im.size,(28,28,30,255));bg.alpha_composite(im)
  sheet.paste(bg.convert('RGB').resize((600,600)),(col*600,96+row*650))
d=ImageDraw.Draw(sheet);d.text((12,8),f'Your marked angle: {angle} degrees — {tags[0]} / {tags[1]}',font=font,fill='black')
for row,view in enumerate(views):
 for col,tag in enumerate(tags):
  x,y=col*600,60+row*650;d.rectangle((x,y,x+599,y+35),fill='white');d.text((x+12,y+3),f'{tag} - {view.replace("_"," ")}',font=font,fill='black')
d.text((12,1372),'Native Blender renders; same cameras and pose. R40 owner review pending.',font=small,fill='black');sheet.save(out,quality=95)
