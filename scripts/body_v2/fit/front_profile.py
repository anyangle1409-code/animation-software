import sys
from PIL import Image
def prof(p):
    m=Image.open(p).convert("RGBA").split()[3].point(lambda q:255 if q>40 else 0); bb=m.getbbox(); px=m.load(); top,bot=bb[1],bb[3]; H=bot-top; cx=(bb[0]+bb[2])//2
    out={}
    for f in [x/100 for x in range(26,72,2)]:
        y=int(bot-f*H)
        if px[cx,y]:
            l=cx; r=cx
            while px[l-1,y]: l-=1
            while px[r+1,y]: r+=1
            out[f]=f"w{(r-l)/H:.3f}"
        else:
            a=cx
            while not px[a,y]: a-=1
            b=a
            while px[b-1,y]: b-=1
            out[f]=f"g{(cx-a)/H:.3f}/{(a-b)/H:.3f}"
    return out
P=[prof(p) for p in sys.argv[1:]]
for f in P[0]: print(f, "  ".join(x[f] for x in P))
