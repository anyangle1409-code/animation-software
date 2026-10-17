"""Densify S7 body increments; original linear arm deformation is reproduced."""
import numpy as np
KEYS=np.array([110.,120.,130.,136.,145.,156.,166.])
DENSE=np.arange(96.,167.)
def hats(e,angles,start=95.):
 e=np.asarray(e);out=np.zeros((*e.shape,len(angles)))
 for j,mid in enumerate(angles):
  lo=start if j==0 else angles[j-1]
  out[...,j]=np.where(e<=mid,np.clip((e-lo)/(mid-lo),0,1),1. if j==len(angles)-1 else np.clip((angles[j+1]-e)/(angles[j+1]-mid),0,1))
 return out
def basis():
 from scipy.interpolate import CubicSpline
 nodes=np.r_[95.,KEYS];values=np.vstack((np.zeros((1,7)),np.eye(7)))
 b=CubicSpline(nodes,values,axis=0,bc_type=((1,np.zeros(7)),(1,np.zeros(7))))(DENSE)
 return b
def coefficients(old):
 # Below110 only the frozen110 increment is active; above166 frozen166.
 e=(old*KEYS[:,None]).sum(0)
 partial=old.sum(0)<.99999;e[partial]=95+15*old[0,partial]
 return (hats(e,DENSE)@basis()).T
