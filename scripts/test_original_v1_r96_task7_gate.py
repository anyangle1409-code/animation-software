import unittest

from original_v1_r96_task7_gate import (
    DEFAULT_REQUIRED_ISSUES,
    evaluate_task7_gate,
    validate_declaration,
)

SHA = "a" * 64


class R96Task7GateTests(unittest.TestCase):
    def test_declaration_requires_exact_parent_and_corrective_only_scope(self):
        record = {
            "declared_before_edit": True,
            "source_candidate_sha256": SHA,
            "left_owned_vertex_ids": [1, 3, 5],
            "mirror_of_strict_left_vertex_ids": [2, 4, 6],
            "theta0_deg": 40.0,
            "theta1_deg": 150.0,
            "allowed_change": "rest-space displacement vectors (shape key data) only",
        }
        self.assertEqual(validate_declaration(record, SHA), [])
        self.assertIn(
            "declaration_parent_mismatch",
            validate_declaration(record, "b" * 64),
        )

    def test_gate_blocks_numerically_clean_candidate_without_visual_approval(self):
        comparison = {
            "status": "IMPROVED",
            "regression_count": 0,
            "baseline_failed_checks": 2,
            "candidate_failed_checks": 2,
        }
        solve = {
            "source_candidate_sha256": SHA,
            "max_abs_delta_m": 0.02,
            "mask_file": "mask.json",
        }
        result = evaluate_task7_gate(
            comparison, solve, {}, expected_parent_sha256=SHA
        )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["task7_gate_pass"])
        self.assertTrue(
            any(reason.startswith("visual_review_") for reason in result["reasons"])
        )

    def test_gate_blocks_any_existing_comparator_regression(self):
        comparison = {
            "status": "REGRESSION",
            "regression_count": 1,
            "baseline_failed_checks": 2,
            "candidate_failed_checks": 3,
        }
        solve = {
            "source_candidate_sha256": SHA,
            "max_abs_delta_m": 0.01,
            "mask_file": "mask.json",
        }
        visual = self._passing_visual()
        result = evaluate_task7_gate(
            comparison, solve, visual, expected_parent_sha256=SHA
        )
        self.assertIn("numerical_comparison_regression", result["reasons"])
        self.assertIn("candidate_failed_checks_increased", result["reasons"])

    def test_gate_passes_only_with_numeric_and_visual_evidence(self):
        comparison = {
            "status": "IMPROVED",
            "regression_count": 0,
            "baseline_failed_checks": 2,
            "candidate_failed_checks": 1,
        }
        solve = {
            "source_candidate_sha256": SHA,
            "max_abs_delta_m": 0.012,
            "mask_file": "mask.json",
        }
        result = evaluate_task7_gate(
            comparison,
            solve,
            self._passing_visual(),
            expected_parent_sha256=SHA,
        )
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["task7_gate_pass"])
        self.assertFalse(result["production_approved"])

    @staticmethod
    def _passing_visual():
        return {
            "production_path_rendered": True,
            "visual_pass": True,
            "symmetry_pass": True,
            "arc_continuity_pass": True,
            "whole_body_regression_pass": True,
            "real_human_reference_checked": True,
            "critical_high_remaining": 0,
            "reviewed_issue_ids": list(DEFAULT_REQUIRED_ISSUES),
        }


if __name__ == "__main__":
    unittest.main()
