"""Lexicographic feasibility LP and sparse minimum-norm constrained step."""
import numpy as np
from scipy import sparse
from scipy.optimize import linprog
from scipy.sparse.linalg import factorized

def minimum_norm(A,upper,trust,warm,tolerance=2e-6,maxiter=30000):
 n=A.shape[1]; C=sparse.vstack([A,sparse.eye(n)],format='csc');u=np.r_[upper,np.full(n,trust)];l=np.r_[np.full(len(upper),-np.inf),np.full(n,-trust)]
 x=warm.copy();z=np.clip(C@x,l,u);y=np.zeros(len(u));rho=1.;identity=sparse.eye(n,format='csc');factor=factorized(identity+rho*(C.T@C))
 for iteration in range(maxiter):
  x=factor(rho*C.T@(z-y));cx=C@x;old=z;z=np.clip(1.6*cx-.6*old+y,l,u);y+=1.6*cx-.6*old-z
  if iteration%100==0:
   primal=np.max(abs(cx-z),initial=0);dual=np.max(abs(rho*C.T@(z-old)),initial=0)
   if max(primal,dual)<tolerance:return x
   if iteration and iteration%1000==0:
    newrho=rho*(2 if primal>10*dual else .5 if dual>10*primal else 1)
    if newrho!=rho:y*=rho/newrho;rho=newrho;factor=factorized(identity+rho*(C.T@C))
 raise RuntimeError(('Minimum norm QP did not converge',primal,dual))

def step(A,rhs,trust,relaxed=None):
 m,n=A.shape;relaxed=np.ones(m) if relaxed is None else np.asarray(relaxed,float)
 active=np.unique(A.indices);A=A[:,active];size=len(active)
 first=linprog(np.r_[np.zeros(size),1.],A_ub=sparse.hstack([A,-relaxed[:,None]],format='csr'),b_ub=rhs,bounds=[(-trust,trust)]*size+[(0,None)],method='highs-ds',options={'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8})
 if not first.success:raise RuntimeError(('Phase I',first.message))
 slack=max(0.,float(first.x[-1]));print('R43_LP_PHASE_I',size,m,slack,flush=True)
 value=minimum_norm(A,rhs+relaxed*(slack+1e-7),trust,first.x[:size]);print('R43_MINIMUM_NORM_QP',flush=True)
 result=np.zeros(n);result[active]=value
 return result,slack
