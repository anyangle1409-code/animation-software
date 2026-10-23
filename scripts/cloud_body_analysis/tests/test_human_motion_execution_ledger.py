"""Guard the 19-test plan against pretending existing failure frames passed."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
REFERENCE = ROOT / "docs" / "anatomy" / "HGPT_HUMAN_JOINT_ROM_REFERENCE_V1.json"
LEDGER = ROOT / "docs" / "anatomy" / "HGPT_HUMAN_MOTION_TEST_EXECUTION_LEDGER_V1.json"
SOURCE_SHA256 = {
    "W8": "2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c",
    "V14": "5969aa98122e267b6bdd94fdfaf6d2877a1b27f7ea8d11c6a8e078b467b0ff91",
    "R120": "fb3b0acfc68bc59952b0fc6c45f7d7715717207fd9ba0b7f2b124e905ce2ddcb",
}

class MotionExecutionLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads(REFERENCE.read_text())
        cls.ledger = json.loads(LEDGER.read_text())

    def test_exact_all_19_reference_scenarios_unexecuted(self):
        names = {t["id"] for t in self.reference["motion_test_program"]}
        entries = self.ledger["tests"]
        self.assertEqual(len(entries), 19)
        self.assertEqual(len({e["id"] for e in entries}), 19)
        self.assertEqual({e["id"] for e in entries}, names)
        self.assertEqual(self.ledger["test_count"], 19)
        self.assertEqual(self.ledger["summary"]["generic_tests_executed"], 0)
        self.assertEqual(self.ledger["summary"]["generic_tests_passed"], 0)
        self.assertEqual(self.ledger["summary"]["production_approved"], 0)

    def test_native_related_failures_not_generic_passes(self):
        records = {e["id"]: e for e in self.ledger["tests"]}
        self.assertEqual(self.ledger["summary"]["related_native_benchmark_failures"], 3)
        for key, path in (
            ("compound_overhead_press", "shoulder_press"),
            ("compound_squat", "squat"),
            ("finger_grip", "grip"),
        ):
            row = records["hgpt.motion_test." + key]
            self.assertEqual(row["prior_benchmark_run_id"], 39937882229)
            self.assertEqual(row["prior_benchmark_path"], path)
            self.assertIn("FAIL", row["related_prior_benchmark_status"])
            self.assertEqual(row["source_blend_sha256"], SOURCE_SHA256)
            self.assertEqual(row["generic_joint_suite_status"], "NOT_RUN")
            self.assertFalse(row["exercise_approved"])

    def test_no_unearned_joint_skin_or_contact_acceptance(self):
        for row in self.ledger["tests"]:
            self.assertFalse(row["blender_joint_axes_calibrated"])
            self.assertFalse(row["individual_joint_motion_validated"])
            self.assertFalse(row["skin_contact_validated"])
            self.assertFalse(row["phone_review_accepted"])
            self.assertFalse(row["exercise_approved"])
        self.assertFalse(self.ledger["clinical_rom_hard_limits_applied"])
        self.assertFalse(self.ledger["anatomical_side_approved"])
        self.assertFalse(self.ledger["production_deployed"])

    def test_prior_native_source_evidence_is_explicit(self):
        prior = self.ledger["native_prior_diagnostics"]
        self.assertEqual(prior["run_id"], 39937882229)
        self.assertEqual(prior["artifacts"], {"W8": 12495910312,
                                              "V14": 12494932817,
                                              "R120": 12495970648})
        for row in self.ledger["tests"]:
            if row["prior_benchmark_run_id"] is None:
                self.assertEqual(row["related_prior_benchmark_status"], "NO_DIRECT_NATIVE_BENCHMARK")
                self.assertIsNone(row["source_blend_sha256"])

if __name__ == "__main__":
    unittest.main()
