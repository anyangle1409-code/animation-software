import copy
import json
from pathlib import Path
import unittest

from experiments.anatomical_muscles import visual_qa


ROOT = Path(__file__).resolve().parents[3]
QA_PATH = ROOT / "experiments/anatomical_muscles/current_w8_visual_qa.json"
SEED_PATH = ROOT / "docs/ORIGINAL_V1_MUSCLE_REGISTRY_SEED_20261022.json"
CONTRACT_PATH = ROOT / "experiments/anatomical_muscles/exercise_contracts.json"


class VisualQATests(unittest.TestCase):
    def setUp(self):
        self.qa = json.loads(QA_PATH.read_text())
        self.seed = json.loads(SEED_PATH.read_text())
        self.contracts = json.loads(CONTRACT_PATH.read_text())

    def test_current_review_is_structurally_valid(self):
        self.assertEqual(visual_qa.validate(self.qa, self.seed, self.contracts), [])

    def test_visual_review_cannot_claim_native_validation_or_causation(self):
        bad = copy.deepcopy(self.qa)
        bad["blender_executed"] = True
        bad["findings"][0]["causal_conclusion"] = "bad weights"
        errors = visual_qa.validate(bad, self.seed, self.contracts)
        self.assertTrue(any("Blender" in error for error in errors))
        self.assertTrue(any("causal" in error for error in errors))

    def test_unknown_muscle_and_phase_references_are_rejected(self):
        bad = copy.deepcopy(self.qa)
        bad["findings"][0]["affected_muscle_ids"] = ["hgpt.muscle.unknown.L"]
        bad["findings"][0]["exercise_phase_refs"] = [
            {"exercise_id": "hgpt.exercise.biceps_curl.bilateral.v1", "phase_id": "unknown"}
        ]
        errors = visual_qa.validate(bad, self.seed, self.contracts)
        self.assertTrue(any("unknown muscle" in error for error in errors))
        self.assertTrue(any("unknown exercise phase" in error for error in errors))

    def test_evidence_metadata_is_pinned(self):
        bad = copy.deepcopy(self.qa)
        bad["evidence_images"][0]["sha256"] = "unverified"
        self.assertTrue(visual_qa.validate(bad, self.seed, self.contracts))


if __name__ == "__main__":
    unittest.main()
