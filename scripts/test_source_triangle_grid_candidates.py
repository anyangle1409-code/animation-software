"""Exact partition completeness, independently compared to exhaustive boxes."""
import importlib.util
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent/'anatomy_fit'))
from test_source_triangle_broadphase import oracle


class GridCandidates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.enumerate=None
        if importlib.util.find_spec('source_triangle_grid_candidates'):
            from source_triangle_grid_candidates import candidate_pairs
            cls.enumerate=staticmethod(candidate_pairs)

    def check(self,a,b,want,**kw):
        self.assertTrue(callable(self.enumerate),'Missing bounded exact grid candidates')
        r=self.enumerate(a,b,**kw)
        self.assertEqual(r['triangle_index_pairs'],want)
        self.assertTrue(r['supplied_box_enumeration_complete'])
        for k in ('whole_surface_clearance_verified','anatomical_contact_accepted','physical_units_verified'):
            self.assertFalse(r[k])
        return r

    def test_negative_coordinates_and_closed_cell_boundaries(self):
        a=[[(-2,-2,0),(0,-2,0),(-2,0,0)]]
        b=[[(0,-2,0),(1,-2,0),(0,-1,0)]]
        self.check(a,b,[[0,0]])

    def test_same_cell_positive_subnormal_gap_still_separates(self):
        self.check([[(0,0,0),(1,0,0),(0,1,0)]],
                   [[(0,0,5e-324),(1,0,5e-324),(0,1,5e-324)]],[])

    def test_duplicate_faces_and_degenerate_islands_preserved(self):
        t=[(0,0,0),(1,0,0),(0,1,0)]
        self.check([t,t,[(0,0,0)]*3],[t],[[0,0],[1,0],[2,0]])

    def test_exact_exhaustive_completeness_for_multiple_partition_widths(self):
        rng=random.Random(711126)
        for _ in range(12):
            a=[[tuple(rng.randint(-3,3) for _ in range(3)) for _ in range(3)] for _ in range(8)]
            b=[[tuple(rng.randint(-3,3) for _ in range(3)) for _ in range(3)] for _ in range(6)]
            for width in (.5,1,2): self.check(a,b,oracle(a,b),cell_width=width)
            self.check(b,a,oracle(b,a))

    def test_work_limit_fails_without_partial_result(self):
        self.assertTrue(callable(self.enumerate),'Missing bounded exact grid candidates')
        t=[(0,0,0),(1,0,0),(0,1,0)]
        with self.assertRaises(RuntimeError): self.enumerate([t,t],[t,t],max_checks=3)
        self.check([t,t],[t,t],[[0,0],[0,1],[1,0],[1,1]],max_checks=4)

    def test_cell_reference_limit_closed_boundary_and_huge_range(self):
        self.assertTrue(callable(self.enumerate),'Missing bounded exact grid candidates')
        t=[(0,0,0),(1,0,0),(0,1,0)]
        with self.assertRaises(RuntimeError): self.enumerate([t],[t],max_cell_references=7)
        self.check([t],[t],[[0,0]],max_cell_references=8)
        with self.assertRaises(RuntimeError): self.enumerate([t],[t],cell_width=5e-324)

    def test_invalid_parameters_and_empty_inputs_refused(self):
        self.assertTrue(callable(self.enumerate),'Missing bounded exact grid candidates')
        t=[(0,0,0),(1,0,0),(0,1,0)]
        for kw in ({'cell_width':0},{'cell_width':True},{'cell_width':float('inf')},
                   {'max_checks':0},{'max_checks':True},{'max_checks':2_000_001},
                   {'max_cell_references':0},{'max_cell_references':True},
                   {'max_cell_references':500_001}):
            with self.assertRaises(ValueError): self.enumerate([t],[t],**kw)
        with self.assertRaises(ValueError): self.enumerate([],[t])

    def test_repeated_cell_hits_have_their_own_work_limit(self):
        self.assertTrue(callable(self.enumerate),'Missing bounded exact grid candidates')
        t=[(0,0,0),(1,0,0),(0,1,0)]
        try:
            with self.assertRaises(RuntimeError):
                self.enumerate([t],[t],max_cell_pair_visits=3)
        except TypeError:
            self.fail('Missing repeated cell-hit work budget')
        r=self.check([t],[t],[[0,0]],max_cell_pair_visits=4)
        self.assertEqual(r['cell_pair_visits'],4)
        self.assertEqual(r['candidate_comparisons'],1)


if __name__=='__main__': unittest.main()
