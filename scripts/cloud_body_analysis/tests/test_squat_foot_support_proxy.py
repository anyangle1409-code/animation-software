"""Synthetic guards for the read-only squat foot-surface proxy."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "squat_foot_support_proxy.py"
proxy = None
if MODULE.exists():
    SPEC = importlib.util.spec_from_file_location("squat_foot_support_proxy", MODULE)
    proxy = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(proxy)


def fixture():
    groups = np.array(["foot_l", "toe_l", "foot_r", "toe_r"])
    rest = np.array([
        [-1.0, 0.0, 0.0], [-1.0, 2.0, 0.2],
        [1.0, 0.0, 0.0], [1.0, 2.0, 0.2],
    ])
    triangles = np.array([[0, 1, 2], [1, 2, 3]], dtype=np.int32)
    standing = rest.copy()
    squat = rest + np.array([
        [0.1, 0.2, 0.01], [0.1, 0.2, 0.01],
        [-0.1, 0.2, 0.01], [-0.1, 0.2, 0.01],
    ])
    returned = rest.copy()
    return {
        0: {"rest_vertices": rest, "posed_vertices": standing,
            "triangles": triangles, "dominant_groups": groups},
        7: {"rest_vertices": rest.copy(), "posed_vertices": squat,
            "triangles": triangles.copy(), "dominant_groups": groups.copy()},
        8: {"rest_vertices": rest.copy(), "posed_vertices": returned,
            "triangles": triangles.copy(), "dominant_groups": groups.copy()},
    }


class SquatFootSupportProxyTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(proxy, "squat_foot_support_proxy module must implement the proxy")

    def test_measures_lower_envelope_and_centroid_drift_without_contact_claim(self):
        result = proxy.analyze_samples("W8", "source-sha", fixture())
        self.assertEqual(
            result["status"],
            "READ_ONLY_SQUAT_FOOT_SURFACE_PROXY_NOT_GROUND_CONTACT_APPROVAL")
        self.assertFalse(result["ground_plane_verified"])
        self.assertFalse(result["contact_approval"])
        left = result["authored_suffixes"]["l"]
        self.assertEqual(left["selected_vertex_count"], 2)
        self.assertEqual(left["label_counts"], {"foot_l": 1, "toe_l": 1})
        self.assertAlmostEqual(left["samples"]["7"]["minimum_z_delta_from_standing_m"], 0.01)
        self.assertEqual(left["samples"]["7"]["centroid_delta_from_standing_m"],
                         [0.1, 0.2, 0.01])
        self.assertAlmostEqual(
            left["samples"]["7"]["maximum_selected_vertex_displacement_m"],
            (0.1**2 + 0.2**2 + 0.01**2) ** 0.5)
        self.assertEqual(left["samples"]["8"]["maximum_selected_vertex_displacement_m"], 0.0)
        self.assertEqual(result["axis_semantics"],
                         "source-authored XYZ; Z treated only as model vertical proxy")

    def test_lowest_one_percent_tracks_exact_vertex_ids_descriptively(self):
        samples = fixture()
        result = proxy.analyze_samples("W8", "source-sha", samples)
        left = result["authored_suffixes"]["l"]
        self.assertEqual(left["standing_lowest_one_percent_vertex_count"], 1)
        self.assertEqual(left["samples"]["7"]["lowest_one_percent_id_overlap_count"], 1)
        self.assertEqual(left["samples"]["7"]["lowest_one_percent_id_overlap_fraction"], 1.0)
        self.assertEqual(left["samples"]["7"]["lowest_one_percent_mean_z_m"], 0.01)

    def test_rejects_changed_topology_groups_rest_or_nonfinite_pose(self):
        mutations = []
        changed = fixture()
        changed[7]["triangles"][0, 0] = 3
        mutations.append((changed, "topology"))
        changed = fixture()
        changed[7]["dominant_groups"][0] = "shin_l"
        mutations.append((changed, "dominant-group"))
        changed = fixture()
        changed[8]["rest_vertices"][0, 2] = 0.5
        mutations.append((changed, "rest vertices"))
        changed = fixture()
        changed[7]["posed_vertices"][0, 2] = np.nan
        mutations.append((changed, "nonfinite"))
        for samples, message in mutations:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    proxy.analyze_samples("W8", "source-sha", samples)

    def test_requires_both_authored_suffixes_and_exact_samples(self):
        samples = fixture()
        samples.pop(8)
        with self.assertRaisesRegex(ValueError, "samples 0, 7 and 8"):
            proxy.analyze_samples("W8", "source-sha", samples)
        samples = fixture()
        samples[0]["dominant_groups"] = np.array(["foot_l", "toe_l", "shin_r", "shin_r"])
        samples[7]["dominant_groups"] = samples[0]["dominant_groups"].copy()
        samples[8]["dominant_groups"] = samples[0]["dominant_groups"].copy()
        with self.assertRaisesRegex(ValueError, "foot/toe vertices for suffix r"):
            proxy.analyze_samples("W8", "source-sha", samples)

    def test_consumed_member_hashes_reject_altered_extracted_evidence(self):
        members = {"diagnosis.json": b"pinned", "sample.npz": b"geometry"}
        expected = {name: hashlib.sha256(data).hexdigest()
                    for name, data in members.items()}
        proxy.verify_member_hashes("W8", members.__getitem__, expected)
        members["sample.npz"] = b"altered geometry"
        with self.assertRaisesRegex(ValueError, "sample.npz member hash mismatch"):
            proxy.verify_member_hashes("W8", members.__getitem__, expected)

    def test_output_writer_rejects_evidence_tree_and_aliases_before_writing(self):
        report = {
            "status": proxy.STATUS, "models": {},
            "anatomical_approval": "NOT_GRANTED",
            "ground_contact_approval": "NOT_GRANTED",
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence_dir = root / "evidence"
            evidence_dir.mkdir()
            evidence_file = evidence_dir / "input.zip"
            evidence_file.write_bytes(b"evidence")
            for out in (
                evidence_dir,
                root / "hardlink-output",
                root / "symlink-output",
            ):
                if out.name == "hardlink-output":
                    out.mkdir()
                    os.link(evidence_file, out / "squat_foot_surface_proxy.json")
                elif out.name == "symlink-output":
                    out.mkdir()
                    (out / "squat_foot_surface_proxy.md").symlink_to(evidence_file)
                with self.subTest(out=out):
                    before = evidence_file.read_bytes()
                    with self.assertRaisesRegex(ValueError, "outside and distinct"):
                        proxy.write_outputs(report, out, [evidence_dir, evidence_file])
                    self.assertEqual(evidence_file.read_bytes(), before)

            safe = root / "safe-output"
            proxy.write_outputs(report, safe, [evidence_dir, evidence_file])
            self.assertEqual(json.loads((safe / "squat_foot_surface_proxy.json").read_text()),
                             report)


if __name__ == "__main__":
    unittest.main()
