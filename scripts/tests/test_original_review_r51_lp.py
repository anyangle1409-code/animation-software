"""Exact box presolve must retain the objective and every hard constraint."""
import sys,unittest
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.optimize import linprog
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r51_lp import reduce_problem

class ExactPresolve(unittest.TestCase):
 def test_stable_hinges_become_exact_linear_cost_or_zero(self):
  B=sparse.csr_matrix([[1.],[1.],[1.],[1.]])
  rhs=np.array([-3.,3.,0.,.4]);soft=np.array([0,1,2]);w=np.array([2.,4.,3.])
  r=reduce_problem(B,rhs,w,soft,.5)
  self.assertEqual(r['matrix'].shape,(2,2))
  self.assertEqual(r['linear'].tolist(),[0]);self.assertEqual(r['zero'].tolist(),[1])
  for x in np.linspace(-.5,.4,13):
   v=np.r_[x,np.maximum(np.asarray(B@np.array([x])).ravel()[r['mixed']]-rhs[r['mixed']],0)]
   old=float(w@np.maximum(np.asarray(B@np.array([x])).ravel()[soft]-rhs[soft],0))
   self.assertAlmostEqual(float(r['cost']@v+r['constant']),old,places=10)

 def test_always_violated_surface_keeps_its_gradient(self):
  r=reduce_problem(sparse.csr_matrix([[-1.],[1.]]),np.array([-3.,.5]),np.array([1.]),np.array([0]),.5)
  z=linprog(r['cost'],A_ub=r['matrix'],b_ub=r['rhs'],bounds=[(-.5,.5)]+[(0,None)]*len(r['mixed']),method='highs')
  self.assertTrue(z.success);self.assertAlmostEqual(float(z.x[0]),.5)
  self.assertAlmostEqual(float(z.fun+r['constant']),2.5)

 def test_infeasible_hard_row_is_never_dropped(self):
  r=reduce_problem(sparse.csr_matrix([[-1.]]),np.array([-2.]),np.array([]),np.array([],int),1.)
  self.assertEqual(r['matrix'].shape[0],1)
  z=linprog(r['cost'],A_ub=r['matrix'],b_ub=r['rhs'],bounds=[(-1.,1.)],method='highs')
  self.assertEqual(z.status,2)

 def test_reduced_and_original_optima_agree_on_seeded_problems(self):
  rng=np.random.default_rng(510018)
  for case in range(30):
   with self.subTest(case=case):
    n=3;m=15;soft=np.arange(12);trust=.7
    B=sparse.csr_matrix(rng.normal(size=(m,n)))
    rhs=rng.uniform(-4.,4.,m);rhs[12:]=abs(rhs[12:])+.01
    w=rng.uniform(.1,3.,len(soft))
    r=reduce_problem(B,rhs,w,soft,trust)
    C=sparse.coo_matrix((-np.ones(len(soft)),(soft,np.arange(len(soft)))),shape=(m,len(soft))).tocsr()
    original=linprog(np.r_[np.zeros(n),w],A_ub=sparse.hstack([B,C]),b_ub=rhs,bounds=[(-trust,trust)]*n+[(0,None)]*len(soft),method='highs')
    reduced=linprog(r['cost'],A_ub=r['matrix'],b_ub=r['rhs'],bounds=[(-trust,trust)]*n+[(0,None)]*len(r['mixed']),method='highs')
    self.assertTrue(original.success);self.assertTrue(reduced.success)
    self.assertAlmostEqual(float(original.fun),float(reduced.fun+r['constant']),places=7)
    self.assertLessEqual(float(np.max(B[12:]@reduced.x[:n]-rhs[12:],initial=0)),1e-7)

if __name__=='__main__':unittest.main()
