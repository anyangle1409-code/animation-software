"""First-party bounded primal-dual proposals for the unchanged repair objective.

Iterations do not certify an optimum. An independent hard-row projection and
original-row reconstruction precede any proposal return. Actual geometry still
requires the unchanged nonlinear/native gates and owner visual review.
"""
import time
import numpy as np
from scipy import sparse
from original_review_r51_lp import reduce_problem

def project_hard(x,H,b,trust):
 original=x.copy();x=np.clip(x,-trust,trust)
 if float(np.max(H@x-b,initial=0))<=1e-7:return x,float(abs(x-original).max(initial=0))
 H=H.tocsr();correction=np.zeros(H.shape[0]);box_correction=np.zeros(len(x));started=time.monotonic()
 rows=[(H.indices[H.indptr[j]:H.indptr[j+1]],H.data[H.indptr[j]:H.indptr[j+1]]) for j in range(H.shape[0])]
 norm=np.array([float(v@v) for _,v in rows])
 if np.any((norm<1e-24)&(b<0)):raise RuntimeError('Uneditable infeasible hard row')
 for cycle in range(2000):
  for j,(ids,values) in enumerate(rows):
   if norm[j]<1e-24:continue
   value=max(0.,correction[j]+float(values@x[ids]-b[j])/norm[j])
   x[ids]-=(value-correction[j])*values;correction[j]=value
  y=x+box_correction;next_x=np.clip(y,-trust,trust);box_correction=y-next_x;x=next_x
  error=float(np.max(H@x-b,initial=0))
  if error<=1e-7:return x,float(abs(x-original).max(initial=0))
  if time.monotonic()-started>4.:break
 raise RuntimeError(('Hard-row projection did not converge within budget',error))

def propose(B,rhs,weights,soft,trust,iterations=800):
 if not np.isfinite(B.data).all() or not np.isfinite(rhs).all() or not np.isfinite(weights).all() or trust<=0:
  raise ValueError('Nonfinite or invalid proposal input')
 started=time.monotonic();r=reduce_problem(B,rhs,weights,soft,trust);n=B.shape[1]
 K=r['matrix'][:,:n].tocsr();KT=K.T.tocsr();gradient=r['cost'][:n]
 sigma=.95/np.maximum(np.asarray(abs(K).sum(1)).ravel(),1e-12)
 tau=.95/np.maximum(np.asarray(abs(K).sum(0)).ravel(),1e-12)
 x=np.zeros(n);bar=x.copy();dual=np.zeros(K.shape[0]);average=np.zeros(n)
 upper=np.r_[np.full(len(r['hard']),np.inf),r['cost'][n:]]
 for i in range(iterations):
  dual=np.clip(dual+sigma*(K@bar-r['rhs']),0.,upper)
  next_x=np.clip(x-tau*(KT@dual+gradient),-trust,trust)
  bar=2*next_x-x;x=next_x;average+=(x-average)/(i+1)
  if (i+1)%20==0:
   if n>100 and (i+1)%100==0:print("R51_BOUNDED_ITERATIONS",i+1,round(time.monotonic()-started,3),flush=True)
   if time.monotonic()-started>12.:break
 candidates=[average,x];best=None
 projection_failures=[]
 for candidate in candidates:
  try:corrected,distance=project_hard(candidate,B[r['hard']],rhs[r['hard']],trust)
  except RuntimeError as error:
   projection_failures.append(str(error));continue
  objective=float(weights@np.maximum(B[soft]@corrected-rhs[soft],0))
  if best is None or objective<best[0]:best=(objective,corrected,distance)
 if best is None:raise RuntimeError(("No hard-feasible bounded proposal",projection_failures))
 objective,x,distance=best
 hard_error=float(np.max(B[r['hard']]@x-rhs[r['hard']],initial=0));bound_error=float(np.max(abs(x)-trust,initial=0))
 if not np.isfinite(x).all() or hard_error>1e-6 or bound_error>1e-8:raise RuntimeError('Proposal verification failed')
 return x,dict(proposal_optimal=False,algorithm='bounded_diagonal_primal_dual_then_verified_hard_projection',requested_iterations=iterations,iterations=i+1,projection_failures=projection_failures,seconds=time.monotonic()-started,hard_violation=hard_error,bound_violation=bound_error,projection_max_control_change_mm=distance,objective=objective,initial_objective=float(weights@np.maximum(-rhs[soft],0)),original_rows=B.shape[0],iterated_rows=K.shape[0])
