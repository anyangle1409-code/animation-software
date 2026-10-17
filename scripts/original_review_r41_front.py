"""Exact front dihedral measurement and analytic crease penalty."""
import numpy as np

def edge_pairs(faces):
 d={}
 for i,f in enumerate(faces):
  for j in range(3):d.setdefault(tuple(sorted((int(f[j]),int(f[(j+1)%3])))),[]).append(i)
 edges=np.array([e for e,v in d.items() if len(v)==2]);ff=np.array([d[tuple(e)] for e in edges])
 return edges,ff

def angles(p,triangles):
 t=p[triangles];c=np.cross(t[:,:,1]-t[:,:,0],t[:,:,2]-t[:,:,0]);c/=np.maximum(np.linalg.norm(c,axis=2)[:,:,None],1e-15)
 return np.degrees(np.arccos(np.clip((c[:,0]*c[:,1]).sum(1),-1,1)))

def front_peak(p,faces,gh,side):
 e,ff=edge_pairs(faces);rel=p[e].mean(1)-gh
 mask=(np.linalg.norm(rel,axis=1)<.08)&(rel[:,0]*(1 if side=='r' else -1)>0)&(rel[:,1]<0)&(rel[:,2]<0)
 if not mask.any():raise ValueError('Missing fixed front patch')
 return float(angles(p,faces[ff[mask]]).max())

def crease_loss(p,triangles,limits):
 """Squared excess in adjacent unit-normal cosine, with exact derivatives."""
 t=p[triangles];c=np.cross(t[:,:,1]-t[:,:,0],t[:,:,2]-t[:,:,0]);length=np.maximum(np.linalg.norm(c,axis=2),1e-15);n=c/length[:,:,None]
 cosine=np.clip((n[:,0]*n[:,1]).sum(1),-1,1);error=np.maximum(np.cos(np.radians(limits))-cosine,0)
 weight=1000.;value=float(weight*(error*error).sum())
 gc=np.empty_like(c)
 gc[:,0]=-2*weight*error[:,None]*(n[:,1]-cosine[:,None]*n[:,0])/length[:,0,None]
 gc[:,1]=-2*weight*error[:,None]*(n[:,0]-cosine[:,None]*n[:,1])/length[:,1,None]
 g=np.stack((np.cross(t[:,:,1]-t[:,:,2],gc),np.cross(t[:,:,2]-t[:,:,0],gc),np.cross(t[:,:,0]-t[:,:,1],gc)),axis=2)
 grad=np.zeros_like(p)
 for axis in range(3):grad[:,axis]=np.bincount(triangles.ravel(),weights=g[:,:,:,axis].ravel(),minlength=len(p))
 excess=np.degrees(np.arccos(cosine))-limits
 return value,grad,float(np.degrees(np.arccos(cosine)).max(initial=0))
