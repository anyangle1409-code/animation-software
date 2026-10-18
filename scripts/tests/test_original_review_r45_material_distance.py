import sys,unittest,numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r45_field import material_field
from original_review_r44_field import material_field as euclidean
class MaterialDistance(unittest.TestCase):
 def test_opposite_fold_surfaces_do_not_share_controls(self):
  r=np.array([[.15+(i if i<5 else 9-i)*.01,j*.01,0 if i<5 else .002] for i in range(10) for j in range(2)])
  faces=np.array([[2*i,2*i+1,2*i+2] for i in range(9)]+[[2*i+1,2*i+3,2*i+2] for i in range(9)])
  mask=np.ones((1,len(r)),bool)
  b=material_field(r,mask,faces,spacing=.015,radius=.025,taper=.005)
  self.assertFalse(set(b[0:6].indices)&set(b[-6:].indices))
  self.assertTrue(np.isfinite(b.data).all());self.assertLessEqual(float(np.max(b.sum(axis=1))),1.+1e-12)
  old=euclidean(r,mask,spacing=.015,radius=.025,taper=.005)
  print('OLD_GEOMETRIC_CONTROL_OVERLAP',len(set(old[0:6].indices)&set(old[-6:].indices)))
  self.assertTrue(set(old[0:6].indices)&set(old[-6:].indices))
 def test_control_weights_remain_nonnegative_bounded_and_separate_sides(self):
  r=np.array([[.15+i*.01,j*.01,0.] for i in range(4) for j in range(2)])
  f=np.array([[2*i,2*i+1,2*i+2] for i in range(3)]+[[2*i+1,2*i+3,2*i+2] for i in range(3)])
  r=np.r_[r,r*[-1,1,1]];f=np.r_[f,f+8];free=np.ones((1,len(r)),bool);free[0,[0,8]]=False
  b=material_field(r,free,f,spacing=.015,radius=.025,taper=.005)
  self.assertTrue((b.data>=0).all());self.assertLessEqual(float(np.max(b.sum(axis=1))),1.+1e-12)
  vertex=np.repeat(np.flatnonzero(free[0]),3)
  left=b[r[vertex,0]<0];right=b[r[vertex,0]>0]
  self.assertFalse(set(left.indices)&set(right.indices))
  full=np.zeros((len(r),3));full[free[0]]=(b@np.ones(b.shape[1])).reshape(-1,3)
  np.testing.assert_array_equal(full[~free[0]],0.)
if __name__=='__main__':unittest.main()
