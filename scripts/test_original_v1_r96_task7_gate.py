import unittest

from original_v1_r96_task7_gate import (
    DEFAULT_REQUIRED_ISSUES,
    evaluate_task7_gate,
    validate_declaration,
    validate_visual_review,
)

SHA = "a" * 64
CANDIDATE_SHA = "c" * 64
COMMIT_SHA = "b" * 40
RENDER_SHA = "d" * 64


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

    def test_visual_review_requires_candidate_bound_issue_evidence(self):
        visual = self._passing_visual()
        visual["issue_reviews"][0]["evidence_paths"] = []
        reasons = validate_visual_review(visual, expected_parent_sha256=SHA)
        self.assertIn(
            "visual_review_issue_evidence_missing:" + DEFAULT_REQUIRED_ISSUES[0],
            reasons,
        )

    def test_visual_review_requires_exact_parent(self):
        visual = self._passing_visual()
        reasons = validate_visual_review(
            visual, expected_parent_sha256="e" * 64
        )
        self.assertIn("visual_review_parent_mismatch", reasons)

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
        self.assertEqual(result["candidate_sha256"], CANDIDATE_SHA)

    @staticmethod
    def _passing_visual():
        issue_reviews = []
        for index, issue_id in enumerate(DEFAULT_REQUIRED_ISSUES):
            issue_reviews.append(
                {
                    "id": issue_id,
                    "status": "PASS",
                    "evidence_paths": [f"review/{issue_id}.png"],
                    "human_evidence_ids": ["HE-TEST-001"],
                    "review_note": "Test fixture: required issue explicitly reviewed.",
                }
            )
        return {
            "schema_version": 1,
            "status": "TASK7_VISUAL_REVIEW",
            "source_candidate_sha256": SHA,
            "candidate_sha256": CANDIDATE_SHA,
            "source_git_commit": COMMIT_SHA,
            "renders": [
                {
                    "path": "review/press_top_front.png",
                    "sha256": RENDER_SHA,
                    "pose": "press_top",
                    "view": "front",
                }
            ],
            "issue_reviews": issue_reviews,
            "production_path_rendered": True,
            "visual_pass": True,
            "symmetry_pass": True,
            "arc_continuity_pass": True,
            "whole_body_regression_pass": True,
            "real_human_reference_checked": True,
            "required_issue_failures_remaining": 0,
        }


if __name__ == "__main__":
    unittest.main()
