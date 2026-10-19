"""R52 matrix-free temporal/spatial feasibility study, never a model save."""
from pathlib import Path
import os,sys,time,json
import numpy as np
from scipy import sparse
from original_review_r52_temporal import decode,blend,blend_adjoint,SOURCE,oscillation
from original_review_r52_projection import allowed_dense,project,motion,motion_adjoint,normal_response,normal_adjoint
from original_review_r52_study import shrink_ball_dual,study_status,retention_key
from original_review_r43_sampling import basis
from original_review_r48_outline import silhouette
from original_review_r52_envelope import make_envelopes,clip_marked

def support_vertices(p,faces):
 ids=[]
 for sign,side in ((-1,'l'),(1,'r')):
  for n in (np.array([sign,0.,0.]),np.array([sign,-1.,0.])/np.sqrt(2.)):
   for h in np.arange(1.18,1.62,.005):ids.extend(silhouette(p,faces,side,n,h)[1])
 return np.unique(ids)

def outline_values(p,faces):
 return np.array([silhouette(p,faces,side,n,h)[0] for sign,side in ((-1,'l'),(1,'r')) for n in (np.array([sign,0.,0.]),np.array([sign,-1.,0.])/np.sqrt(2.)) for h in np.arange(1.18,1.62,.005)])

def solve(source,seed,output,iterations=1200,seconds=600.):
 with np.load(source) as z:d={k:z[k] for k in z.files}
 old=np.load(seed)['delta'];initial_full=np.concatenate([np.zeros_like(old[:1]),np.einsum('dk,knj->dnj',basis(),old)])
 allowed_full=allowed_dense(d);ids=np.flatnonzero(allowed_full.any(0));rest=d['rest'];faces=d['faces'];allowed=allowed_full[:,ids]
 mapping=decode(d['weight'][:41][:,:,ids]);full_marked_mapping=decode(d['weight'][25:26])
 marked=tuple(v[25] for v in mapping);initial=initial_full[:,ids]*1000
 back=(abs(rest[:,0])>.08)&(abs(rest[:,0])<.25)&(rest[:,2]>1.27)&(rest[:,2]<1.49)&(rest[:,1]>.025)
 bb=np.flatnonzero(back[ids]);bm=tuple(v[:,bb] for v in mapping);mat=d['mat'][:41][:,ids[bb]].astype(float)
 ba=np.diff(d['base'][:41,ids[bb]].astype(float)*1000,n=2,axis=0);prior=np.linalg.norm(ba,axis=2);limit=prior+.45
 early=(95.+bm[0]+bm[2])<110.;sign=np.sign(rest[ids[bb],0])
 early_normal=np.zeros((len(mat),len(bb),3));early_normal[:,:,0]=sign[None]*early
 local_at_marked=blend(initial,mapping)[25]
 marked_points=d['base'][25]+np.einsum('nij,nj->ni',d['mat'][25],np.einsum('kn,knj->nj',d['weight'][25],old))
 pin=np.isin(ids,support_vertices(marked_points,faces));target=local_at_marked
 envelopes=make_envelopes(marked_points,faces)
 def preserve(value):
  value=project(value,allowed,marked,pin,target,cap=45.)
  for _ in range(4):
   value=clip_marked(value,allowed,marked,d['base'][25,ids]*1000,d['mat'][25,ids],envelopes,margin_mm=.2)
   value=project(value,allowed,marked,pin,target,cap=45.)
  return value
 target_outline=outline_values(d['r48_profile_target_points'],faces)
 edges=np.unique(np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1),axis=0)
 lookup=np.full(len(rest),-1,int);lookup[ids]=np.arange(len(ids));ee=lookup[edges];ee=ee[(ee>=0).all(1)];a,b=ee.T
 adj=sparse.coo_matrix((np.ones(len(a)*2),(np.r_[a,b],np.r_[b,a])),shape=(len(ids),len(ids))).tocsr();L=sparse.diags(np.asarray(adj.sum(1)).ravel())-adj
 def mforward(x):return motion(x[:,bb],mat,bm)
 def madjoint(y):
  out=np.zeros_like(initial);out[:,bb]=motion_adjoint(y,mat,bm);return out
 def outward(x):return normal_response(x[:,bb],mat,bm,early_normal)
 def oadjoint(y):
  out=np.zeros_like(initial);out[:,bb]=normal_adjoint(y,mat,bm,early_normal);return out
 def d1t(y):
  out=np.zeros_like(initial);out[:-1]-=y;out[1:]+=y;return out
 def d2t(y):
  out=np.zeros_like(initial);out[:-2]+=y;out[1:-1]-=2*y;out[2:]+=y;return out
 def lap(x):return (L@x.transpose(1,0,2).reshape(len(ids),-1)).reshape(len(ids),72,3).transpose(1,0,2)
 rng=np.random.default_rng(52);q=rng.normal(size=initial.shape);q[~allowed]=0;q/=np.linalg.norm(q)
 for _ in range(14):
  kq=madjoint(mforward(q))+d1t(np.diff(q,axis=0))+oadjoint(outward(q));kq[~allowed]=0;q=kq/max(np.linalg.norm(kq),1e-30)
 norm2=float((q*(madjoint(mforward(q))+d1t(np.diff(q,axis=0))+oadjoint(outward(q)))).sum())*1.2
 rate=np.sqrt(max(norm2,1.));sigma=.9/rate;grad_bound=.001+.02*16+.005*2*float(np.asarray(adj.sum(1)).max());tau=.8/(rate+grad_bound)
 x=preserve(initial);bar=x.copy();ym=np.zeros_like(ba);yd=np.zeros_like(np.diff(x,axis=0));yo=np.zeros((len(mat),len(bb)));history=[];best=None;best_rank=None;best_iteration=None;start=time.monotonic()
 output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
 def metrics(value):
  acceleration=ba+mforward(value);excess=float((np.linalg.norm(acceleration,axis=2)-prior).max());full=np.zeros_like(initial_full);full[:,ids]=value/1000
  increment=blend(full,full_marked_mapping)[0]
  points=d['base'][25]+np.einsum('nij,nj->ni',d['mat'][25],increment);outline=float(abs(outline_values(points,faces)-target_outline).max()*1000)
  step=oscillation(full)['maximum_adjacent_mm'];cap=float(np.linalg.norm(full,axis=2).max()*1000)
  return excess,step,outline,cap,full
 for iteration in range(iterations+1):
  if iteration%25==0 or iteration==iterations or time.monotonic()-start>seconds:
   excess,step,outline,cap,full=metrics(x);row=dict(iteration=iteration,seconds=round(time.monotonic()-start,2),motion_excess_mm=excess,maximum_adjacent_mm=step,approved_outline_error_mm=outline,maximum_material_mm=cap)
   row['early_outward_increment_mm']=float(np.maximum(outward(x),0).max());row['fully_feasible']=bool(excess<=.5 and step<=3. and outline<=1. and cap<=45.+1e-7 and row['early_outward_increment_mm']<=.05);history.append(row);print('R52_TEMPORAL_SEARCH',json.dumps(row),flush=True)
   # Retain a bounded outline-preserving study, but never call it accepted.
   rank=retention_key(row)
   if rank is not None and (best_rank is None or rank<best_rank):
    best=full.copy();best_rank=rank;best_iteration=iteration;row['retained']=True
    np.savez_compressed(str(output)+'.progress.npz',dense_delta=best,delta=best[SOURCE])
    Path(str(output)+'.progress.json').write_text(json.dumps(history,indent=2)+'\n')
   if time.monotonic()-start>seconds:break
  ym=shrink_ball_dual(ym+sigma*(mforward(bar)+ba),sigma*limit)
  yd=shrink_ball_dual(yd+sigma*np.diff(bar,axis=0),sigma*3.)
  yo=np.maximum(yo+sigma*outward(bar),0.)
  grad=madjoint(ym)+d1t(yd)+oadjoint(yo)+.001*(x-initial)+.02*d2t(np.diff(x,n=2,axis=0))+.005*lap(x)
  previous=x;x=preserve(x-tau*grad);bar=2*x-previous
  if not np.isfinite(x).all():raise ValueError('Nonfinite primal state; no repaired model produced')
 if best is None:
  best=initial_full.copy();retained='original_R51_dense_fallback_NOT_REPAIRED'
 else:retained='best_bounded_outline_preserving_temporal_study' if best_iteration else 'initial_dense_state_no_improving_bounded_step'
 final=np.zeros_like(initial);final[:]=best[:,ids]*1000;excess,step,outline,cap,_=metrics(final)
 status=study_status(excess,step,outline);status.update(retained_state=retained,history=history,independent_nodes=72,pinned_marked_vertices=int(pin.sum()),editable_vertices=len(ids),iterations=iteration,elapsed_seconds=time.monotonic()-start,maximum_material_mm=cap,early_outward_increment_mm=float(np.maximum(outward(final),0).max()))
 np.savez_compressed(output,dense_delta=best,delta=best[SOURCE]);Path(str(output)+'.json').write_text(json.dumps(status,indent=2)+'\n');print('R52_STUDY_RETAINED',json.dumps({k:v for k,v in status.items() if k!='history'}),flush=True)
 return status
if __name__=='__main__':solve(*sys.argv[1:4],iterations=int(os.environ.get('HGPT_R52_ITERATIONS','1200')),seconds=float(os.environ.get('HGPT_R52_SECONDS','600')))
