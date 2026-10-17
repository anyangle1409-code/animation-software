import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r43_geometry import area_gradient,outline,cosine_gradient,normal_difference_gradient
class ConstraintGradients(unittest.TestCase):
 def test_area_and_cosine(self):
  p=np.array([[.02,.01,.03],[.03,-.01,.01],[-.01,.03,.02],[.01,.04,.025]])
  f=np.array([[0,1,2],[1,3,2]])
  for mode in ('area','cosine'):
   if mode=='area':
    ids=f[0];g=area_gradient(p[ids]);fn=lambda q:.5*np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]));q=p[ids]
   else:ids=f.ravel();_,g=cosine_gradient(p[f]);g=g.reshape(-1,3);fn=lambda q:cosine_gradient(q.reshape(2,3,3))[0];q=p[ids]
   for i in np.ndindex(q.shape):
    a=q.copy();b=q.copy();a[i]+=1e-7;b[i]-=1e-7
    self.assertAlmostEqual(g[i],(fn(a)-fn(b))/2e-7,delta=1e-7)
 def test_plane_intersection_silhouette(self):
  p=np.array([[.04,0,-.02],[.05,0,.03],[.02,.01,.01]])
  f=np.array([[0,1,2]]);gh=np.zeros(3);axis=np.array([0.,0.,1.]);normal=np.array([1.,0.,0.])
  value,ids,g=outline(p,f,gh,axis,normal,'r',0.)
  actual=np.zeros_like(p)
  for i,v in enumerate(ids):actual[v]+=g[i]
  for i in np.ndindex(p.shape):
   a=p.copy();b=p.copy();a[i]+=1e-7;b[i]-=1e-7
   numeric=(outline(a,f,gh,axis,normal,'r',0.)[0]-outline(b,f,gh,axis,normal,'r',0.)[0])/2e-7
   self.assertAlmostEqual(actual[i],numeric,delta=1e-7)
 def test_normal_vector_constraint_sees_coplanar_bending(self):
  t=np.array([[[0.,0.,0.],[.01,0.,0.],[0.,.01,0.]],[[.01,0.,0.],[.01,.01,0.],[0.,.01,0.]]])
  axis=np.array([1.,0.,0.]);_,g=normal_difference_gradient(t,axis)
  self.assertGreater(np.linalg.norm(g),1.)
  for i in np.ndindex(t.shape):
   a=t.copy();b=t.copy();a[i]+=1e-8;b[i]-=1e-8
   numeric=(normal_difference_gradient(a,axis)[0]-normal_difference_gradient(b,axis)[0])/2e-8
   self.assertAlmostEqual(g[i],numeric,delta=1e-6)
if __name__=='__main__':unittest.main()
