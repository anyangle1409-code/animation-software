import json
import subprocess
import unittest
from pathlib import Path

from validate_original_o1_generator import validate_generator_policy


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "ORIGINAL_V1_GENERATOR_PROVENANCE.json"
GENERATOR = "scripts/generate_original_v1_clean_scaffold.py"


class O1GeneratorProvenanceTests(unittest.TestCase):
    def test_committed_generator_matches_frozen_policy(self):
        policy = json.loads(POLICY_PATH.read_text())
        committed = subprocess.check_output(
            ["git", "rev-parse", f"HEAD:{GENERATOR}"],
            cwd=ROOT,
            text=True,
        ).strip()
        self.assertEqual(validate_generator_policy(policy, committed), [])

    def test_rejects_generator_blob_drift(self):
        policy = json.loads(POLICY_PATH.read_text())
        self.assertIn(
            "generator blob mismatch",
            validate_generator_policy(policy, "0" * 40),
        )

    def test_rejects_pinned_source_drift_and_dirty_generator(self):
        policy = json.loads(POLICY_PATH.read_text())
        committed = policy["generator_blob_sha"]
        changed = {**policy, "pinned_profile_commit": "0" * 40}
        self.assertIn(
            "pinned profile commit",
            validate_generator_policy(changed, committed),
        )
        self.assertIn(
            "generator working tree modified",
            validate_generator_policy(policy, committed, dirty=True),
        )


if __name__ == "__main__":
    unittest.main()
