"""Reference vs model silhouettes, per height (fractions of stature).  usage: silfit.py <model_dir> [out.json]"""
import sys, json
from PIL import Image
m=Image.open("fit/ref1_skinmask.png"); mp=m.load()
def ref_panel(x0,x1,top=20,bot=919):
    return lambda f: [x for x in range(x0,x1) if mp[x,int(bot-f*(bot-top))]>128], bot-top
def runs(xs):
    if not xs: return []
    out=[[xs[0],xs[0]]]
    for x in xs[1:]:
        if x==out[-1][1]+1: out[-1][1]=x
        else: out.append([x,x])
    return out
FS=[round(0.05+0.01*i,2) for i in range(84)]
def side_ref():
    g,H=ref_panel(600,985); return {f:(max(g(f))/H, min(g(f))/H) for f in FS}   # front faces +x: (front, back)
def front_ref():
    g,H=ref_panel(0,590); out={}
    for f in FS:
        xs=g(f); rs=runs(xs); c=313
        tor=[r for r in rs if r[0]<=c<=r[1]]
        out[f]=((max(xs)-min(xs))/H, (tor[0][1]-tor[0][0])/H if tor else None, len(rs))
    return out
def model(path, side):
    im=Image.open(path).convert("RGBA"); a=im.split()[3].load(); bb=im.split()[3].getbbox(); H=bb[3]-bb[1]; out={}
    cx=(bb[0]+bb[2])//2
    for f in FS:
        y=int(bb[3]-f*H); xs=[x for x in range(im.size[0]) if a[x,y]>40]
        if side: out[f]=(-min(xs)/H, -max(xs)/H)        # front faces -x: (front, back) in a +front axis
        else:
            rs=runs(xs); tor=[r for r in rs if r[0]<=cx<=r[1]]
            out[f]=((max(xs)-min(xs))/H, (tor[0][1]-tor[0][0])/H if tor else None, len(rs))
    return out
d=sys.argv[1]
rs,rf=side_ref(),front_ref(); ms,mf=model(f"{d}/V2_full_stand_side.png",True),model(f"{d}/V2_full_stand_front.png",False)
# side positions relative to each body's own front at f=0.60 (belly) and back at f=0.60
print(" f   | depth ref  model  diff | front(rel .60) ref  model | back(rel .60) ref model | width ref model | torso ref model")
res={}
for f in FS:
    rd=rs[f][0]-rs[f][1]; md=ms[f][0]-ms[f][1]
    rfr=rs[f][0]-rs[0.6][0]; mfr=ms[f][0]-ms[0.6][0]; rbk=rs[f][1]-rs[0.6][1]; mbk=ms[f][1]-ms[0.6][1]
    res[f]=dict(depth=(rd,md),front=(rfr,mfr),back=(rbk,mbk),width=(rf[f][0],mf[f][0]),torso=(rf[f][1],mf[f][1]))
    tw=lambda v: f"{v:.3f}" if v is not None else "  -  "
    print(f"{f:.2f} | {rd:.3f} {md:.3f} {rd-md:+.3f} | {rfr:+.3f} {mfr:+.3f} | {rbk:+.3f} {mbk:+.3f} | {rf[f][0]:.3f} {mf[f][0]:.3f} | {tw(rf[f][1])} {tw(mf[f][1])}")
if len(sys.argv)>2: json.dump({str(k):v for k,v in res.items()},open(sys.argv[2],"w"))
