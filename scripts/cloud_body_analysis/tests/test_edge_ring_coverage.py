"""Synthetic tests for read-only mesh ring coverage."""
import unittest
from scripts.cloud_body_analysis.edge_ring_coverage import describe, measure_ring_edges

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


    def test_expanded_edge_measurements(self):
        region = describe(V,T,S,1)
        posed = list(V)
        posed[4] = (3,0,0)
        measured = measure_ring_edges(V,posed,T,region["regions"][0],region["topology_sha256"])
        self.assertEqual(measured["edge_count"], 7)
        self.assertEqual(measured["min_ratio"], 1)
        self.assertGreater(measured["max_ratio"], 1)
        self.assertFalse(measured["anatomical_region_certified"])
    def test_measurement_rejects_stale_membership(self):
        region = describe(V,T,S,1)
        bad = dict(region["regions"][0])
        bad["rings"] = [{"ring":0,"vertex_ids":[0,1]},{"ring":1,"vertex_ids":[2]}]
        with self.assertRaises(ValueError):
            measure_ring_edges(V,V,T,bad,region["topology_sha256"])
    def test_measurement_rejects_stale_topology(self):
        region = describe(V,T,S,1)
        with self.assertRaises(ValueError):
            measure_ring_edges(V,V,T,region["regions"][0],"0"*64)
    def test_measurement_rejects_nonfinite_pose(self):
        region = describe(V,T,S,1)
        with self.assertRaises(ValueError):
            measure_ring_edges(V,[(float("nan"),0,0)]+V[1:],T,
                               region["regions"][0],region["topology_sha256"])

if __name__ == "__main__":
    unittest.main()
