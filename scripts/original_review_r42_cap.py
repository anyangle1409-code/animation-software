"""Bound final S7 vectors while retaining exact contour covector components."""
import numpy as np
def bounded_material(x,initial,free,normal,limit):
 def project(v):
  v=v*free[:,:,None];return v-normal*(v*normal).sum(2)[:,:,None]
 floor=normal*(initial*normal).sum(2)[:,:,None]
 radius2=limit*limit-(floor*floor).sum(2)
 if np.any(radius2<0):raise ValueError('Fixed contour component exceeds material cap')
 raw=initial+.01*project(x);q=raw-floor
 length=np.linalg.norm(q,axis=2);radius=np.sqrt(radius2)
 scale=np.minimum(1.,radius/np.maximum(length,1e-20));clipped=scale<1.
 actual=floor+scale[:,:,None]*q
 unit=q/np.maximum(length[:,:,None],1e-20)
 def pullback(g):
  tangent=g-unit*(g*unit).sum(2)[:,:,None]
  dq=np.where(clipped[:,:,None],scale[:,:,None]*tangent,g)
  return .01*project(dq)
 return actual,pullback
