"""Prepare trial 2 with narrower contour locks and unchanged acceptance gates."""
import json,sys
from pathlib import Path
import numpy as np
from original_review_r42_target import target
from original_review_r42_line import frame
def prepare(source,destination,absolute=False):
 with np.load(source) as z:d={k:z[k] for k in z.files}
 rest=d['rest'];n=len(rest);authored=np.zeros((7,n,3));free=np.zeros((7,n),bool);cn=np.zeros_like(authored);mask=np.zeros((7,n),bool);rows=[]
 region=(abs(rest[:,0])>.08)&(abs(rest[:,0])<.35)&(rest[:,2]>1.20)&(rest[:,2]<1.51)
 mirror=int(np.argmin(np.linalg.norm(rest-rest[18633]*[-1,1,1],axis=1)))
 for k,ht,gain in [(1,120,.55),(2,130,.85),(3,136,.85),(4,145,.65)]:
  p=d['key_base'][k];a=d['key_mat'][k];bones=dict(zip(('l','r'),d['key_bones'][k]));world,fixed=target(p,d['faces'],bones,rest,gain)
  coeff=d['key_weight'][k,k];active=np.linalg.norm(world,axis=1)>0
  assert coeff[active].min()>.95
  authored[k]=np.einsum('nij,nj->ni',np.linalg.pinv(a,rcond=1e-4),world/np.maximum(coeff[:,None],1e-20))
  for side,(gh,el) in bones.items():
   axis,normal=frame(gh,el,side);rel=p-gh;s=rel@axis;same=p[:,0]*(1 if side=='r' else -1)>0
   eligible=region&same&(s>-.40)&(s<0)&(rel@normal>-.03)&(rel[:,1]>-.065)
   free[k]|=eligible
   cov=np.einsum('nji,j->ni',a,normal);cov/=np.maximum(np.linalg.norm(cov,axis=1)[:,None],1e-20)
   cn[k,same]=cov[same]
  free[k]&=~d['frozen_arm'][k];free[k,[18633,mirror]]=False;free[k,rest[:,0]==0]=False
  mask[k]=fixed&free[k];authored[k,~free[k]]=0
  rows.append(dict(elevation=ht,free=int(free[k].sum()),fixed=int(mask[k].sum()),max_world_mm=float(np.linalg.norm(world,axis=1).max()*1000),max_material_mm=float(np.linalg.norm(authored[k],axis=1).max()*1000)))
 assert np.linalg.norm(authored,axis=2).max()<=.040
 d.update(delta=authored,free=free,constraint_normal=cn,constraint_mask=mask,constraint_value=(cn*authored).sum(2),max_delta_mm=np.array(5.))
 
 if absolute:d['absolute_material_limit_mm']=np.array(45.)
 np.savez_compressed(destination,**d);Path(destination+'.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows),flush=True)
if __name__=='__main__':prepare(*sys.argv[1:3],absolute='--absolute-cap' in sys.argv[3:])
