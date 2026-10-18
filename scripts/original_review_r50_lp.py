"""Internal unsafe-surface repair proposals with hard outline/material bounds.

The slack objective proposes search steps only. It is never a model acceptance
test; all unchanged native and nonlinear checks still run on the retained state.
"""
import numpy as np
from scipy import sparse
from scipy.optimize import linprog

def step(A,rhs,trust,labels,scales):
    soft=np.flatnonzero([not name.startswith(('profile_','material_bound','dense_material_bound')) for name in labels])
    m,n=A.shape
    controls=np.unique(A.indices)
    B=A[:,controls]
    slack=sparse.coo_matrix((-np.ones(len(soft)),(soft,np.arange(len(soft)))),shape=(m,len(soft))).tocsr()
    units={'area_upper':1e-5,'area_lower':1e-5,'orientation':1e-5,'contact':.001,'front':1.,'posterior_normal_cone':1.,'back_motion':.001,'back_motion_cone':.001}
    weights=np.array([scales[j]/units.get(labels[j],1.) for j in soft])
    weights/=max(float(np.median(weights[weights>0])),1e-15)
    matrix=sparse.hstack([B,slack],format='csr')
    print('R50_COMBINED_LP_BEGIN',m,len(controls),len(soft),flush=True)
    result=linprog(np.r_[np.zeros(len(controls)),weights],A_ub=matrix,b_ub=rhs,
        bounds=[(-trust,trust)]*len(controls)+[(0,None)]*len(soft),method='highs-ipm',
        options={'primal_feasibility_tolerance':1e-8,'dual_feasibility_tolerance':1e-8,'time_limit':90.})
    if not result.success:raise RuntimeError(result.message)
    if not np.isfinite(result.x).all() or np.max(matrix@result.x-rhs,initial=0)>1e-6:
        raise RuntimeError('LP returned a nonfinite or infeasible proposal')
    movement=np.zeros(n);movement[controls]=result.x[:len(controls)]
    print('R50_COMBINED_LP_END',result.fun,flush=True)
    return movement,float(result.fun)
