"""Independent exhaustive box oracle for bounded source candidate enumeration."""
import copy
import importlib.util
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent / 'anatomy_fit'))


def oracle(a, b):
    # Exhaustive independent coordinate interval comparisons, not a sweep.
    pairs = []
    for i, ta in enumerate(a):
        for j, tb in enumerate(b):
            if all(not (max(v[k] for v in ta) < min(v[k] for v in tb) or
                        max(v[k] for v in tb) < min(v[k] for v in ta))
                   for k in range(3)):
                pairs.append([i,j])
    return pairs


class BroadphaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.enumerate = None
        if importlib.util.find_spec('source_triangle_broadphase'):
            import source_triangle_broadphase
            cls.enumerate = staticmethod(source_triangle_broadphase.candidate_pairs)

    def check(self, a, b, want, **kwargs):
        self.assertTrue(callable(self.enumerate), 'Missing complete candidate box sweep')
        before = copy.deepcopy([a,b])
        r = self.enumerate(a,b,**kwargs)
        self.assertEqual(r['triangle_index_pairs'],want)
        self.assertEqual([a,b],before)
        self.assertTrue(r['supplied_box_enumeration_complete'])
        self.assertFalse(r['whole_surface_clearance_verified'])
        self.assertFalse(r['anatomical_contact_accepted'])
        self.assertFalse(r['physical_units_verified'])
        self.assertEqual(r['source_triangle_counts'],[len(a),len(b)])
        return r

    def test_closed_boxes_keep_boundary_contact_and_original_ids(self):
        a = [[(4,0,0),(5,0,0),(4,1,0)],[(0,0,0),(2,0,0),(0,2,0)]]
        b = [[(2,0,0),(3,0,0),(2,1,0)],[(8,0,0),(9,0,0),(8,1,0)]]
        self.check(a,b,[[1,0]])

    def test_positive_subnormal_gap_not_rounded_into_candidate(self):
        a = [[(0,0,0),(1,0,0),(0,1,0)]]
        b = [[(0,0,5e-324),(1,0,5e-324),(0,1,5e-324)]]
        self.check(a,b,[])

    def test_duplicate_faces_and_degenerate_islands_are_not_removed(self):
        t = [(0,0,0),(1,0,0),(0,1,0)]
        a, b = [t,t,[(0,0,0)]*3],[t,[(0,0,0)]*3]
        self.check(a,b,[[0,0],[0,1],[1,0],[1,1],[2,0],[2,1]])

    def test_box_overlap_is_not_triangle_intersection(self):
        self.check([[(0,0,0),(2,0,0),(0,2,0)]],
                   [[(2,2,0),(1,2,0),(2,1,0)]],[[0,0]])

    def test_ordered_random_sets_match_exhaustive_box_oracle(self):
        rng = random.Random(620111)
        for _ in range(25):
            a = [[tuple(rng.randint(-4,4) for _ in range(3)) for _ in range(3)]
                 for _ in range(9)]
            b = [[tuple(rng.randint(-4,4) for _ in range(3)) for _ in range(3)]
                 for _ in range(7)]
            self.check(a,b,oracle(a,b))
            self.check(b,a,oracle(b,a))

    def test_check_limit_never_returns_partial_candidates(self):
        self.assertTrue(callable(self.enumerate), 'Missing complete candidate box sweep')
        t = [(0,0,0),(1,0,0),(0,1,0)]
        with self.assertRaises(RuntimeError): self.enumerate([t,t],[t,t],max_checks=3)
        self.check([t,t],[t,t],[[0,0],[0,1],[1,0],[1,1]],max_checks=4)

    def test_invalid_limit_rejected_even_for_disjoint_sets(self):
        self.assertTrue(callable(self.enumerate), 'Missing complete candidate box sweep')
        t = [(0,0,0),(1,0,0),(0,1,0)]
        for limit in (0,-1,True,1.5,2_000_001):
            with self.assertRaises(ValueError): self.enumerate([t],[t],max_checks=limit)

    def test_empty_malformed_and_invalid_coordinates_refused(self):
        self.assertTrue(callable(self.enumerate), 'Missing complete candidate box sweep')
        t = [(0,0,0),(1,0,0),(0,1,0)]
        for bad in ([],None,[t[:2]],[[(float('nan'),0,0),(1,0,0),(0,1,0)]],
                    [[(True,0,0),(1,0,0),(0,1,0)]]):
            with self.assertRaises(ValueError): self.enumerate(bad,[t])


if __name__ == '__main__':
    unittest.main()
