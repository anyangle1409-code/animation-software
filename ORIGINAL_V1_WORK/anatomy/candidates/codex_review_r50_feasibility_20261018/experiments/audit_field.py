import sys,json,time
from pathlib import Path
import numpy as np
from scipy.sparse.linalg import lsqr
sys.path[:0]=['r47-audit/scripts','r48-work/scripts']
from original_review_r46_field import material_field
from original_review_r48_outline import silhouette
start=time.monotonic()
with np.load('r49-review/extracted/tmp/r49-response/source.npz') as z:d={k:z[k] for k in z.files}
old=np.load('r47-review/native/tmp/r47-response/solved.npz')['delta']
current=np.load('r49-review/extracted/tmp/r49-response/solved.npz')['delta']
free=d['r49_allowed'];F=material_field(d['rest'],free,d['faces'])
print('FIELD',F.shape,F.nnz,flush=True)
y=old[free].ravel()*1000
fit=lsqr(F,y,atol=1e-7,btol=1e-7,iter_lim=200)
delta=np.zeros_like(old);delta[free]=(F@fit[0]).reshape(-1,3)*.001
base=d['base'][25];mat=d['mat'][25];w=d['weight'][25]
def pose(x):return base+np.einsum('nij,nj->ni',mat,np.einsum('kn,knj->nj',w,x))
def outline(x):
 p=pose(x);rows=[]
 for side in ('l','r'):
  sign=-1 if side=='l' else 1
  for n in (np.array([sign,0.,0.]),np.array([sign,-1.,0.])/np.sqrt(2)):
   for h in np.arange(1.18,1.62,.005):rows.append(silhouette(p,d['faces'],side,n,h)[0])
 return np.array(rows)
goal=outline(old)
r={'seconds':time.monotonic()-start,'lsqr_status':fit[1],'iterations':fit[2],'target_material_mm':float(np.linalg.norm(old,axis=2).max()*1000),'current_material_mm':float(np.linalg.norm(current,axis=2).max()*1000),'field_fit_residual_max_mm':float(np.linalg.norm(delta-old,axis=2).max()*1000),'field_projected_outline_error_mm':float(abs(outline(delta)-goal).max()*1000),'current_outline_error_mm':float(abs(outline(current)-goal).max()*1000),'controls_max_abs_mm':float(abs(fit[0]).max()),'field_projected_material_max_mm':float(np.linalg.norm(delta,axis=2).max()*1000)}
print(json.dumps(r,indent=2),flush=True)
Path('r50-work/diagnostics/field_audit.json').write_text(json.dumps(r,indent=2)+'\n')
np.savez_compressed('r50-work/diagnostics/projected.npz',delta=delta)
