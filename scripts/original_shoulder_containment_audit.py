"""Conservative ray-vote classification for read-only shoulder diagnostics."""
import numpy as np

def classify_hits(hits,nearest):
 if not np.isfinite(nearest) or nearest<0:raise ValueError('Invalid nearest distance')
 counts=[]
 for ray in hits:
  if ray is None:counts.append(None);continue
  raw=[float(v) for v in ray]
  if not np.isfinite(raw).all():raise ValueError('Invalid ray distance')
  values=sorted(v for v in raw if v>1e-9)
  distinct=[]
  for v in values:
   if not distinct or v-distinct[-1]>1e-6:distinct.append(v)
  counts.append(len(distinct))
 votes=[n%2 if n is not None else None for n in counts]
 if nearest<=1e-5:status='on_skin'
 elif len(votes)>=3 and all(v==1 for v in votes):status='inside'
 elif len(votes)>=3 and all(v==0 for v in votes):status='outside'
 else:status='ambiguous'
 signed=nearest*1000 if status=='inside' else -nearest*1000 if status=='outside' else 0. if status=='on_skin' else None
 return dict(classification=status,ray_hit_counts=counts,nearest_skin_distance_mm=nearest*1000,signed_clearance_mm=signed)

def closed_triangle_surface(faces):
 f=np.asarray(faces,int)
 if f.ndim!=2 or f.shape[1]!=3 or not len(f):return False
 e=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1)
 _,counts=np.unique(e,axis=0,return_counts=True)
 return bool(np.all(counts==2))
