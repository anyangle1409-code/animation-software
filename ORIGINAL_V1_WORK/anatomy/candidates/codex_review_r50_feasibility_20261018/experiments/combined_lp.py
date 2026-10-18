"""Throwaway LP probe; hard outline/material, soft internal repair residuals."""
import numpy as np
from scipy import sparse
from scipy.optimize import linprog
scales=None;labels=None

def reset_cache():pass

def step(A,rhs,trust,relaxed=None,profile_opt_tolerance=1e-7):
 m,n=A.shape;soft=np.flatnonzero(relaxed);hard=np.flatnonzero(~relaxed.astype(bool));keep=np.unique(A.indices);B=A[:,keep];size=len(keep)
 C=sparse.coo_matrix((-np.ones(len(soft)),(soft,np.arange(len(soft)))),shape=(m,len(soft))).tocsr()
 units={'area_upper':1e-5,'area_lower':1e-5,'orientation':1e-5,'contact':.001,'front':1.,'posterior_normal_cone':1.,'back_motion':.001,'back_motion_cone':.001}
 w=np.array([scales[j]/units.get(labels[j],1.) for j in soft]);w/=max(np.median(w[w>0]),1e-15)
 cost=np.r_[np.zeros(size),w]
 print('R50_COMBINED_LP_BEGIN',m,size,len(soft),flush=True)
 res=linprog(cost,A_ub=sparse.hstack([B,C],format='csr'),b_ub=rhs,bounds=[(-trust,trust)]*size+[(0,None)]*len(soft),method='highs-ipm',options={'primal_feasibility_tolerance':1e-8,'dual_feasibility_tolerance':1e-8,'time_limit':90.})
 if not res.success:raise RuntimeError(res.message)
 if np.max(sparse.hstack([B,C])@res.x-rhs,initial=0)>1e-6:raise RuntimeError('Infeasible LP result')
 x=np.zeros(n);x[keep]=res.x[:size]
 print('R50_COMBINED_LP_END',res.fun,flush=True)
 return x,float(res.fun)
