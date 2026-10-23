"""No Blender dependency: guard the report-only cross-model comparator."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "compare_reports.py"
SPEC = importlib.util.spec_from_file_location("compare_reports", SCRIPT)
comparison = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(comparison)

def fixture(root, model, x=0.1):
    folder = root / model
    folder.mkdir()
    base = {"model": model, "source_sha256": comparison.EXPECTED[model]}
    inv = {**base, "source_unchanged": True, "approved": False, "vertices": 10,
           "bones": 1, "groups": 1, "shape_keys": 1, "run": "unit-test"}
    integrity = {**base, "result": "PASS", "approval": "NOT_GRANTED", "unweighted_vertices": 0}
    audit = {
        **base, "approval": "NOT_GRANTED",
        "mesh": {"vertices": 10, "unweighted_vertices": 0},
        "rig": {"bones": [{"name": "bone", "parent": None, "head_body_local_m": [0, 0, 0],
                           "tail_body_local_m": [0, 0, 0.1], "use_deform": True}]},
        "groups": [{"name": "bone", "weighted_centroid_body_local_m": [x, 0, 0],
                    "vertices_with_influence": 10}],
    }
    for file, data in (("inventory.json", inv), ("integrity_checks.json", integrity),
                       ("rest_anatomy_inventory.json", audit)):
        (folder / file).write_text(json.dumps(data), encoding="utf-8")

class ComparisonTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for i, m in enumerate(comparison.MODELS):
            fixture(self.root, m, 0.1 + i * 0.01)

    def replace(self, model, file, transform):
        p = self.root / model / file
        data = json.loads(p.read_text())
        transform(data)
        p.write_text(json.dumps(data))

    def test_three_models_and_explicit_nonapproval(self):
        result = comparison.build_report(self.root)
        self.assertEqual(len(result["pairs"]), 3)
        self.assertEqual(result["models"]["W8"]["vertices"], 10)
        self.assertIn("NOT_APPROVED", result["status"])
        self.assertTrue(all(p["same_rest_bone_coordinates_at_six_decimal_metres"] for p in result["pairs"]))
        self.assertEqual(result["pairs"][0]["largest_centroid_shifts"][0]["centroid_separation_mm"], 10)
        self.assertIn("No .blend modified", comparison.markdown(result))

    def test_bad_sha_rejected(self):
        self.replace("V14", "inventory.json", lambda d: d.update(source_sha256="wrong"))
        with self.assertRaisesRegex(ValueError, "source hash"):
            comparison.build_report(self.root)

    def test_failed_integrity_rejected(self):
        self.replace("W8", "integrity_checks.json", lambda d: d.update(result="FAIL"))
        with self.assertRaisesRegex(ValueError, "integrity not established"):
            comparison.build_report(self.root)

    def test_changed_skeleton_flagged(self):
        self.replace("R120", "rest_anatomy_inventory.json",
                     lambda d: d["rig"]["bones"][0]["tail_body_local_m"].__setitem__(2, 0.2))
        result = comparison.build_report(self.root)
        self.assertFalse(result["pairs"][1]["same_rest_bone_coordinates_at_six_decimal_metres"])

    def test_group_name_mismatch_rejected(self):
        self.replace("V14", "rest_anatomy_inventory.json",
                     lambda d: d["groups"][0].update(name="other"))
        with self.assertRaisesRegex(ValueError, "vertex-group names differ"):
            comparison.build_report(self.root)

if __name__ == "__main__":
    unittest.main()
