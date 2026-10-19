"""Local upper-outline projection; exact actual outline still decides retention."""
import numpy as np
from original_review_r48_outline import silhouette

def make_envelopes(points,faces):
 levels=np.arange(1.14,1.701,.001);out=[]
 for sign,side in ((-1,'l'),(1,'r')):
  for normal in (np.array([sign,0.,0.]),np.array([sign,-1.,0.])/np.sqrt(2.)):
   values=np.array([silhouette(points,faces,side,normal,h)[0] for h in levels])
   out.append((sign,normal,levels*1000,values*1000))
 return out

def clip_marked(x,allowed,marked,base,mat,envelopes,margin_mm=0.):
 lo,hi,t=marked;ids=np.arange(len(t));a=(1-t)*allowed[lo,ids];b=t*allowed[hi,ids];coeff=a*a+b*b
 for sign,normal,levels,values in envelopes:
  increment=(1-t[:,None])*x[lo,ids]+t[:,None]*x[hi,ids];world=base+np.einsum('nij,nj->ni',mat,increment)
  goal=np.interp(world[:,2],levels,values)-margin_mm;segment=np.clip(np.searchsorted(levels,world[:,2])-1,0,len(levels)-2);slope=(values[segment+1]-values[segment])/(levels[segment+1]-levels[segment])
  miss=world@normal-goal;active=(world[:,0]*sign>80.)&(world[:,2]>=levels[0])&(world[:,2]<=levels[-1])&(miss>0)&(coeff>1e-20)
  g=np.repeat(normal[None],len(t),axis=0);g[:,2]-=slope;g=np.einsum('nji,nj->ni',mat,g);den=coeff*(g*g).sum(1)
  v=np.flatnonzero(active);correction=miss[v,None]*g[v]/np.maximum(den[v,None],1e-30)
  x[lo[v],v]-=a[v,None]*correction;x[hi[v],v]-=b[v,None]*correction
 return x
