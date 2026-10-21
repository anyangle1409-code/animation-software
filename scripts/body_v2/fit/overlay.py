import sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont
SP="/tmp/claude-0/-home-user-animation-software/b0b01a8a-22fb-52cd-85ad-39c74496ecb2/scratchpad"
model_dir=sys.argv[1]; tag=sys.argv[2]; PREFIX=sys.argv[3] if len(sys.argv)>3 else "V2_full_standing"
ref=Image.open("/root/.claude/uploads/b0b01a8a-22fb-52cd-85ad-39c74496ecb2/4a64128b-image.png").convert("RGB")
panels={"front":(0,255),"back":(258,503),"side":(506,655),"front34":(658,884),"back34":(887,1100)}
F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',14)
tiles=[]
for view,(x0,x1) in panels.items():
    S=3
    r=ref.crop((x0+2,0,x1-2,512)); r=r.resize((r.width*S,r.height*S))
    mask=Image.open(f"{SP}/fit/mask_{view}.png").resize(r.size)
    ys=[y for y in range(0,mask.height) if mask.crop((0,y,mask.width,y+1)).getbbox()]
    top=ys[0]; stat=(505*S-top)*0.985
    m=Image.open(f"{model_dir}/{PREFIX}_{view}.png").convert("RGBA").split()[3]
    bb=m.getbbox(); m=m.crop(bb); sc=stat/m.height; m=m.resize((max(1,int(m.width*sc)),int(m.height*sc)))
    # centre: align the model's torso centre with the reference torso centre at chest height (fraction .30)
    yy=int(top+0.30*stat); row=mask.crop((0,yy,mask.width,yy+1)); rb=row.getbbox(); rc=(rb[0]+rb[2])/2 if rb else r.width/2
    mr=m.crop((0,int(0.30*m.height),m.width,int(0.30*m.height)+1)).getbbox(); mc=(mr[0]+mr[2])/2 if mr else m.width/2
    canvas=Image.new("L",r.size,0); canvas.paste(m,(int(rc-mc),top))
    edge=canvas.filter(ImageFilter.FIND_EDGES).point(lambda v:255 if v>60 else 0).filter(ImageFilter.MaxFilter(3))
    out=r.copy(); red=Image.new("RGB",r.size,(255,30,30)); out=Image.composite(red,out,edge)
    d=ImageDraw.Draw(out)
    for k in range(0,101,5):
        y=int(top+k/100*stat); d.line((0,y,out.width,y),fill=(0,170,255) if k%10==0 else (120,200,255),width=1)
        if k%10==0: d.text((2,y+1),f"{k/100:.1f}",fill=(0,120,255),font=F)
    d.text((4,out.height-20),view,fill=(255,255,255),font=F)
    tiles.append(out)
W=sum(t.width for t in tiles)+8*len(tiles); s=Image.new("RGB",(W,tiles[0].height),(28,28,30)); x=0
for t in tiles: s.paste(t,(x,0)); x+=t.width+8
s.save(f"{SP}/fit/overlay_{tag}.jpg",quality=88)
