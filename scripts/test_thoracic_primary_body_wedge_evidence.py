#!/usr/bin/env python3
"""Independent source-numeric and fail-closed tests: Kunkel 2011 Table 2."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))
import thoracic_primary_body_wedge_evidence as w

# Independent fixed manual transcription from published primary Table 2;
# tuples = (level, VBHA mean, VBHA SD, VBHP mean, VBHP SD, published average).
PRIMARY_TABLE2 = [
    ("C7", 13.89, 1.42, 14.38, 2.22, 14.14),
    ("T1", 14.49, 1.23, 15.28, 1.14, 14.88),
    ("T2", 15.01, 1.51, 16.11, 1.67, 15.56),
    ("T3", 15.65, 1.85, 17.41, 1.12, 16.53),
    ("T4", 15.42, 1.46, 18.15, 1.54, 16.79),
    ("T5", 15.84, 1.07, 17.33, 2.16, 16.59),
    ("T6", 16.04, 1.43, 18.22, 1.38, 17.13),
    ("T7", 15.94, 1.61, 18.67, 1.64, 17.31),
    ("T8", 16.99, 1.70, 20.05, 1.77, 18.52),
    ("T9", 18.26, 2.12, 20.25, 2.44, 19.26),
    ("T10", 18.98, 1.40, 20.35, 1.89, 19.67),
    ("T11", 19.60, 1.92, 22.67, 1.38, 21.14),
    ("T12", 20.80, 1.96, 23.12, 1.94, 21.96),
]


class PrimaryThoracicEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(w.LEDGER.read_text(encoding="utf-8"))
        cls.stack = json.loads(w.STACK.read_text(encoding="utf-8"))
        cls.constraints = json.loads(w.CONSTRAINTS.read_text(encoding="utf-8"))

    def assess(self, new_data=None, new_stack=None, new_constraints=None):
        return w.evaluate(
            self.data if new_data is None else new_data,
            self.stack if new_stack is None else new_stack,
            self.constraints if new_constraints is None else new_constraints)

    def test_exact_primary_table2_numbers_all_thirteen_levels(self):
        rows = self.data["levels"]
        self.assertEqual(len(rows), 13)
        tuples = [(r["level"], r["anterior_mean_mm"], r["anterior_sd_mm"],
                   r["posterior_mean_mm"], r["posterior_sd_mm"],
                   r["published_average_mm"]) for r in rows]
        self.assertEqual(tuples, PRIMARY_TABLE2)

    def test_primary_method_and_sample_provenance(self):
        src = self.data["source"]
        self.assertEqual(src["doi"], "10.1111/j.1469-7580.2011.01397.x")
        self.assertEqual(src["table"], "Table 2")
        self.assertEqual(src["segments_total"], 72)
        self.assertEqual(src["spines_total"], 30)
        self.assertEqual((src["donors_female"], src["donors_male"]), (15, 15))
        self.assertIn("radiographic", src["measurement_method"])

    def test_live_canonical_stack_preserved_and_exact_mean_alignment(self):
        result = self.assess()
        self.assertEqual(result["thoracic_levels"], 12)
        self.assertTrue(result["matched_existing_12_thoracic_average_heights"])
        for row in self.data["levels"][1:]:
            self.assertAlmostEqual(
                self.stack["vertebral_bodies_mm"][row["level"]]["candidate"],
                row["published_average_mm"], delta=0.001)

    def test_derived_wedge_never_reports_angle(self):
        result = self.assess()
        self.assertEqual(result["degrees_computed"], 0)
        self.assertFalse(result["body_geometry_changed"])
        self.assertFalse(result["anatomical_acceptance"])
        self.assertEqual(len(result["measurements"]), 13)
        self.assertTrue(all(r["angle_deg"] is None and
                            r["replaces_existing_source_height"] is False
                            for r in result["measurements"]))
        t4 = result["measurements"][4]
        self.assertEqual(t4["level"], "T4")
        self.assertAlmostEqual(t4["posterior_minus_anterior_mm"], 2.73)
        self.assertAlmostEqual(t4["posterior_anterior_height_ratio"],
                               18.15 / 15.42, delta=0.000001)

    def test_no_missing_or_swapped_vertebral_levels(self):
        bad = copy.deepcopy(self.data)
        bad["levels"][5], bad["levels"][6] = bad["levels"][6], bad["levels"][5]
        with self.assertRaisesRegex(ValueError, "order/count"):
            self.assess(bad)
        bad = copy.deepcopy(self.data)
        bad["levels"].pop()
        with self.assertRaisesRegex(ValueError, "order/count"):
            self.assess(bad)

    def test_no_silently_modified_radiographic_values(self):
        bad = copy.deepcopy(self.data)
        bad["levels"][4]["anterior_mean_mm"] += 1.0
        with self.assertRaisesRegex(ValueError, "average disagrees"):
            self.assess(bad)
        bad = copy.deepcopy(self.data)
        bad["levels"][4]["posterior_sd_mm"] = -0.1
        with self.assertRaisesRegex(ValueError, "invalid source"):
            self.assess(bad)

    def test_reject_false_expert_anatomical_approval(self):
        for field in ("anatomical_approval", "canonical_geometry_change_allowed"):
            bad = copy.deepcopy(self.data)
            bad["interpretation"][field] = True
            with self.assertRaisesRegex(ValueError, "never approve"):
                self.assess(bad)

    def test_reject_injected_unsourced_angles(self):
        bad = copy.deepcopy(self.data)
        bad["levels"][3]["angle_deg"] = 4
        with self.assertRaisesRegex(ValueError, "unsourced coordinates"):
            self.assess(bad)

    def test_reject_tampered_original_source_height_stack(self):
        bad = copy.deepcopy(self.stack)
        bad["vertebral_bodies_mm"]["T6"]["candidate"] += 1.0
        with self.assertRaisesRegex(ValueError, "conflicts"):
            self.assess(new_stack=bad)

    def test_reject_geometry_promotion_in_existing_statuses(self):
        bad = copy.deepcopy(self.constraints)
        bad["status"] = "READY"
        with self.assertRaisesRegex(ValueError, "status changed"):
            self.assess(new_constraints=bad)

    def test_reject_missing_source_population_limits(self):
        bad = copy.deepcopy(self.data)
        bad["interpretation"]["unavailable_from_table"] = []
        with self.assertRaisesRegex(ValueError, "limitations removed"):
            self.assess(bad)


if __name__ == "__main__":
    unittest.main()
