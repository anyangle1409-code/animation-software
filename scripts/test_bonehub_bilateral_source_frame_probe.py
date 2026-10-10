"""Read-only tests: 27 bilateral source bounding-box pairs, not anatomy registration."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_bonehub_54_surface_audit import make_index
from anatomy_fit.bonehub_bilateral_source_frame_probe import build_pairs, main, FROZEN


def pair_fixture():
    index = make_index()
    items = []
    for item in index["source_file_candidates"]:
        rel = item["source_relpath"]
        group = item["category"]
        side = "LEFT" if rel.endswith("_LEFT.stl") else "RIGHT"
        x = 150 if side == "LEFT" else -150
        items.append({
            "source_relpath": rel,
            "source_file_group": group,
            "reference_sha256_verified": "a"*64,
            "bbox_min_source_units_unknown": [x, 4, 90],
            "bbox_max_source_units_unknown": [x+5, 8, 96],
        })
    return {
        "kind": "HGPT_NONCANONICAL_54_BONE_SURFACE_QA",
        "source_revision": FROZEN,
        "cp1_gate6_approved": False,
        "canonical_geometry_changed": False,
        "independent_subject_evidence": False,
        "stl_physical_units_and_axes_confirmed": False,
        "items": items,
    }


class BilateralProbeTests(unittest.TestCase):
    def test_27_pairs_produce_noncanonical_orientation_hypothesis(self):
        result = build_pairs(pair_fixture())
        self.assertEqual(result["bilateral_file_pairs"], 27)
        self.assertEqual(result["labelled_left_x_greater_than_right"], 27)
        self.assertEqual(result["dominant_source_x_difference_pairs"], 27)
        self.assertTrue(result["hypothesis_left_label_on_source_positive_x"])
        self.assertFalse(result["anat_left_correspondence_proven"])
        self.assertFalse(result["runtime_adapter_approved"])
        self.assertFalse(result["source_units_and_scanner_axes_verified"])
        self.assertEqual(len(result["pair_deltas_source_units_unknown"]), 27)

    def test_sign_counterexample_does_not_approve_orientation(self):
        f = pair_fixture()
        item = next(i for i in f["items"]
                    if i["source_relpath"] == "HAND_LEFT/SCAPHOID_LEFT.stl")
        item["bbox_min_source_units_unknown"][0] = -180
        item["bbox_max_source_units_unknown"][0] = -175
        result = build_pairs(f)
        self.assertEqual(result["labelled_left_x_greater_than_right"], 26)
        self.assertFalse(result["hypothesis_left_label_on_source_positive_x"])

    def test_missing_side_pair_rejected(self):
        f = pair_fixture()
        f["items"] = f["items"][:-1]
        with self.assertRaisesRegex(ValueError, "report"):
            build_pairs(f)

    def test_forged_anatomy_acceptance_rejected(self):
        f = pair_fixture()
        f["cp1_gate6_approved"] = True
        with self.assertRaisesRegex(ValueError, "falsely accepted"):
            build_pairs(f)

    def test_changed_upstream_revision_rejected(self):
        f = pair_fixture()
        f["source_revision"] = "b"*40
        with self.assertRaisesRegex(ValueError, "Invalid"):
            build_pairs(f)

    def test_filename_folder_side_incoherence_rejected(self):
        f = pair_fixture()
        f["items"][0]["source_relpath"] = "HAND_LEFT/SCAPHOID_RIGHT.stl"
        with self.assertRaisesRegex(ValueError, "side disagreement"):
            build_pairs(f)

    def test_duplicate_source_path_rejected(self):
        f = pair_fixture()
        f["items"][0] = copy.deepcopy(f["items"][1])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            build_pairs(f)

    def test_missing_raw_sha_pin_rejected(self):
        f = pair_fixture()
        f["items"][0]["reference_sha256_verified"] = None
        with self.assertRaisesRegex(ValueError, "SHA"):
            build_pairs(f)

    def test_nonfinite_source_bbox_rejected(self):
        f = pair_fixture()
        f["items"][0]["bbox_min_source_units_unknown"][0] = float("nan")
        with self.assertRaisesRegex(ValueError, "bounding box"):
            build_pairs(f)

    def test_measured_coordinate_used_not_bone_centroid(self):
        r = build_pairs(pair_fixture())
        self.assertFalse(r["bone_centroids_measured"])
        self.assertEqual(r["groups"]["carpus_file_candidate"]["pair_count"], 8)
        self.assertEqual(r["groups"]["tarsus_file_candidate"]["pair_count"], 7)
        self.assertEqual(r["groups"]["rib_file_candidate"]["pair_count"], 12)

    def test_cli_writes_external_report_without_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            inp = Path(temp)/"raw-numeric.json"
            output = Path(temp)/"pairwise.json"
            inp.write_text(json.dumps(pair_fixture()), encoding="utf-8")
            with patch("sys.argv", ["probe", "--input", str(inp), "--output", str(output)]):
                self.assertEqual(main(), 0)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertFalse(report["cp1_gate6_approved"])
            self.assertEqual(report["bilateral_file_pairs"], 27)
            with patch("sys.argv", ["probe", "--input", str(inp), "--output", str(output)]):
                self.assertEqual(main(), 2)


if __name__ == "__main__":
    unittest.main()
