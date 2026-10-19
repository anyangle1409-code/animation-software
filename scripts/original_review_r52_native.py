"""Install actual independent dense increments on immutable R41 in memory."""
import numpy as np
from original_review_r43_sampling import hats,KEYS,DENSE
from original_review_r43_native import coords,PREFIX
def install(res,dense,basis_unused=None):
 dense=np.asarray(dense,float)
 if dense.shape[0]!=72 or not np.isfinite(dense).all():raise ValueError('Invalid independent temporal solution')
 if np.linalg.norm(dense,axis=2).max()>.045+1e-10:raise ValueError('Dense material cap exceeded')
 if np.max(abs(dense[[0,15,71]]))>1e-12:raise ValueError('Protected95/110/166 increment changed')
 body,rig=res['body'],res['runtime'];blocks=body.data.shape_keys.key_blocks;rest=coords(blocks[0]);before={k.name:coords(k) for k in blocks if k.name.startswith(PREFIX)}
 interpolation=hats(DENSE,KEYS)
 for side in ('l','r'):
  old=np.array([before[f'{PREFIX}{side}_{int(ht)}'] for ht in KEYS]);baseline=rest+np.einsum('dk,knj->dnj',interpolation,old-rest);mask=rest[:,0]*(1 if side=='r' else -1)>0
  for j,ht in enumerate(DENSE):
   name=f'{PREFIX}{side}_{int(ht)}';kb=blocks.get(name) or body.shape_key_add(name=name,from_mix=False);add=dense[j+1].copy();add[~mask]=0;kb.data.foreach_set('co',(baseline[j]+add).ravel())
  rig[f'hgpt_s7_angles_{side}']=DENSE.tolist()
 body.data.update()
 return dict(independent_temporal_controls=True,model_saved=False,approved=False)
