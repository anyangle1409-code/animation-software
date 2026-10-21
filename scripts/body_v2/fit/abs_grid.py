import sys
from PIL import Image, ImageDraw, ImageFont
F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',16)
U="/root/.claude/uploads/b0b01a8a-22fb-52cd-85ad-39c74496ecb2/"
W=H=800; f0,f1,wf=0.58,0.80,0.11
def refc(path,top,bot,cx):
    im=Image.open(path).convert("RGB"); h=bot-top
    return im.crop((int(cx-wf*h),int(bot-f1*h),int(cx+wf*h),int(bot-f0*h))).resize((W,H))
def mod(p):
    im=Image.open(p).convert("RGBA"); bg=Image.new("RGBA",im.size,(28,28,30,255)); bg.alpha_composite(im); bb=im.split()[3].getbbox(); h=bb[3]-bb[1]; cx=(bb[0]+bb[2])/2
    return bg.convert("RGB").crop((int(cx-wf*h),int(bb[3]-f1*h),int(cx+wf*h),int(bb[3]-f0*h))).resize((W,H))
ims=[(refc(U+"6c6ff811-image.png",26,1296,436),"Reference")]+[(mod(a.split("=")[0]),a.split("=")[1]) for a in sys.argv[2:]]
s=Image.new("RGB",(W*len(ims),H)); d=ImageDraw.Draw(s)
for i,(t,l) in enumerate(ims): s.paste(t,(i*W,0))
for k in range(0,23):
    f=f0+k*0.01; y=int(H-(f-f0)/(f1-f0)*H)
    d.line((0,y,W*len(ims),y),fill=(0,120,170) if k%2==0 else (0,60,90),width=1)
    if k%2==0: d.text((2,y-17),f"{f:.2f}",fill=(0,200,255),font=F)
for i in range(len(ims)):
    for k in range(-10,11):
        x=int(i*W+W/2+k*0.01/(2*wf)*W)
        d.line((x,0,x,H),fill=(160,60,0) if k%2==0 else (80,30,0),width=1)
        if k%2==0 and k!=0: d.text((x+2,H-20),f"{abs(k)/100:.2f}",fill=(255,140,0),font=F)
for i,(t,l) in enumerate(ims): d.text((i*W+340,4),l,fill=(255,255,0),font=F)
s.save(sys.argv[1],quality=92)
