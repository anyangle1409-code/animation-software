"""Synthetic guards for the read-only native grip evidence coverage audit."""
import importlib.util
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "grip_evidence_coverage.py"
audit = None
if MODULE.exists():
    SPEC = importlib.util.spec_from_file_location("grip_evidence_coverage", MODULE)
    audit = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(audit)


def trial(suffix="l", pairs=5, collapse=24, angle=None):
    return {
        "runtime_suffix": suffix,
        "thumb_01_euler_rad": [0.0, math.pi / 6.0, 0.0] if angle is None else angle,
        "pairs": pairs,
        "hand_collapse": collapse,
    }


class GripEvidenceCoverageTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(audit, "grip_evidence_coverage module must implement the audit")

    def test_separates_pair_guard_observation_from_grip_acceptance(self):
        trials = [trial(), trial(pairs=12,
                                 collapse="NOT_RUN: pair guard short-circuits")]
        result = audit.analyze_trials("W8", trials)
        self.assertEqual(result["status"],
                         "READ_ONLY_GRIP_COVERAGE_AND_GUARD_AUDIT_NOT_ACCEPTANCE")
        self.assertEqual(result["trial_count"], 2)
        self.assertEqual(result["authored_runtime_suffix_counts"], {"l": 2, "r": 0})
        self.assertEqual(result["missing_authored_runtime_suffixes"], ["r"])
        self.assertFalse(result["bilateral_trial_coverage"])
        self.assertEqual(result["project_solver_pair_guard_max"], 5)
        self.assertEqual(result["trials_reaching_collapse_measurement"], 1)
        self.assertEqual(result["trials_short_circuited_by_pair_guard"], 1)
        self.assertEqual(result["observed_collapse_counts"], [24])
        self.assertFalse(result["pair_guard_is_anatomical_threshold"])
        self.assertFalse(result["collapse_acceptance_threshold_defined"])
        self.assertFalse(result["contact_validation_performed"])
        self.assertFalse(result["grip_acceptance"])

    def test_bilateral_trial_presence_still_does_not_create_acceptance(self):
        result = audit.analyze_trials("V14", [trial("l"), trial("r", 4, 23)])
        self.assertTrue(result["bilateral_trial_coverage"])
        self.assertEqual(result["missing_authored_runtime_suffixes"], [])
        self.assertFalse(result["grip_acceptance"])
        self.assertFalse(result["anatomical_side_verified"])

    def test_rejects_invalid_trial_types_values_and_guard_inconsistency(self):
        cases = [
            ([trial("x")], "runtime suffix"),
            ([trial(pairs=True)], "pairs"),
            ([trial(pairs=-1)], "pairs"),
            ([trial(angle=[0.0, float("nan"), 0.0])], "Euler"),
            ([trial(angle=[0.0, 0.0])], "Euler"),
            ([trial(pairs=6, collapse=24)], "short-circuit"),
            ([trial(pairs=5, collapse="NOT_RUN: pair guard short-circuits")],
             "collapse count"),
            ([trial(collapse=True)], "collapse count"),
        ]
        for trials, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    audit.analyze_trials("W8", trials)

    def test_validates_failed_solver_outcome_without_treating_it_as_acceptance(self):
        diagnosis = {
            "model": "W8",
            "source_sha256": "source",
            "source_and_copy_unchanged": True,
            "anatomical_approval": "NOT_GRANTED",
            "approved": False,
            "paths": {"grip": {
                "grip_trials": [trial()],
                "exception": "RuntimeError: no thumb placement within the pair limit",
                "grip_exception_expected": True,
            }},
        }
        result = audit.validate_diagnosis("W8", "source", diagnosis)
        self.assertTrue(result["solver_failed_without_placement"])
        self.assertFalse(result["grip_acceptance"])
        for key, value in (
                ("grip_exception_expected", False),
                ("exception", "RuntimeError: unrelated failure")):
            changed = json.loads(json.dumps(diagnosis))
            changed["paths"]["grip"][key] = value
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError, "expected failed grip solver"):
                    audit.validate_diagnosis("W8", "source", changed)

    def test_consumed_diagnosis_hash_rejects_altered_extracted_evidence(self):
        members = {"diagnosis.json": b"pinned diagnosis"}
        expected = {"diagnosis.json": hashlib.sha256(members["diagnosis.json"]).hexdigest()}
        audit.verify_member_hashes("W8", members.__getitem__, expected)
        members["diagnosis.json"] = b"altered diagnosis"
        with self.assertRaisesRegex(ValueError, "diagnosis.json member hash mismatch"):
            audit.verify_member_hashes("W8", members.__getitem__, expected)

    def test_output_writer_rejects_evidence_tree_and_aliases_before_writing(self):
        report = {"status": audit.STATUS, "models": {},
                  "anatomical_approval": "NOT_GRANTED", "grip_acceptance": False}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence_dir = root / "evidence"
            evidence_dir.mkdir()
            evidence_file = evidence_dir / "input.zip"
            evidence_file.write_bytes(b"evidence")
            for out in (evidence_dir, root / "hardlink-output", root / "symlink-output"):
                if out.name == "hardlink-output":
                    out.mkdir()
                    os.link(evidence_file, out / "grip_evidence_coverage.json")
                elif out.name == "symlink-output":
                    out.mkdir()
                    (out / "grip_evidence_coverage.md").symlink_to(evidence_file)
                with self.subTest(out=out):
                    before = evidence_file.read_bytes()
                    with self.assertRaisesRegex(ValueError, "outside and distinct"):
                        audit.write_outputs(report, out, [evidence_dir, evidence_file])
                    self.assertEqual(evidence_file.read_bytes(), before)

            safe = root / "safe-output"
            audit.write_outputs(report, safe, [evidence_dir, evidence_file])
            self.assertEqual(json.loads((safe / "grip_evidence_coverage.json").read_text()),
                             report)


if __name__ == "__main__":
    unittest.main()
