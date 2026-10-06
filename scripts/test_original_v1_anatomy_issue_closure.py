"""Tests for candidate-bound Critical/High anatomy issue closure evidence."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import original_v1_anatomy_issue_closure as closure


class AnatomyIssueClosureTests(unittest.TestCase):
    def fixture(self, root: Path):
        human = {
            "schema_version": 1,
            "asset": "HomeGymPT_Male_ORIGINAL_v1",
            "entries": [{"id": "HE-TEST-001", "review_status": "verified"}],
        }
        (root / "ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json").write_text(json.dumps(human))

        reproduction = root / "reproduction.png"
        visual = root / "visual.png"
        numeric = root / "numeric.json"
        regression = root / "regression.json"
        for path, payload in (
            (reproduction, "repro"),
            (visual, "visual"),
            (numeric, "{}"),
            (regression, "{}"),
        ):
            path.write_text(payload)

        sha = "a" * 64
        issue = {
            "id": "WB-TEST-999",
            "region": "fixture transition",
            "severity": "Critical",
            "state": "Fixed",
            "candidate": {"revision": "r99", "sha256": sha},
            "reproduction": {
                "poses": ["fixture_pose"],
                "views": ["fixture_view"],
                "description": "Fixture reproduction.",
            },
            "evidence_paths": ["reproduction.png"],
            "human_evidence_ids": ["HE-TEST-001"],
            "evidence_gap": None,
            "defect": "Fixture anatomy defect.",
            "acceptance": "Fixture closure criterion.",
            "closure_evidence": ["closure.json"],
        }
        receipt = {
            "schema_version": 1,
            "status": closure.CLOSURE_STATUS,
            "production_approved": False,
            "issue_id": issue["id"],
            "candidate_revision": "r99",
            "candidate_sha256": sha,
            "source_git_commit": "b" * 40,
            "production_path_rendered": True,
            "visual_pass": True,
            "numerical_pass": True,
            "whole_body_regression_pass": True,
            "real_human_reference_checked": True,
            "closure_decision": "Fixed",
            "visual_evidence": [{"path": "visual.png", "sha256": closure.digest(visual), "passed": True}],
            "numerical_evidence": [{"path": "numeric.json", "sha256": closure.digest(numeric), "passed": True}],
            "regression_evidence": [{"path": "regression.json", "sha256": closure.digest(regression), "passed": True}],
            "human_evidence_ids": ["HE-TEST-001"],
            "review_note": "Fixture issue was explicitly reviewed against all required evidence.",
        }
        (root / "closure.json").write_text(json.dumps(receipt))
        ledger = {
            "schema_version": 1,
            "asset": "HomeGymPT_Male_ORIGINAL_v1",
            "issues": [issue],
        }
        return ledger, human, receipt

    def test_valid_structured_closure_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ledger, human, _ = self.fixture(root)
            self.assertEqual(closure.verify_closed_issues(root, ledger, human), [])

    def test_visual_or_regression_failure_blocks_closure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ledger, human, receipt = self.fixture(root)
            receipt["visual_pass"] = False
            receipt["whole_body_regression_pass"] = False
            (root / "closure.json").write_text(json.dumps(receipt))
            errors = "\n".join(closure.verify_closed_issues(root, ledger, human))
            self.assertIn("visual_pass must be true", errors)
            self.assertIn("whole_body_regression_pass must be true", errors)

    def test_tampered_nested_evidence_blocks_closure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ledger, human, _ = self.fixture(root)
            (root / "visual.png").write_text("tampered")
            errors = "\n".join(closure.verify_closed_issues(root, ledger, human))
            self.assertIn("hash differs", errors)

    def test_unverified_human_reference_blocks_closure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ledger, human, _ = self.fixture(root)
            human["entries"][0]["review_status"] = "needs_review"
            (root / "ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json").write_text(json.dumps(human))
            errors = "\n".join(closure.verify_closed_issues(root, ledger, human))
            self.assertIn("unknown/unverified human evidence", errors)

    def test_open_issue_is_not_falsely_treated_as_a_closure_error(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ledger, human, _ = self.fixture(root)
            ledger["issues"][0]["state"] = "Open"
            ledger["issues"][0]["closure_evidence"] = []
            self.assertEqual(closure.verify_closed_issues(root, ledger, human), [])
            # The separate issue-ledger blocker gate is responsible for Open state.


if __name__ == "__main__":
    unittest.main()
