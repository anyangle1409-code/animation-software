"""Same feasibility/minimum-L1 field problems, scaling the projected constraints consistently."""
import numpy as np
from scipy import sparse
from scipy.optimize import linprog

def reset_cache():pass

def optimize(cost,A,rhs,bounds):
 options={'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8}
 result=linprog(cost,A_ub=A,b_ub=rhs,bounds=bounds,method='highs-ipm',options=options)
 if not result.success:raise RuntimeError(result.message)
 if np.max(A@result.x-rhs,initial=0)>1e-6:raise RuntimeError('LP returned an infeasible proposal')
 return result

def step(A,rhs,trust,relaxed=None,profile_opt_tolerance=1e-7):
 m,n=A.shape;relaxed=np.ones(m) if relaxed is None else np.asarray(relaxed,float)
 active=np.unique(A.indices);A=A[:,active];size=len(active)
 # Rescale rows and their slack coefficients together: identical LP,
 # better numerical conditioning after the smooth-field projection.
 row_scale=1/np.maximum(np.asarray(abs(A).sum(axis=1)).ravel(),1e-14)
 A=(sparse.diags(row_scale)@A).tocsr();rhs=rhs*row_scale;relaxed=relaxed*row_scale
 first=optimize(np.r_[np.zeros(size),1.],sparse.hstack([A,-relaxed[:,None]],format='csr'),rhs,[(-trust,trust)]*size+[(0,None)])
 slack=max(0.,float(first.x[-1]));print('R45_LP_PHASE_I',size,m,slack,flush=True)
 # x=u-v with nonnegative bounded parts is the same minimum-L1
 # problem, without two extra absolute-value constraints per control.
 matrix=sparse.hstack([A,-A],format='csr')
 second=optimize(np.ones(size*2),matrix,rhs+relaxed*(slack+profile_opt_tolerance),[(0,trust)]*(size*2))
 result=np.zeros(n);result[active]=second.x[:size]-second.x[size:]
 return result,slack
