"""Lexicographic feasibility and minimum-step LPs with meaningful cost scale."""
import numpy as np
from scipy import sparse
from scipy.optimize import linprog
def step(A,rhs,trust,relaxed=None):
 m,n=A.shape
 relaxed=np.ones(m) if relaxed is None else np.asarray(relaxed,float)
 active=np.unique(A.indices);A=A[:,active];size=len(active)
 opts={'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8,'ipm_optimality_tolerance':1e-9}
 phase1=sparse.hstack([A,-relaxed[:,None]],format='csr')
 first=linprog(np.r_[np.zeros(size),1.],A_ub=phase1,b_ub=rhs,bounds=[(-trust,trust)]*size+[(0,None)],method='highs-ds',options=opts)
 if not first.success:raise RuntimeError(('Phase I',first.message))
 slack=max(0.,float(first.x[-1]));print('R43_LP_PHASE_I',size,m,slack,flush=True);eye=sparse.eye(size,format='csr')
 matrix=sparse.vstack([sparse.hstack([A,sparse.csr_matrix((m,size))]),sparse.hstack([eye,-eye]),sparse.hstack([-eye,-eye])],format='csr')
 second=linprog(np.r_[np.zeros(size),np.ones(size)],A_ub=matrix,b_ub=np.r_[rhs+relaxed*(slack+1e-7),np.zeros(size*2)],bounds=[(-trust,trust)]*size+[(0,trust)]*size,method='highs-ds',options=opts)
 if not second.success:raise RuntimeError(('Phase II',second.message))
 result=np.zeros(n);result[active]=second.x[:size]
 return result,slack
