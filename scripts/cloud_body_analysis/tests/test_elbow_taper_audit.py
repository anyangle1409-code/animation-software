"""Synthetic PCA and fail-closed source guards; no anatomical approval."""
import ast
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import elbow_taper_audit as a

class ElbowPcaTests(unittest.TestCase):
    def test_rotation_invariant(self):
        r=np.random.default_rng(73)
        p=r.normal(size=(200,3))@np.diag([0.04,0.03,0.002])
        t=0.9
        q=np.array([[np.cos(t),-np.sin(t),0],[np.sin(t),np.cos(t),0],[0,0,1]])
        self.assertAlmostEqual(a.pca_spread_mm2(p),a.pca_spread_mm2(p@q.T),places=7)

    def test_quadratic_scale_not_circumference(self):
        p=np.random.default_rng(12).normal(size=(30,3))*0.03
        self.assertAlmostEqual(a.pca_spread_mm2(2*p),4*a.pca_spread_mm2(p),places=6)

    def test_degenerate_nonfinite_rejected(self):
        for p in (np.zeros((20,3)),np.ones((9,3)),np.full((20,3),np.nan)):
            with self.assertRaises(ValueError):
                a.pca_spread_mm2(p)

    def test_fixed_band_side_radius_and_labels(self):
        h=np.zeros(3); t=np.array([0.,0.,0.3])
        xyz=np.array([[.01,0,.165],[.02,0,.165],[.095,0,.165],
                      [.01,0,.19],[.01,0,.285]])
        labels=np.array(["upperarm_l","forearm_tw0_l","upperarm_l",
                         "upperarm_l","upperarm_r"])
        self.assertEqual(a.band_ids(xyz,labels,h,t,"l",.55).tolist(),[0,1])
        self.assertEqual(a.band_ids(xyz,labels,h,t,"l",.95).tolist(),[])

    def test_bad_skin_and_zero_control(self):
        with self.assertRaises(ValueError):
            a.band_ids(np.zeros((2,3)),np.array(["upperarm_l"]),np.zeros(3),np.ones(3),"l",.55)
        with self.assertRaises(ValueError):
            a.band_ids(np.zeros((2,3)),np.array(["upperarm_l"]*2),np.zeros(3),np.zeros(3),"l",.55)
        with self.assertRaises(ValueError):
            a.band_ids(np.zeros((2,3)),np.array(["upperarm_l"]*2),np.zeros(3),np.ones(3),"left",.55)

    def test_rig_hash_pinned(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"rig.json";p.write_text("{}")
            with self.assertRaisesRegex(ValueError,"SHA256"):
                a.controls(p)

    def test_anatomical_promotion_rejected_even_if_digest_matches(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"rig.json"
            raw=json.dumps({"model":"W8","source_sha256":a.W8_SHA,
              "original_source_unchanged":True,"bone_count":77,
              "status":"BLENDER_LOCAL_BONE_AXIS_INVENTORY_ONLY_ANATOMICAL_MAPPING_NOT_APPROVED",
              "anatomical_side_mapped":True}).encode()
            p.write_bytes(raw)
            with patch.object(a,"RIG_SHA",hashlib.sha256(raw).hexdigest()):
                with self.assertRaisesRegex(ValueError,"approval"):
                    a.controls(p)

    def test_no_blender_or_source_save(self):
        tree=ast.parse((ROOT/"elbow_taper_audit.py").read_text())
        imports=[n for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]
        self.assertFalse(any(x.name=="bpy" for n in imports for x in n.names))
        self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
          and n.func.attr in ("save_mainfile","save_as_mainfile") for n in ast.walk(tree)))
        self.assertIn("ANATOMY NOT APPROVED",a.markdown({"sides":{}}))

if __name__=="__main__":
    unittest.main()
