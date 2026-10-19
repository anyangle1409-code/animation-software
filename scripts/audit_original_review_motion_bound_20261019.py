"""Convex single-vertex motion bound; no model or candidate is changed."""
from pathlib import Path
import numpy as np,json,sys
from scipy.optimize import linprog
if len(sys.argv)!=4:raise SystemExit('usage: audit SOURCE.npz SOLUTION.npz OUTPUT.json')
source,solution,output=map(Path,sys.argv[1:])
with np.load(source) as z:d={k:z[k] for k in z.files}
delta=np.load(solution)['delta'];v=21317
active=np.flatnonzero(d['r47_allowed'][:,v]);x0=(delta[active,v]*1000).ravel()
base=d['base'][:41,v].astype(float)*1000
T=np.einsum('sk,sij->sikj',d['weight'][:41,:,v],d['mat'][:41,v]).reshape(41,3,21)
cols=(active[:,None]*3+np.arange(3)).ravel();T=T[:,:,cols]
A=np.diff(T,n=2,axis=0);ba=np.diff(base,n=2,axis=0);limits=np.linalg.norm(ba,axis=1)
target=T[25]@x0;n=len(x0);c=np.r_[np.zeros(n),1.]
results={'vertex':v,'units':'mm','diagnostic_only':True,'caveat':'Per-vertex point constraints are not the whole-outline acceptance test. Coordinate box45mm is a relaxation of the unchanged norm45mm cap. No spatial/native acceptance is inferred.','cases':{}}
for policy in ('exact_marked_xyz','within1mm_marked_xyz_box','within1mm_marked_x','unconstrained_marked'):
 rows=[];rhs=[];history=[]
 def cut(s,u):rows.append(np.r_[u@A[s],-1.]);rhs.append(limits[s]-u@ba[s])
 for s in range(len(A)):
  for u in np.r_[np.eye(3),-np.eye(3)]:cut(s,u)
 eq=beq=None
 if policy=='exact_marked_xyz':eq=np.c_[T[25],np.zeros(3)];beq=target
 elif policy!='unconstrained_marked':
  axes=range(3) if policy=='within1mm_marked_xyz_box' else (0,)
  for axis in axes:
   for sign in (-1,1):rows.append(np.r_[sign*T[25,axis],0.]);rhs.append(sign*target[axis]+1.)
 for iteration in range(120):
  M=np.array(rows);b=np.array(rhs)
  r=linprog(c,A_ub=M,b_ub=b,A_eq=eq,b_eq=beq,bounds=[(-45.,45.)]*n+[(0.,None)],method='highs',options={'dual_feasibility_tolerance':1e-9,'primal_feasibility_tolerance':1e-9})
  if not r.success:raise RuntimeError((policy,r.message))
  acc=ba+np.einsum('sij,j->si',A,r.x[:-1]);excess=np.linalg.norm(acc,axis=1)-limits;actual=float(excess.max());lb=float(r.fun)
  history.append({'iteration':iteration,'lp_lower_bound_mm':lb,'exact_norm_excess_mm':actual,'rows':len(rows)})
  if actual-lb<1e-7:break
  for s in np.flatnonzero(excess>lb+1e-8):cut(int(s),acc[s]/np.linalg.norm(acc[s]))
 # Check primal and dual LP residuals independently, including variable bounds.
 dual=r.ineqlin.marginals;deq=np.zeros(n+1) if eq is None else eq.T@r.eqlin.marginals
 station=c-M.T@dual-deq-r.lower.marginals-r.upper.marginals
 objective_dual=float(b@dual+np.sum(-45*r.lower.marginals[:n])+np.sum(45*r.upper.marginals[:n])+(0 if eq is None else beq@r.eqlin.marginals))
 info={'converged_cone':actual-lb<1e-7,'minimum_motion_excess_lower_mm':lb,'exact_trial_motion_excess_upper_mm':actual,'unchanged_guard_mm':.5,'meets_motion_guard':actual<=.5+1e-7,'marked_world_change_mm':(T[25]@r.x[:-1]-target).tolist(),'max_source_vector_norm_mm':float(np.linalg.norm(r.x[:-1].reshape(-1,3),axis=1).max()),'lp_primal_violation_mm':float(np.maximum(M@r.x-b,0).max()),'lp_dual_stationarity_max':float(abs(station).max()),'lp_duality_gap_mm':float(r.fun-objective_dual),'history':history}
 results['cases'][policy]=info;print(policy,{k:v for k,v in info.items() if k!='history'},flush=True)
output.write_text(json.dumps(results,indent=2)+'\n')
