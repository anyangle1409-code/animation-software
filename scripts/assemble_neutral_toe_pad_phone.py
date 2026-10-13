"""Phone sheet from actual native before/after renders, no generated imagery."""
import sys,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
out=Path(sys.argv[1]);W=1400
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def f(size):return ImageFont.truetype(font,size)
canvas=Image.new('RGB',(W,2600),(19,27,37));d=ImageDraw.Draw(canvas)
d.text((35,25),'ORIGINAL_v1 | neutral toe-pad trial',font=f(44),fill='white')
d.text((35,85),'Actual current mesh | skeleton and foot length preserved',font=f(27),fill='#b2c4d8')
d.text((35,130),'REVIEW ONLY: shape still rejected; no production approval',font=f(28),fill='#ffc36b')
d.text((35,175),'Left-foot surface extract below 160 mm; full-body candidate intact',font=f(24),fill='#b2c4d8')
y=230
for tag,view,label in [('before','side','BEFORE | true neutral, no toe rotation'),
                       ('after','side','TRIAL | rounded underside contact')]:
    d.text((35,y),label,font=f(29),fill='white');y+=48
    im=Image.open(out/(tag+'_'+view+'.png')).convert('RGB')
    if view=='side':
        draw=ImageDraw.Draw(im)
        draw.line((0,827,1800,827),fill='#72d2e8',width=3)
        draw.text((35,865),'Reference floor z=0',font=f(27),fill='#72d2e8')
    im=im.resize((1330,887));canvas.paste(im,(35,y));y+=907
    if y>2000:break
canvas=canvas.crop((0,0,W,2380))
d=ImageDraw.Draw(canvas)
d.text((35,2200),'Each digit sample has a point within 0.001 mm of the floor.',font=f(28),fill='#b2c4d8')
d.text((35,2245),'Feet still 309.16 mm; individual toe articulation unresolved.',font=f(28),fill='#ffc36b')
d.text((35,2290),'902 vertices changed. Loaded/posed contact is NOT validated.',font=f(28),fill='#ffc36b')
canvas.save(out/'NEUTRAL_TOE_PAD_TRIAL_PHONE.png')
