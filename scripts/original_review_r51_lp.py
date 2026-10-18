"""Exact box presolve for R50's weighted-hinge search objective.

Only soft epigraph rows whose hinge branch cannot change inside the trust box
are eliminated. Their constant/linear objective contributions are retained.
Every hard outline/material row remains. This is a proposal calculation only;
it does not accept a model or relax any final nonlinear/native check.
"""
import json,os,time
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.optimize import linprog

def reduce_problem(B,rhs,weights,soft,trust):
 m,n=B.shape
 is_soft=np.zeros(m,bool);is_soft[soft]=True
 radius=trust*np.asarray(abs(B).sum(axis=1)).ravel()
 margin=1e-9*np.maximum(1.,np.abs(rhs)+radius)
 linear=np.flatnonzero(is_soft&(-radius-rhs>margin))
 zero=np.flatnonzero(is_soft&(radius-rhs< -margin))
 remains=is_soft.copy();remains[linear]=False;remains[zero]=False
 mixed=np.flatnonzero(remains);hard=np.flatnonzero(~is_soft)
 weight_by_row=np.zeros(m);weight_by_row[soft]=weights
 keep=np.r_[hard,mixed]
 slack=sparse.coo_matrix((-np.ones(len(mixed)),(len(hard)+np.arange(len(mixed)),np.arange(len(mixed)))),shape=(len(keep),len(mixed))).tocsr()
 linear_cost=np.asarray(B[linear].T@weight_by_row[linear]).ravel()
 return dict(matrix=sparse.hstack([B[keep],slack],format='csr'),rhs=rhs[keep],
  cost=np.r_[linear_cost,weight_by_row[mixed]],constant=-float(weight_by_row[linear]@rhs[linear]),
  mixed=mixed,hard=hard,linear=linear,zero=zero)

def step(A,rhs,trust,labels,scales):
 soft=np.flatnonzero([not name.startswith(('profile_','material_bound','dense_material_bound')) for name in labels])
 controls=np.unique(A.indices);B=A[:,controls]
 units={'area_upper':1e-5,'area_lower':1e-5,'orientation':1e-5,'contact':.001,'front':1.,'posterior_normal_cone':1.,'back_motion':.001,'back_motion_cone':.001}
 weights=np.array([scales[j]/units.get(labels[j],1.) for j in soft]);weights/=max(float(np.median(weights[weights>0])),1e-15)
 r=reduce_problem(B,rhs,weights,soft,trust)
 report=dict(original_rows=A.shape[0],reduced_rows=r['matrix'].shape[0],controls=len(controls),original_slacks=len(soft),remaining_slacks=len(r['mixed']),linear_rows=len(r['linear']),zero_rows=len(r['zero']),trust_mm=trust)
 directory=os.environ.get('HGPT_R51_LP_DIAGNOSTICS')
 def record():
  if directory:
   p=Path(directory);p.mkdir(exist_ok=True,parents=True);(p/'latest_linear_status.json').write_text(json.dumps(report,indent=2)+'\n')
 report['status']='SOLVING';record();print('R51_EXACT_PRESOLVE',json.dumps(report),flush=True)
 start=time.monotonic()
 result=linprog(r['cost'],A_ub=r['matrix'],b_ub=r['rhs'],bounds=[(-trust,trust)]*len(controls)+[(0,None)]*len(r['mixed']),method='highs-ipm',options={'primal_feasibility_tolerance':1e-8,'dual_feasibility_tolerance':1e-8,'time_limit':45.})
 report.update(seconds=time.monotonic()-start,solver_status=int(result.status),solver_message=result.message)
 if not result.success:
  report['status']='FAILED';record();print('R51_LINEAR_FAILED',json.dumps(report),flush=True);raise RuntimeError(result.message)
 x=result.x[:len(controls)]
 hard_error=float(np.max(B[r['hard']]@x-rhs[r['hard']],initial=0))
 bound_error=float(np.max(abs(x)-trust,initial=0))
 objective=float(weights@np.maximum(B[soft]@x-rhs[soft],0.))
 equivalent=float(result.fun+r['constant'])
 if not np.isfinite(result.x).all() or hard_error>1e-6 or bound_error>1e-8 or abs(objective-equivalent)>1e-7*max(1.,abs(objective)):
  raise RuntimeError(('Original LP reconstruction failed',hard_error,bound_error,objective,equivalent))
 movement=np.zeros(A.shape[1]);movement[controls]=x
 report.update(status='SOLVED',original_objective=objective,equivalent_objective=equivalent,original_hard_violation=hard_error,trust_violation=bound_error);record();print('R51_LINEAR_SOLVED',json.dumps(report),flush=True)
 return movement,objective
