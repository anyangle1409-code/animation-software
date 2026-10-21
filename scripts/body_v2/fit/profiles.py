import sys, json
from PIL import Image
SP="/tmp/claude-0/-home-user-animation-software/b0b01a8a-22fb-52cd-85ad-39c74496ecb2/scratchpad"
def segs(row):
    out=[];s=None
    for i,v in enumerate(row):
        if v and s is None: s=i
        if not v and s is not None: out.append((s,i));s=None
    if s is not None: out.append((s,len(row)))
    return [g for g in out if g[1]-g[0]>1]
def load(path, alpha):
    im=Image.open(path); W,H=im.size
    if alpha: a=im.convert("RGBA").split()[3]
    else: a=im.convert("L")
    px=a.load(); rows=[[px[x,y]>128 for x in range(W)] for y in range(H)]
    ys=[y for y in range(H) if any(rows[y])]
    return rows, ys[0], ys[-1], W
def profile(rows, top, bot, W, stature_px, fr):
    y=int(top+fr*stature_px)
    if y>=len(rows): return None
    sg=segs(rows[y]); 
    return [(round((a-W/2)/stature_px,4), round((b-W/2)/stature_px,4)) for a,b in sg]
if __name__=="__main__":
    out={}
    for view in ("front","side","back"):
        r,t,b,W=load(f"{SP}/fit/mask_{view}.png",False)
        # reference stature: head top to sole; mask bottom misses white shoe soles -> use 505 (measured on the grid) minus 1.5% shoe
        stat=(505-t)*0.985
        m,mt,mb,mW=load(f"{SP}/v2n/V2_full_standing_{view}.png",True)
        mstat=mb-mt
        out[view]={}
        for i in range(2,96,2):
            f=i/100
            out[view][f]={"ref":profile(r,t,b,W,stat,f),"model":profile(m,mt,mb,mW,mstat,f)}
    json.dump(out,open(f"{SP}/fit/profiles.json","w"))
    for view in ("front","side"):
        print("==",view,"(fraction of height from top: segments as x/H from image centre)")
        for f,v in out[view].items():
            def w(s): return " ".join(f"[{a:+.3f},{b:+.3f}]" for a,b in s) if s else "-"
            print(f"{f:.2f} REF {w(v['ref'])}\n     MOD {w(v['model'])}")
