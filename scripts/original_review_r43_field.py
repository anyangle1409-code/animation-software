"""Optional compact smooth material field; exact native gates remain unchanged."""
import numpy as np
from scipy import sparse
from scipy.spatial import cKDTree

def material_field(rest,free,spacing=.045,radius=.105,taper=.035):
 """Partition of unity on free vertices, fading to fixed material boundaries.

Wendland C2 weights share nearby control movements, avoiding independent
single-vertex repairs. Separate hemispheres never share a control.
"""
 rows=[];cols=[];values=[];count=0;offset=0
 for k,mask in enumerate(free):
  vertices=np.flatnonzero(mask)
  if not len(vertices):continue
  for sign in (-1,1):
   v=vertices[rest[vertices,0]*sign>0]
   if not len(v):continue
   points=rest[v];centers=[];distance=np.full(len(v),np.inf)
   while distance.max()>spacing:
    i=0 if not centers else int(distance.argmax());centers.append(points[i]);distance=np.minimum(distance,np.linalg.norm(points-points[i],axis=1))
   centers=np.array(centers);tree=cKDTree(centers);fixed=cKDTree(rest[~mask]);fade=np.clip(fixed.query(points)[0]/taper,0,1);fade=fade*fade*(3-2*fade)
   local=np.searchsorted(vertices,v)
   for j,near in enumerate(tree.query_ball_point(points,radius)):
    near=np.array(near);r=np.linalg.norm(centers[near]-points[j],axis=1)/radius;w=(1-r)**4*(1+4*r);w=w/w.sum()*fade[j]
    for axis in range(3):
     rows.extend([offset+int(local[j])*3+axis]*len(near));cols.extend((count+near*3+axis).tolist());values.extend(w.tolist())
   count+=len(centers)*3
  offset+=len(vertices)*3
 return sparse.coo_matrix((values,(rows,cols)),shape=(int(free.sum())*3,count)).tocsr()
