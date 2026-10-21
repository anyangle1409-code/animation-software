import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps
F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',18)
U="/root/.claude/uploads/b0b01a8a-22fb-52cd-85ad-39c74496ecb2/"
f0,f1,wf=0.58,0.78,0.10
def prep(c,l):
    c=ImageOps.autocontrast(c.convert("L"),cutoff=1).convert("RGB").resize((700,700)); d=ImageDraw.Draw(c)
    for k in range(0,21):
        f=f0+k*0.01; y=int(700-(f-f0)/(f1-f0)*700); d.line((0,y,25,y),fill=(0,200,255),width=2)
        if k%2==0: d.text((28,y-10),f"{f:.2f}",fill=(0,160,255),font=F)
    d.text((300,5),l,fill=(255,200,0),font=F); return c
im=Image.open(U+"6702846a-image.png").convert("RGB"); top,bot,cx=26,1296,436; h=bot-top
ims=[prep(im.crop((int(cx-wf*h),int(bot-f1*h),int(cx+wf*h),int(bot-f0*h))),"Reference")]
for a in sys.argv[2:]:
    p,l=a.split("=")
    m=Image.open(p).convert("RGBA"); bg=Image.new("RGBA",m.size,(28,28,30,255)); bg.alpha_composite(m); bb=m.split()[3].getbbox(); hh=bb[3]-bb[1]; c=(bb[0]+bb[2])/2
    ims.append(prep(bg.convert("RGB").crop((int(c-wf*hh),int(bb[3]-f1*hh),int(c+wf*hh),int(bb[3]-f0*hh))),l))
s=Image.new("RGB",(700*len(ims),700))
for i,t in enumerate(ims): s.paste(t,(i*700,0))
s.save(sys.argv[1],quality=90)
