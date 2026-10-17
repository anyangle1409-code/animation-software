"""Expand only body-side110/156 support for the whole-motion correction."""
from pathlib import Path
import sys,json,numpy as np
from original_review_r43_sampling import coefficients,basis,DENSE
from original_review_r42_line import frame
source,initial,dest=sys.argv[1:4]
with np.load(source) as z:d={k:z[k] for k in z.files}
rest=d['rest'];free=d['free'].copy();mirror=int(np.argmin(np.linalg.norm(rest-rest[18633]*[-1,1,1],axis=1)))
region=(abs(rest[:,0])>.08)&(abs(rest[:,0])<.35)&(rest[:,2]>1.20)&(rest[:,2]<1.51)
for k in (0,5):
 p=d['key_base'][k];eligible=np.zeros(len(rest),bool)
 for side,(gh,el) in zip(('l','r'),d['key_bones'][k]):
  axis,normal=frame(gh,el,side);rel=p-gh;s=rel@axis;same=p[:,0]*(1 if side=='r' else -1)>0
  eligible|=same&(s>-.40)&(s<0)&(rel@normal>-.03)&(rel[:,1]>-.065)
 free[k]=eligible&region&~d['frozen_arm'][k];free[k,[18633,mirror]]=False;free[k,rest[:,0]==0]=False
delta=np.load(initial)['delta'];d['profile_target_points']=d['base'][25]+np.einsum('nij,nj->ni',d['mat'][25],np.einsum('kn,knj->nj',d['weight'][25],delta))
d.update(free=free,weight=np.array([coefficients(w) for w in d['weight']]),front_weight=coefficients(d['front_weight']),sampling_basis=basis(),dense_angles=DENSE)
np.savez_compressed(dest,**d)
Path(dest+'.json').write_text(json.dumps(dict(free=free.sum(1).tolist(),old_frozen_body_controls_now_editable=[110,156],arm_and_elbow_frozen=True,control166_frozen=True,dense_angles=DENSE.tolist()),indent=2)+'\n')
