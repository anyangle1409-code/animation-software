"""Pure-Python mock tests for immutable rest-mesh skin/shape-key hotspot probes."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import unittest

p = Path(__file__).resolve().parents[2] / "phone_blender" / "rest_roi_audit.py"
spec = importlib.util.spec_from_file_location("rest_roi_audit", p)
roi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(roi)

def sample_body(weight=0.75, delta=0.005):
    xyz = [(0.12, 0.17, 1.47), (0.13, 0.18, 1.48), (0.8, 0.9, 1.5)]
    vertices = [NS(index=i, co=p, groups=[NS(group=0, weight=weight)]) for i, p in enumerate(xyz)]
    basis = NS(name="Basis", data=[NS(co=p) for p in xyz], value=0, relative_key=None)
    key = NS(name="shoulder_corrective",
             data=[NS(co=(p[0]+delta, p[1], p[2])) for p in xyz],
             value=0, relative_key=basis)
    mesh = NS(vertices=vertices, shape_keys=NS(key_blocks=[basis, key]))
    return NS(name="body", data=mesh, vertex_groups=[NS(index=0, name="shoulder_cap_r")])

class TestROI(unittest.TestCase):
    def test_weight_and_stored_key_delta(self):
        report = roi.analyze(sample_body())
        cell = next(x for x in report["regions"] if x["name"] == "press_posterior_posX_high")
        self.assertEqual(cell["sampled_vertices"], 2)
        self.assertEqual(cell["mean_total_skin_weight"], 0.75)
        self.assertEqual(cell["top_influence_group_means"][0]["name"], "shoulder_cap_r")
        self.assertEqual(cell["largest_stored_shape_key_deltas"][0]["mean_absolute_delta_from_basis_mm"], 5.0)
        self.assertIn("NOT_ANATOMICAL_APPROVAL", report["status"])

    def test_missing_shape_keys_rejected(self):
        b = sample_body()
        b.data.shape_keys = None
        with self.assertRaisesRegex(ValueError, "shape-key"):
            roi.analyze(b)

    def test_mismatched_shape_key_topology_rejected(self):
        b = sample_body()
        b.data.shape_keys.key_blocks[1].data.pop()
        with self.assertRaisesRegex(ValueError, "mismatches mesh topology"):
            roi.analyze(b)

    def test_negative_group_weight_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid group"):
            roi.analyze(sample_body(weight=-0.01))

    def test_nonfinite_coordinates_rejected(self):
        b = sample_body()
        b.data.vertices[0].co = (float("nan"), 0, 0)
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            roi.analyze(b)

    def test_empty_roi_is_explicit(self):
        b = sample_body()
        b.data.vertices = [NS(index=0, co=(9, 9, 9), groups=[])]
        b.data.shape_keys.key_blocks[0].data = [NS(co=(9, 9, 9))]
        b.data.shape_keys.key_blocks[1].data = [NS(co=(9, 9, 9))]
        report = roi.analyze(b)
        self.assertTrue(all(x["sampled_vertices"] == 0 for x in report["regions"]))
        self.assertTrue(all(x["mean_total_skin_weight"] is None for x in report["regions"]))

if __name__ == "__main__":
    unittest.main()
