import sys
from PIL import Image
def segs(row):
    out=[];s=None
    for i,v in enumerate(row):
        if v and s is None: s=i
        if not v and s is not None: out.append((s,i));s=None
    if s is not None: out.append((s,len(row)))
    return out
for p in sys.argv[1:]:
    im=Image.open(p).convert("RGBA"); a=im.split()[3]; W,H=im.size; px=a.load()
    rows=[[px[x,y]>128 for x in range(W)] for y in range(H)]
    ys=[y for y in range(H) if any(rows[y])]; top,bot=ys[0],ys[-1]; h=bot-top
    res={}
    for name,f in (("shoulders",0.218),("chest",0.27),("waist",0.414),("thigh",0.66)):
        sg=segs(rows[int(top+f*h)])
        if name=="shoulders": w=sg[-1][1]-sg[0][0]
        elif name=="thigh": w=max(b-a_ for a_,b in sg)
        else:
            c=[(a_,b) for a_,b in sg if a_<W/2<b]; w=(c[0][1]-c[0][0]) if (c and len(sg)>=3) else -1
        res[name]=round(w/h,3)
    print(p.split('/')[-2], res, "segments chest/waist:", len(segs(rows[int(top+0.27*h)])), len(segs(rows[int(top+0.414*h)])))
print("reference: shoulders 0.300 chest 0.20 waist 0.187 thigh 0.099")
