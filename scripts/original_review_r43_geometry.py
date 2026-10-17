"""Analytic gradients for exact silhouette and triangle constraints."""
import numpy as np
def area_gradient(t,normal=None):
 c=np.cross(t[1]-t[0],t[2]-t[0]);length=np.linalg.norm(c)
 n=c/max(length,1e-20) if normal is None else normal
 return .5*np.array([np.cross(t[1]-t[2],n),np.cross(t[2]-t[0],n),np.cross(t[0]-t[1],n)])
def outline(points,faces,gh,axis,normal,side,station):
 a=faces[:,[0,1,2]].ravel();b=faces[:,[1,2,0]].ravel()
 sa=(points[a]-gh)@axis;sb=(points[b]-gh)@axis
 choose=((sa<=station)&(sb>station))|((sb<=station)&(sa>station))
 a=a[choose];b=b[choose];sa=sa[choose];sb=sb[choose]
 t=(station-sa)/(sb-sa);p=(1-t[:,None])*points[a]+t[:,None]*points[b]
 keep=(np.linalg.norm(p-gh,axis=1)<.36)&(p[:,0]*(1 if side=='r' else -1)>0)
 a,b,sa,sb,t,p=[x[keep] for x in (a,b,sa,sb,t,p)]
 radial=(p-gh)@normal;j=int(np.argmax(radial));i0,i1=int(a[j]),int(b[j])
 slope=((points[i1]-points[i0])@normal)/(sb[j]-sa[j]);g=normal-slope*axis
 return float(radial[j]),np.array([i0,i1]),np.array([(1-t[j])*g,t[j]*g])
def cosine_gradient(t):
 c=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);length=np.maximum(np.linalg.norm(c,axis=1),1e-20);n=c/length[:,None]
 cosine=float(np.clip(n[0]@n[1],-1,1));gc=np.array([(n[1]-cosine*n[0])/length[0],(n[0]-cosine*n[1])/length[1]])
 g=np.stack([np.cross(t[:,1]-t[:,2],gc),np.cross(t[:,2]-t[:,0],gc),np.cross(t[:,0]-t[:,1],gc)],axis=1)
 return cosine,g
