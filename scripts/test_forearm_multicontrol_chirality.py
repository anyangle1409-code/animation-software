#!/usr/bin/env python3
"""Mutation tests: shared anatomical radius/ulna to three forearm controls."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))
import forearm_multicontrol_chirality as m
import anatomical_runtime_chirality_gate as base


class ForearmMulticontrolChiralityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {k: json.loads((ROOT / path).read_text(encoding="utf-8"))
                       for k, path in base.SOURCE.items()}

    def records(self):
        x = copy.deepcopy(self.sources)
        return x["fitted_skeleton"], x["runtime_skeleton"], x["alias_inventory"]

    def test_exact_twelve_extra_links_and_four_reference_bones(self):
        result = m.from_repository()
        self.assertEqual(result["additional_crossed_alias_links"], 12)
        self.assertEqual(result["independent_bone_id_count"], 4)
        self.assertEqual(result["total_crossed_side_links_when_combined"], 130)
        self.assertEqual(len(result["source_sha256"]), 3)
        self.assertEqual(len(result["evidence"]), 12)
        self.assertEqual({v["anatomical_reference"] for v in result["evidence"]},
                         {"radius_left", "radius_right", "ulna_left", "ulna_right"})
        self.assertFalse(result["source_anatomical_bones_verified"])
        self.assertFalse(result["twist_motion_or_pronation_supination_verified"])
        self.assertFalse(result["rig_export_approved"])

    def test_all_eight_twist_helper_links_are_crossed(self):
        evidence = m.from_repository()["evidence"]
        twist = [x for x in evidence if "tw" in x["legacy_alias"]]
        self.assertEqual(len(twist), 8)  # 2 bones x 2 sides x 2 helpers
        for row in twist:
            self.assertEqual(row["status"], "OPPOSITE_PHYSICAL_SIDE_IN_NAME_ONLY_ALIAS")
            if row["anatomical_reference"].endswith("_left"):
                self.assertTrue(row["opposite_side_candidate"].endswith("_r"))
                self.assertGreater(row["candidate_lateral_m"], 0)
            else:
                self.assertTrue(row["opposite_side_candidate"].endswith("_l"))
                self.assertLess(row["candidate_lateral_m"], 0)

    def test_alias_and_runtime_sources_unchanged_by_inspection(self):
        before = [hashlib.sha256((ROOT / f).read_bytes()).hexdigest()
                  for f in base.SOURCE.values()]
        a, b, c = self.records()
        snapshot = json.dumps([a, b, c], sort_keys=True)
        m.report(a, b, c)
        self.assertEqual(json.dumps([a, b, c], sort_keys=True), snapshot)
        self.assertEqual(before, [hashlib.sha256((ROOT / f).read_bytes()).hexdigest()
                                  for f in base.SOURCE.values()])

    def test_wrong_multicontrol_alias_rejected(self):
        fit, runtime, aliases = self.records()
        row = next(x for x in aliases["aliases"] if x["anatomical_id"] == "radius_left")
        row["current_rig"] = ["forearm_r", "forearm_tw0_r", "forearm_tw1_r"]
        with self.assertRaisesRegex(ValueError, "Unexpected multi-control map"):
            m.report(fit, runtime, aliases)

    def test_missing_twist_helper_rejected(self):
        fit, runtime, aliases = self.records()
        next(x for x in runtime["bones"] if x["name"] == "forearm_tw1_r")["name"] = "unknown_spare_runtime_control"
        with self.assertRaisesRegex(ValueError, "Missing forearm or twist helper"):
            m.report(fit, runtime, aliases)

    def test_misplaced_twist_helper_rejected(self):
        fit, runtime, aliases = self.records()
        bone = next(x for x in runtime["bones"] if x["name"] == "forearm_tw0_r")
        bone["head"][0] = -0.215
        bone["tail"][0] = -0.215
        with self.assertRaisesRegex(ValueError, "physical side"):
            m.report(fit, runtime, aliases)

    def test_wrong_source_anatomical_side_rejected(self):
        fit, runtime, aliases = self.records()
        fit["bones"]["ulna_left"]["head_m"][0] = -0.2
        fit["bones"]["ulna_left"]["tail_m"][0] = -0.2
        with self.assertRaisesRegex(ValueError, "Source radius/ulna side"):
            m.report(fit, runtime, aliases)

    def test_unmarked_collapsed_relationship_rejected(self):
        fit, runtime, aliases = self.records()
        row = next(x for x in aliases["aliases"] if x["anatomical_id"] == "ulna_right")
        row["relationship"] = "independent_measured_anatomical_ulna"
        with self.assertRaisesRegex(ValueError, "shared radius/ulna"):
            m.report(fit, runtime, aliases)

    def test_cli_serialization_nonmutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "forearm.json"
            script = ROOT / "scripts/anatomy_fit/forearm_multicontrol_chirality.py"
            result = subprocess.run([sys.executable, str(script), "--out", str(dest)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(dest.read_text())
            self.assertEqual(report["additional_crossed_alias_links"], 12)
            self.assertFalse(report["source_or_runtime_modified"])


if __name__ == "__main__":
    unittest.main()
