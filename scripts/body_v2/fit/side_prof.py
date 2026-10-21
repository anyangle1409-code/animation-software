import sys
from PIL import Image
U="/root/.claude/uploads/b0b01a8a-22fb-52cd-85ad-39c74496ecb2/"
r=Image.open(U+"c6ee5aa2-image.png").convert("RGB"); px=r.load(); top,bot=18,918; H=bot-top; bgc=px[960,300]
isb=lambda p: sum(abs(p[i]-bgc[i]) for i in range(3))>60
fs=[x/100 for x in range(66,85)]
ref={f:max([x for x in range(640,980) if isb(px[x,int(bot-f*H)])])/H for f in fs}
out=[]
for p in sys.argv[1:]:
    m=Image.open(p).convert("RGBA"); a=m.split()[3].load(); bb=m.split()[3].getbbox(); hh=bb[3]-bb[1]
    out.append({f:-min([x for x in range(m.size[0]) if a[x,int(bb[3]-f*hh)]>40])/hh for f in fs})
print("f     ref   "+"  ".join(p.split('/')[-2] for p in sys.argv[1:]))
for f in fs: print(f, f"{ref[f]-ref[0.70]:+.4f}", "  ".join(f"{o[f]-o[0.70]:+.4f}" for o in out))
