import sys
from PIL import Image, ImageDraw, ImageFont
F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',18)
U="/root/.claude/uploads/b0b01a8a-22fb-52cd-85ad-39c74496ecb2/"
W,H=600,700
def refc(path,top,bot,cx,f0,f1,wf):
    im=Image.open(path).convert("RGB"); h=bot-top
    return im.crop((int(cx-wf*h),int(bot-f1*h),int(cx+wf*h),int(bot-f0*h))).resize((W,H))
def mod(p,f0,f1,wf):
    im=Image.open(p).convert("RGBA"); bg=Image.new("RGBA",im.size,(28,28,30,255)); bg.alpha_composite(im); bb=im.split()[3].getbbox(); h=bb[3]-bb[1]; cx=(bb[0]+bb[2])/2
    return bg.convert("RGB").crop((int(cx-wf*h),int(bb[3]-f1*h),int(cx+wf*h),int(bb[3]-f0*h))).resize((W,H))
out=sys.argv[1]; f0,f1,wf=0.55,0.83,0.12
ims=[(refc(U+"c6ee5aa2-image.png",18,918,313,f0,f1,wf),"Ref 1"),(refc(U+"6c6ff811-image.png",26,1296,436,f0,f1,wf),"Ref 2")]+[(mod(a.split("=")[0],f0,f1,wf),a.split("=")[1]) for a in sys.argv[2:]]
s=Image.new("RGB",(W*len(ims),H)); d=ImageDraw.Draw(s)
for i,(t,l) in enumerate(ims): s.paste(t,(i*W,0))
for k in range(0,29):
    f=f0+k*0.01; y=int(H-(f-f0)/(f1-f0)*H)
    if k%5==0: d.line((0,y,W*len(ims),y),fill=(0,160,220),width=1); d.text((2,y-18),f"{f:.2f}",fill=(0,200,255),font=F)
for i,(t,l) in enumerate(ims): d.text((i*W+230,4),l,fill=(255,255,0),font=F)
s.save(out,quality=90)
