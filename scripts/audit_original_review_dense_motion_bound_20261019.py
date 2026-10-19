"""Temporal-resolution experiment on one vertex; no candidate/model changes."""
from pathlib import Path
import sys,json
import numpy as np
from scipy.optimize import linprog
sys.path.insert(0,str(Path(__file__).resolve().parent))
from original_review_r43_sampling import basis,DENSE
if len(sys.argv)!=4:raise SystemExit('usage: audit SOURCE.npz SOLUTION.npz OUTPUT.json')
source,solution,output=map(Path,sys.argv[1:])
with np.load(source) as z:d={k:z[k] for k in z.files}
delta=np.load(solution)['delta'];v=21317;B=basis();w=d['weight'][:41,:,v]
curve=np.r_[np.zeros((1,7)),B];diff=np.diff(curve,axis=0);den=np.maximum((diff*diff).sum(1),1e-30)
weights=np.zeros((41,72));maxerr=0.
for s in range(41):
 t=np.clip(np.einsum('dk,dk->d',w[s]-curve[:-1],diff)/den,0,1);err=np.linalg.norm(curve[:-1]+t[:,None]*diff-w[s],axis=1);j=err.argmin();maxerr=max(maxerr,float(err[j]));weights[s,j]=1-t[j];weights[s,j+1]=t[j]
assert maxerr<1e-10
angle_nodes=np.r_[95.,DENSE];active=np.flatnonzero(~np.isin(angle_nodes,[95.,110.,166.]))
base=d['base'][:41,v].astype(float)*1000;mat=d['mat'][:41,v]
T=np.einsum('sk,sij->sikj',weights[:,active],mat).reshape(41,3,-1)
A=np.diff(T,n=2,axis=0);ba=np.diff(base,n=2,axis=0);limits=np.linalg.norm(ba,axis=1);target=np.einsum('ij,j->i',mat[25],w[25]@(delta[:,v]*1000));n=T.shape[-1];c=np.r_[np.zeros(n),1.]
caps=np.abs(np.linalg.solve(mat[25],target));caps=caps/np.linalg.norm(caps)*45.
out={'diagnostic_only':True,'vertex':v,'fixed_integer_controls':[95.,110.,166.],'editable_integer_controls':angle_nodes[active].tolist(),'coefficient_reconstruction_error':maxerr,'inscribed_material_box_axis_caps_mm':caps.tolist(),'caveats':['Single vertex only','Same affine poses, but extra temporal degrees of freedom','Inscribed axis box guarantees each temporal control vector norm <=45mm','No spatial folds/contact/outline/other vertices/native acceptance'],'cases':{}}
for prevent in (False,True):
 rows=[];rhs=[]
 def cut(s,u):rows.append(np.r_[u@A[s],-1.]);rhs.append(limits[s]-u@ba[s])
 for s in range(len(A)):
  for u in np.r_[np.eye(3),-np.eye(3)]:cut(s,u)
 if prevent:
  for s in range(18):rows.append(np.r_[-T[s,0],0.]);rhs.append(0.)
 eq=np.c_[T[25],np.zeros(3)];history=[]
 for iteration in range(150):
  M=np.array(rows);b=np.array(rhs);r=linprog(c,A_ub=M,b_ub=b,A_eq=eq,b_eq=target,bounds=[(-float(caps[j%3]),float(caps[j%3])) for j in range(n)]+[(0.,None)],method='highs',options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
  if not r.success:raise RuntimeError(r.message)
  acc=ba+np.einsum('sij,j->si',A,r.x[:-1]);excess=np.linalg.norm(acc,axis=1)-limits;actual=float(excess.max());lb=float(r.fun);history.append({'iteration':iteration,'lower_mm':lb,'upper_mm':actual})
  control=r.x[:-1].reshape(-1,3);length=np.linalg.norm(control,axis=1);maximum=float(length.max())
  if (actual-lb<1e-7 or actual<=.45+1e-8) and maximum<=45.+1e-7:break
  for s in np.flatnonzero(excess>lb+1e-8):cut(int(s),acc[s]/np.linalg.norm(acc[s]))
  for j in np.flatnonzero(length>45.+1e-8):
   row=np.zeros(n+1);row[3*j:3*j+3]=control[j]/length[j];rows.append(row);rhs.append(45.)
 coordinates=np.zeros((72,3));coordinates[active]=r.x[:-1].reshape(-1,3);inc=np.einsum('sij,j->si',T,r.x[:-1]);station=c-M.T@r.ineqlin.marginals-eq.T@r.eqlin.marginals-r.lower.marginals-r.upper.marginals
 rec={'prevents_early_outward_increment':prevent,'lp_lower_mm':lb,'exact_norm_motion_excess_mm':actual,'meets_motion_guard':actual<=.5+1e-7,'cone_gap_mm':actual-lb,'max_control_vector_norm_mm':float(np.linalg.norm(coordinates,axis=1).max()),'marked_world_change_mm':float(np.linalg.norm(inc[25]-target)),'max_early_outward_increment_mm':float((-inc[:18,0]).max()),'primal_violation_mm':float(np.maximum(M@r.x-b,0).max()),'dual_stationarity_max':float(abs(station).max()),'iterations':iteration+1,'history':history,'sampled_world_increment_mm':inc.tolist()}
 out['cases'][str(prevent)]=rec;print({k:v for k,v in rec.items() if k not in ('history','sampled_world_increment_mm')},flush=True)
out['control_coordinates_mm_last_case']=coordinates.tolist()
out['additional_rejection_checks']={'maximum_neighbor_integer_degree_change_mm':float(np.linalg.norm(np.diff(coordinates,axis=0),axis=1).max()),'curve_is_usable':False,'reason':'Large oscillations between the 41 sampled poses. Passing sampled acceleration alone is insufficient; reject this curve.'}
assert np.linalg.norm(coordinates,axis=1).max()<=45.+1e-7
assert np.max(abs(coordinates[np.isin(angle_nodes,[95.,110.,166.])]))==0.
assert actual<=.5+1e-7 and np.linalg.norm(inc[25]-target)<1e-8
assert (-inc[:18,0]).max()<1e-8
output.write_text(json.dumps(out,indent=2)+'\n')
