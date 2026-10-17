import unittest
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from solve_original_review_r38 import solve

class CoupledAreaSolverTests(unittest.TestCase):
    def test_recoverable_reversal_does_not_stop_at_unsigned_convergence(self):
        rest=np.array([[0.,0.,0.],[.002,0.,0.],[0.,.002,0.]])
        delta=np.zeros((1,3,3));delta[0,1,0]=-.006
        data={'rest':rest,'faces':np.array([[0,1,2]]),'base':rest[None],
              'mat':np.broadcast_to(np.eye(3),(1,3,3,3)).copy(),
              'weight':np.ones((1,1,3)),'delta':delta,
              'free':np.array([[False,True,False]]),
              'normal':np.tile([0.,0.,1.],(1,3,1))}
        result,report=solve(data,epochs=40)
        self.assertGreater(rest[1,0]+result[0,1,0],0)
        self.assertEqual(report['normal_rotations_over_90_degrees'],[0])

    def test_unsigned_area_cannot_hide_a_reversed_triangle(self):
        rest=np.array([[0.,0.,0.],[.004,0.,0.],[0.,.004,0.]])
        delta=np.zeros((1,3,3));delta[0,1,0]=-.006
        data={'rest':rest,'faces':np.array([[0,1,2]]),'base':rest[None],
              'mat':np.broadcast_to(np.eye(3),(1,3,3,3)).copy(),
              'weight':np.ones((1,1,3)),'delta':delta,
              'free':np.array([[False,True,False]]),
              'normal':np.tile([0.,0.,1.],(1,3,1))}
        result,report=solve(data,epochs=40)
        self.assertGreater(rest[1,0]+result[0,1,0],0)
        self.assertEqual(report['normal_rotations_over_90_degrees'],[0])

    def test_nonfinite_response_is_rejected(self):
        rest=np.array([[0.,0.,0.],[.01,0.,0.],[0.,.01,0.]])
        mat=np.broadcast_to(np.eye(3),(1,3,3,3)).copy();mat[0,0,0,0]=np.nan
        data={'rest':rest,'faces':np.array([[0,1,2]]),'base':rest[None],
              'mat':mat,'weight':np.ones((1,1,3)),'delta':np.zeros((1,3,3)),
              'free':np.ones((1,3),bool),'normal':np.tile([0.,0.,1.],(1,3,1))}
        with self.assertRaises(ValueError):solve(data,epochs=1)

    def test_both_poses_and_fixed_vertices(self):
        rest=np.array([[0.,0.,0.],[.01,0.,0.],[0.,.01,0.]])
        rot=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]])
        base=np.stack([rest,rest@rot.T])
        mat=np.broadcast_to(np.stack([np.eye(3),rot])[:,None],(2,3,3,3)).copy()
        delta=np.zeros((1,3,3));delta[0,1,0]=.015
        data={'rest':rest,'faces':np.array([[0,1,2]]),'base':base,'mat':mat,
              'weight':np.ones((2,1,3)), 'delta':delta,
              'free':np.array([[False,True,False]]),
              'normal':np.tile([0.,0.,1.],(1,3,1))}
        result,report=solve(data,epochs=40)
        self.assertEqual(report['extra_stretch_samples'],0)
        self.assertEqual(report['extra_collapse_samples'],0)
        np.testing.assert_array_equal(result[0,[0,2]],0)
        self.assertLess(result[0,1,0],.01)

if __name__=='__main__':unittest.main()

