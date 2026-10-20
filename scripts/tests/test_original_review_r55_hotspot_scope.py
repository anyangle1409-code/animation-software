"""Synthetic read-only hotspot, topology and owner-scope regressions."""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_original_review_r55_hotspot_scope import (
    dense_per_vertex_excess_mm, allowed_weight_scope, geodesic_to_patch_mm,
    compare_both_s7_muted_mm)


class R55(unittest.TestCase):
    def test_reproduces_original_curvature_difference_convention(self):
        a=np.zeros((161,1,3))
        b=a.copy()
        b[80,0,0]=.001
        self.assertAlmostEqual(dense_per_vertex_excess_mm(a,b)[0],32.)
        c=a.copy()
        c[80,0,1]=.001
        self.assertAlmostEqual(dense_per_vertex_excess_mm(b,c)[0],0.)

    def test_requires_s7_muted_in_both_source_models(self):
        base=np.zeros((161,1,3))
        r52=base.copy()
        r52[:,:,0]=.020
        off41=base.copy()
        off41[:,:,0]=.001
        off52=base.copy()
        off52[:,:,0]=-.019
        self.assertAlmostEqual(compare_both_s7_muted_mm(base,off41,r52,off52),0)
        self.assertGreater(np.linalg.norm(r52+off52-base,axis=2).max()*1000,0.9)

    def test_reject_incomplete_or_nonfinite_clip(self):
        a=np.zeros((161,2,3))
        for b in (a[:10],np.ones((161,3,3)),np.full_like(a,np.nan)):
            with self.assertRaises(ValueError):
                dense_per_vertex_excess_mm(a,b)

    def test_rest_mesh_geodesic_not_cross_fold_euclidean(self):
        rest=np.array([[0.,0.,0.],[1,0,0],[1,1,0],[0,1,0],[0,0,0.00001]])
        edges=np.array([[0,1],[1,2],[2,3],[3,4]])
        d=geodesic_to_patch_mm(rest,edges,np.array([0]))
        self.assertAlmostEqual(d[4],4000.0,places=2)
        self.assertEqual(d[0],0)

    def test_disconnected_rest_component_never_gets_false_zero(self):
        rest=np.array([[0,0,0],[1,0,0],[1,1,0],[2,2,0]],float)
        edges=np.array([[0,1],[1,2]])
        d=geodesic_to_patch_mm(rest,edges,np.array([0]))
        self.assertTrue(np.isinf(d[3]))

    def test_reject_invalid_patch_scope(self):
        s=dict(proposed_edit_vertices=list(range(26)),
               excluded_source_frozen_vertices=[27],
               vertices=list(range(26))+[27],
               seed_edge=[18081,21057],mirror_edge=[18057,21044])
        allowed=np.ones(50,dtype=bool)
        frozen=np.zeros(50,dtype=bool)
        self.assertEqual(len(allowed_weight_scope(s,allowed,frozen,50)),26)
        frozen[4]=True
        with self.assertRaises(ValueError):
            allowed_weight_scope(s,allowed,frozen,50)
        frozen[4]=False
        s["proposed_edit_vertices"]=[0]*26
        with self.assertRaises(ValueError):
            allowed_weight_scope(s,allowed,frozen,50)


if __name__=="__main__":
    unittest.main()
