"""R57 unit tests: do not accept a smooth-looking invalid shoulder candidate."""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r57_local_temporal import bounded_smoothing,mirror_centres


class R57(unittest.TestCase):
    def setUp(self):
        self.rest=np.array([[-.1,0,1.4],[-.12,0,1.4],
                            [.1,0,1.4],[.12,0,1.4],
                            [0.,0.,1.5]],float)
        self.edges=np.array([[0,1],[2,3]])
        self.delta=np.zeros((72,5,3),float)
        self.delta[118-95,0,0]=.024
        self.delta[118-95,2,0]=.024
        self.allowed=np.ones((72,5),bool)
        self.allowed[[0,15,71]]=False

    def test_only_local_controls_move_and_original_data_immutable(self):
        original=self.delta.copy()
        r,metrics=bounded_smoothing(self.delta,self.allowed,self.rest,self.edges,[0,2])
        self.assertTrue(np.array_equal(self.delta,original))
        self.assertLess(abs(r[118-95,0,0]),abs(original[118-95,0,0]))
        self.assertTrue(np.array_equal(r[123-95:],original[123-95:]))
        self.assertTrue(np.array_equal(r[:114-95],original[:114-95]))
        self.assertEqual(metrics["model_saved"],False)

    def test_neither_source_lockout_nor_distant_components_move(self):
        result,_=bounded_smoothing(self.delta,self.allowed,self.rest,self.edges,[0,2])
        self.assertTrue(np.array_equal(result[[0,15,71]],self.delta[[0,15,71]]))
        self.assertTrue(np.array_equal(result[:,4],self.delta[:,4]))

    def test_per_node_frozen_values_remain_exact(self):
        self.allowed[118-95,0]=False
        self.delta[118-95,0]=0
        result,_=bounded_smoothing(self.delta,self.allowed,self.rest,self.edges,[0,2])
        self.assertTrue(np.array_equal(result[118-95,0],self.delta[118-95,0]))
        self.assertFalse(np.any(result[~self.allowed]))

    def test_never_adopt_out_of_scope_source(self):
        self.allowed[118-95,0]=False
        with self.assertRaises(ValueError):
            bounded_smoothing(self.delta,self.allowed,self.rest,self.edges,[0,2])

    def test_frozen_45_mm_cap_guard(self):
        self.delta[118-95,0,0]=.05
        with self.assertRaises(ValueError):
            bounded_smoothing(self.delta,self.allowed,self.rest,self.edges,[0,2])

    def test_bilateral_correspondence_rejects_inaccurate_mirror(self):
        self.assertEqual(mirror_centres(self.rest,(0,),1.).tolist(),[0,2])
        broken=self.rest.copy()
        broken[2,0]=.15
        with self.assertRaises(ValueError):
            mirror_centres(broken,(0,),1.)


if __name__=="__main__":
    unittest.main()
