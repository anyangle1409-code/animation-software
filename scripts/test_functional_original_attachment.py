import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "anatomy_fit"))

import functional_original_attachment as attachment


class FunctionalOriginalAttachmentTests(unittest.TestCase):
    def test_evidence_views_separate_full_body_from_shoulder_detail(self):
        self.assertEqual(set(attachment.EVIDENCE_VIEWS), {
            "full_front", "full_side", "full_rear",
            "shoulder_front", "shoulder_side", "shoulder_rear",
        })
        self.assertEqual(attachment.EVIDENCE_VIEWS["full_front"]["scope"], "full_body")
        self.assertEqual(attachment.EVIDENCE_VIEWS["shoulder_front"]["scope"], "shoulder")

    def test_attachment_map_preserves_anatomical_side_and_declares_collapse(self):
        mapping = attachment.ATTACHMENT_MAPPING
        self.assertEqual(mapping["anat_clavicle_left"], "clavicle_r")
        self.assertEqual(mapping["anat_scapula_left"], "scapula_r")
        self.assertEqual(mapping["anat_clavicle_right"], "clavicle_l")
        self.assertEqual(mapping["anat_scapula_right"], "scapula_l")
        self.assertEqual(mapping["anat_rib_01_left"], "spine_02")
        self.assertEqual(mapping["anat_rib_12_right"], "spine_02")
        self.assertEqual(mapping["anat_sternum"], "spine_02")
        self.assertLess(len(set(mapping.values())), len(mapping))

    def test_similarity_fit_maps_both_segment_anchors(self):
        points = [(1.0, 0.0, 0.0), (1.0, 0.5, 0.0), (1.0, 1.0, 0.0)]
        fitted = attachment.fit_segment_similarity(
            points,
            source_head=(1.0, 0.0, 0.0),
            source_tail=(1.0, 1.0, 0.0),
            target_head=(0.0, 0.0, 2.0),
            target_tail=(2.0, 0.0, 2.0),
        )
        self.assertEqual(fitted[0], (0.0, 0.0, 2.0))
        self.assertEqual(fitted[-1], (2.0, 0.0, 2.0))
        self.assertTrue(all(math.isclose(a, b, abs_tol=1e-12)
                            for a, b in zip(fitted[1], (1.0, 0.0, 2.0))))

    def test_similarity_fit_rejects_collapsed_or_nonfinite_segments(self):
        with self.assertRaisesRegex(ValueError, "collapsed source segment"):
            attachment.fit_segment_similarity([(0, 0, 0)], (0, 0, 0), (0, 0, 0),
                                              (0, 0, 0), (1, 0, 0))
        with self.assertRaisesRegex(ValueError, "collapsed target segment"):
            attachment.fit_segment_similarity([(0, 0, 0)], (0, 0, 0), (1, 0, 0),
                                              (0, 0, 0), (0, 0, 0))
        with self.assertRaisesRegex(ValueError, "finite"):
            attachment.fit_segment_similarity([(math.nan, 0, 0)], (0, 0, 0), (1, 0, 0),
                                              (0, 0, 0), (1, 0, 0))

    def test_contract_fails_closed_on_missing_or_unexpected_inventory(self):
        anatomical = set(attachment.ATTACHMENT_MAPPING)
        runtime = set(attachment.ATTACHMENT_MAPPING.values())
        result = attachment.validate_attachment_inventory(anatomical, runtime)
        self.assertEqual(result["errors"], [])
        self.assertFalse(result["anatomy_approved"])
        self.assertEqual(result["attachment_scope"], "provisional rigid guide attachment")

        missing = attachment.validate_attachment_inventory(anatomical - {"anat_scapula_left"}, runtime)
        self.assertIn("missing anatomical attachment bones: anat_scapula_left", missing["errors"])
        extra = attachment.validate_attachment_inventory(anatomical, runtime | {"invented_control"})
        self.assertIn("unexpected runtime attachment bones: invented_control", extra["errors"])


if __name__ == "__main__":
    unittest.main()
