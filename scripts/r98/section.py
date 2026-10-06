"""Planar cross-sections of a rest mesh (tris) -> PNG. usage: section.py npz out.png axis val [axis val ...]; colours by upperarm_l weight."""
import sys, numpy as np
from PIL import Image, ImageDraw
d=np.load(sys.argv[1]); co=d['co']; T=d['tris']; W=d['W']; names=[str(x) for x in d['names']]
ua=W[:,names.index('upperarm_l')] + (W[:,names.index('glenohumeral_half_l')]*0.5 if 'glenohumeral_half_l' in names else 0)
out=sys.argv[2]; specs=sys.argv[3:]
cells=[]
for k in range(0,len(specs),2):
    ax='xyz'.index(specs[k]); v=float(specs[k+1])
    a,b=[i for i in range(3) if i!=ax]
    if ax==1: a,b=0,2
    if ax==0: a,b=1,2
    if ax==2: a,b=0,1
    S=500; img=Image.new('RGB',(S,S+20),(25,25,28)); dr=ImageDraw.Draw(img)
    lo=np.array([-0.32,-0.2]) if ax!=0 else np.array([-0.2,1.1]); 
    if ax==1: lo=np.array([-0.32,1.12])
    if ax==2: lo=np.array([-0.32,-0.2])
    span=0.4
    def px(p): return ((p[0]-lo[0])/span*S, S+20-(p[1]-lo[1])/span*S)
    for gx in np.arange(0,span+1e-9,0.05):
        x0=px((lo[0]+gx,lo[1]))[0]; dr.line([(x0,20),(x0,S+20)],fill=(45,45,50))
        y0=px((lo[0],lo[1]+gx))[1]; dr.line([(0,y0),(S,y0)],fill=(45,45,50))
    s=co[T][:,:,ax]-v
    for t,ss in zip(T,s):
        if (ss>0).all() or (ss<0).all(): continue
        pts=[]
        for i,j in ((0,1),(1,2),(2,0)):
            if (ss[i]>0)!=(ss[j]>0):
                f=ss[i]/(ss[i]-ss[j]); p=co[t[i]]+f*(co[t[j]]-co[t[i]]); u=ua[t[i]]+f*(ua[t[j]]-ua[t[i]])
                pts.append((p,u))
        if len(pts)==2:
            u=(pts[0][1]+pts[1][1])/2; col=(int(80+175*u),int(200-120*u),int(255-200*u))
            dr.line([px((pts[0][0][a],pts[0][0][b])),px((pts[1][0][a],pts[1][0][b]))],fill=col,width=2)
    dr.text((4,3),f"{specs[k]}={v}  grid 5cm  axes {'xyz'[a]},{'xyz'[b]}",fill=(230,230,230))
    cells.append(img)
Sh=Image.new('RGB',(520*len(cells),520),(0,0,0))
for i,c in enumerate(cells): Sh.paste(c,(i*520,0))
Sh.save(out)
