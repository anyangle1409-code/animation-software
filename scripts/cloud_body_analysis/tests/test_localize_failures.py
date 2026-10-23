"""Synthetic fixture tests for read-only native triangle localization."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np

PATH = Path(__file__).resolve().parents[1] / "localize_failures.py"
SPEC = importlib.util.spec_from_file_location("localize_failures", PATH)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def fixture(root, model):
    folder = root / model / "visual_evidence_new"
    folder.mkdir(parents=True)
    tri = np.array([[0, 1, 2], [1, 2, 3]], dtype=np.int32)
    points = np.array([[0, 0, 0], [.1, 0, 0], [0, .1, 0], [.1, .1, 0]], dtype=np.float32)
    groups = np.array(["shoulder_cap_l", "shoulder_cap_l", "spine_03", "spine_03"])
    summary = {
        "model": model, "source_sha256": mod.SOURCES[model][0], "approved": False,
        "anatomical_approval": "NOT_GRANTED", "source_and_copy_unchanged": True,
        "paths": {},
    }
    for name, numbers in mod.FRAMES.items():
        frames = []
        for number in numbers:
            prefix = f"{model}__{name}__sample{number:02d}"
            collapsed, stretched, intersect = ([0] if number else []), ([1] if number else []), ([[0, 1]] if number else [])
            counts = {"collapse_lt_0_1": len(collapsed), "stretch_gt_2": len(stretched),
                      "self_intersecting_pairs": len(intersect)}
            record = {
                "sample_index": number, "t": number / 8, "counts": counts,
                "triangle_indices_sha256": "stable-mock-rest-triangles",
                "geometry_file": prefix + "__geometry.npz",
                "metrics": {"self_intersection_classes_top": []},
                "flags": {"collapsed": collapsed, "stretched": stretched, "intersections": intersect},
            }
            (folder / (prefix + "__triangles.json")).write_text(json.dumps(record))
            np.savez(folder / (prefix + "__geometry.npz"), triangles=tri, posed_vertices=points,
                     dominant_groups=groups, collapsed=np.asarray(collapsed, dtype=np.int32),
                     stretched=np.asarray(stretched, dtype=np.int32),
                     intersections=np.asarray(intersect, dtype=np.int32).reshape(-1, 2))
            frames.append(record)
        summary["paths"][name] = {"frames": frames}
    summary["paths"]["grip"] = {
        "grip_trials": [
            {"runtime_suffix": "l", "pairs": 2, "hand_collapse": 24},
            {"runtime_suffix": "l", "pairs": 14, "hand_collapse": "NOT_RUN"},
        ],
    }
    (folder / "diagnosis.json").write_text(json.dumps(summary))


class LocalizerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for model in mod.SOURCES:
            fixture(self.root, model)

    def mutate(self, model, file, change):
        path = self.root / model / "visual_evidence_new" / file
        doc = json.loads(path.read_text())
        change(doc)
        path.write_text(json.dumps(doc))

    def test_integrity_and_persistence_for_each_model(self):
        for model in mod.SOURCES:
            row = mod.process(model, self.root / model)
            self.assertEqual(row["anatomical_approval"], "NOT_GRANTED")
            self.assertEqual(row["grip"]["trial_count"], 2)
            self.assertEqual(row["grip"]["trials_meeting_collision_pair_limit"], 1)
            press = row["paths"]["shoulder_press"]
            persistence = press["flag_persistence"]["stretched"]
            self.assertEqual(persistence["new_vs_initial"]["6"], 1)
            self.assertEqual(persistence["same_flag_at_two_later_samples"], 1)
            labels = press["samples"][1]["flags"]["stretched"]["dominant_group_proxies"]
            self.assertEqual(labels[0]["group_label"], "spine_03")
            self.assertEqual(labels[0]["triangle_corner_equivalent"], .667)

    def test_source_hash_mismatch_refused(self):
        self.mutate("W8", "diagnosis.json", lambda d: d.update(source_sha256="wrong"))
        with self.assertRaisesRegex(ValueError, "source SHA256"):
            mod.process("W8", self.root / "W8")

    def test_approval_refused(self):
        self.mutate("V14", "diagnosis.json", lambda d: d.update(approved=True))
        with self.assertRaisesRegex(ValueError, "approval guard"):
            mod.process("V14", self.root / "V14")

    def test_unchanged_bytes_required(self):
        self.mutate("R120", "diagnosis.json", lambda d: d.update(source_and_copy_unchanged=False))
        with self.assertRaisesRegex(ValueError, "approval guard"):
            mod.process("R120", self.root / "R120")

    def test_flag_count_disagreement_refused(self):
        filename = "W8__shoulder_press__sample06__triangles.json"
        self.mutate("W8", filename, lambda d: d["counts"].update(stretch_gt_2=17))
        with self.assertRaisesRegex(ValueError, "counts or flags differ"):
            mod.process("W8", self.root / "W8")

    def test_rest_topology_mismatch_refused(self):
        name = "V14__squat__sample08__triangles.json"
        self.mutate("V14", name, lambda d: d.update(triangle_indices_sha256="different"))
        self.mutate("V14", "diagnosis.json", lambda d: d["paths"]["squat"]["frames"][2].update(triangle_indices_sha256="different"))
        with self.assertRaisesRegex(ValueError, "changed rest triangle"):
            mod.process("V14", self.root / "V14")

    def test_bin_counts(self):
        points = np.array([[0, 0, 0], [.01, 0, 0], [0, .01, 0]], dtype=float)
        tris = np.array([[0, 1, 2]], dtype=int)
        rows = mod.bins(points, tris, np.array([0]))
        self.assertEqual(rows[0]["flagged_triangles"], 1)
        self.assertEqual(rows[0]["xyz_cell"], [0, 0, 0])


if __name__ == "__main__":
    unittest.main()
