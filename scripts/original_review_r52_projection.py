"""Preservation projections and matrix-free exact original motion response."""
import numpy as np
from original_review_r52_temporal import blend,blend_adjoint,SOURCE

def allowed_dense(data):
 old=np.asarray(data['r47_allowed'],bool);allowed=np.repeat(old.any(0)[None],72,axis=0)
 allowed[SOURCE]=old;allowed[[0,15,71]]=False
 return allowed

def project(x,allowed,marked,pin,target,cap=.045):
 out=np.asarray(x,float).copy();out[~allowed]=0
 out*=np.minimum(1.,cap/np.maximum(np.linalg.norm(out,axis=2),1e-30))[:,:,None]
 ids=np.flatnonzero(pin)
 if not len(ids):return out
 lo,hi,t=marked;ll,hh,tt=lo[ids],hi[ids],t[ids];aa=(1-tt)*allowed[ll,ids];bb=tt*allowed[hh,ids];den=aa*aa+bb*bb
 if np.any((den<1e-20)&(np.linalg.norm(target[ids],axis=1)>1e-12)):raise ValueError('Uneditable marked pin')
 den=np.maximum(den,1e-30);v=np.stack((out[ll,ids],out[hh,ids]));p=np.zeros_like(v);q=np.zeros_like(v);mask=np.stack((allowed[ll,ids],allowed[hh,ids]))
 for _ in range(100):
  z=v+p;z[~mask]=0;u=z*np.minimum(1.,cap/np.maximum(np.linalg.norm(z,axis=2),1e-30))[:,:,None];p=v+p-u
  z=u+q;miss=target[ids]-((1-tt[:,None])*z[0]+tt[:,None]*z[1]);v=z.copy();v[0]+=aa[:,None]*miss/den[:,None];v[1]+=bb[:,None]*miss/den[:,None];q=z-v
  if np.linalg.norm(v,axis=2).max()<=cap+1e-12 and np.max(abs(v[~mask]),initial=0)<1e-12:break
 out[ll,ids]=v[0];out[hh,ids]=v[1]
 return out

def motion(x,mat,mapping):
 return np.diff(np.einsum('snij,snj->sni',mat,blend(x,mapping)),n=2,axis=0)

def motion_adjoint(force,mat,mapping):
 y=np.zeros((force.shape[0]+2,force.shape[1],3));y[:-2]+=force;y[1:-1]-=2*force;y[2:]+=force
 return blend_adjoint(np.einsum('snji,snj->sni',mat,y),mapping)

def normal_response(x,mat,mapping,normal):
 return np.einsum('sni,sni->sn',np.einsum('snij,snj->sni',mat,blend(x,mapping)),normal)

def normal_adjoint(force,mat,mapping,normal):
 return blend_adjoint(np.einsum('snji,snj->sni',mat,force[:,:,None]*normal),mapping)
