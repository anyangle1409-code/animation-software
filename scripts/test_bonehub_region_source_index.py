"""No-network adversarial tests for BoneHub candidate source tree discovery."""
import copy
import unittest
from unittest.mock import patch

from anatomy_fit.bonehub_region_source_index import (
    EXPECTED_SAMPLE_PINS, MALE_ROOT, analyze_tree, build_report,
    classify, permitted_api_url,
)

SHA = "a" * 40


def fixture_entries():
    return [
        {
            "path": MALE_ROOT + rel,
            "type": "file",
            "size": 2048,
            "lfs": {"oid": digest},
        }
        for rel, digest in EXPECTED_SAMPLE_PINS.items()
    ]


class RegionSourceIndexTests(unittest.TestCase):
    def test_four_existing_pins_are_required(self):
        report = analyze_tree(fixture_entries(), SHA)
        self.assertEqual(len(report["source_file_candidates"]), 4)
        self.assertFalse(report["cp1_anatomical_acceptance"])
        self.assertFalse(report["canonical_geometry_modified"])
        self.assertFalse(report["source_subject_independent_of_existing_CT"])

    def test_unsafe_url_rejected(self):
        good = "https://huggingface.co/api/datasets/BoneHub/visible-human-3d-models/tree/abc"
        self.assertTrue(permitted_api_url(good))
        self.assertTrue(permitted_api_url("https://huggingface.co/api/datasets/BoneHub/visible-human-3d-models"))
        for bad in (
            "http://huggingface.co/api/datasets/BoneHub/visible-human-3d-models/tree",
            "https://untrusted.example/api/datasets/BoneHub/visible-human-3d-models/tree",
            "https://huggingface.co.evil.example/api/datasets/BoneHub/visible-human-3d-models/tree",
            "https://huggingface.co/api/models/BoneHub/visible-human-3d-models/tree",
            "https://user:pw@huggingface.co/api/datasets/BoneHub/visible-human-3d-models/tree",
        ):
            self.assertFalse(permitted_api_url(bad))

    def test_reject_missing_pinned_mesh(self):
        with self.assertRaisesRegex(ValueError, "Pinned baseline"):
            analyze_tree(fixture_entries()[1:], SHA)

    def test_reject_changed_upstream_sha(self):
        entries = fixture_entries()
        entries[0]["lfs"]["oid"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "differs"):
            analyze_tree(entries, SHA)

    def test_reject_duplicate_remote_paths(self):
        entries = fixture_entries()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            analyze_tree(entries + [copy.deepcopy(entries[0])], SHA)

    def test_reject_changed_revision(self):
        with self.assertRaisesRegex(ValueError, "revision"):
            analyze_tree(fixture_entries(), "main")

    def test_reject_unknown_tree_types(self):
        entries = fixture_entries()
        entries[0]["type"] = "symlink"
        with self.assertRaisesRegex(ValueError, "object type"):
            analyze_tree(entries, SHA)

    def test_reject_unreasonable_sizes(self):
        entries = fixture_entries()
        entries[0]["size"] = 0
        with self.assertRaisesRegex(ValueError, "size"):
            analyze_tree(entries, SHA)

    def test_reject_bad_lfs_identifier(self):
        entries = fixture_entries()
        entries[0]["lfs"]["oid"] = "xyz"
        with self.assertRaisesRegex(ValueError, "checksum"):
            analyze_tree(entries, SHA)

    def test_filename_classification_does_not_claim_anatomy(self):
        self.assertEqual(classify(MALE_ROOT+"HAND_RIGHT/HAMATE_RIGHT.stl")[0],
                         "carpus_file_candidate")
        self.assertEqual(classify(MALE_ROOT+"FOOT_LEFT/CUNEIFORM_2_LEFT.stl")[0],
                         "tarsus_file_candidate")
        self.assertEqual(classify(MALE_ROOT+"THORAX/RIB_12_RIGHT.stl")[0],
                         "rib_file_candidate")
        self.assertIsNone(classify(MALE_ROOT+"THORAX/../HAND_LEFT/SCAPHOID_LEFT.stl"))
        self.assertIsNone(classify("other_dataset/HAND_LEFT/SCAPHOID_LEFT.stl"))
        self.assertIsNone(classify(MALE_ROOT+"HAND_LEFT/../../evil.stl"))
        self.assertIsNone(classify(MALE_ROOT+"HAND_LEFT/SCAPHOID_LEFT.jpg"))

    def test_reports_other_filename_groups_separately(self):
        entries = fixture_entries()
        entries.append({
            "path": MALE_ROOT+"HAND_LEFT/THUMB_LEFT.stl",
            "size": 123, "type": "file", "lfs": None})
        report = analyze_tree(entries, SHA)
        self.assertEqual(report["counts_by_source_filename_category"]["other_hand_file"], 1)
        item = next(v for v in report["source_file_candidates"]
                    if v["source_relpath"] == "HAND_LEFT/THUMB_LEFT.stl")
        self.assertIsNone(item["lfs_sha256_metadata"])
        self.assertFalse(item["source_file_sha256_verified"])

    def test_revision_fixed_before_tree_fetch(self):
        visited = []
        def mock_read(url):
            visited.append(url)
            if "/tree/" in url:
                return fixture_entries(), None
            return {"sha": SHA}, None
        with patch("anatomy_fit.bonehub_region_source_index.read_api", side_effect=mock_read):
            report = build_report()
        self.assertEqual(report["source_revision"], SHA)
        self.assertIn("/tree/"+SHA+"/", visited[1])
        self.assertEqual(len(visited), 2)

    def test_looped_pagination_is_rejected(self):
        def mock_read(url):
            if "/tree/" in url:
                return fixture_entries(), url
            return {"sha": SHA}, None
        with patch("anatomy_fit.bonehub_region_source_index.read_api", side_effect=mock_read):
            with self.assertRaisesRegex(ValueError, "pagination loop"):
                build_report()


if __name__ == "__main__":
    unittest.main()
