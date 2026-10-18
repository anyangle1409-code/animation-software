"""Diagnostic field using material distance, without changing any free vertex."""
import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import dijkstra

def material_field(rest,free,faces,spacing=.025,radius=.070,taper=.025):
 e=np.unique(np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1),axis=0)
 length=np.linalg.norm(rest[e[:,0]]-rest[e[:,1]],axis=1)
 graph=sparse.coo_matrix((np.r_[length,length],(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=(len(rest),len(rest))).tocsr()
 rows=[];cols=[];values=[];count=0;offset=0
 for mask in free:
  vertices=np.flatnonzero(mask)
  if not len(vertices):continue
  boundary=dijkstra(graph,indices=np.flatnonzero(~mask),directed=False,min_only=True) if (~mask).any() else np.full(len(rest),np.inf)
  for sign in (-1,1):
   v=vertices[rest[vertices,0]*sign>0]
   if not len(v):continue
   local_graph=graph[v][:,v];distances=[];distance=np.full(len(v),np.inf)
   while distance.max()>spacing:
    i=0 if not distances else int(distance.argmax());d=dijkstra(local_graph,indices=i,directed=False);distances.append(d);distance=np.minimum(distance,d)
   dd=np.array(distances).T;fade=np.clip(boundary[v]/taper,0,1);fade=fade*fade*(3-2*fade);local=np.searchsorted(vertices,v)
   for j in range(len(v)):
    near=np.flatnonzero(dd[j]<radius);r=dd[j,near]/radius;w=(1-r)**4*(1+4*r);w=w/w.sum()*fade[j]
    for axis in range(3):
     rows.extend([offset+int(local[j])*3+axis]*len(near));cols.extend((count+near*3+axis).tolist());values.extend(w.tolist())
   count+=len(distances)*3
  offset+=len(vertices)*3
 return sparse.coo_matrix((values,(rows,cols)),shape=(int(free.sum())*3,count)).tocsr()
