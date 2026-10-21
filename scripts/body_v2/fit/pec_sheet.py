import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps
F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',16)
U="/root/.claude/uploads/b0b01a8a-22fb-52cd-85ad-39c74496ecb2/"
f0,f1,wf=0.70,0.86,0.12; W=H=700
contrast=sys.argv[1].endswith("_c.jpg")
def fin(c,l,ref=False):
    if contrast: c=ImageOps.autocontrast(c.convert("L"),cutoff=1).convert("RGB")
    c=c.resize((W,H)); d=ImageDraw.Draw(c)
    for k in range(0,17):
        f=f0+k*0.01; y=int(H-(f-f0)/(f1-f0)*H); d.line((0,y,20,y),fill=(0,200,255),width=2)
        if k%2==0: d.text((22,y-9),f"{f:.2f}",fill=(0,160,255),font=F)
    for k in range(-12,13,2):
        x=int(W/2+k*0.01/(2*wf)*W); d.line((x,H-14,x,H),fill=(255,140,0),width=2)
    d.text((W//2-40,4),l,fill=(255,220,0),font=F); return c
im=Image.open(U+"6702846a-image.png").convert("RGB"); top,bot,cx=26,1296,436; h=bot-top
ims=[fin(im.crop((int(cx-wf*h),int(bot-f1*h),int(cx+wf*h),int(bot-f0*h))),"Reference")]
for a in sys.argv[2:]:
    p,l=a.split("=")
    m=Image.open(p).convert("RGBA"); bg=Image.new("RGBA",m.size,(28,28,30,255)); bg.alpha_composite(m); bb=m.split()[3].getbbox(); hh=bb[3]-bb[1]; c=(bb[0]+bb[2])/2
    ims.append(fin(bg.convert("RGB").crop((int(c-wf*hh),int(bb[3]-f1*hh),int(c+wf*hh),int(bb[3]-f0*hh))),l))
s=Image.new("RGB",(W*len(ims),H))
for i,t in enumerate(ims): s.paste(t,(i*W,0))
s.save(sys.argv[1],quality=90)
