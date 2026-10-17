"""Sequential sparse feasibility solve. Only free S7 material coordinates vary."""
import sys,json,time
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.optimize import linprog
from original_review_r43_geometry import area_gradient,outline,cosine_gradient
from original_review_r42_line import frame,guide
from original_review_r41_strain import area_safety
from optimize_original_review_r42 import separating_plane
class Constraints:
 def __init__(self,count):self.count=count;self.rr=[];self.cc=[];self.vv=[];self.rhs=[];self.labels=[]
 def add(self,cols,values,rhs,label):
  cols=np.asarray(cols).ravel();values=np.asarray(values).ravel();keep=(cols>=0)&(abs(values)>1e-16);cols=cols[keep];values=values[keep]
  scale=float(abs(values).sum())
  if scale<1e-15:
   if rhs< -1e-8:raise ValueError(('Uneditable violated constraint',label,rhs))
   return
  r=len(self.rhs);self.rr.extend([r]*len(cols));self.cc.extend(cols.tolist());self.vv.extend((values/scale).tolist());self.rhs.append(rhs/scale);self.labels.append(label)
 def matrix(self):return sparse.coo_matrix((self.vv,(self.rr,self.cc)),shape=(len(self.rhs),self.count)).tocsr()
def solve(data,initial,reference,contacts,dest,epochs=120):
 d=data;free=d['free'];ids=np.full((*free.shape,3),-1,int);ids[free]=np.arange(int(free.sum())*3).reshape(-1,3);count=int(free.sum())*3
 delta=initial.copy();delta[~free]=0;faces=d['faces'];used=free.any(0);fids=np.flatnonzero(used[faces].any(1));f=faces[fids]
 base=np.concatenate((d['base'],d['front_base'][None]));mat=np.concatenate((d['mat'],d['front_mat'][None]));weight=np.concatenate((d['weight'],d['front_weight'][None]));rest=d['rest']
 def areas(p,ff):
  t=p[ff];return .5*np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)
 a0=areas(rest,f);parent_area=np.array([areas(p,f) for p in base]);full_a0=areas(rest,faces)
 parent_max=np.array([(areas(p,faces)/np.maximum(full_a0,1e-20)).max() for p in base])
 upper=np.where(parent_area<=2*a0,np.maximum(1.999*a0,parent_area),parent_max[:,None]*1.009*a0)
 lower=np.where(parent_area>=.1*a0,np.minimum(.1001*a0,parent_area),parent_area*.99)
 parent_tri=base[:,f];parent_cross=np.cross(parent_tri[:,:,1]-parent_tri[:,:,0],parent_tri[:,:,2]-parent_tri[:,:,0]);parent_normal=parent_cross/np.maximum(np.linalg.norm(parent_cross,axis=2)[:,:,None],1e-20)
 back=(abs(rest[:,0])>.08)&(abs(rest[:,0])<.25)&(rest[:,2]>1.27)&(rest[:,2]<1.49)&(rest[:,1]>.025)&used
 backids=np.flatnonzero(back);ba=np.diff(base[:41,backids],n=2,axis=0);motion_limit=np.linalg.norm(ba,axis=2)+.00048
 separation=[]
 for r in contacts:
  s=int(r['sample']);fa=faces[r['a']];fb=faces[r['b']];n,margin=separating_plane(base[s,fa],base[s,fb]);separation.append((s,fa,fb,n,margin))
 def spatial(rows,s,v,g,rhs,label):
  v=np.asarray(v);g=np.asarray(g);coeff=weight[s][:,v]
  values=.001*coeff[:,:,None]*np.einsum('nji,nj->ni',mat[s,v],g)[None]
  rows.add(ids[:,v],values,rhs,label)
 marked=25;levels=np.array([-.12,-.10,-.08,-.06]);target={}
 # Preserve the rejected study's marked silhouette within0.5mm, while the
 # unchanged wider owner-envelope test remains a separate final gate.
 p0=d.get('profile_target_points',base[marked]+np.einsum('nij,nj->ni',mat[marked],np.einsum('kn,knj->nj',weight[marked],initial)))
 for side in ('l','r'):
  gh=reference[f'gh_{side}_135.625'];el=reference[f'elbow_{side}_135.625'];axis,n=frame(gh,el,side)
  target[side]=[outline(p0,faces,gh,axis,n,side,s)[0] for s in levels]
 history=[];start=time.time();last_violation=float('inf');trust=1.
 for epoch in range(epochs):
  p=base+np.einsum('snij,snj->sni',mat,np.einsum('skn,knj->snj',weight,delta))
  rows=Constraints(count);t=p[:,f];cr=np.cross(t[:,:,1]-t[:,:,0],t[:,:,2]-t[:,:,0]);ar=.5*np.linalg.norm(cr,axis=2)
  for s,j in np.argwhere(ar>upper*.985):spatial(rows,int(s),f[j],area_gradient(t[s,j]),float(upper[s,j]-ar[s,j]),'area_upper')
  for s,j in np.argwhere((ar<lower*1.1)&(a0[None]>1e-12)):spatial(rows,int(s),f[j],-area_gradient(t[s,j]),float(ar[s,j]-lower[s,j]),'area_lower')
  signed=.5*(cr*parent_normal).sum(2)
  for s,j in np.argwhere((signed<.1*parent_area)&(parent_area>1e-12)):spatial(rows,int(s),f[j],-area_gradient(t[s,j],parent_normal[s,j]),float(signed[s,j]-.045*parent_area[s,j]),'orientation')
  for s,fa,fb,n,margin in separation:
   for ia in fa:
    for ib in fb:spatial(rows,s,[ia,ib],[n,-n],float((p[s,ib]-p[s,ia])@n-margin),'contact')
  ft=d['front_triangles'];pts=p[82,ft];cc=np.cross(pts[:,:,1]-pts[:,:,0],pts[:,:,2]-pts[:,:,0]);nn=cc/np.maximum(np.linalg.norm(cc,axis=2)[:,:,None],1e-20);cos=np.einsum('ni,ni->n',nn[:,0],nn[:,1]);cl=np.cos(np.radians(d['front_limits']))
  for j in np.flatnonzero(cos<cl+.003):
   value,g=cosine_gradient(pts[j]);spatial(rows,82,ft[j].ravel(),-g.reshape(-1,3),float(value-cl[j]),'front')
  for side in ('l','r'):
   gh=reference[f'gh_{side}_135.625'];el=reference[f'elbow_{side}_135.625'];axis,n=frame(gh,el,side);fit=guide(reference['all_135.625'],faces,gh,el,side)
   for j,station in enumerate(levels):
    value,v,g=outline(p[marked],faces,gh,axis,n,side,station);goal=target[side][j]
    spatial(rows,marked,v,g,goal+.0005-value,'profile_upper');spatial(rows,marked,v,-g,value-(goal-.0005),'profile_lower')
   for station in np.arange(0,.16001,.005):
    value,v,g=outline(p[marked],faces,gh,axis,n,side,station);goal=np.polyval(fit,station)
    spatial(rows,marked,v,g,goal+.00195-value,'arm_upper');spatial(rows,marked,v,-g,value-(goal-.00195),'arm_lower')
  acc=np.diff(p[:41,backids],n=2,axis=0);an=np.linalg.norm(acc,axis=2)
  for s,j in np.argwhere(an>motion_limit-.0002):
   vertex=backids[j];unit=acc[s,j]/max(an[s,j],1e-20)
   transform=weight[s,:,vertex,None,None]*mat[s,vertex]-2*weight[s+1,:,vertex,None,None]*mat[s+1,vertex]+weight[s+2,:,vertex,None,None]*mat[s+2,vertex]
   g=.001*np.einsum('kji,j->ki',transform,unit)
   rows.add(ids[:,vertex],g,float(motion_limit[s,j]-an[s,j]),'back_motion')
  length=np.linalg.norm(delta,axis=2)
  for k,v in np.argwhere(free&(length>.043)):
   rows.add(ids[k,v],.001*delta[k,v]/length[k,v],.044999-length[k,v],'material_bound')
  if 'sampling_basis' in d:
   dense_delta=np.einsum('dk,knj->dnj',d['sampling_basis'],delta);dense_length=np.linalg.norm(dense_delta,axis=2)
   for k,v in np.argwhere(dense_length>.043):
    rows.add(ids[:,v],.001*d['sampling_basis'][k,:,None]*dense_delta[k,v]/dense_length[k,v],.044999-dense_length[k,v],'dense_material_bound')
  # Sparse LP phase I: minimize maximum constraint violation in millimetres.
  # Phase II's L1 step cost picks the smallest material repair at that violation.
  A=rows.matrix();m=A.shape[0];eye=sparse.eye(count,format='csr')
  AA=sparse.vstack([sparse.hstack([A,sparse.csr_matrix((m,count)),-np.ones((m,1))]),sparse.hstack([eye,-eye,sparse.csr_matrix((count,1))]),sparse.hstack([-eye,-eye,sparse.csr_matrix((count,1))])],format='csr')
  rhs=np.r_[rows.rhs,np.zeros(count*2)];objective=np.r_[np.zeros(count),np.full(count,.0001/max(count,1)),1.]
  result=linprog(objective,A_ub=AA,b_ub=rhs,bounds=[(-trust,trust)]*count+[(0,trust)]*count+[(0,None)],method='highs',options={'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8})
  if not result.success:raise RuntimeError(('Feasibility LP failed',result.message))
  step=np.zeros_like(delta);step[free]=result.x[:count].reshape(-1,3)*.001
  alpha=1.;accepted=False
  for trial in range(12):
   candidate=delta+alpha*step
   maximum=np.linalg.norm(candidate,axis=2).max()
   if 'sampling_basis' in d:maximum=max(maximum,np.linalg.norm(np.einsum('dk,knj->dnj',d['sampling_basis'],candidate),axis=2).max())
   if maximum<=.045:accepted=True;break
   alpha*=.5
  if not accepted:raise RuntimeError('Material bound prevents linearized step')
  violation=max(0.,float(-np.min(rows.rhs,initial=0)));z=float(result.x[-1]);delta=candidate
  worst=int(np.argmin(rows.rhs))
  row=dict(worst_constraint=rows.labels[worst],epoch=epoch,seconds=round(time.time()-start,1),constraints=m,violation_mm=violation,linearized_slack_mm=z,step_mm=float(np.linalg.norm(alpha*step,axis=2).max()*1000),motion_excess_mm=float((an-np.linalg.norm(ba,axis=2)).max()*1000))
  history.append(row);print('R43_FEASIBILITY',json.dumps(row),flush=True);np.savez_compressed(dest+'.progress.npz',delta=delta);Path(dest+'.progress.json').write_text(json.dumps(history,indent=2)+'\n')
  if violation<1e-4 and row['step_mm']<.001:break
  if z>trust*.2:trust=min(2.,trust*1.2)
 np.savez_compressed(dest,delta=delta);Path(dest+'.json').write_text(json.dumps(dict(history=history,maximum_update_mm=float(np.linalg.norm(delta,axis=2).max()*1000)),indent=2)+'\n')
 return delta
if __name__=='__main__':
 source,initial,reference,contacts,dest=sys.argv[1:6]
 with np.load(source) as z:d={k:z[k] for k in z.files}
 with np.load(reference) as z:ref={k:z[k] for k in z.files}
 solve(d,np.load(initial)['delta'],ref,json.loads(Path(contacts).read_text())['contacts'],dest)
