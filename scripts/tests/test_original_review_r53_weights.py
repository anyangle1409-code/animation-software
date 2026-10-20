import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r53_weights import propose, validate

class Patch(unittest.TestCase):
 def setUp(self):
  self.w=np.array([[1.,0],[.8,.2],[.2,.8],[0,1.]])
  self.edges=np.array([[0,1],[1,2],[2,3]])
 def test_reduces_short_edge_gradient_without_touching_boundary(self):
  q=propose(self.w,self.edges,[1,2])
  self.assertLess(np.linalg.norm(q[1]-q[2]),np.linalg.norm(self.w[1]-self.w[2]))
  np.testing.assert_array_equal(q[[0,3]],self.w[[0,3]])
  np.testing.assert_allclose(q.sum(1),1,atol=1e-12)
  self.assertLessEqual(abs(q-self.w).max(),.025+1e-12)
 def test_rejects_outside_change(self):
  q=self.w.copy();q[0]=[.99,.01]
  with self.assertRaises(ValueError):validate(self.w,q,[1,2])
 def test_rejects_nonfinite_negative_and_unnormalized(self):
  for row in ([np.nan,0],[-.01,1.01],[.8,.1]):
   q=self.w.copy();q[1]=row
   with self.assertRaises(ValueError):validate(self.w,q,[1,2])
 def test_rejects_excessive_change(self):
  q=self.w.copy();q[1]=[.7,.3]
  with self.assertRaises(ValueError):validate(self.w,q,[1,2])

if __name__=='__main__':unittest.main()
