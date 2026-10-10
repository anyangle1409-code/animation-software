"""No-network first-party adversarial tests of the whole wrist/foot source graph."""
import copy
import math
import random
import unittest
from pathlib import Path
from unittest.mock import patch

from anatomy_fit import bonehub_wrist_foot_pair_graph as g


class FullCarpalTarsalSourceGraphTests(unittest.TestCase):
    def test_30_unique_carpal_tarsal_meshes(self):
        self.assertEqual(g.MESH_COUNT,30)
        self.assertEqual(len(g.CARPAL_LABELS),8)
        self.assertEqual(len(g.TARSAL_LABELS),7)
        self.assertEqual(len(set(g.CARPAL_LABELS)),8)
        self.assertEqual(len(set(g.TARSAL_LABELS)),7)

    def test_graph_has_44_label_pairs(self):
        self.assertEqual(g.PAIR_COUNT,44)
        self.assertEqual(len(g.CARPAL_CANDIDATES),12)
        self.assertEqual(len(g.TARSAL_CANDIDATES),10)
        g.verify_graph()

    def test_each_of_15_bones_appears_in_graph(self):
        for labels, edges in ((g.CARPAL_LABELS,g.CARPAL_CANDIDATES),
                              (g.TARSAL_LABELS,g.TARSAL_CANDIDATES)):
            self.assertEqual({bone for a,b,_ in edges for bone in (a,b)},set(labels))

    def test_carpal_edges_provisional_and_morphological(self):
        self.assertIn(("TRIQUETRUM","PISIFORM","PISOTRIQUETRAL"),g.CARPAL_CANDIDATES)
        self.assertIn(("SCAPHOID","CAPITATE","MIDCARPAL"),g.CARPAL_CANDIDATES)
        self.assertIn(("LUNATE","HAMATE","CONTEXT_CANDIDATE"),g.CARPAL_CANDIDATES)
        self.assertNotIn(("SCAPHOID","HAMATE","MIDCARPAL"),g.CARPAL_CANDIDATES)

    def test_foot_has_all_three_naviculocuneiform_links(self):
        for name in ("MEDIAL_CUNEIFORM","INTERMEDIATE_CUNEIFORM",
                     "LATERAL_CUNEIFORM"):
            self.assertIn(("NAVICULAR",name,"NAVICULOCUNEIFORM"),g.TARSAL_CANDIDATES)

    def test_foot_variant_navicular_cuboid_is_not_mandatory(self):
        self.assertIn(("NAVICULAR","CUBOID","CONTEXT_CANDIDATE"),g.TARSAL_CANDIDATES)

    def test_exact_original_four_pair_families_preserved(self):
        self.assertEqual(len(g.PR38_REFERENCE_ROUNDED),8)
        for a,b in (("SCAPHOID","LUNATE"),("TALUS","CALCANEUS"),
                    ("TALUS","NAVICULAR"),("CALCANEUS","CUBOID")):
            for side in ("LEFT","RIGHT"):
                self.assertIn((side,a,b),g.PR38_REFERENCE_ROUNDED)

    def test_source_path_construction_no_missing_or_invented_bone(self):
        self.assertEqual(g.label_path("carpus","LEFT","SCAPHOID"),
                         "HAND_LEFT/SCAPHOID_LEFT.stl")
        self.assertEqual(g.label_path("tarsus","RIGHT","INTERMEDIATE_CUNEIFORM"),
                         "FOOT_RIGHT/INTERMEDIATE_CUNEIFORM_RIGHT.stl")
        self.assertNotEqual(g.label_path("tarsus","LEFT","TALUS"),
                            g.label_path("tarsus","RIGHT","TALUS"))

    def test_unknown_bones_not_guessed(self):
        with self.assertRaisesRegex(ValueError,"Unknown carpal"):
            g.label_path("carpus","LEFT","ULNA")
        with self.assertRaisesRegex(ValueError,"Unknown tarsal"):
            g.label_path("tarsus","LEFT","METATARSAL")
        with self.assertRaisesRegex(ValueError,"Invalid"):
            g.label_path("ribs","LEFT","TALUS")

    def test_reject_duplicate_candidate_edge_even_reversed(self):
        with patch.object(g,"CARPAL_CANDIDATES",
                          g.CARPAL_CANDIDATES[:-1]+(("LUNATE","SCAPHOID","PROXIMAL_ROW"),)):
            with self.assertRaisesRegex(ValueError,"Duplicate anatomical"):
                g.verify_graph()

    def test_reject_unverified_carpal_label(self):
        with patch.object(g,"CARPAL_CANDIDATES",
                          g.CARPAL_CANDIDATES[:-1]+(("SCAPHOID","ULNA","MIDCARPAL"),)):
            with self.assertRaisesRegex(ValueError,"Unexpected"):
                g.verify_graph()

    def test_dist2_uses_all_three_dimensions(self):
        points_a=((0.,0.,0.),(10.,0.,0.),(0.,10.,0.))
        points_b=((0.,0.,5.),(10.,0.,5.),(0.,10.,5.))
        trees=(g.kd_tree(list(points_a)),g.kd_tree(list(points_b)))
        self.assertEqual(g.min_vertex_distance_with_cached_tree(
            points_a,points_b,*trees),5.0)

    def test_closest_point_is_not_aabb_overlap(self):
        a=((-1.,-1.,0.),(1.,0.,0.),(0.,1.,0.))
        b=((-1.,-1.,2.),(1.,0.,2.),(0.,1.,2.))
        trees=g.kd_tree(list(a)),g.kd_tree(list(b))
        self.assertEqual(g.min_vertex_distance_with_cached_tree(a,b,*trees),2)
        self.assertEqual(g.bbox_lower_bound(a,b),2)
        self.assertGreaterEqual(g.min_vertex_distance_with_cached_tree(a,b,*trees),
                                g.bbox_lower_bound(a,b))

    def test_cached_tree_exact_matches_quadratic_bruteforce(self):
        rng=random.Random(1729)
        for len_a,len_b in ((7,13),(35,10),(200,100)):
            a=tuple(tuple(rng.uniform(-10.,10.) for _ in range(3))
                    for _ in range(len_a))
            b=tuple(tuple(rng.uniform(-10.,10.) for _ in range(3))
                    for _ in range(len_b))
            exact=min(math.sqrt(sum((p[j]-q[j])**2 for j in range(3)))
                      for p in a for q in b)
            actual=g.min_vertex_distance_with_cached_tree(
                a,b,g.kd_tree(list(a)),g.kd_tree(list(b)))
            self.assertAlmostEqual(exact,actual,places=11)

    def test_tree_direction_does_not_change_minimum(self):
        a=((1.,3.,5.),(2.,4.,6.),(5.,1.,2.))
        b=((8.,3.,9.),(-1.,9.,3.),(3.,4.,1.),(2.,3.,5.))
        first=g.min_vertex_distance_with_cached_tree(
            a,b,g.kd_tree(list(a)),g.kd_tree(list(b)))
        second=g.min_vertex_distance_with_cached_tree(
            b,a,g.kd_tree(list(b)),g.kd_tree(list(a)))
        self.assertEqual(first,second)

    def test_invalid_empty_mesh_refused(self):
        with self.assertRaisesRegex(ValueError,"Incomplete actual"):
            g.min_vertex_distance_with_cached_tree((),((1.,2.,3.),),None,g.kd_tree([(1.,2.,3.)]))

    def test_frozen_revision_and_no_unsafe_build_index(self):
        with self.assertRaisesRegex(ValueError,"revision"):
            g.audit_graph({"source_revision":"bad"},Path("/tmp/hgpt-full-graph"),False)

    def test_graph_sources_are_labels_not_physiological_targets(self):
        self.assertIn("intercarpal-joints",g.RAW_GRAPH_URLS[0])
        self.assertIn("intertarsal-joints",g.RAW_GRAPH_URLS[1])
        self.assertEqual(g.FROZEN_UPSTREAM_REV,
                         "ac8de2b38f5ae1a0996053ca0639dd6ae43358f1")

    def test_duplicate_pair_mutation_with_unchanged_count_refused(self):
        modified=list(g.TARSAL_CANDIDATES)
        modified[-1]=modified[0]
        with patch.object(g,"TARSAL_CANDIDATES",tuple(modified)):
            with self.assertRaisesRegex(ValueError,"Duplicate"):
                g.verify_graph()

if __name__=="__main__":
    unittest.main()
