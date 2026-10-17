"""Coupled local skin optimization with exact approved-line components.

All82 native responses remain in the objective. No skeleton, topology, weights,
non-S7 coordinates, fixed anchors or terminal S7 keys are optimization variables.
"""
import json,time
import numpy as np
from scipy.optimize import minimize

def separating_plane(a,b):
 """Parent separating axis: face normals, edge crosses and coplanar axes."""
 ea=np.roll(a,-1,axis=0)-a;eb=np.roll(b,-1,axis=0)-b
 na=np.cross(ea[0],ea[1]);nb=np.cross(eb[0],eb[1])
 axes=np.vstack((na,nb,np.cross(ea[:,None],eb[None]).reshape(-1,3),np.cross(ea,na),np.cross(eb,nb)))
 axes=axes[np.linalg.norm(axes,axis=1)>1e-14];axes/=np.linalg.norm(axes,axis=1)[:,None]
 axes=np.vstack((axes,-axes));gap=(b@axes.T).min(0)-(a@axes.T).max(0)
 i=int(np.argmax(gap))
 if gap[i]<-1e-7:raise ValueError('Parent contact has no separating axis')
 return axes[i],float(np.clip(.2*gap[i],1e-5,2e-4))

def objective(data):
 d=data
 f0=d['faces'];used=d['free'].any(0);fsel=used[f0].any(1);contact_rows=data.get('contacts',[]);contact_faces=[r[k] for r in contact_rows for k in ('a','b')];verts=np.unique(np.concatenate((f0[fsel].ravel(),f0[contact_faces].ravel(),data.get('front_triangles',np.empty(0,int)).ravel())));rev=np.full(len(used),-1);rev[verts]=np.arange(len(verts));f=rev[f0[fsel]]
 free=d['free'][:,verts];n=d['constraint_normal'][:,verts]*d['constraint_mask'][:,verts,None]
 initial=d['delta'][:,verts].copy();base=d['base'][:,verts].astype(float);mat=d['mat'][:,verts].astype(float);weight=d['weight'][:,:,verts].astype(float)
 if 'front_base' in data:
  base=np.concatenate((base,data['front_base'][verts][None]));mat=np.concatenate((mat,data['front_mat'][verts][None]));weight=np.concatenate((weight,data['front_weight'][:,verts][None]))
 rest=d['rest'][verts];rf=rest[f];a0=.5*np.linalg.norm(np.cross(rf[:,1]-rf[:,0],rf[:,2]-rf[:,0]),axis=1)
 t=base[:,f];cross=np.cross(t[:,:,1]-t[:,:,0],t[:,:,2]-t[:,:,0]);b=.5*np.linalg.norm(cross,axis=2);ref=cross/np.maximum(2*b[:,:,None],1e-20)
 upper=np.maximum(1.95*a0,b*1.001);lower=np.minimum(.15*a0,b*.99);units=np.maximum(a0,1e-8)
 strain=bool(data.get('strain_mode',False))
 fixed_stretch=fixed_collapse=reference_max=None
 if strain:
  full_tri=d['rest'][f0];full_a0=.5*np.linalg.norm(np.cross(full_tri[:,1]-full_tri[:,0],full_tri[:,2]-full_tri[:,0]),axis=1)
  full_base=list(d['base'])+([d['front_base']] if 'front_base' in d else [])
  full_st=[];full_co=[];full_max=[]
  for pp in full_base:
   tt=pp[f0];ar=.5*np.linalg.norm(np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0]),axis=1)
   full_st.append(int((ar>2*full_a0).sum()));full_co.append(int(((ar<.1*full_a0)&(full_a0>1e-12)).sum()))
   full_max.append(float((ar/np.maximum(full_a0,1e-20)).max()))
  fixed_stretch=np.asarray(full_st)-(b>2*a0).sum(1)
  fixed_collapse=np.asarray(full_co)-((b<.1*a0)&(a0>1e-12)).sum(1)
  reference_max=np.asarray(full_max)
 edges=np.unique(np.sort(np.concatenate((f[:,[0,1]],f[:,[1,2]],f[:,[2,0]])),axis=1),axis=0) if strain else None
 shape=initial.shape;count=0;start=time.time()
 contacts=[]
 for row in contact_rows:
  cs=int(row['sample']);ca=rev[f0[int(row['a'])]];cb=rev[f0[int(row['b'])]]
  cn,margin=separating_plane(base[cs,ca],base[cs,cb])
  contacts.append((cs,ca,cb,cn,margin))
 front=None
 if 'front_base' in data:
  front=(data['front_base'][verts],data['front_mat'][verts],data['front_weight'][:,verts],rev[data['front_triangles']],data['front_limits'])
 state={}
 def project(x):
  x=x.reshape(shape)*free[:,:,None];return x-n*(x*n).sum(2)[:,:,None]
 def fun(x):
  nonlocal count
  change=project(x)*.01;delta=initial+change
  dr=np.einsum('skn,knj->snj',weight,delta);p=base+np.einsum('snij,snj->sni',mat,dr)
  t=p[:,f];cr=np.cross(t[:,:,1]-t[:,:,0],t[:,:,2]-t[:,:,0]);area=.5*np.linalg.norm(cr,axis=2);nn=cr/np.maximum(2*area[:,:,None],1e-20)
  ae=np.maximum(area-upper,0)+np.minimum(area-lower,0)
  signed=.5*(cr*ref).sum(2);se=np.minimum(signed-.08*b,0)*(b>1e-12)
  loss=(ae/units)**2+4*(se/units)**2
  quality_loss=0.;quality_gradient=np.zeros_like(area)
  if strain:
   from original_review_r41_strain import area_log_penalty
   quality_loss,quality_gradient=area_log_penalty(area,a0)
  # derivative wrt cross: 0.5*normal for unsigned; same for signed
  gnorm=(ae/units**2+.5*quality_gradient)[:,:,None]*nn+4*(se/units**2)[:,:,None]*ref
  g=np.stack([np.cross(t[:,:,1]-t[:,:,2],gnorm),np.cross(t[:,:,2]-t[:,:,0],gnorm),np.cross(t[:,:,0]-t[:,:,1],gnorm)],axis=2)
  gp=np.zeros_like(p)
  for s in range(len(base)):
   for ax in range(3):gp[s,:,ax]=np.bincount(f.ravel(),weights=g[s,:,:,ax].ravel(),minlength=len(verts))
  contact_loss=0.;contact_safe=True
  for cs,ca,cb,cn,margin in contacts:
   qa=p[cs,ca]@cn;qb=p[cs,cb]@cn
   gap=qb[None,:]-qa[:,None];error=np.minimum(gap-margin,0.)
   contact_safe &= bool(np.all(gap>=.9*margin))
   contact_loss+=4*np.sum((error/.001)**2)
   gp[cs,ca]-=8*error.sum(1)[:,None]/.001**2*cn
   gp[cs,cb]+=8*error.sum(0)[:,None]/.001**2*cn
  gm=np.einsum('snji,snj->sni',mat,gp)
  grad=np.einsum('skn,snj->knj',weight,gm)
  front_loss=0.;front_excess=0.
  if front is not None:
   from original_review_r41_front import crease_loss,angles
   fb,fm,fw,ft,fl=front
   fp=fb+np.einsum('nij,nj->ni',fm,np.einsum('kn,knj->nj',fw,delta))
   front_loss,fg,front_peak=crease_loss(fp,ft,fl)
   front_excess=float((angles(fp,ft)-fl).max(initial=0))
   material=np.einsum('nji,nj->ni',fm,fg)
   grad+=fw[:,:,None]*material[None,:,:]
  fair_loss=0.
  if strain:
   edge_delta=change[:,edges[:,0]]-change[:,edges[:,1]]
   coefficient=.002/.001**2
   fair_loss=coefficient*float((edge_delta*edge_delta).sum())
   for k in range(len(delta)):
    for axis in range(3):
     grad[k,:,axis]+=2*coefficient*(np.bincount(edges[:,0],weights=edge_delta[k,:,axis],minlength=len(verts))-np.bincount(edges[:,1],weights=edge_delta[k,:,axis],minlength=len(verts)))
  reg=1e-4
  val=loss.sum()+contact_loss+front_loss+quality_loss+fair_loss+reg*np.sum((change/.01)**2)
  grad=project(grad)*.01+2*reg*project(x)
  count+=1
  if count%20==0:
   st=(area>2*a0).sum(1);bs=(b>2*a0).sum(1);co=(area<.1*a0).sum(1);bc=(b<.1*a0).sum(1)
   print(count,round(time.time()-start,1),'loss',val,'extra',int((st>bs).sum()),int((co>bc).sum()),'rev',int(((signed<0)&(b>1e-12)).sum()),'front_excess_deg',front_excess,flush=True)
  quality_goals=True
  if strain:
   st=fixed_stretch+(area>2*a0).sum(1);co=fixed_collapse+((area<.1*a0)&(a0>1e-12)).sum(1)
   quality_goals=bool(st[25]<=40 and st[40]<=70 and co[41:82].max()==0 and np.all((area/np.maximum(a0,1e-20)).max(1)<=reference_max*1.01))
   if count%20==0:print('R41_STRAIN',int(st[25]),int(st[40]),int(co[41:82].max()),flush=True)
  state.update(delta=delta,area=area,signed=signed,contact_safe=contact_safe,front_excess=front_excess,quality_goals=quality_goals)
  return val,grad.ravel()
 def expand(x):
  out=d['delta'].copy();out[:,verts]=initial+project(x)*.01
  return out
 def safe():
  area,signed=state['area'],state['signed']
  return (bool(np.all((area>2*a0).sum(1)<=(b>2*a0).sum(1))) and
          bool(np.all((area<.1*a0).sum(1)<=(b<.1*a0).sum(1))) and
          not np.any((signed<.04*b)&(b>1e-12)) and state['contact_safe'] and state['front_excess']<=.25 and state['quality_goals'])
 return fun,expand,safe,shape

def solve(data,epochs=1000):
 for key in ('rest','base','mat','weight','delta','constraint_normal','constraint_value'):
  if not np.isfinite(data[key]).all():raise ValueError('Nonfinite response: '+key)
 fun,expand,safe,shape=objective(data)
 class Satisfied(Exception):pass
 latest=[np.zeros(shape).ravel()];iterations=[0]
 if 'warm_start' in data:
  # Expand needs full vertex indices; use objective's compact inverse mapping.
  f=data['faces'];active=data['free'].any(0);rows=data.get('contacts',[]);cf=[r[k] for r in rows for k in ('a','b')]
  ids=np.unique(np.concatenate((f[active[f].any(1)].ravel(),f[cf].ravel(),data.get('front_triangles',np.empty(0,int)).ravel())))
  latest[0]=((data['warm_start'][:,ids]-data['delta'][:,ids])/.01).ravel()
 def callback(x):
  latest[0]=x.copy();iterations[0]+=1;fun(x)
  if safe():raise Satisfied()
 try:
  bound=float(data.get('max_delta_mm',.70))/.01/1000/np.sqrt(3)
  bounds=[(-bound,bound)]*len(latest[0]) if bool(data.get('strain_mode',False)) else None
  result=minimize(fun,latest[0],jac=True,method='L-BFGS-B',callback=callback,bounds=bounds,
                  options={'maxiter':epochs,'maxls':40,'ftol':1e-12,'gtol':1e-8,'maxcor':20})
  latest[0]=result.x;message=str(result.message)
 except Satisfied:message='All path, exact-front, area, orientation and contact constraints satisfied'
 fun(latest[0]);out=expand(latest[0])
 mask=data['constraint_mask'];n=data['constraint_normal'];v=data['constraint_value']
 error=float(abs((out*n).sum(2)[mask]-v[mask]).max(initial=0)*1000)
 if error>1e-5:raise ValueError(('Optimization erased approved line',error))
 return out,{'message':message,'iterations':iterations[0],'optimization_sample_count':len(data['base'])+int('front_base' in data),'constraints_satisfied':safe(),
             'max_line_component_error_mm':error,
             'max_material_adjustment_mm':float(np.linalg.norm(out-data['delta'],axis=2).max()*1000),
             'frozen_vertices_unchanged':bool(np.array_equal(out[~data['free']],data['delta'][~data['free']]))}
