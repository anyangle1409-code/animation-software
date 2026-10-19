"""Read-only interpolation ablation. No candidate, model, or prior test edits."""
from pathlib import Path
import sys,json
import numpy as np
from scipy.interpolate import PchipInterpolator
sys.path.insert(0,str(Path(__file__).resolve().parent))
from original_review_r43_sampling import basis,KEYS,DENSE,hats
if len(sys.argv)!=4:raise SystemExit('usage: audit SOURCE.npz SOLUTION.npz OUTPUT.json')
source,solution,output=map(Path,sys.argv[1:])
with np.load(source) as z:d={k:z[k] for k in z.files}
delta=np.load(solution)['delta'];rest=d['rest'];B=basis()
mask=(abs(rest[:,0])>.08)&(abs(rest[:,0])<.25)&(rest[:,2]>1.27)&(rest[:,2]<1.49)&(rest[:,1]>.025);ids=np.flatnonzero(mask)
base=d['base'][:41,ids].astype(float);a=d['mat'][:41][:,ids];old=d['weight'][:41][:,:,ids]
nodes=np.r_[95.,KEYS];values=np.concatenate([np.zeros_like(delta[:1]),delta])
pc=PchipInterpolator(nodes,values,axis=0,extrapolate=False)(DENSE)
linear=np.einsum('dk,knj->dnj',hats(DENSE,KEYS),delta)
results={'method':'Change only interpolation of R51 increments in exact affine response. R41 baseline and poses fixed. Diagnostic probe, no native rerender or acceptance.','states':{}}
# Infer exact active dense interval from the seven stored coefficient values.
# This matches the renderer's piecewise-linear sampling of integer-degree keys.
weights=np.concatenate([np.zeros((1,7)),B]);angles=np.r_[95.,DENSE]
diff=np.diff(weights,axis=0);den=(diff*diff).sum(1);den=np.maximum(den,1e-30)
recovered=[];err=0.
for s in range(41):
 w=old[s].T
 t=np.clip(np.einsum('vdk,dk->vd',w[:,None]-weights[:-1],diff)/den,0,1)
 residual=np.linalg.norm(weights[:-1][None]+t[:,:,None]*diff[None]-w[:,None],axis=2)
 j=residual.argmin(1);alpha=t[np.arange(len(ids)),j];err=max(err,float(residual[np.arange(len(ids)),j].max()))
 recovered.append((j,alpha))
results['coefficient_reconstruction_max_error']=err;assert err<1e-10
for name,curve in [('current_cubic',np.einsum('dk,knj->dnj',B,delta)),('pchip_probe',pc),('linear_probe',linear)]:
 cv=np.concatenate([np.zeros_like(delta[:1]),curve])[:,ids];adds=[]
 for s,(j,t) in enumerate(recovered):
  inc=(1-t[:,None])*cv[j,np.arange(len(ids))]+t[:,None]*cv[j+1,np.arange(len(ids))]
  adds.append(np.einsum('nij,nj->ni',a[s],inc))
 add=np.array(adds);now=base+add
 acc=np.linalg.norm(np.diff(now,n=2,axis=0),axis=2);prior=np.linalg.norm(np.diff(base,n=2,axis=0),axis=2)
 signs=np.sign(rest[ids,0]);outward=add[:,:,0]*signs
 row={'max_motion_excess_mm':float((acc-prior).max()*1000),'max_outward_before110_mm':float(outward[:18].max()*1000),'max_dense_material_mm':float(np.linalg.norm(curve,axis=2).max()*1000),'max_marked_geometry_change_from_cubic_mm':None,'timeline_max_outward_mm':[float(x.max()*1000) for x in outward]}
 if name=='current_cubic':ref=now;row['max_marked_geometry_change_from_cubic_mm']=0.
 else:row['max_marked_geometry_change_from_cubic_mm']=float(np.linalg.norm(now[25]-ref[25],axis=1).max()*1000)
 results['states'][name]=row
print(json.dumps(results,indent=2));output.write_text(json.dumps(results,indent=2)+'\n')
