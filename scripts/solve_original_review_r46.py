"""Sequential sparse feasibility solve. Only free S7 material coordinates vary."""
import sys,json,time,os
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.optimize import linprog
from original_review_r43_geometry import area_gradient,outline,cosine_gradient,normal_difference_gradient
from original_review_r42_line import frame,guide
from original_review_r41_strain import area_safety
from original_review_r41_front import edge_pairs,angles
from original_review_r46_lp import step as linear_step
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
def solve(data,initial,reference,contacts,dest,epochs=400):
 d=data;free=d['free'];ids=np.full((*free.shape,3),-1,int);ids[free]=np.arange(int(free.sum())*3).reshape(-1,3);count=int(free.sum())*3
 field=None
 if os.environ.get('HGPT_R43_MATERIAL_FIELD')=='1':
  from original_review_r46_field import material_field
  field=material_field(d['rest'],free,d['faces']);print('R46_MATERIAL_FIELD',field.shape,field.nnz,flush=True)
 delta=initial.copy();delta[~free]=0;faces=d['faces'];used=free.any(0);fids=np.flatnonzero(used[faces].any(1));f=faces[fids]
 base=np.concatenate((d['base'],d['front_base'][None]));mat=np.concatenate((d['mat'],d['front_mat'][None]));weight=np.concatenate((d['weight'],d['front_weight'][None]));rest=d['rest']
 def areas(p,ff):
  t=p[ff];return .5*np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)
 a0=areas(rest,f);parent_area=np.array([areas(p,f) for p in base]);full_a0=areas(rest,faces)
 parent_max=np.array([(areas(p,faces)/np.maximum(full_a0,1e-20)).max() for p in base])
 from original_review_r44_area import upper_bounds
 upper=upper_bounds(a0,parent_area,parent_max)
 lower=np.where(parent_area>=.1*a0,np.minimum(.1001*a0,parent_area),parent_area*.99)
 parent_tri=base[:,f];parent_cross=np.cross(parent_tri[:,:,1]-parent_tri[:,:,0],parent_tri[:,:,2]-parent_tri[:,:,0]);parent_normal=parent_cross/np.maximum(np.linalg.norm(parent_cross,axis=2)[:,:,None],1e-20)
 back=(abs(rest[:,0])>.08)&(abs(rest[:,0])<.25)&(rest[:,2]>1.27)&(rest[:,2]<1.49)&(rest[:,1]>.025)&used
 backids=np.flatnonzero(back);ba=np.diff(base[:41,backids],n=2,axis=0);motion_limit=np.linalg.norm(ba,axis=2)+.00045
 separation=[]
 for r in contacts:
  s=int(r['sample']);fa=faces[r['a']];fb=faces[r['b']];n,margin=separating_plane(base[s,fa],base[s,fb]);gap=float((base[s,fb]@n).min()-(base[s,fa]@n).max());margin=min(margin,max(.1*gap,1e-9));separation.append((s,fa,fb,n,margin))
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
 edges,pairs=edge_pairs(faces);cent=rest[edges].mean(1)
 rear=(abs(cent[:,0])>.08)&(abs(cent[:,0])<.35)&(cent[:,1]>.025)&(cent[:,2]>1.20)&(cent[:,2]<1.51)&used[edges].any(1)
 rear_tri=faces[pairs[rear]];rear_limits=np.array([np.minimum(angles(b,rear_tri)+1.8,179.999) for b in base]);rear_cos=np.cos(np.radians(rear_limits))
 rb=base.astype(float)[:,rear_tri];rc0=np.cross(rb[:,:,:,1]-rb[:,:,:,0],rb[:,:,:,2]-rb[:,:,:,0]);rl0=np.maximum(np.linalg.norm(rc0,axis=3),1e-20);rn0=rc0/rl0[:,:,:,None];rd0=rn0[:,:,0]-rn0[:,:,1]
 rear_cube=np.maximum(2*np.sin(np.radians(rear_limits)/2)-np.linalg.norm(rd0,axis=2),1e-9)*.99/np.sqrt(3)
 rear_needed=rear_limits<179.9
 rejection=['none']
 def fail(reason):rejection[0]=reason;return False
 def nonprofile_ok(candidate):
  q=base+np.einsum('snij,snj->sni',mat,np.einsum('skn,knj->snj',weight,candidate));qt=q[:,f];qc=np.cross(qt[:,:,1]-qt[:,:,0],qt[:,:,2]-qt[:,:,0]);qa=.5*np.linalg.norm(qc,axis=2)
  true_upper=upper_bounds(a0,parent_area,parent_max,margin=.0099,count_ratio=1.9999)
  if np.any(qa>true_upper+np.maximum(1e-6*a0,1e-12)) or np.any(qa<np.minimum(.1*a0,parent_area)-np.maximum(1e-6*a0,1e-12)):return fail('area')
  if np.any((.5*(qc*parent_normal).sum(2)<.04*parent_area)&(parent_area>1e-12)):return fail('orientation')
  for cs,fa,fb,cn,margin in separation:
   if (q[cs,fb]@cn).min()-(q[cs,fa]@cn).max()<margin*.8:return fail('contact')
  if np.any(angles(q[82],d['front_triangles'])>d['front_limits']+.01):return fail('front')
  for cs in range(83):
   if np.any(angles(q[cs],rear_tri)>rear_limits[cs]+.18):return fail('posterior')
  if np.any(np.linalg.norm(np.diff(q[:41,backids],n=2,axis=0),axis=2)>motion_limit+.00003):return fail('motion')
  return True
 history=[];start=time.time();last_violation=float('inf');trust=.5
 for epoch in range(epochs):
  p=base+np.einsum('snij,snj->sni',mat,np.einsum('skn,knj->snj',weight,delta))
  from original_review_r46_lp import reset_cache
  reset_cache()
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
  rt=p[:,rear_tri];rc=np.cross(rt[:,:,:,1]-rt[:,:,:,0],rt[:,:,:,2]-rt[:,:,:,0]);rl=np.maximum(np.linalg.norm(rc,axis=3),1e-20);rn=rc/rl[:,:,:,None];rd=rn[:,:,0]-rn[:,:,1]-rd0
  cone_keys=set()
  def add_normal_cone(rs,j,direction):
   key=(rs,j,*np.round(direction,4))
   if key in cone_keys:return False
   cone_keys.add(key);value,g=normal_difference_gradient(rt[rs,j],direction)
   radius=2*np.sin(np.radians(rear_limits[rs,j])/2)
   spatial(rows,rs,rear_tri[j].ravel(),g.reshape(-1,3),float(radius-value),'posterior_normal_cone')
   return True
  normal_diff=rn[:,:,0]-rn[:,:,1];radius=2*np.sin(np.radians(rear_limits)/2)
  norm=np.linalg.norm(normal_diff,axis=2)
  for rs,j in np.argwhere((norm>radius*.99)&rear_needed):add_normal_cone(int(rs),int(j),normal_diff[rs,j]/max(norm[rs,j],1e-20))
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
  # Phase II seeks a minimum-norm step; exact nonlinear gates decide acceptance.
  for cut_round in range(8):
   A=rows.matrix();m=A.shape[0];movement,z=linear_step(A if field is None else (A@field).tocsr(),np.asarray(rows.rhs),trust,np.array([name.startswith('profile_') for name in rows.labels]),profile_opt_tolerance=.001)
   if field is not None:movement=field@movement
   step=np.zeros_like(delta);step[free]=movement.reshape(-1,3)*.001
   dq=np.einsum('snij,snj->sni',mat,np.einsum('skn,knj->snj',weight,step))
   dqt=dq[:,rear_tri];dc=np.cross(dqt[:,:,:,1]-dqt[:,:,:,0],rt[:,:,:,2]-rt[:,:,:,0])+np.cross(rt[:,:,:,1]-rt[:,:,:,0],dqt[:,:,:,2]-dqt[:,:,:,0]);dn=(dc-rn*(dc*rn).sum(3)[:,:,:,None])/rl[:,:,:,None]
   forecast=normal_diff+dn[:,:,0]-dn[:,:,1];forecast_norm=np.linalg.norm(forecast,axis=2);added=0
   for rs,j in np.argwhere((forecast_norm>radius+1e-7)&rear_needed):added+=add_normal_cone(int(rs),int(j),forecast[rs,j]/max(forecast_norm[rs,j],1e-20))
   forecast_acc=acc+np.diff(dq[:41,backids],n=2,axis=0);forecast_length=np.linalg.norm(forecast_acc,axis=2)
   for si,j in np.argwhere(forecast_length>motion_limit+1e-8):
    vertex=backids[j];unit=forecast_acc[si,j]/max(forecast_length[si,j],1e-20)
    transform=weight[si,:,vertex,None,None]*mat[si,vertex]-2*weight[si+1,:,vertex,None,None]*mat[si+1,vertex]+weight[si+2,:,vertex,None,None]*mat[si+2,vertex]
    rows.add(ids[:,vertex],.001*np.einsum('kji,j->ki',transform,unit),float(motion_limit[si,j]-acc[si,j]@unit),'back_motion_cone');added+=1
   print('R46_CONE_CUTS',epoch,cut_round,added,flush=True)
   if not added:break
  alpha=1.;accepted=False
  for trial in range(18):
   candidate=delta+alpha*step
   maximum=np.linalg.norm(candidate,axis=2).max()
   if 'sampling_basis' in d:maximum=max(maximum,np.linalg.norm(np.einsum('dk,knj->dnj',d['sampling_basis'],candidate),axis=2).max())
   if maximum<=.045 and nonprofile_ok(candidate):accepted=True;break
   if trial<2:print('R46_REJECT_STEP',epoch,alpha,rejection[0],flush=True)
   alpha*=.5
  if not accepted:raise RuntimeError('No step maintains the hard motion/surface/area/contact gates')
  violation=max(0.,float(-np.min(rows.rhs,initial=0)));delta=candidate
  worst=int(np.argmin(rows.rhs))
  row=dict(worst_constraint=rows.labels[worst],epoch=epoch,seconds=round(time.time()-start,1),constraints=m,violation_mm=violation,linearized_slack_mm=z,step_mm=float(np.linalg.norm(alpha*step,axis=2).max()*1000),motion_excess_mm=float((an-np.linalg.norm(ba,axis=2)).max()*1000))
  history.append(row);print('R46_FEASIBILITY',json.dumps(row),flush=True);np.savez_compressed(dest+'.progress.npz',delta=delta);Path(dest+'.progress.json').write_text(json.dumps(history,indent=2)+'\n')
  if violation<1e-4 and row['step_mm']<.001:break
  if len(history)>=5 and max(h['step_mm'] for h in history[-5:])<1e-4:
   print('R46_STALLED_RETAIN_FAILED_STUDY',violation,flush=True);break
  if alpha>=.5 and z>trust*.2:trust=min(4.,trust*1.5)
 np.savez_compressed(dest,delta=delta);Path(dest+'.json').write_text(json.dumps(dict(history=history,maximum_update_mm=float(np.linalg.norm(delta,axis=2).max()*1000)),indent=2)+'\n')
 return delta
if __name__=='__main__':
 source,initial,reference,contacts,dest=sys.argv[1:6]
 with np.load(source) as z:d={k:z[k] for k in z.files}
 with np.load(reference) as z:ref={k:z[k] for k in z.files}
 solve(d,np.load(initial)['delta'],ref,json.loads(Path(contacts).read_text())['contacts'],dest)
