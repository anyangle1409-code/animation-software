"""Adversarial no-network tests for bilateral source surface-vertex proximity."""
import hashlib
import math
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

from anatomy_fit.bonehub_carpal_tarsal_vertex_proximity import (
    PAIR_NAMES, FROZEN_UPSTREAM_REV, audit, bbox_lower_bound,
    closest_vertex_pair, dist2, kd_tree, nearest_point,
    pair_diagnostic, vertices_from_binary_stl,
)


def stl(triangles, frame=b"3D Slicer output. SPACE=LPS"):
    result=bytearray(frame.ljust(80,b" "))
    result.extend(struct.pack("<I",len(triangles)))
    for a,b,c in triangles:
        flat=[0.0]*3+list(a)+list(b)+list(c)
        result.extend(struct.pack("<12fH",*flat,0))
    return bytes(result)


BASE=((0.,0.,0.),(1.,0.,0.),(0.,1.,0.))
SEPARATE=((0.,0.,2.),(1.,0.,2.),(0.,1.,2.))

class SourceVertexProximityTests(unittest.TestCase):
    def test_raw_binary_valid_face_vertices(self):
        src=stl([BASE,SEPARATE])
        verts,stats=vertices_from_binary_stl(src)
        self.assertEqual(len(verts),6)
        self.assertEqual(stats["source_triangle_count"],2)
        self.assertEqual(stats["header_declared_frame"],"LPS")

    def test_do_not_count_degenerate_orphan_vertex(self):
        bad=((100.,100.,100.),(100.,100.,100.),(100.,100.,100.))
        verts,stats=vertices_from_binary_stl(stl([BASE,bad]))
        self.assertEqual(len(verts),3)
        self.assertNotIn((100.,100.,100.),verts)
        self.assertEqual(stats["source_degenerate_triangles_excluded"],1)
        self.assertTrue(stats["all_valid_face_islands_retained"])

    def test_collinear_nonidentical_vertices_also_excluded(self):
        tri=((100.,0.,0.),(101.,0.,0.),(102.,0.,0.))
        verts,stats=vertices_from_binary_stl(stl([BASE,tri]))
        self.assertEqual(len(verts),3)
        self.assertEqual(stats["source_degenerate_triangles_excluded"],1)

    def test_reject_source_with_no_actual_face(self):
        with self.assertRaisesRegex(ValueError,"No usable"):
            vertices_from_binary_stl(stl([((1.,)*3,)*3]))

    def test_reject_invalid_lps(self):
        for frame in (b"SPACE=RAS", b"SPACE=LPS SPACE=RAS", b"unknown binary STL"):
            with self.subTest(frame=frame):
                with self.assertRaisesRegex(ValueError,"LPS"):
                    vertices_from_binary_stl(stl([BASE],frame))

    def test_nonfinite_coordinate_rejected(self):
        z=((float("nan"),0.,0.),(1.,0.,0.),(0.,1.,0.))
        with self.assertRaisesRegex(ValueError,"Nonfinite"):
            vertices_from_binary_stl(stl([z]))

    def test_mismatching_binary_triangle_count_rejected(self):
        src=stl([BASE])
        with self.assertRaisesRegex(ValueError,"count"):
            vertices_from_binary_stl(src[:80]+struct.pack("<I",2)+src[84:])
        with self.assertRaisesRegex(ValueError,"count"):
            vertices_from_binary_stl(src+b"\x00")

    def test_balanced_tree_matches_bruteforce_over_multiple_quadrants(self):
        sites=[(float(i%11-5),float(i//11-5),float((i*i)%7-3))
               for i in range(102)]
        tree=kd_tree(list(sites))
        for q in ((0.,0.,0.),(3.9,-2.7,5.2),(-100.,2.,3.),
                  (10.,12.,-9.),(1.1,1.2,1.3)):
            actual=nearest_point(tree,q)
            expected=min((dist2(s,q),s) for s in sites)
            self.assertEqual(actual,expected)

    def test_nearest_points_opposite_signs_and_no_axis_assumptions(self):
        a=((-100.,0.,0.),(-99.,0.,0.),(-100.,1.,0.))
        b=((-100.,0.,2.),(-99.,0.,2.),(-100.,1.,2.))
        d,pa,pb=closest_vertex_pair(a,b)
        self.assertEqual(d,2.0)
        self.assertEqual(pa[0],pb[0])
        self.assertEqual(pa[1],pb[1])
        self.assertEqual(bbox_lower_bound(a,b),2.0)

    def test_nearest_pair_symmetric_without_changing_source_orientation(self):
        a=((-2.,-1.,1.),(-1.,2.,4.),(0.,4.,0.))
        b=((1.,-1.,0.),(2.,2.,5.),(5.,4.,0.),(3.,2.,5.))
        d,pa,pb=closest_vertex_pair(a,b)
        e,pb2,pa2=closest_vertex_pair(b,a)
        self.assertEqual(d,e)
        self.assertEqual((pa,pb),(pa2,pb2))

    def test_overlapping_aabb_is_just_zero_lower_bound_not_contact(self):
        a=((0.,0.,0.),(2.,0.,0.),(1.,2.,0.))
        b=((0.,0.,1.),(2.,0.,1.),(1.,2.,1.))
        p=pair_diagnostic(a,b)
        self.assertEqual(p["bbox_separation_lower_bound_source_units_unknown"],1)
        self.assertEqual(p["minimum_source_face_vertex_pair_distance_source_units_unknown"],1)
        self.assertFalse(p["contact_patch_or_joint_centre_identified"])

    def test_orthogonal_crossing_surface_vertices_do_not_prove_intersection(self):
        a=((0.,0.,0.),(2.,0.,0.),(0.,2.,0.))
        b=((1.,0.,-1.),(1.,0.,1.),(1.,3.,0.))
        d=pair_diagnostic(a,b)
        self.assertEqual(d["bbox_separation_lower_bound_source_units_unknown"],0)
        self.assertGreater(d["minimum_source_face_vertex_pair_distance_source_units_unknown"],0)
        self.assertTrue(d["no_triangle_intersection_or_containment_test_performed"])
        self.assertFalse(d["skeletal_geometry_accepted"])

    def test_reports_all_contact_results_noncanonical(self):
        p=pair_diagnostic(BASE,SEPARATE)
        self.assertTrue(p["vertex_distance_is_upper_bound_on_true_triangle_surface_minimum"])
        self.assertTrue(p["bbox_distance_is_lower_bound_on_true_triangle_surface_minimum"])
        self.assertFalse(p["real_physical_units_verified"])
        self.assertFalse(p["ct_to_stl_registration_accepted"])

    def test_refuse_empty_and_invalid_points(self):
        with self.assertRaisesRegex(ValueError,"Empty"):
            closest_vertex_pair((),BASE)
        with self.assertRaisesRegex(ValueError,"Empty"):
            closest_vertex_pair(BASE,())

    def test_bilateral_pair_manifest_is_symmetric_and_explicit(self):
        self.assertEqual(len(PAIR_NAMES),4)
        self.assertEqual(len(set(p[2] for p in PAIR_NAMES)),4)
        for p in PAIR_NAMES:
            self.assertIn("{side}",p[0])
            self.assertIn("{side}",p[1])
            self.assertNotEqual(p[0],p[1])

    def test_fail_closed_cohort_and_missing_source_identity(self):
        with self.assertRaisesRegex((ValueError),"(revision|flags)"):
            audit({"source_revision":"forged"},Path("/tmp/not-patient-data"),False)

    def test_no_canonical_promotion_possible_in_no_network_synthetic_audit(self):
        index={"source_revision":FROZEN_UPSTREAM_REV}
        with self.assertRaises(ValueError):
            audit(index,Path("/tmp/not-patient-data"),False)


if __name__=="__main__":
    unittest.main()
