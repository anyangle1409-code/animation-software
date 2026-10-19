"""Independent integer-degree S7 increments; exact decoding of old responses.

All arrays use metres. The ghost95 control is always zero and is not installed
as a Blender key. No independent curve is validated by a seven-knot projection.
"""
import numpy as np
ANGLES=np.arange(95.,167.)
SOURCE=np.array([110,120,130,136,145,156,166])-95

def response_basis():
 """Exact original clamped cubic basis, without a SciPy dependency in Blender."""
 nodes=np.array([95.,110.,120.,130.,136.,145.,156.,166.]);values=np.vstack([np.zeros((1,7)),np.eye(7)]);h=np.diff(nodes);system=np.zeros((8,8));rhs=np.zeros((8,7));slope=np.diff(values,axis=0)/h[:,None]
 system[0,0]=2*h[0];system[0,1]=h[0];rhs[0]=6*slope[0]
 system[-1,-2]=h[-1];system[-1,-1]=2*h[-1];rhs[-1]=-6*slope[-1]
 for j in range(1,7):system[j,j-1:j+2]=[h[j-1],2*(h[j-1]+h[j]),h[j]];rhs[j]=6*(slope[j]-slope[j-1])
 moments=np.linalg.solve(system,rhs);sample=np.arange(96.,167.);i=np.clip(np.searchsorted(nodes,sample,side='right')-1,0,6);b=(sample-nodes[i])/h[i];a=1-b
 return a[:,None]*values[i]+b[:,None]*values[i+1]+((a*a*a-a)*h[i]*h[i]/6)[:,None]*moments[i]+((b*b*b-b)*h[i]*h[i]/6)[:,None]*moments[i+1]

def decode(weight,tolerance=1e-9):
 w=np.asarray(weight,float)
 if w.ndim!=3 or w.shape[1]!=7 or not np.isfinite(w).all():raise ValueError('Invalid seven-control response coefficients')
 curve=np.concatenate([np.zeros((1,7)),response_basis()]);edge=np.diff(curve,axis=0);den=np.maximum((edge*edge).sum(1),1e-30)
 lo=np.empty((len(w),w.shape[2]),np.int16);alpha=np.empty(lo.shape)
 for s in range(len(w)):
  unique,inverse=np.unique(w[s].T,axis=0,return_inverse=True)
  t=np.clip(np.einsum('udk,dk->ud',unique[:,None]-curve[:-1],edge)/den,0,1)
  error=np.linalg.norm(curve[:-1][None]+t[:,:,None]*edge[None]-unique[:,None],axis=2)
  j=error.argmin(1);r=np.arange(len(unique))
  if float(error[r,j].max())>tolerance:raise ValueError('Response coefficients do not identify an original dense interval')
  lo[s]=j[inverse];alpha[s]=t[r,j][inverse]
 return lo,lo+1,alpha

def blend(dense,mapping):
 lo,hi,t=mapping;x=np.asarray(dense);v=np.arange(x.shape[1])[None]
 return (1-t[:,:,None])*x[lo,v]+t[:,:,None]*x[hi,v]

def blend_adjoint(force,mapping,nodes=72):
 lo,hi,t=mapping;y=np.asarray(force);v=np.arange(y.shape[1])[None];out=np.zeros((nodes,y.shape[1],3))
 np.add.at(out,(lo,v),(1-t[:,:,None])*y);np.add.at(out,(hi,v),t[:,:,None]*y)
 return out

def oscillation(dense,limit_mm=3.):
 x=np.asarray(dense)
 if not np.isfinite(x).all():return dict(passed=False,maximum_adjacent_mm=None,limit_mm=limit_mm)
 maximum=float(np.linalg.norm(np.diff(x,axis=0),axis=2).max()*1000)
 return dict(passed=maximum<=limit_mm+1e-8,maximum_adjacent_mm=maximum,limit_mm=limit_mm)

def posed(data,dense,index,mapping=None):
 if index<82:base,mat,w=data['base'][index],data['mat'][index],data['weight'][index]
 else:base,mat,w=data['front_base'],data['front_mat'],data['front_weight']
 m=decode(w[None]) if mapping is None else tuple(a[index:index+1] for a in mapping)
 return base+np.einsum('nij,nj->ni',mat,blend(dense,m)[0])
