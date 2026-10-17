"""Install the new candidate's S7 samples on immutable R41 in memory."""
import numpy as np
from original_review_r43_sampling import hats,KEYS,DENSE
PREFIX='HGPT_S7_DELT_'
def coords(k):
 a=np.empty(len(k.data)*3);k.data.foreach_get('co',a);return a.reshape(-1,3)
def install(res,delta,basis):
 body,rig=res['body'],res['runtime'];blocks=body.data.shape_keys.key_blocks;rest=coords(blocks[0]);before={k.name:coords(k) for k in blocks if k.name.startswith(PREFIX)}
 interpolation=hats(DENSE,KEYS);dense_delta=np.einsum('dk,knj->dnj',basis,delta)
 if np.linalg.norm(dense_delta,axis=2).max()>.045:raise ValueError('Dense body increment exceeds45mm')
 for side in ('l','r'):
  old=np.array([before[f'{PREFIX}{side}_{int(ht)}'] for ht in KEYS])
  baseline=rest+np.einsum('dk,knj->dnj',interpolation,old-rest)
  mask=rest[:,0]*(1 if side=='r' else -1)>0
  for j,ht in enumerate(DENSE):
   name=f'{PREFIX}{side}_{int(ht)}';kb=blocks.get(name) or body.shape_key_add(name=name,from_mix=False)
   add=dense_delta[j].copy();add[~mask]=0;kb.data.foreach_set('co',(baseline[j]+add).ravel())
  rig[f'hgpt_s7_angles_{side}']=DENSE.tolist()
 body.data.update()
 return {'new_control_angles':DENSE.tolist(),'max_dense_body_update_mm':float(np.linalg.norm(dense_delta,axis=2).max()*1000),'baseline_interpolation':'exact original piecewise-linear S7 function, sampled at added angles'}
