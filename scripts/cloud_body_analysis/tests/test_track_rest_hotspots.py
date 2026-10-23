"""Synthetic, no-Blender regression tests for rest-space triangle persistence."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np

P = Path(__file__).resolve().parents[1] / "track_rest_hotspots.py"
SPEC = importlib.util.spec_from_file_location("track_rest_hotspots", P)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)

def fixture(root, model):
    directory = root / model / "visual_evidence_new"
    directory.mkdir(parents=True)
    tri = np.array([[0, 1, 2], [1, 2, 3], [2, 3, 4]], dtype=np.int32)
    rest = np.array([[0, 0, 0], [0.1, 0, 0], [0, 0.1, 0],
                     [0.1, 0.1, 0], [0.2, 0.1, 0]], dtype=np.float32)
    groups = np.array(["shoulder_cap_l", "clavicle_l", "spine_03", "upperarm_l", "neck"])
    diagnosis = {"model": model, "source_sha256": audit.MODELS[model][0],
                 "source_and_copy_unchanged": True, "approved": False,
                 "anatomical_approval": "NOT_GRANTED", "paths": {}}
    for movement, numbers in audit.FRAMES.items():
        rows = []
        for index, sample in enumerate(numbers):
            name = f"{model}__{movement}__sample{sample:02d}"
            stretched, collapsed = ([0], [0, 1], [1, 2])[index], ([], [2], [2])[index]
            row = {"sample_index": sample, "t": sample / 8,
                   "geometry_file": name + "__geometry.npz",
                   "triangle_indices_sha256": "synthetic-rest-" + movement,
                   "counts": {"stretch_gt_2": len(stretched), "collapse_lt_0_1": len(collapsed),
                              "self_intersecting_pairs": 0},
                   "flags": {"stretched": stretched, "collapsed": collapsed, "intersections": []}}
            (directory / (name + "__triangles.json")).write_text(json.dumps(row))
            np.savez(directory / (name + "__geometry.npz"),
                     triangles=tri, rest_vertices=rest,
                     posed_vertices=rest + np.array([0, 0, 0.01 * index], dtype=np.float32),
                     dominant_groups=groups,
                     stretched=np.asarray(stretched, dtype=np.int32),
                     collapsed=np.asarray(collapsed, dtype=np.int32))
            rows.append(row)
        diagnosis["paths"][movement] = {"frames": rows}
    (directory / "diagnosis.json").write_text(json.dumps(diagnosis))

class TestRestHotspots(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for m in audit.MODELS:
            fixture(self.root, m)

    def analyse(self):
        return audit.analyse({m: self.root / m for m in audit.MODELS})

    def change_npz(self, model, movement, sample, change):
        file = (self.root / model / "visual_evidence_new" /
                f"{model}__{movement}__sample{sample:02d}__geometry.npz")
        with np.load(file, allow_pickle=False) as data:
            arrays = {k: data[k].copy() for k in data.files}
        change(arrays)
        np.savez(file, **arrays)

    def change_summary(self, model, change):
        file = self.root / model / "visual_evidence_new" / "diagnosis.json"
        data = json.loads(file.read_text())
        change(data)
        file.write_text(json.dumps(data))

    def test_exact_triangle_persistence_and_metadata(self):
        d = self.analyse()
        rows = d["models"]["W8"]["movements"]["shoulder_press"]["categories"]
        self.assertEqual(rows["stretched"]["sample_counts"], {"0": 1, "6": 2, "8": 2})
        events = rows["stretched"]["events"]
        self.assertEqual(events["new_at_middle_vs_start"]["count"], 1)
        self.assertEqual(events["persisting_at_last_from_new_middle"]["count"], 1)
        self.assertEqual(events["resolved_at_last_from_new_middle"]["count"], 0)
        self.assertEqual(rows["collapsed"]["events"]["new_at_middle_vs_start"]["count"], 1)
        self.assertTrue(d["models"]["W8"]["movements"]["shoulder_press"]["stable_rest_topology"])
        self.assertIn("NOT_APPROVED", d["status"])
        self.assertIn("No", "No model edit performed")

    def test_reject_source_hash_mismatch(self):
        self.change_summary("V14", lambda d: d.update(source_sha256="not-matching"))
        with self.assertRaisesRegex(ValueError, "hash"):
            self.analyse()

    def test_reject_false_model_approval(self):
        self.change_summary("W8", lambda d: d.update(approved=True))
        with self.assertRaisesRegex(ValueError, "approval"):
            self.analyse()

    def test_reject_changed_rest_coordinates(self):
        self.change_npz("W8", "shoulder_press", 6,
                        lambda d: d["rest_vertices"].__setitem__((0, 0), 0.5))
        with self.assertRaisesRegex(ValueError, "rest topology"):
            self.analyse()

    def test_reject_changed_triangle_topology(self):
        self.change_npz("V14", "squat", 7,
                        lambda d: d["triangles"].__setitem__((0, 0), 4))
        with self.assertRaisesRegex(ValueError, "rest topology"):
            self.analyse()

    def test_reject_changed_dominant_weight_labels(self):
        self.change_npz("R120", "shoulder_press", 8,
                        lambda d: d["dominant_groups"].__setitem__(0, "pelvis"))
        with self.assertRaisesRegex(ValueError, "rest topology"):
            self.analyse()

    def test_reject_nonfinite_geometry(self):
        self.change_npz("W8", "squat", 8,
                        lambda d: d["posed_vertices"].__setitem__((0, 0), np.nan))
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            self.analyse()

    def test_reject_mismatched_flag_counts(self):
        file = self.root / "R120" / "visual_evidence_new" / "R120__shoulder_press__sample06__triangles.json"
        data = json.loads(file.read_text())
        data["counts"]["stretch_gt_2"] += 1
        file.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "flags/counts"):
            self.analyse()

if __name__ == "__main__":
    unittest.main()
