"""Lexicographic feasibility LP and sparse minimum-norm constrained step."""
import numpy as np
from scipy import sparse
from scipy.optimize import linprog
from scipy.sparse.linalg import factorized

def make_factor(A,rho):
 n=A.shape[1];a=1+rho
 if A.shape[0]<n:
  f=factorized(sparse.eye(A.shape[0],format='csc')+(rho/a)*(A@A.T).tocsc())
  return lambda v:v/a-(rho/a**2)*A.T@f(A@v)
 return factorized(a*sparse.eye(n,format='csc')+rho*(A.T@A).tocsc())

def minimum_norm(A,upper,trust,warm,tolerance=2e-6,maxiter=3000):
 from scipy.optimize import minimize
 def objective(y):
  v=A.T@y;x=np.clip(-v,-trust,trust)
  return float(-.5*x@x-v@x+upper@y),upper-A@x
 fit=minimize(objective,np.zeros(A.shape[0]),jac=True,method='L-BFGS-B',bounds=[(0,None)]*A.shape[0],options={'maxiter':maxiter,'maxls':50,'ftol':1e-14,'gtol':1e-9,'maxcor':30})
 value=np.clip(-A.T@fit.x,-trust,trust);residual=float(np.max(A@value-upper,initial=0))
 print('R43_QP_DUAL',fit.nit,residual,fit.message,flush=True)
 # The nonlinear line search independently enforces every hard gate.
 if residual>.02:raise RuntimeError(('Minimum norm QP residual',residual))
 return value

def step(A,rhs,trust,relaxed=None):
 m,n=A.shape;relaxed=np.ones(m) if relaxed is None else np.asarray(relaxed,float)
 active=np.unique(A.indices);A=A[:,active];size=len(active)
 first=linprog(np.r_[np.zeros(size),1.],A_ub=sparse.hstack([A,-relaxed[:,None]],format='csr'),b_ub=rhs,bounds=[(-trust,trust)]*size+[(0,None)],method='highs-ds',options={'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8})
 if not first.success:raise RuntimeError(('Phase I',first.message))
 slack=max(0.,float(first.x[-1]));print('R43_LP_PHASE_I',size,m,slack,flush=True)
 value=minimum_norm(A,rhs+relaxed*(slack+1e-7),trust,first.x[:size]);print('R43_MINIMUM_NORM_QP',flush=True)
 result=np.zeros(n);result[active]=value
 return result,slack
