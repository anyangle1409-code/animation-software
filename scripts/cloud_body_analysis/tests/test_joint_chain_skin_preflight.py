"""Synthetic numerical guards only: no Blender model or ISB approval."""
import copy
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import joint_chain_skin_preflight as mod


class JointChainSkinPreflightTests(unittest.TestCase):
    def setUp(self):
        self.fixture = mod.synthetic_fixture()

    def test_all_regions_present_and_no_native_approval(self):
        r = mod.analyze(self.fixture)
        self.assertEqual(len(r["chain_pairs"]), 8)
        self.assertFalse(r["isb_joint_frames_calibrated"])
        self.assertEqual(r["generic_motion_tests_executed"], 0)
        self.assertFalse(r["clinical_rom_limits_applied"])

    def test_relative_rotation_and_return(self):
        r = mod.analyze(self.fixture)
        angles = r["chain_pairs"][0]["unsigned_relative_orientation_change_deg_NOT_ISB"]
        self.assertAlmostEqual(angles[1], 10.0, places=5)
        self.assertAlmostEqual(angles[2], 0.0, places=5)

    def test_skin_edge_ratios_not_strain(self):
        r = mod.analyze(self.fixture)
        self.assertEqual(r["skin_edges"][0]["mesh_edge_length_ratios_NOT_tissue_strain"], [1.0, 1.2, 1.0])

    def test_global_rigid_rotation_does_not_change_relative_motion(self):
        original = mod.analyze(self.fixture)
        fixture = copy.deepcopy(self.fixture)
        for sample in fixture["samples"]:
            for frame in sample["segments"].values():
                frame["axes"] = [[-v[1], v[0], v[2]] for v in frame["axes"]]
            for key, v in sample["skin_vertices"].items():
                sample["skin_vertices"][key] = [-v[1], v[0], v[2]]
        new = mod.analyze(fixture)
        self.assertEqual(original["chain_pairs"], new["chain_pairs"])
        self.assertEqual(original["skin_edges"], new["skin_edges"])

    def test_global_translation_does_not_change_edge_ratios(self):
        fixture = copy.deepcopy(self.fixture)
        for sample in fixture["samples"]:
            for key, v in sample["skin_vertices"].items():
                sample["skin_vertices"][key] = [v[0]+5, v[1]-2, v[2]+1]
        self.assertEqual(mod.analyze(fixture)["skin_edges"][0]["mesh_edge_length_ratios_NOT_tissue_strain"], [1, 1.2, 1])

    def test_reflection_rejected(self):
        self.fixture["samples"][1]["segments"]["humerus"]["axes"][0][0] *= -1
        with self.assertRaises(ValueError): mod.analyze(self.fixture)

    def test_missing_forearm_or_foot_segment_rejected(self):
        del self.fixture["samples"][1]["segments"]["forefoot"]
        with self.assertRaises(ValueError): mod.analyze(self.fixture)

    def test_mesh_topology_change_rejected(self):
        del self.fixture["samples"][1]["skin_vertices"]["2"]
        with self.assertRaises(ValueError): mod.analyze(self.fixture)

    def test_duplicate_undirected_edge_rejected(self):
        self.fixture["edges"].append([2, 1])
        with self.assertRaises(ValueError): mod.analyze(self.fixture)

    def test_zero_length_reference_edge_rejected(self):
        self.fixture["samples"][0]["skin_vertices"]["2"] = [0, 0, 0]
        with self.assertRaises(ValueError): mod.analyze(self.fixture)

    def test_nonfinite_coordinates_rejected(self):
        self.fixture["samples"][1]["skin_vertices"]["2"][0] = math.nan
        with self.assertRaises(ValueError): mod.analyze(self.fixture)

    def test_false_approval_rejected(self):
        self.fixture["anatomical_approval"] = True
        with self.assertRaises(ValueError): mod.analyze(self.fixture)

    def test_markdown_does_not_claim_validation(self):
        md = mod.markdown(mod.analyze(self.fixture))
        self.assertIn("NO BLENDER MODEL OR ANATOMY VALIDATED", md)
        self.assertIn("0/19", md)


if __name__ == "__main__":
    unittest.main()
