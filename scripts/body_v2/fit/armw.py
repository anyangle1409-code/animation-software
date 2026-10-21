import sys
from PIL import Image
SP="/tmp/claude-0/-home-user-animation-software/b0b01a8a-22fb-52cd-85ad-39c74496ecb2/scratchpad"
def segs(row):
    out=[];s=None
    for i,v in enumerate(row):
        if v and s is None: s=i
        if not v and s is not None: out.append((s,i));s=None
    if s is not None: out.append((s,len(row)))
    return [g for g in out if g[1]-g[0]>1]
def arms(img, alpha, statf):
    im=Image.open(img); a=(im.convert("RGBA").split()[3] if alpha else im.convert("L")); W,H=a.size; px=a.load()
    ys=[y for y in range(H) if any(px[x,y]>128 for x in range(0,W,2))]; top=ys[0]; stat=statf(top,ys[-1])
    res={}
    for f in (0.26,0.30,0.34,0.38,0.42,0.46,0.50):
        y=int(top+f*stat); sg=segs([px[x,y]>128 for x in range(W)])
        if len(sg)>=3: res[f]=round(((sg[0][1]-sg[0][0])+(sg[-1][1]-sg[-1][0]))/2/stat,4)
        else: res[f]=None
    return res
r=arms(SP+"/fit/mask_front.png",False,lambda t,b:(505-t)*0.985)
for p in sys.argv[1:]:
    m=arms(p,True,lambda t,b:b-t)
    print(p.split('/')[-2]); print("  f     ref arm w/H   model   ratio")
    for f in r:
        if r[f] and m[f]: print(f"  {f:.2f}  {r[f]:.4f}      {m[f]:.4f}  {r[f]/m[f]:.2f}")
