"""Synthetic tests for read-only mesh ring coverage."""
import unittest
from scripts.cloud_body_analysis.edge_ring_coverage import describe

V = [(0,0,0), (1,0,0), (1,1,0), (0,1,0), (2,0,0)]
T = [(0,1,2), (0,2,3), (1,4,2)]
S = [{"name":"pinned", "vertex_ids":[0,1]}]

class RingTests(unittest.TestCase):
    def test_exact_membership(self):
        r = describe(V,T,S,2)
        self.assertEqual([x["vertex_ids"] for x in r["regions"][0]["rings"]],
                         [[0,1],[2,3,4],[]])
        self.assertFalse(r["anatomical_region_certified"])
        self.assertFalse(r["movement_approved"])
    def test_deterministic(self):
        self.assertEqual(describe(V,T,S),describe(V,T,S))
    def test_missing_edge(self):
        with self.assertRaises(ValueError):
            describe(V,T,[{"name":"bad","vertex_ids":[3,4]}])
    def test_duplicate_name(self):
        with self.assertRaises(ValueError): describe(V,T,S+S)
    def test_bad_edge_ids(self):
        for pair in ([0,False],[0,5],[0,0]):
            with self.subTest(pair=pair), self.assertRaises(ValueError):
                describe(V,T,[{"name":"bad","vertex_ids":pair}])
    def test_bad_faces(self):
        for faces in ([(0,1,1)],[(0,1,5)],[(0,1,True)]):
            with self.subTest(faces=faces), self.assertRaises(ValueError):
                describe(V,faces,S)
    def test_nonfinite(self):
        with self.assertRaises(ValueError):
            describe([(float("nan"),0,0)]+V[1:],T,S)
    def test_degenerate(self):
        with self.assertRaises(ValueError): describe([V[0],V[0]]+V[2:],T,S)
    def test_depth_validation(self):
        for depth in (-1,13,True,1.5):
            with self.subTest(depth=depth), self.assertRaises(ValueError):
                describe(V,T,S,depth)
    def test_missing_seeds(self):
        with self.assertRaises(ValueError): describe(V,T,[])

if __name__ == "__main__":
    unittest.main()
