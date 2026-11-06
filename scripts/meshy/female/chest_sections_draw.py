"""Draw chest_sections_f_blender.py output (PIL): three panels, white source, orange body, blue bra.
usage: python3.11 chest_sections_draw.py <sections .json> <out .png>
"""
import json,sys
from PIL import Image,ImageDraw
r=json.load(open(sys.argv[1])); cols={'HGPT_FEMALE_SOURCE_Mesh_0':((255,255,255),3),'HGPT_Female_Body':((240,150,60),2),'HGPT_Female_Bra':((80,170,255),1)}
ims=[]
for key,(ix,iy,cx,cy,sc,title) in {'h':(0,1,0,-0.1,2400,'horizontal z=1.20 (x right, front down)'),'s0':(1,2,-0.1,1.2,2400,'sagittal x=0 sternum (front left)'),'s8':(1,2,-0.1,1.2,2400,'sagittal x=0.085 breast (front left)')}.items():
    im=Image.new('RGB',(700,700),(20,20,20)); d=ImageDraw.Draw(im)
    for n,(c,w) in cols.items():
        for s in r[key][n]:
            if key=='h': tr=lambda p:(350+(p[0]-cx)*sc,350-(p[1]-cy)*sc)
            else: tr=lambda p:(350+(p[1]-cx)*sc,350-(p[2]-cy)*sc)
            d.line([tr(s[0]),tr(s[1])],fill=c,width=w)
    d.text((5,5),title+'  white source, orange body, blue bra',fill=(255,255,255)); ims.append(im)
o=Image.new('RGB',(2100,700)); [o.paste(im,(i*700,0)) for i,im in enumerate(ims)]; o.save(sys.argv[2])
