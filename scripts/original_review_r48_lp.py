"""Return the optimal feasible contour step without a costly L1 tie-break.

Only shape rows receive slack. Every nonlinear safety gate is still checked
by the caller before accepting a step; no model test is changed.
"""
import numpy as np
from scipy import sparse
from scipy.optimize import linprog

def reset_cache():pass

def step(A,rhs,trust,relaxed=None,profile_opt_tolerance=1e-7):
    m,n=A.shape
    relaxed=np.ones(m) if relaxed is None else np.asarray(relaxed,float)
    active=np.unique(A.indices);local=A[:,active];size=len(active)
    scale=1/np.maximum(np.asarray(abs(local).sum(axis=1)).ravel(),1e-14)
    local=(sparse.diags(scale)@local).tocsr()
    matrix=sparse.hstack([local,-(relaxed*scale)[:,None]],format='csr')
    result=linprog(np.r_[np.zeros(size),1.],A_ub=matrix,b_ub=rhs*scale,
        bounds=[(-trust,trust)]*size+[(0,None)],method='highs-ipm',
        options={'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8})
    if not result.success:raise RuntimeError(result.message)
    if np.max(matrix@result.x-rhs*scale,initial=0)>1e-6:raise RuntimeError('R48 LP returned an infeasible proposal')
    movement=np.zeros(n);movement[active]=result.x[:-1]
    slack=max(0.,float(result.x[-1]))
    print('R48_LP_FEASIBILITY',size,m,slack,flush=True)
    return movement,slack
